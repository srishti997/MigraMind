from datetime import date, datetime, timezone
from typing import Literal
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from .assistance_defaults import DEFAULT_HELP_MESSAGE
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .security import SecuritySettings, PrivateBoundary
from .deployment import database_ready, DemoBoundary, operation_event
from pydantic import BaseModel, Field, ConfigDict, field_validator
from .phone import dialable_phone
from sqlalchemy import create_engine, event, String, Integer, Text, CheckConstraint, JSON, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

load_dotenv()
security = SecuritySettings.load()
url = security.database_url
engine = create_engine(url, connect_args={'check_same_thread': False} if url.startswith('sqlite') else {'connect_timeout':5},
    **({} if url.startswith('sqlite') else {'pool_timeout':5, 'pool_pre_ping':True}), echo=False, hide_parameters=True)
if url.startswith('sqlite'):
    @event.listens_for(engine, 'connect')
    def enforce_sqlite_foreign_keys(connection, _):
        connection.execute('PRAGMA foreign_keys=ON')
SessionLocal = sessionmaker(bind=engine)
class Base(DeclarativeBase): pass
class DemoDeployment(Base):
    __tablename__ = 'demo_deployments'
    id: Mapped[int] = mapped_column(primary_key=True)
    fixture_version: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[str] = mapped_column(String(40))
class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    display_name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[str] = mapped_column(String(40))
class LoginSession(Base):
    __tablename__ = 'login_sessions'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True, index=True)
    token_digest: Mapped[str] = mapped_column(String(64), unique=True)
    csrf_token: Mapped[str] = mapped_column(String(100))
    expires_at: Mapped[str] = mapped_column(String(40), index=True)
class Owned:
    # NULL means preserved, unclaimed pre-authentication records.
    owner_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True, index=True)
from .prospective_models import collection_models
DailyCheckin, CheckinRevision = collection_models(Base, Owned)

class SharingConsent(Owned, Base):
    __tablename__ = 'sharing_consents'
    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True)
    scope: Mapped[str] = mapped_column(String(30))
    granted_at: Mapped[str] = mapped_column(String(40))
    revoked_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
class Episode(Owned, Base):
    __tablename__ = 'episodes'
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[str] = mapped_column(String(10))
    severity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trigger: Mapped[str] = mapped_column(String(100))
    notes: Mapped[str] = mapped_column(Text)
    started_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ended_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    timezone_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pain_location: Mapped[str] = mapped_column(String(200), default='')
    symptoms: Mapped[list] = mapped_column(JSON, default=list)
    functional_impact: Mapped[str] = mapped_column(String(100), default='')
    medications: Mapped[list] = mapped_column(JSON, default=list)
    attack_session_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
