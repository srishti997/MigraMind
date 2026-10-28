"""Read-only quality review and explicit local preparation exports; never model labels."""
from datetime import datetime, timezone, timedelta, time
from uuid import uuid4
from zoneinfo import ZoneInfo
from typing import Literal
from fastapi import Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .auth import owned
from .tracking_schemas import valid_zone
from .prospective import episode_dates
from research.revision_contract import DailyValues, RevisionBundle

FIELDS = tuple(DailyValues.model_fields)

class ExportRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confirmed: Literal[True]
    scope: Literal['local_research_preparation']
    timezone_name: str = Field(default='UTC', max_length=100)
    days: int = 30

    @field_validator('confirmed', mode='before')
    @classmethod
    def explicit_confirmation(cls, value):
        if value is not True: raise ValueError('Explicit confirmation is required')
        return value


def analyze(rows, episodes, wellness, revisions, zone_name, days, now):
    zone = ZoneInfo(zone_name)
    last = now.astimezone(zone).date()-timedelta(days=1)
    first = last-timedelta(days=days-1)
    issues, eligible, states, seen = [], [], {}, set()
    def flag(code, day=None):
        if day is None or first.isoformat() <= day <= last.isoformat():
            issues.append({'code':code, 'date':day})
    valid_episodes=[]
    uncertain_episode_dates=set()
    for e in episodes:
        try:
            if e.severity is not None and (isinstance(e.severity,bool) or not 0 <= e.severity <= 10): flag('invalid_severity',e.date)
            if not e.started_at:
                flag('missing_episode_timestamp',e.date); valid_episodes.append(e); continue
            onset=datetime.fromisoformat(e.started_at)
            finish=datetime.fromisoformat(e.ended_at) if e.ended_at else None
            if onset.tzinfo is None or (finish and (finish.tzinfo is None or finish <= onset or finish > now)) or onset > now: raise ValueError()
            if not finish: flag('incomplete_episode_interval',e.date)
            valid_episodes.append(e)
        except (ValueError,TypeError):
            flag('inconsistent_episode_interval',e.date); uncertain_episode_dates.add(e.date)
    attacks=episode_dates(valid_episodes,zone,first.isoformat(),last.isoformat())
    attacks.update(day for day in uncertain_episode_dates if first.isoformat() <= day <= last.isoformat())
    other_zones=0
    for row in rows:
        if not first.isoformat() <= row.date <= last.isoformat() or row.deleted_at: continue
        if row.timezone_name != zone_name: other_zones+=1; continue
        if row.date in seen: flag('duplicate_daily_observation',row.date); states[row.date]='unknown'; continue
        seen.add(row.date)
        try:
            value=DailyValues.model_validate({k:row.values.get(k) for k in FIELDS})
            if value.date.isoformat()!=row.date or value.timezone_name!=row.timezone_name: raise ValueError()
            if value.status_recorded_at > now: raise ValueError()
        except (ValueError,TypeError,AttributeError):
            flag('invalid_daily_timestamps_or_values',row.date); states[row.date]='unknown'; continue
        end=datetime.combine(value.date+timedelta(days=1),time.min,zone)
        state=value.status
        if value.status_recorded_at < end:
            flag('incomplete_observation_coverage',row.date); state='unknown'
        legacy=[w.episode_observation for w in wellness if w.date==row.date and w.episode_observation]
        if (state=='no_migraine' and row.date in attacks) or any(
            x != {'migraine':'episode','no_migraine':'no_episode'}.get(state,x) for x in legacy):
            flag('conflicting_daily_observation',row.date); state='unknown'
        states[row.date]=state
        chain=[r for r in revisions if r.checkin_id==row.id]
        try:
            journal=[{'account_key':'local-account','record_id':str(row.id),'revision':r.revision,
                'action':r.action,'recorded_at':r.recorded_at,
                'values':{k:r.values.get(k) for k in FIELDS} if r.values else None} for r in chain]
            b=RevisionBundle(account_key='local-account',captured_at=now,
                provenance={'source_kind':'consented','source_reference':'local-preparation-only'},daily_revisions=journal)
            creation=min(b.daily_revisions,key=lambda r:r.revision)
            if creation.recorded_at != datetime.fromisoformat(row.created_at): raise ValueError()
            latest=max(b.daily_revisions,key=lambda r:r.revision)
            if latest.revision!=row.revision or latest.values!=value or latest.action=='deletion': raise ValueError()
            eligible.extend(b.daily_revisions)
        except (ValueError,TypeError,AttributeError): flag('unverifiable_revision_history',row.date)
        if any(getattr(value,k) is None for k in ('sleep_hours','sleep_quality','stress','hydration_ml')):
            flag('optional_observations_missing',row.date)
    # Duplicate source dates are excluded in their entirety, including previously selected history.
    duplicate_dates={i['date'] for i in issues if i['code']=='duplicate_daily_observation'}
    eligible=[r for r in eligible if r.values and r.values.date.isoformat() not in duplicate_dates]
    result={'window_start':first.isoformat(),'window_end':last.isoformat(),'timezone_name':zone_name,'days':days,
        'observed_days':len(states),'missing_days':days-len(states),
        'confirmed_episode_days':sum(v=='migraine' for v in states.values()),
        'explicit_no_episode_days':sum(v=='no_migraine' for v in states.values()),
        'unknown_days':days-sum(v in ('migraine','no_migraine') for v in states.values()),
        'incomplete_records':len({i['date'] for i in issues if i['code'] not in ('optional_observations_missing',)}),
        'other_timezone_reports':other_zones,'issues':issues,'verified_outcomes':0,
        'eligible_observations':len({r.record_id for r in eligible}), 'research_ready':False,
        'blockers':['Research enrollment and independent source review are not established.',
            'No independently verified onset and full-horizon outcome coverage journal is available.',
            'Collection counts are descriptive; no clinically validated readiness threshold exists.']}
    return result,eligible


