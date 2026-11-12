"""Opaque database sessions; no authentication tokens in browser storage or logs."""
import hashlib
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from threading import Lock
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from .security import SecuritySettings
from .deployment import DEMO_EMAIL

hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2, type=Type.ID)
DUMMY_HASH = hasher.hash(secrets.token_urlsafe(32))
IDLE_TIMEOUT_MS = 30 * 60 * 1000
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

def epoch_ms(value):
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('Session clock must be timezone-aware')
    return (value - EPOCH) // timedelta(milliseconds=1)
def now(): return datetime.now(timezone.utc)
def digest(value): return hashlib.sha256(value.encode()).hexdigest()
def owned(s, model, user): return s.query(model).filter_by(owner_id=user.id)
def owned_row(s, model, id, user):
    row = owned(s, model, user).filter_by(id=id).first()
    if row is None: raise HTTPException(404, 'Record not found')
    return row
class Credentials(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128, repr=False)
    @field_validator('email')
    @classmethod
    def email_address(cls, value):
        value = value.strip().lower()
        if value.count('@') != 1 or not all(value.split('@')) or any(c.isspace() for c in value):
            raise ValueError('Enter an email address')
        return value
class Registration(Credentials):
    password: str = Field(min_length=12, max_length=128, repr=False)
    display_name: str = Field(min_length=1, max_length=100)
class AccountUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    display_name: str = Field(min_length=1, max_length=100)
class DeleteAccount(BaseModel):
    model_config = ConfigDict(extra='forbid')
    password: str = Field(min_length=1, max_length=128, repr=False)
    confirmation: str
class PasswordConfirmation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    password: str = Field(min_length=1, max_length=128, repr=False)
class ActivityIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    # A concurrency/retry precondition, never a trusted client clock.
    expected_last_activity_at_ms: int = Field(strict=True, ge=0, le=2**63-1)
class ConsentIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    contact_id: int = Field(gt=0)
    scope: str = Field(pattern='^support_card$')
    confirmed: StrictBool
class Limiter:
    """Process-local sliding windows. Multi-worker deployments need a shared store."""
    def __init__(self): self.windows = defaultdict(deque); self.lock = Lock()
    def check(self, key, limit=10):
        with self.lock:
            stamp = time.monotonic()
            for k in list(self.windows):
                while self.windows[k] and self.windows[k][0] <= stamp-900:
                    self.windows[k].popleft()
                if not self.windows[k]: del self.windows[k]
            window = self.windows[key]
            if len(window) >= limit: raise HTTPException(429, 'Too many attempts. Try again later.', headers={'Retry-After':'900'})
            window.append(stamp)
    def clear(self): self.windows.clear()