class Wellness(Owned, Base):
    __tablename__ = 'wellness'
    __table_args__ = (UniqueConstraint('owner_id', 'date', name='wellness_owner_date'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[str] = mapped_column(String(10))
    timezone_name: Mapped[str] = mapped_column(String(100))
    recorded_at: Mapped[str] = mapped_column(String(40))
    sleep_hours: Mapped[float | None] = mapped_column(nullable=True)
    sleep_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stress: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hydration_ml: Mapped[int | None] = mapped_column(Integer, nullable=True)
    missed_meals: Mapped[bool | None] = mapped_column(nullable=True)
    screen_hours: Mapped[float | None] = mapped_column(nullable=True)
    menstrual_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    episode_observation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    observation_recorded_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
class EarlySymptom(Owned, Base):
    __tablename__ = 'early_symptoms'
    id: Mapped[int] = mapped_column(primary_key=True)
    symptom: Mapped[str] = mapped_column(String(200))
    onset_at: Mapped[str] = mapped_column(String(40))
    timezone_name: Mapped[str] = mapped_column(String(100))
    recorded_at: Mapped[str] = mapped_column(String(40))
    notes: Mapped[str] = mapped_column(Text, default='')
class Contact(Owned, Base):
    __tablename__ = 'contacts'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    relationship: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(32))
class Profile(Owned, Base):
    __tablename__ = 'profiles'
    __table_args__ = (UniqueConstraint('owner_id', name='profiles_owner'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), default='Alex')
    support: Mapped[str] = mapped_column(Text, default='Please keep the room quiet and dim. Ask before calling or visiting.')
    avoid: Mapped[str] = mapped_column(Text, default='Bright lights, strong fragrances, and loud sounds.')
    communication: Mapped[str] = mapped_column(Text, default='')
    environment: Mapped[str] = mapped_column(Text, default='')
class AttackSession(Owned, Base):
    __tablename__ = 'attack_sessions'
    __table_args__ = (CheckConstraint('(ended_at IS NULL AND active_slot = 1) OR (ended_at IS NOT NULL AND active_slot IS NULL)', name='session_state'), UniqueConstraint('owner_id','active_slot',name='session_owner_active'))
    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[str] = mapped_column(String(40))
    ended_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    active_slot: Mapped[int | None] = mapped_column(Integer, nullable=True)
class SupportPreferences(Owned, Base):
    __tablename__ = 'support_preferences'
    __table_args__ = (UniqueConstraint('owner_id', name='support_preferences_owner'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    preferred_contact_id: Mapped[int | None] = mapped_column(ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True)
    communication_method: Mapped[str] = mapped_column(String(20), default='none')
    preferred_actions: Mapped[list] = mapped_column(JSON, default=list)
    large_text: Mapped[bool] = mapped_column(Boolean, default=False)
    reduce_motion: Mapped[bool] = mapped_column(Boolean, default=False)
    simplified_view: Mapped[bool] = mapped_column(Boolean, default=False)
    use_feedback: Mapped[bool] = mapped_column(Boolean, default=False)
    ranking_mode: Mapped[str] = mapped_column(String(20), default='adaptive')
    help_message: Mapped[str] = mapped_column(String(400), default=DEFAULT_HELP_MESSAGE)
    emergency_number: Mapped[str] = mapped_column(String(6), default='112')
class SupportFeedback(Owned, Base):
    __tablename__ = 'support_feedback'
    __table_args__ = (UniqueConstraint('session_id','action_id',name='one_rating_per_session_action'),
        CheckConstraint("action_id IN ('call_contact','prepare_sms','support_card')",name='nonemergency_feedback_action'))
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey('attack_sessions.id'))
    action_id: Mapped[str] = mapped_column(String(30))
    helpful: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[str] = mapped_column(String(40))
from .tracking_schemas import EpisodeIn, episode_values
class ContactIn(BaseModel):
    model_config=ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    relationship: str = Field(max_length=100)
    phone: str = Field(min_length=1, max_length=32)
    @field_validator('phone')
    @classmethod
    def phone_syntax(cls,value):
        dialable_phone(value)
        return value
class ProfileIn(BaseModel):
    model_config=ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    support: str = Field(max_length=3000)
    avoid: str = Field(max_length=3000)
    communication: str = Field(default='', max_length=3000)
    environment: str = Field(default='', max_length=2000)
def db():
    with SessionLocal() as session: yield session
@asynccontextmanager
async def lifespan(application):
    if security.synthetic_demo and not database_ready(engine, True):
        operation_event('startup_blocked')
        raise RuntimeError('Synthetic demonstration database is not initialized at the required schema')
    operation_event('startup_ready')
    yield

app = FastAPI(title='MigraMind API', description='Account-isolated local prototype. Not production hardened. No emergency dispatch.', lifespan=lifespan,
    docs_url=None if security.production else '/docs', redoc_url=None if security.production else '/redoc',
    openapi_url=None if security.production else '/openapi.json')
app.state.synthetic_demo = security.synthetic_demo
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
@app.exception_handler(RequestValidationError)
async def private_validation_errors(request, error):
    # Do not echo passwords, health fields, or raw validation inputs.
    return JSONResponse(status_code=422, content={'detail':[
        {'loc':[item['loc'][0]], 'msg':'Invalid or unexpected value', 'type':item['type']} for item in error.errors()]})
@app.exception_handler(SQLAlchemyError)
async def private_database_errors(request, error):
    # SQL exceptions may contain bound health values: never print their text.
    return JSONResponse(status_code=503, content={'detail':'The database could not complete this request. Try again.'})
app.add_middleware(CORSMiddleware, allow_origins=list(security.origins), allow_methods=['GET','POST','PUT','DELETE'], allow_headers=['Content-Type','X-CSRF-Token'], allow_credentials=True)
app.add_middleware(DemoBoundary, enabled=security.synthetic_demo, probe=lambda: database_ready(engine, True))
app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(security.hosts), www_redirect=False)
from .auth import Authentication, owned, owned_row
# Account deletion: feedback/episodes before referenced sessions; preferences before contacts.
auth = Authentication(app, db, User, LoginSession, SharingConsent, Contact,
    [CheckinRevision, DailyCheckin, SupportFeedback, Episode, SupportPreferences, Wellness, EarlySymptom, Profile, AttackSession, Contact], settings=security)
require_user = auth.require_user
@app.get('/api/health')
def health(): return {'status':'ok'}
@app.get('/api/ready')
def ready():
    available = database_ready(engine, security.synthetic_demo)
    if not available:
        operation_event('readiness_unavailable')
    return JSONResponse({'status': 'ready' if available else 'unavailable'}, status_code=200 if available else 503)
@app.get('/api/episodes')
def episodes(s: Session = Depends(db), user=Depends(require_user)): return owned(s,Episode,user).order_by(Episode.date.desc(), Episode.id.desc()).all()
@app.post('/api/episodes', status_code=201)
def add_episode(data: EpisodeIn, s: Session = Depends(db), user=Depends(require_user)):
    values = episode_values(data)
    if data.attack_session_id is not None and not owned(s,AttackSession,user).filter_by(id=data.attack_session_id).first(): raise HTTPException(422, 'Attack session not found')
    row = Episode(owner_id=user.id,**values); s.add(row); s.commit(); s.refresh(row); return row
@app.put('/api/episodes/{id}')
def edit_episode(id: int, data: EpisodeIn, s: Session = Depends(db), user=Depends(require_user)):
    row = owned_row(s,Episode,id,user)
    if not row: raise HTTPException(404, 'Episode not found')
    if data.attack_session_id is not None and not owned(s,AttackSession,user).filter_by(id=data.attack_session_id).first(): raise HTTPException(422, 'Attack session not found')
    for k,v in episode_values(data).items(): setattr(row,k,v)
    s.commit(); s.refresh(row); return row
@app.delete('/api/episodes/{id}', status_code=204)
def delete_episode(id: int, s: Session = Depends(db), user=Depends(require_user)):
    row=owned_row(s,Episode,id,user)
    if not row: raise HTTPException(404,'Episode not found')
    s.delete(row); s.commit()
@app.get('/api/contacts')
def contacts(s: Session = Depends(db), user=Depends(require_user)): return owned(s,Contact,user).all()
@app.post('/api/contacts', status_code=201)
def add_contact(data: ContactIn, s: Session = Depends(db), user=Depends(require_user)):
    row=Contact(owner_id=user.id,**data.model_dump()); s.add(row); s.commit(); s.refresh(row); return row
@app.put('/api/contacts/{id}')
def edit_contact(id: int, data: ContactIn, s: Session = Depends(db), user=Depends(require_user)):
    row=owned_row(s,Contact,id,user)
    if not row: raise HTTPException(404,'Contact not found')
    for k,v in data.model_dump().items(): setattr(row,k,v)
    s.commit(); s.refresh(row); return row
@app.delete('/api/contacts/{id}', status_code=204)
def delete_contact(id: int, s: Session = Depends(db), user=Depends(require_user)):
    row=owned_row(s,Contact,id,user)
    if not row: raise HTTPException(404,'Contact not found')
    owned(s,SupportPreferences,user).filter_by(preferred_contact_id=id).update({'preferred_contact_id':None})
    owned(s,SharingConsent,user).filter_by(contact_id=id).update({'contact_id':None,'revoked_at':datetime.now(timezone.utc).isoformat()})
    s.delete(row); s.commit()
@app.get('/api/profile')
def profile(s: Session = Depends(db), user=Depends(require_user)):
    row=owned(s,Profile,user).first()
    if not row and security.synthetic_demo: raise HTTPException(503, 'Demonstration unavailable')
    if not row: row=Profile(owner_id=user.id,name=user.display_name); s.add(row); s.commit(); s.refresh(row)
    return row
@app.put('/api/profile')
def save_profile(data: ProfileIn, s: Session = Depends(db), user=Depends(require_user)):
    row=owned(s,Profile,user).first()
    if not row: row=Profile(owner_id=user.id,name=user.display_name); s.add(row)
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(row,k,v)
    s.commit(); s.refresh(row); return row


def session_out(row):
    return {'id': row.id, 'started_at': row.started_at, 'ended_at': row.ended_at} if row else None

@app.get('/api/attack-sessions/current')
def current_session(s: Session = Depends(db), user=Depends(require_user)):
    return session_out(owned(s,AttackSession,user).order_by(AttackSession.id.desc()).first())

@app.get('/api/attack-sessions')
def attack_sessions(s: Session = Depends(db), user=Depends(require_user)):
    return [session_out(row) for row in owned(s,AttackSession,user).order_by(AttackSession.id.desc()).all()]

@app.post('/api/attack-sessions/start')
def start_session(s: Session = Depends(db), user=Depends(require_user)):
    row = owned(s,AttackSession,user).filter_by(active_slot=1).first()
    if row: return session_out(row)
    row = AttackSession(owner_id=user.id,started_at=datetime.now(timezone.utc).isoformat(), active_slot=1)
    s.add(row)
    try:
        s.commit()
    except IntegrityError:
        s.rollback()
        row = owned(s,AttackSession,user).filter_by(active_slot=1).first()
        if not row: raise HTTPException(409, 'Session changed; retry starting your session')
    s.refresh(row)
    return session_out(row)

@app.post('/api/attack-sessions/{id}/end')
def end_session(id: int, s: Session = Depends(db), user=Depends(require_user)):
    row = owned_row(s,AttackSession,id,user)
    if not row: raise HTTPException(404, 'Attack session not found')
    # Conditional update keeps repeat requests from changing the end timestamp.
    owned(s,AttackSession,user).filter(AttackSession.id == id, AttackSession.ended_at.is_(None)).update(
        {'ended_at': datetime.now(timezone.utc).isoformat(), 'active_slot': None})
    s.commit(); s.refresh(row)
    return session_out(row)

from .tracking_routes import register_tracking
register_tracking(app, db, Episode, Wellness, EarlySymptom, Contact, Profile, AttackSession, SupportPreferences, SupportFeedback, require_user, SharingConsent)


from .forecasting import ForecastServiceV1, ForecastResponseV1
forecast_service = ForecastServiceV1()

@app.get('/api/v1/forecast', response_model=ForecastResponseV1)
def forecast_status(user=Depends(require_user)):
    # Daily reports do not establish complete surveillance or validated prospective outcomes.
    # No request can train, load, or activate an experimental model.
    from fastapi.responses import JSONResponse
    return JSONResponse(forecast_service.status().model_dump(),headers={'Cache-Control':'no-store'})

from .support_routes import register_support
register_support(app, db, Contact, AttackSession, SupportPreferences, SupportFeedback, require_user)


@app.middleware('http')
async def private_api_responses(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response

from .prospective import register_collection
register_collection(app, db, DailyCheckin, CheckinRevision, Episode, Wellness, require_user, auth.limiter)
app.add_middleware(PrivateBoundary, production=security.production)
