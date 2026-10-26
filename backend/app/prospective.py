"""Daily reports are separate from episodes and are never forecasting labels."""
from datetime import date, datetime, timezone, time, timedelta
from typing import Literal
from zoneinfo import ZoneInfo
from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, field_validator, model_validator
from sqlalchemy.exc import IntegrityError
from .auth import owned, owned_row
from .tracking_schemas import valid_zone, utc

OPTIONAL = ('sleep_hours', 'sleep_quality', 'stress', 'hydration_ml', 'routine_changes', 'early_symptoms')


class CheckinIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    date: date
    timezone_name: str = Field(max_length=100)
    status: Literal['migraine', 'no_migraine', 'unknown']
    observed_at: AwareDatetime
    event_at: AwareDatetime
    sleep_hours: float | None = Field(default=None, ge=0, le=24, allow_inf_nan=False)
    sleep_quality: int | None = Field(default=None, ge=0, le=10)
    stress: int | None = Field(default=None, ge=0, le=10)
    hydration_ml: int | None = Field(default=None, ge=0, le=20000)
    routine_changes: str | None = Field(default=None, max_length=1000)
    early_symptoms: str | None = Field(default=None, max_length=1000)
    _zone = field_validator('timezone_name')(valid_zone)

    @model_validator(mode='after')
    def chronology(self):
        if not self.event_at <= self.observed_at <= datetime.now(timezone.utc):
            raise ValueError('Event time must be at or before observation time; neither may be in the future')
        if self.event_at.astimezone(ZoneInfo(self.timezone_name)).date() != self.date:
            raise ValueError('Event time must fall on the reported date in the recorded timezone')
        return self


class Correction(CheckinIn):
    expected_revision: int = Field(ge=1)


def payload(data):
    values = data.model_dump(mode='json', exclude={'expected_revision'})
    values.update(observed_at=utc(data.observed_at), event_at=utc(data.event_at))
    return values


def retrospective(row):
    # Same-day collection is a timing description, never a prospective outcome label.
    available_at = row.values.get('status_recorded_at', row.created_at) if row.values else row.created_at
    return row.date < datetime.fromisoformat(available_at).astimezone(ZoneInfo(row.timezone_name)).date().isoformat()


def episode_dates(episodes, zone, start, end):
    dates = set()
    for episode in episodes:
        if not episode.started_at:
            if start <= episode.date <= end: dates.add(episode.date)
            continue
        onset = datetime.fromisoformat(episode.started_at)
        finish = datetime.fromisoformat(episode.ended_at) if episode.ended_at else onset
        first = onset.astimezone(zone).date()
        last = (max(onset, finish - timedelta(microseconds=1))).astimezone(zone).date()
        cursor = max(first, date.fromisoformat(start))
        last = min(last, date.fromisoformat(end))
        while cursor <= last:
            dates.add(cursor.isoformat()); cursor += timedelta(days=1)
    return dates