class Authentication:
    def __init__(self, app, db, User, LoginSession, Consent, Contact, models, settings=None, clock=None):
        self.limiter = Limiter()
        settings = settings or SecuritySettings.load()
        secure = settings.production
        cookie = '__Host-migramind_session' if secure else 'migramind_session'
        origins = set(settings.origins)
        ttl = settings.session_hours
        idle_enabled = settings.session_idle_timeout_enabled
        def current_time(): return clock() if clock is not None else now()
        def valid(row, stamp):
            if row is None: return False
            try:
                if datetime.fromisoformat(row.expires_at) <= stamp: return False
                if idle_enabled and row.user_id is not None:
                    activity = row.last_activity_at_ms
                    tick = epoch_ms(stamp)
                    if not isinstance(activity, int) or not 0 <= activity <= tick < activity + IDLE_TIMEOUT_MS:
                        return False
                return True
            except (ValueError, TypeError, OverflowError):
                return False
        def session(request, s, lock=False):
            raw = request.cookies.get(cookie, '')
            query = s.query(LoginSession).filter_by(token_digest=digest(raw))
            if lock: query = query.with_for_update()
            row = query.first() if raw else None
            return row if valid(row, current_time()) else None
        def csrf(request, row):
            if request.headers.get('origin') not in origins:
                raise HTTPException(403, 'Request origin is not allowed')
            token = request.headers.get('x-csrf-token', '')
            if not row or not secrets.compare_digest(token.encode('utf-8'), row.csrf_token.encode()): raise HTTPException(403, 'Refresh the page and try again')
        def require_user(request: Request, s=Depends(db)):
            row = session(request, s)
            user = s.get(User, row.user_id) if row and row.user_id else None
            if not user: raise HTTPException(401, 'Sign in to continue')
            if settings.synthetic_demo and user.email != DEMO_EMAIL:
                raise HTTPException(401, 'Sign in to the synthetic demonstration')
            # Cookies are shared across tabs. Bind reads to the mounted UI's session.
            token = request.headers.get('x-csrf-token', '').encode('utf-8')
            if request.method in ('GET','HEAD') and not secrets.compare_digest(token, row.csrf_token.encode()):
                raise HTTPException(401, 'Session changed. Sign in to continue')
            if request.method not in ('GET','HEAD','OPTIONS'): csrf(request, row)
            return user
        self.require_user = require_user
        def public(user): return {'id':user.id,'email':user.email,'display_name':user.display_name,'created_at':user.created_at} if user else None
        def state(row, user, stamp):
            result = {'user':public(user),'csrf_token':row.csrf_token,'expires_at':row.expires_at,'demo_mode':settings.synthetic_demo}
            if idle_enabled and user is not None:
                result.update(server_time=stamp.isoformat(), last_activity_at_ms=row.last_activity_at_ms,
                    idle_expires_at=min(datetime.fromisoformat(row.expires_at),
                        EPOCH+timedelta(milliseconds=row.last_activity_at_ms+IDLE_TIMEOUT_MS)).isoformat())
            return result
        def issue(s, response, user=None, previous=None):
            if previous: s.delete(previous)
            raw = secrets.token_urlsafe(32)
            stamp = current_time()
            row = LoginSession(user_id=user.id if user else None, token_digest=digest(raw), csrf_token=secrets.token_urlsafe(32), expires_at=(stamp+timedelta(hours=ttl if user else 1)).isoformat(),
                last_activity_at_ms=epoch_ms(stamp) if user else None)
            s.add(row); s.commit()
            response.set_cookie(cookie, raw, httponly=True, secure=secure, samesite='lax', path='/', max_age=ttl*3600 if user else 3600)
            return state(row,user,stamp)
        def attempts(request, email=''):
            self.limiter.check(('ip', request.client.host if request.client else 'unknown'), 30)
            if email: self.limiter.check(('account',digest(email)),10)
        @app.get('/api/auth/session')
        def bootstrap(request: Request, response: Response, s=Depends(db)):
            row = session(request,s)
            if row:
                return state(row,s.get(User,row.user_id) if row.user_id else None,current_time())
            attempts(request)
            # Expired sessions are removed; opaque identifiers never reused on login.
            s.query(LoginSession).filter(LoginSession.expires_at < current_time().isoformat()).delete()
            return issue(s,response)
        @app.post('/api/auth/activity')
        def activity(data:ActivityIn,request:Request,user=Depends(require_user),s=Depends(db)):
            if not idle_enabled: raise HTTPException(409,'Session activity tracking is disabled')
            user_id = user.id
            # End the preliminary read-only auth transaction. This route has no health writes.
            s.rollback()
            dialect = s.get_bind().dialect.name
            if dialect == 'sqlite': s.execute(text('BEGIN IMMEDIATE'))
            elif dialect != 'postgresql': raise HTTPException(503,'Session activity is unavailable')
            # PostgreSQL locks this row; SQLite already holds its writer reservation.
            # Recheck after waiting, including CSRF and expiry, never upsert on a miss.
            row = session(request,s,lock=dialect == 'postgresql')
            if not row or row.user_id != user_id or s.get(User,user_id) is None:
                raise HTTPException(401,'Sign in to continue')
            csrf(request,row)
            stamp = current_time()
            if not valid(row,stamp): raise HTTPException(401,'Sign in to continue')
            tick = epoch_ms(stamp)
            if row.last_activity_at_ms != data.expected_last_activity_at_ms or tick <= row.last_activity_at_ms:
                raise HTTPException(409,'Activity was not refreshed. Check the session before a new interaction.')
            row.last_activity_at_ms = tick
            result = {'server_time':stamp.isoformat(), 'expires_at':row.expires_at,
                'last_activity_at_ms':tick, 'idle_expires_at':min(datetime.fromisoformat(row.expires_at),
                    EPOCH+timedelta(milliseconds=tick+IDLE_TIMEOUT_MS)).isoformat()}
            s.commit()
            return result
        @app.post('/api/auth/register', status_code=201)
        def register(data:Registration, request:Request, response:Response, s=Depends(db)):
            if settings.synthetic_demo: raise HTTPException(403, 'Registration is disabled in the synthetic demonstration')
            previous=session(request,s); csrf(request,previous)
            attempts(request,data.email)
            password_hash=hasher.hash(data.password)
            user=User(email=data.email,display_name=data.display_name,password_hash=password_hash,created_at=now().isoformat())
            s.add(user)
            try: s.flush()
            except IntegrityError:
                s.rollback(); raise HTTPException(400,'Unable to create an account with those details')
            return issue(s,response,user,previous)
        @app.post('/api/auth/login')
        def login(data:Credentials, request:Request, response:Response, s=Depends(db)):
            if settings.synthetic_demo and data.email != DEMO_EMAIL:
                raise HTTPException(401, 'Use the provided synthetic demonstration account')
            previous=session(request,s); csrf(request,previous)
            attempts(request,data.email)
            user=s.query(User).filter_by(email=data.email).first()
            try: valid=hasher.verify(user.password_hash if user else DUMMY_HASH,data.password)
            except (VerificationError,InvalidHashError): valid=False
            if not user or not valid: raise HTTPException(401,'Email or password is incorrect')
            if not settings.synthetic_demo and hasher.check_needs_rehash(user.password_hash): user.password_hash=hasher.hash(data.password)
            return issue(s,response,user,previous)
        @app.post('/api/auth/logout',status_code=204)
        def logout(request:Request,response:Response,user=Depends(require_user),s=Depends(db)):
            s.delete(session(request,s));s.commit()
            response.delete_cookie(cookie,path='/',secure=secure,httponly=True,samesite='lax')
        @app.post('/api/auth/logout-all',status_code=204)
        def logout_all(data:PasswordConfirmation,request:Request,response:Response,user=Depends(require_user),s=Depends(db)):
            if settings.synthetic_demo:
                raise HTTPException(403,'Signing out all sessions is unavailable in the shared synthetic demonstration')
            attempts(request,user.email)
            try: valid=hasher.verify(user.password_hash,data.password)
            except (VerificationError,InvalidHashError): valid=False
            if not valid: raise HTTPException(400,'Password confirmation failed')
            s.query(LoginSession).filter_by(user_id=user.id).delete(synchronize_session=False)
            s.commit()
            response.delete_cookie(cookie,path='/',secure=secure,httponly=True,samesite='lax')
        @app.get('/api/account')
        def account(user=Depends(require_user)): return public(user)
        @app.put('/api/account')
        def update_account(data:AccountUpdate,user=Depends(require_user),s=Depends(db)):
            user.display_name=data.display_name;s.commit();return public(user)
        @app.delete('/api/account',status_code=204)
        def delete_account(data:DeleteAccount,request:Request,response:Response,user=Depends(require_user),s=Depends(db)):
            attempts(request,user.email)
            try: valid=hasher.verify(user.password_hash,data.password)
            except (VerificationError,InvalidHashError): valid=False
            if data.confirmation!='DELETE' or not valid: raise HTTPException(400,'Confirmation or password is incorrect')
            # Order is child-first. Unassigned legacy rows are never touched.
            owned(s,Consent,user).delete(synchronize_session=False)
            for model in models: owned(s,model,user).delete(synchronize_session=False)
            s.query(LoginSession).filter_by(user_id=user.id).delete(synchronize_session=False)
            s.delete(user);s.commit()
            response.delete_cookie(cookie,path='/',secure=secure,httponly=True,samesite='lax')
        @app.get('/api/account/consents')
        def consents(user=Depends(require_user),s=Depends(db)):return owned(s,Consent,user).all()
        @app.post('/api/account/consents',status_code=201)
        def grant(data:ConsentIn,user=Depends(require_user),s=Depends(db)):
            owned_row(s,Contact,data.contact_id,user)
            if not data.confirmed: raise HTTPException(422,'Explicit confirmation is required')
            row=Consent(owner_id=user.id,contact_id=data.contact_id,scope=data.scope,granted_at=now().isoformat())
            s.add(row);s.commit();s.refresh(row);return row
        @app.delete('/api/account/consents/{id}',status_code=204)
        def revoke(id:int,user=Depends(require_user),s=Depends(db)):
            row=owned_row(s,Consent,id,user);row.revoked_at=now().isoformat();s.commit()
