"""Synthetic fixtures only. Descriptions are not clinical/forecasting validation."""
from datetime import datetime, timedelta, timezone, date
from types import SimpleNamespace as Row
from zoneinfo import ZoneInfo
import pytest
from app.pattern_insights import describe, day_bounds
from test_auth import clients, register

NOW=datetime(2026,10,20,12,tzinfo=timezone.utc)
def attack(id,day='2026-10-14',**values):
    return Row(id=id,date=day,started_at=day+'T10:00:00+00:00',ended_at=day+'T11:00:00+00:00',severity=5,**values)
def checkin(id,day='2026-10-14',status=None,**values):
    defaults=dict(id=id,date=day,timezone_name='UTC',recorded_at=NOW.isoformat(),
        episode_observation=status,observation_recorded_at=NOW.isoformat() if status else None,
        sleep_hours=None,sleep_quality=None,stress=None,hydration_ml=None,screen_hours=None,missed_meals=None,menstrual_notes=None)
    return Row(**{**defaults,**values})
def symptom(id,at,**values):return Row(**dict(id=id,symptom='Synthetic yawning',onset_at=at,recorded_at=NOW.isoformat(),**values))
def report(attacks=(),wellness=(),early=(),zone='UTC',now=NOW):return describe(attacks,wellness,early,zone,30,now)

def test_missing_records_are_unknown_not_negative_observations():
    empty=report();assert empty['data_status']=='insufficient_data'
    assert all(d['status']=='unknown' for d in empty['daily'])
    data=report(wellness=[checkin(i,f'2026-10-{10+i:02}',sleep_hours=8) for i in range(7)])
    factor=data['factors'][0]
    assert factor['count']==7 and factor['non_episode_days']==0
    assert factor['comparison_status']=='insufficient_data' and factor['non_episode_mean'] is None
    assert data['daily_observations'][0]['exposure_at'] is None

def test_supported_comparisons_use_distinct_days_and_explicit_confirmed_negatives():
    attacks=[attack(i,f'2026-10-{14+i:02}') for i in range(3)]
    attacks.append(attack(9,'2026-10-14'))
    wellness=[checkin(i,f'2026-10-{14+i:02}',sleep_hours=6,stress=8,missed_meals=True) for i in range(3)]
    wellness += [checkin(i+3,f'2026-10-{17+i:02}',status='no_episode',sleep_hours=8,stress=2,missed_meals=False) for i in range(3)]
    data=report(attacks,wellness)
    assert data['summary']['timed_episodes']==4
    sleep=data['factors'][0];assert sleep['comparison_status']=='available'
    assert sleep['episode_days']==sleep['non_episode_days']==3
    assert sleep['episode_mean']==6 and sleep['non_episode_mean']==8
    assert data['factors'][-1]['episode_mean']==1 and data['factors'][-1]['non_episode_mean']==0
    assert data['factors'][1]['mean'] is None # Unknown sleep quality is never zero-filled.

def test_unknown_ends_do_not_invent_recovery_or_continuing_headache_days():
    row=attack(1);row.ended_at=None
    data=report([row],[checkin(i,f'2026-10-{17+i:02}',status='no_episode',sleep_hours=8) for i in range(3)])
    assert data['factors'][0]['non_episode_days']==0
    assert data['warnings']['unresolved_overlap_exclusions']==3
    assert next(d for d in data['daily'] if d['date']=='2026-10-18')['status']=='unknown'

def test_conflicts_legacy_dates_and_confirmation_timing_are_excluded():
    legacy=attack(2,'2026-10-18');legacy.started_at=None;legacy.ended_at=None
    invalid_confirmation=checkin(3,'2026-10-11',status='no_episode',observation_recorded_at='2026-10-11T12:00:00Z')
    data=report([attack(1),legacy],[checkin(1,status='no_episode'),checkin(2,'2026-10-19',status='no_episode'),invalid_confirmation])
    assert data['warnings']['conflicting_observations']==1
    assert data['warnings']['legacy_timing_exclusions']==1
    assert data['warnings']['unconfirmed_observation_dates']==1
    assert all(f['non_episode_days']==0 for f in data['factors'])