def register_research_quality(app,db,Daily,Revision,Episode,Wellness,require_user,limiter):
    def prepare(s,user,zone_name,days):
        try:
            valid_zone(zone_name)
            if isinstance(days,bool) or not 7 <= days <= 90: raise ValueError()
        except ValueError: raise HTTPException(422,'Choose a valid timezone and 7 to 90 days.')
        now=datetime.now(timezone.utc)
        result,rows=analyze(owned(s,Daily,user).all(),owned(s,Episode,user).all(),owned(s,Wellness,user).all(),
            owned(s,Revision,user).all(),zone_name,days,now)
        return result,rows,now

    @app.get('/api/v1/research-quality')
    def quality(timezone_name:str=Query('UTC',max_length=100),days:int=Query(30,ge=7,le=90),s=Depends(db),user=Depends(require_user)):
        result,_,_=prepare(s,user,timezone_name,days)
        return result

    @app.post('/api/v1/research-export')
    def export(data:ExportRequest,s=Depends(db),user=Depends(require_user)):
        limiter.check(('research-export',user.id),10)
        result,rows,now=prepare(s,user,data.timezone_name,data.days)
        mapping={r.record_id:uuid4().hex for r in rows}
        journal=[{**r.model_dump(mode='json'),'account_key':'local-account','record_id':mapping[r.record_id]} for r in rows]
        return JSONResponse({'export_schema':'migramind-research-preparation/1','exported_at':now.isoformat(),
            'synthetic_demo':bool(getattr(app.state, 'synthetic_demo', False)),
            'provenance':{'collection_schema':'daily-checkins/migration-008','quality_policy':'completed-local-days/v1',
                'history':'application_revision_journal','independently_reviewed':False},
            'clinically_validated':False,'automatically_deidentified':False,
            'consent':{'scope':data.scope,'confirmed_at':now.isoformat(),'research_enrollment':False},
            'scope':result,'daily_revisions':journal,'outcome_revisions':[],
            'provenance_verified':False,'outcome_history_complete':False,'training_eligible':False,
            'limitations':['Private health data; not automatically de-identified or clinically validated.',
                'Includes historical numeric daily values, including corrections; excludes deleted chains, free text and legacy records.',
                'Not a Sprint 10 training bundle. Unknown and absent dates never mean no episode.']},
            headers={'Cache-Control':'no-store','Content-Disposition':'attachment; filename="migramind-research-preparation.json"'})
