from datetime import date, datetime, timezone
from typing import Literal
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, String, Integer, Text, CheckConstraint, JSON, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

load_dotenv()
url = os.getenv('DATABASE_URL', 'sqlite:///./migramind.db')
engine = create_engine(url, connect_args={'check_same_thread': False} if url.startswith('sqlite') else {}, echo=False)
SessionLocal = sessionmaker(bind=engine)
class Base(DeclarativeBase): pass
class Episode(Base):
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
class Wellness(Base):
    __tablename__ = 'wellness'
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[str] = mapped_column(String(10), unique=True)
    timezone_name: Mapped[str] = mapped_column(String(100))
    recorded_at: Mapped[str] = mapped_column(String(40))
    sleep_hours: Mapped[float | None] = mapped_column(nullable=True)
    sleep_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stress: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hydration_ml: Mapped[int | None] = mapped_column(Integer, nullable=True)
    missed_meals: Mapped[bool | None] = mapped_column(nullable=True)
    screen_hours: Mapped[float | None] = mapped_column(nullable=True)
    menstrual_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
class EarlySymptom(Base):
    __tablename__ = 'early_symptoms'
    id: Mapped[int] = mapped_column(primary_key=True)
    symptom: Mapped[str] = mapped_column(String(200))
    onset_at: Mapped[str] = mapped_column(String(40))
    timezone_name: Mapped[str] = mapped_column(String(100))
    recorded_at: Mapped[str] = mapped_column(String(40))
    notes: Mapped[str] = mapped_column(Text, default='')
class Contact(Base):
    __tablename__ = 'contacts'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    relationship: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(32))
class Profile(Base):
    __tablename__ = 'profiles'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), default='Alex')
    support: Mapped[str] = mapped_column(Text, default='Please keep the room quiet and dim. Ask before calling or visiting.')
    avoid: Mapped[str] = mapped_column(Text, default='Bright lights, strong fragrances, and loud sounds.')
    communication: Mapped[str] = mapped_column(Text, default='')