def register_collection(app, db, Daily, Revision, Episode, Wellness, require_user, limiter):
    def sources(s, user):
        return owned(s, Episode, user).all(), {row.date:row for row in owned(s, Wellness, user).all()}

    def output(row, s, user, context=None):
        episodes, wellness = context if context is not None else sources(s, user)
        value = {key:getattr(row, key) for key in ('id','date','timezone_name','created_at','revision','deleted_at','values')}
        value['retrospective'] = retrospective(row)
        day = date.fromisoformat(row.date)
        day_end = datetime.combine(day + timedelta(days=1), time.min, ZoneInfo(row.timezone_name))
        value['day_complete'] = day_end <= datetime.now(timezone.utc)
        value['whole_day_confirmed'] = bool(row.values and datetime.fromisoformat(row.values['status_recorded_at']) >= day_end)
        dates = episode_dates(episodes, ZoneInfo(row.timezone_name), row.date, row.date)
        status = row.values.get('status') if row.values else None
        value['episode_discrepancy'] = ('no_migraine_with_diary_episode' if status == 'no_migraine' and row.date in dates
            else 'migraine_without_diary_episode' if status == 'migraine' and row.date not in dates else None)
        legacy = wellness.get(row.date)
        legacy_status = {'episode':'migraine', 'no_episode':'no_migraine'}.get(legacy.episode_observation) if legacy else None
        value['wellness_discrepancy'] = bool(status and legacy_status and status != legacy_status)
        return value

    def revision(s, row, action, stamp):
        s.add(Revision(owner_id=row.owner_id, checkin_id=row.id, revision=row.revision,
            action=action, recorded_at=stamp, values=row.values))

    def commit(s):
        try: s.commit()
        except IntegrityError:
            s.rollback(); raise HTTPException(409, 'This date or revision already exists. Reload your check-ins before editing.')

    @app.get('/api/daily-checkins')
    def listing(include_deleted:bool=False, s=Depends(db), user=Depends(require_user)):
        query = owned(s, Daily, user)
        if not include_deleted: query = query.filter(Daily.deleted_at.is_(None))
        context = sources(s, user)
        return [output(row, s, user, context) for row in query.order_by(Daily.date.desc()).all()]

    @app.post('/api/daily-checkins', status_code=201)
    def create(data:CheckinIn, s=Depends(db), user=Depends(require_user)):
        limiter.check(('collection', user.id), 120)
        values = payload(data)
        existing = owned(s, Daily, user).filter_by(date=data.date.isoformat()).first()
        if existing:
            if not existing.deleted_at and {k:v for k,v in existing.values.items() if k!='status_recorded_at'} == values:
                return output(existing, s, user)
            raise HTTPException(409, 'A check-in already exists for this date, including any deleted history. Review that entry.')
        stamp = datetime.now(timezone.utc).isoformat()
        values['status_recorded_at'] = stamp
        row = Daily(owner_id=user.id, date=data.date.isoformat(), timezone_name=data.timezone_name,
            created_at=stamp, revision=1, values=values)
        s.add(row)
        try: s.flush()
        except IntegrityError:
            s.rollback(); raise HTTPException(409, 'A check-in already exists for this date. Reload your check-ins.')
        revision(s, row, 'creation', stamp); commit(s)
        return output(row, s, user)

    @app.get('/api/daily-checkins/{id}/history')
    def history(id:int, s=Depends(db), user=Depends(require_user)):
        owned_row(s, Daily, id, user)
        return owned(s, Revision, user).filter_by(checkin_id=id).order_by(Revision.revision).all()

    @app.put('/api/daily-checkins/{id}')
    def correct(id:int, data:Correction, s=Depends(db), user=Depends(require_user)):
        limiter.check(('collection', user.id), 120)
        row = owned_row(s, Daily, id, user)
        if row.deleted_at: raise HTTPException(410, 'This check-in was deleted. Its history remains available.')
        if data.date.isoformat() != row.date or data.timezone_name != row.timezone_name:
            raise HTTPException(422, 'The date and timezone identify this daily report and cannot change. Correct its values or delete it.')
        if row.revision != data.expected_revision: raise HTTPException(409, 'This entry changed. Reload before editing.')
        # Compare-and-swap prevents concurrent writers from losing corrections.
        stamp = datetime.now(timezone.utc).isoformat()
        values = {**payload(data), 'status_recorded_at':stamp}
        changed = owned(s, Daily, user).filter_by(id=id, revision=data.expected_revision, deleted_at=None).update(
            {'values':values, 'revision':data.expected_revision + 1}, synchronize_session=False)
        if changed != 1: s.rollback(); raise HTTPException(409, 'This entry changed. Reload before editing.')
        s.expire(row); s.refresh(row)
        revision(s, row, 'correction', stamp); commit(s)
        return output(row, s, user)

    @app.delete('/api/daily-checkins/{id}', status_code=204)
    def remove(id:int, expected_revision:int=Query(ge=1), s=Depends(db), user=Depends(require_user)):
        limiter.check(('collection', user.id), 120)
        row = owned_row(s, Daily, id, user)
        if row.deleted_at: return
        stamp = datetime.now(timezone.utc).isoformat()
        changed = owned(s, Daily, user).filter_by(id=id, revision=expected_revision, deleted_at=None).update(
            {'values':None, 'revision':expected_revision + 1, 'deleted_at':stamp}, synchronize_session=False)
        if changed != 1: s.rollback(); raise HTTPException(409, 'This entry changed. Reload before deleting.')
        s.expire(row); s.refresh(row); revision(s, row, 'deletion', stamp); commit(s)

    @app.get('/api/v1/collection-quality')
    def quality(timezone_name:str=Query(default='UTC',max_length=100), days:int=Query(default=30,ge=7,le=90),
                s=Depends(db), user=Depends(require_user)):
        try: zone = ZoneInfo(valid_zone(timezone_name))
        except ValueError: raise HTTPException(422, 'Invalid reporting timezone')
        today = datetime.now(zone).date(); first = today-timedelta(days=days-1)
        rows = owned(s, Daily, user).filter(Daily.date >= first.isoformat(), Daily.date <= today.isoformat()).all()
        current = [row for row in rows if not row.deleted_at]
        context = sources(s, user)
        descriptions = {row.id:output(row, s, user, context) for row in current}
        # Report source dates only: avoid silently remapping travel-day reports to a different zone.
        aligned = [row for row in current if row.timezone_name == timezone_name]
        negatives = sum(row.values['status']=='no_migraine' and descriptions[row.id]['whole_day_confirmed']
            and not descriptions[row.id]['episode_discrepancy'] and not descriptions[row.id]['wellness_discrepancy'] for row in aligned)
        corrections = owned(s, Revision, user).filter(Revision.checkin_id.in_([row.id for row in rows]), Revision.action=='correction').count()
        return {'status':'insufficient_evidence_for_forecasting','days':days,'window_start':first.isoformat(),
            'window_end':today.isoformat(),'timezone_name':timezone_name,'observed_days':len(aligned),
            'explicit_no_episode_days':negatives,
            'unknown_days':days-sum(row.values['status']!='unknown' for row in aligned),
            'explicit_unknown_days':sum(row.values['status']=='unknown' for row in aligned),
            'same_day_observations':sum(not retrospective(row) for row in current),
            'retrospective_observations':sum(retrospective(row) for row in current),
            'other_timezone_reports':len(current)-len(aligned),
            'discrepancies':sum(bool(descriptions[row.id]['episode_discrepancy'] or descriptions[row.id]['wellness_discrepancy']) for row in current),
            'correction_count':corrections,'deleted_reports':len(rows)-len(current),
            'missing_fields':{key:sum(row.values[key] is None for row in current) for key in OPTIONAL},
            'forecasting_justified':False}

    from .research_quality import register_research_quality
    register_research_quality(app, db, Daily, Revision, Episode, Wellness, require_user, limiter)