def test_early_symptoms_separate_before_during_and_uncertain_timing():
    early=[symptom(1,'2026-10-14T09:00:00Z'),symptom(2,'2026-10-14T10:00:00Z'),symptom(3,'2026-10-14T10:30:00Z'),symptom(4,'2026-10-12T09:00:00Z')]
    data=report([attack(1)],early=early)
    assert data['summary']['early_before_onset']==1
    events={e['id']:e for e in data['timeline'] if e['kind']=='early_symptom'}
    assert events[1]['hours_before']==1 and 'not a confirmed prodrome' in events[1]['relation']
    assert events[2]['relation']==events[3]['relation']=='During a recorded episode'
    assert 'coverage unknown' in events[4]['relation']
    unresolved=attack(8,'2026-10-13');unresolved.ended_at=None
    assert report([unresolved,attack(1)],early=[early[0]])['summary']['early_before_onset']==0

def test_dst_and_alias_zones_use_aware_instants_and_actual_civil_boundaries():
    now=datetime(2026,11,3,12,tzinfo=timezone.utc)
    row=attack(1,'2026-11-01');row.started_at='2026-11-01T01:15:00-05:00';row.ended_at='2026-11-01T02:15:00-05:00'
    early=symptom(1,'2026-11-01T01:30:00-04:00');early.recorded_at=now.isoformat()
    data=report([row],early=[early],zone='America/New_York',now=now)
    assert next(e for e in data['timeline'] if e['kind']=='early_symptom')['hours_before']==0.75
    left,right=day_bounds(date(2026,11,1),ZoneInfo('America/New_York'))
    assert (right-left).total_seconds()==25*3600
    check=checkin(1,'2026-10-14',timezone_name='Asia/Calcutta')
    assert report([attack(1)],[check],zone='Asia/Kolkata')['warnings'].get('unaligned_wellness_days',0)==0
    assert report([attack(1)],[check],zone='UTC')['warnings']['unaligned_wellness_days']==1

def test_future_naive_or_invalid_timestamps_do_not_become_observed_history():
    invalid=attack(1);invalid.started_at='not-a-time'
    future=attack(2,'2026-10-21')
    late=symptom(1,'2026-10-14T09:00:00Z');late.recorded_at='2026-10-21T00:00:00Z'
    data=report([invalid,future],early=[late])
    assert data['summary']['timed_episodes']==data['summary']['early_observations']==0
    assert data['warnings']['invalid_episode_timestamps']==1

def test_patterns_and_observations_require_ownership_and_completed_dates(clients):
    a,b,_=clients;register(a);register(b,'patterns-b@example.test')
    yesterday=(datetime.now(timezone.utc)-timedelta(days=1)).date().isoformat()
    assert a.post('/api/episodes',json={'started_at':yesterday+'T10:00:00Z','ended_at':yesterday+'T11:00:00Z','timezone_name':'UTC','severity':6}).status_code==201
    assert a.post('/api/early-symptoms',json={'symptom':'Synthetic private marker','onset_at':yesterday+'T09:00:00Z','timezone_name':'UTC'}).status_code==201
    r=a.post('/api/wellness',json={'date':yesterday,'timezone_name':'UTC','sleep_hours':6,'episode_observation':'episode'})
    assert r.status_code==201;record=r.json()
    assert record['observation_recorded_at'] is not None
    # Old clients preserve confirmation; moving to another date clears it.
    a.put('/api/wellness/'+str(record['id']),json={'date':yesterday,'timezone_name':'UTC','sleep_hours':7})
    assert a.get('/api/wellness').json()[0]['episode_observation']=='episode'
    assert b.put('/api/wellness/'+str(record['id']),json={'date':yesterday,'timezone_name':'UTC','episode_observation':'no_episode'}).status_code==404
    assert a.get('/api/pattern-insights?timezone_name=UTC').json()['summary']['timed_episodes']==1
    other=b.get('/api/pattern-insights?timezone_name=UTC&owner_id=1')
    assert other.json()['summary']['timed_episodes']==0 and 'Synthetic private marker' not in other.text
    assert a.get('/api/pattern-insights',headers={'X-CSRF-Token':''}).status_code==401
    assert a.get('/api/pattern-insights?timezone_name=../bad').status_code==422
    assert a.get('/api/pattern-insights?days=91').status_code==422
    today=datetime.now(timezone.utc).date().isoformat()
    assert a.post('/api/wellness',json={'date':today,'timezone_name':'UTC','episode_observation':'no_episode'}).status_code==422
    assert a.post('/api/wellness',json={'date':today,'timezone_name':'UTC','episode_observation':'invented'}).status_code==422
    a.cookies.clear();assert a.get('/api/pattern-insights').status_code==401