class AttackSession(Base):
    __tablename__ = 'attack_sessions'
    __table_args__ = (CheckConstraint('(ended_at IS NULL AND active_slot = 1) OR (ended_at IS NOT NULL AND active_slot IS NULL)', name='session_state'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[str] = mapped_column(String(40))
    ended_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    active_slot: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
class SupportPreferences(Base):
    __tablename__ = 'support_preferences'
    id: Mapped[int] = mapped_column(primary_key=True)
    preferred_contact_id: Mapped[int | None] = mapped_column(ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True)
    communication_method: Mapped[str] = mapped_column(String(20), default='none')
    preferred_actions: Mapped[list] = mapped_column(JSON, default=list)
    large_text: Mapped[bool] = mapped_column(Boolean, default=False)
    reduce_motion: Mapped[bool] = mapped_column(Boolean, default=False)
    simplified_view: Mapped[bool] = mapped_column(Boolean, default=False)
    use_feedback: Mapped[bool] = mapped_column(Boolean, default=False)
    ranking_mode: Mapped[str] = mapped_column(String(20), default='adaptive')
class SupportFeedback(Base):
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
    name: str = Field(min_length=1, max_length=100)
    relationship: str = Field(max_length=100)
    phone: str = Field(min_length=3, max_length=32, pattern=r'^\+?[0-9 ()-]+$')
class ProfileIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    support: str = Field(max_length=3000)
    avoid: str = Field(max_length=3000)
    communication: str = Field(default='', max_length=3000)
def db():
    with SessionLocal() as session: yield session
app = FastAPI(title='MigraMind API', description='Single-user local synthetic demo. No emergency dispatch.')
app.add_middleware(CORSMiddleware, allow_origins=os.getenv('CORS_ORIGINS','http://localhost:5173').split(','), allow_methods=['GET','POST','PUT','DELETE'], allow_headers=['Content-Type'])
@app.get('/api/health')
def health(): return {'status':'ok'}
@app.get('/api/episodes')
def episodes(s: Session = Depends(db)): return s.query(Episode).order_by(Episode.date.desc(), Episode.id.desc()).all()
@app.post('/api/episodes', status_code=201)
def add_episode(data: EpisodeIn, s: Session = Depends(db)):
    values = episode_values(data)
    if data.attack_session_id is not None and not s.get(AttackSession, data.attack_session_id): raise HTTPException(422, 'Attack session not found')
    row = Episode(**values); s.add(row); s.commit(); s.refresh(row); return row
@app.put('/api/episodes/{id}')
def edit_episode(id: int, data: EpisodeIn, s: Session = Depends(db)):
    row = s.get(Episode,id)
    if not row: raise HTTPException(404, 'Episode not found')
    if data.attack_session_id is not None and not s.get(AttackSession, data.attack_session_id): raise HTTPException(422, 'Attack session not found')
    for k,v in episode_values(data).items(): setattr(row,k,v)
    s.commit(); s.refresh(row); return row
@app.delete('/api/episodes/{id}', status_code=204)
def delete_episode(id: int, s: Session = Depends(db)):
    row=s.get(Episode,id)
    if not row: raise HTTPException(404,'Episode not found')
    s.delete(row); s.commit()
@app.get('/api/contacts')
def contacts(s: Session = Depends(db)): return s.query(Contact).all()
@app.post('/api/contacts', status_code=201)
def add_contact(data: ContactIn, s: Session = Depends(db)):
    row=Contact(**data.model_dump()); s.add(row); s.commit(); s.refresh(row); return row
@app.put('/api/contacts/{id}')
def edit_contact(id: int, data: ContactIn, s: Session = Depends(db)):
    row=s.get(Contact,id)
    if not row: raise HTTPException(404,'Contact not found')
    for k,v in data.model_dump().items(): setattr(row,k,v)
    s.commit(); s.refresh(row); return row
@app.delete('/api/contacts/{id}', status_code=204)
def delete_contact(id: int, s: Session = Depends(db)):
    row=s.get(Contact,id)
    if not row: raise HTTPException(404,'Contact not found')
    s.query(SupportPreferences).filter_by(preferred_contact_id=id).update({'preferred_contact_id':None})
    s.delete(row); s.commit()
@app.get('/api/profile')
def profile(s: Session = Depends(db)):
    row=s.get(Profile,1)
    if not row: row=Profile(id=1); s.add(row); s.commit(); s.refresh(row)
    return row
@app.put('/api/profile')
def save_profile(data: ProfileIn, s: Session = Depends(db)):
    row=s.get(Profile,1)
    if not row: row=Profile(id=1); s.add(row)
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(row,k,v)
    s.commit(); s.refresh(row); return row


def session_out(row):
    return {'id': row.id, 'started_at': row.started_at, 'ended_at': row.ended_at} if row else None

@app.get('/api/attack-sessions/current')
def current_session(s: Session = Depends(db)):
    return session_out(s.query(AttackSession).order_by(AttackSession.id.desc()).first())

@app.get('/api/attack-sessions')
def attack_sessions(s: Session = Depends(db)):
    return [session_out(row) for row in s.query(AttackSession).order_by(AttackSession.id.desc()).all()]

@app.post('/api/attack-sessions/start')
def start_session(s: Session = Depends(db)):
    row = s.query(AttackSession).filter_by(active_slot=1).first()
    if row: return session_out(row)
    row = AttackSession(started_at=datetime.now(timezone.utc).isoformat(), active_slot=1)
    s.add(row)
    try:
        s.commit()
    except IntegrityError:
        s.rollback()
        row = s.query(AttackSession).filter_by(active_slot=1).first()
        if not row: raise HTTPException(409, 'Session changed; retry starting your session')
    s.refresh(row)
    return session_out(row)

@app.post('/api/attack-sessions/{id}/end')
def end_session(id: int, s: Session = Depends(db)):
    row = s.get(AttackSession, id)
    if not row: raise HTTPException(404, 'Attack session not found')
    # Conditional update keeps repeat requests from changing the end timestamp.
    s.query(AttackSession).filter(AttackSession.id == id, AttackSession.ended_at.is_(None)).update(
        {'ended_at': datetime.now(timezone.utc).isoformat(), 'active_slot': None})
    s.commit(); s.refresh(row)
    return session_out(row)

from .tracking_routes import register_tracking
register_tracking(app, db, Episode, Wellness, EarlySymptom, Contact, Profile, AttackSession, SupportPreferences, SupportFeedback)


from .forecasting import ForecastServiceV1, ForecastResponseV1
forecast_service = ForecastServiceV1()

@app.get('/api/v1/forecast', response_model=ForecastResponseV1)
def forecast_status():
    # Current collection has no explicit coverage or immutable research history.
    # No request can train, load, or activate an experimental model.
    from fastapi.responses import JSONResponse
    return JSONResponse(forecast_service.status().model_dump(),headers={'Cache-Control':'no-store'})

from .support_routes import register_support
register_support(app, db, Contact, AttackSession, SupportPreferences, SupportFeedback)


@app.middleware('http')
async def private_api_responses(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response
