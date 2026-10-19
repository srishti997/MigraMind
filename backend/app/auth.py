"""Opaque database sessions; no authentication tokens in browser storage or logs."""
import hashlib
import os
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from threading import Lock
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.exc import IntegrityError

hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2, type=Type.ID)
DUMMY_HASH = hasher.hash(secrets.token_urlsafe(32))
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
class ConsentIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    contact_id: int = Field(gt=0)
    scope: str = Field(pattern='^support_card$')
    confirmed: bool
class Limiter:
    """Process-local sliding windows. Multi-worker deployments need a shared store."""
    def __init__(self): self.windows = defaultdict(deque); self.lock = Lock()
    def check(self, key, limit=10):
        with self.lock:
            stamp = time.monotonic()
            for k in list(self.windows):
                if not self.windows[k] or self.windows[k][-1] < stamp-900: del self.windows[k]
            window = self.windows[key]
            if len(window) >= limit: raise HTTPException(429, 'Too many attempts. Try again later.', headers={'Retry-After':'900'})
            window.append(stamp)
    def clear(self): self.windows.clear()

class Authentication:
    def __init__(self, app, db, User, LoginSession, Consent, Contact, models):
        self.limiter = Limiter()
        secure = os.getenv('APP_ENV', 'development') == 'production'
        cookie = '__Host-migramind_session' if secure else 'migramind_session'
        origins = set(os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(','))
        ttl = int(os.getenv('SESSION_HOURS', '12'))
        if ttl < 1 or ttl > 168: raise RuntimeError('SESSION_HOURS must be 1–168')
        def session(request, s):
            raw = request.cookies.get(cookie, '')
            row = s.query(LoginSession).filter_by(token_digest=digest(raw)).first() if raw else None
            return row if row and datetime.fromisoformat(row.expires_at) > now() else None
        def csrf(request, row):
            if request.headers.get('origin') not in origins:
                raise HTTPException(403, 'Request origin is not allowed')
            token = request.headers.get('x-csrf-token', '')
            if not row or not secrets.compare_digest(token, row.csrf_token): raise HTTPException(403, 'Refresh the page and try again')
        def require_user(request: Request, s=Depends(db)):
            row = session(request, s)
            user = s.get(User, row.user_id) if row and row.user_id else None
            if not user: raise HTTPException(401, 'Sign in to continue')
            if request.method not in ('GET','HEAD','OPTIONS'): csrf(request, row)
            return user
        self.require_user = require_user
        def public(user): return {'id':user.id,'email':user.email,'display_name':user.display_name,'created_at':user.created_at} if user else None
        def issue(s, response, user=None, previous=None):
            if previous: s.delete(previous)
            raw = secrets.token_urlsafe(32)
            row = LoginSession(user_id=user.id if user else None, token_digest=digest(raw), csrf_token=secrets.token_urlsafe(32), expires_at=(now()+timedelta(hours=ttl if user else 1)).isoformat())
            s.add(row); s.commit()
            response.set_cookie(cookie, raw, httponly=True, secure=secure, samesite='lax', path='/', max_age=ttl*3600 if user else 3600)
            return {'user':public(user),'csrf_token':row.csrf_token}
        def attempts(request, email=''):
            self.limiter.check(('ip', request.client.host if request.client else 'unknown'), 30)
            if email: self.limiter.check(('account',digest(email)),10)
        @app.get('/api/auth/session')
        def bootstrap(request: Request, response: Response, s=Depends(db)):
            row = session(request,s)
            if row:
                return {'user':public(s.get(User,row.user_id)) if row.user_id else None,'csrf_token':row.csrf_token}
            attempts(request)
            # Expired sessions are removed; opaque identifiers never reused on login.
            s.query(LoginSession).filter(LoginSession.expires_at < now().isoformat()).delete()
            return issue(s,response)
        @app.post('/api/auth/register', status_code=201)
        def register(data:Registration, request:Request, response:Response, s=Depends(db)):
            attempts(request,data.email); previous=session(request,s); csrf(request,previous)
            password_hash=hasher.hash(data.password)
            user=User(email=data.email,display_name=data.display_name,password_hash=password_hash,created_at=now().isoformat())
            s.add(user)
            try: s.flush()
            except IntegrityError:
                s.rollback(); raise HTTPException(400,'Unable to create an account with those details')
            return issue(s,response,user,previous)
        @app.post('/api/auth/login')
        def login(data:Credentials, request:Request, response:Response, s=Depends(db)):
            attempts(request,data.email); previous=session(request,s); csrf(request,previous)
            user=s.query(User).filter_by(email=data.email).first()
            try: valid=hasher.verify(user.password_hash if user else DUMMY_HASH,data.password)
            except (VerificationError,InvalidHashError): valid=False
            if not user or not valid: raise HTTPException(401,'Email or password is incorrect')
            if hasher.check_needs_rehash(user.password_hash): user.password_hash=hasher.hash(data.password)
            return issue(s,response,user,previous)
        @app.post('/api/auth/logout',status_code=204)
        def logout(request:Request,response:Response,user=Depends(require_user),s=Depends(db)):
            s.delete(session(request,s));s.commit()
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