def test_007_migration_keeps_unknown_old_records_unknown(tmp_path):
    import os,subprocess,sys,sqlite3
    from pathlib import Path
    path=tmp_path/'patterns.db';cwd=Path(__file__).resolve().parents[1]
    env={**os.environ,'DATABASE_URL':f'sqlite:///{path.as_posix()}'}
    def migrate(version):subprocess.run([sys.executable,'-m','alembic','upgrade',version],cwd=cwd,env=env,check=True,capture_output=True)
    migrate('006')
    with sqlite3.connect(path) as c:
        c.execute("INSERT INTO wellness(date,timezone_name,recorded_at,sleep_hours) VALUES('2026-10-14','UTC','2026-10-15T00:00:00Z',8)")
    migrate('head')
    with sqlite3.connect(path) as c:
        assert c.execute('SELECT date,sleep_hours,owner_id,episode_observation,observation_recorded_at FROM wellness').fetchone()==('2026-10-14',8,None,None,None)
        assert c.execute('PRAGMA foreign_key_check').fetchall()==[]


def test_missing_severity_is_excluded_but_reported_zero_is_preserved():
    missing=attack(1);missing.severity=None
    zero=attack(2);zero.severity=0
    rated=attack(3);rated.severity=8
    data=report([missing,zero,rated])
    assert data['summary']['average_severity']==4
    assert data['summary']['severity_count']==2
    assert data['warnings']['missing_severity']==1
    unknown=report([missing])
    assert unknown['summary']['average_severity'] is None
    assert unknown['summary']['severity_count']==0
    assert report([zero])['summary']['average_severity']==0


@pytest.mark.parametrize('zone',['UTC','Asia/Kolkata','America/New_York'])
@pytest.mark.parametrize('days',[30,90])
def test_reporting_window_includes_local_start_and_now_not_outside_instants(zone,days):
    reporting_zone=ZoneInfo(zone)
    first=NOW.astimezone(reporting_zone).date()-timedelta(days=days-1)
    start=day_bounds(first,reporting_zone)[0]
    times=[start-timedelta(microseconds=1),start,NOW,NOW+timedelta(microseconds=1)]
    rows=[]
    for i,onset in enumerate(times):
        row=attack(i);row.started_at=onset.isoformat();row.ended_at=None
        rows.append(row)
    data=describe(rows,[],[],zone,days,NOW)
    assert data['window_start']==first.isoformat()
    assert data['window_end']==NOW.astimezone(reporting_zone).date().isoformat()
    assert len(data['daily'])==days
    assert data['summary']['timed_episodes']==2
    assert sum(day['episodes'] for day in data['daily'])==2
    assert {event['id'] for event in data['timeline']}=={1,2}
    assert data['daily'][0]['completed'] is True
    assert data['daily'][-1]['completed'] is False
    assert data['summary']['average_duration_minutes'] is None
    assert all(day['status']!='no_episode_reported' for day in data['daily'])
