"""Synthetic records and isolated in-memory accounts only."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS
import pytest
from test_auth import clients, register
from test_prospective import report
from app.main import CheckinRevision, DailyCheckin
from app.research_quality import analyze

REQUEST={'confirmed':True,'scope':'local_research_preparation','timezone_name':'UTC','days':30}


def test_missing_days_and_unknown_are_not_negatives(clients):
    a,_,_=clients;register(a)
    q=a.get('/api/v1/research-quality').json()
    assert q['missing_days']==q['unknown_days']==30 and q['explicit_no_episode_days']==0
    a.post('/api/daily-checkins',json=report(status='unknown'))
    q=a.get('/api/v1/research-quality').json()
    assert q['missing_days']==29 and q['unknown_days']==30 and q['verified_outcomes']==0
    assert q['research_ready'] is False


def test_completed_reports_conflicts_and_revision_export(clients):
    a,_,factory=clients;register(a)
    data=report(stress=0,routine_changes='Synthetic secret text')
    row=a.post('/api/daily-checkins',json=data).json()
    assert a.get('/api/v1/research-quality').json()['explicit_no_episode_days']==1
    a.put(f"/api/daily-checkins/{row['id']}",json={**data,'stress':4,'expected_revision':1})
    a.post('/api/episodes',json={'started_at':data['event_at'],'timezone_name':'UTC','severity':2})
    q=a.get('/api/v1/research-quality').json()
    assert q['explicit_no_episode_days']==0 and q['unknown_days']==30
    assert 'conflicting_daily_observation' in [i['code'] for i in q['issues']]
    with factory() as s:before=s.query(CheckinRevision).count()
    result=a.post('/api/v1/research-export',json=REQUEST)
    assert result.status_code==200 and result.headers['cache-control']=='no-store'
    export=result.json();history=export['daily_revisions']
    assert [r['values']['stress'] for r in history]==[0,4]
    assert len({r['record_id'] for r in history})==1
    assert 'Synthetic secret text' not in result.text and 'owner_id' not in result.text
    assert export['outcome_revisions']==[] and not export['training_eligible']
    assert not export['consent']['research_enrollment']
    assert not export['clinically_validated'] and not export['automatically_deidentified']
    assert export['provenance']['history']=='application_revision_journal'
    with factory() as s:assert s.query(CheckinRevision).count()==before
    a.delete(f"/api/daily-checkins/{row['id']}?expected_revision=2")
    assert a.post('/api/v1/research-export',json=REQUEST).json()['daily_revisions']==[]


@pytest.mark.parametrize('changes',[{'confirmed':False},{'confirmed':1},{'confirmed':'true'},{'scope':'support_card'},{'owner_id':1},{'days':6},{'timezone_name':'bad/zone'}])
def test_explicit_scoped_download_consent_required(clients,changes):
    a,_,_=clients;register(a)
    assert a.post('/api/v1/research-export',json={**REQUEST,**changes}).status_code==422


def test_exports_and_quality_isolated_and_csrf_protected(clients):
    a,b,_=clients;register(a);register(b,'research-b@example.test')
    a.post('/api/daily-checkins',json=report(stress=9))
    assert b.get('/api/v1/research-quality').json()['observed_days']==0
    assert b.post('/api/v1/research-export',json=REQUEST).json()['daily_revisions']==[]
    assert a.post('/api/v1/research-export',json=REQUEST,headers={'X-CSRF-Token':''}).status_code==403
    assert a.get('/api/v1/research-quality',headers={'X-CSRF-Token':''}).status_code==401
    assert a.post('/api/v1/research-export',json=REQUEST,headers={'Origin':'https://invalid.test'}).status_code==403
    assert a.post('/api/v1/research-export',json={}).status_code==422


def test_invalid_and_truncated_histories_flagged_not_exported(clients):
    a,_,factory=clients;register(a)
    row=a.post('/api/daily-checkins',json=report()).json()
    with factory() as s:
        s.query(CheckinRevision).filter_by(checkin_id=row['id']).delete();s.commit()
    q=a.get('/api/v1/research-quality').json()
    assert 'unverifiable_revision_history' in [i['code'] for i in q['issues']]
    assert a.post('/api/v1/research-export',json=REQUEST).json()['daily_revisions']==[]
    with factory() as s:
        r=s.get(DailyCheckin,row['id']);r.values={**r.values,'event_at':None};s.commit()
    q=a.get('/api/v1/research-quality').json()
    assert 'invalid_daily_timestamps_or_values' in [i['code'] for i in q['issues']]


def test_dst_completed_day_cutoff_duplicates_and_invalid_intervals():
    now=datetime(2025,11,3,4,30,tzinfo=timezone.utc)
    # New York November 2 is a 25-hour day and has not ended at this instant.
    q,_=analyze([],[],[],[],'America/New_York',7,now)
    assert q['window_end']=='2025-11-01'
    now+=timedelta(hours=1)
    q,_=analyze([],[],[],[],'America/New_York',7,now)
    assert q['window_end']=='2025-11-02'
    day='2025-11-02'
    values={'date':day,'timezone_name':'America/New_York','status':'no_migraine',
        'event_at':'2025-11-02T06:30:00Z','observed_at':'2025-11-02T06:30:00Z',
        'status_recorded_at':'2025-11-03T04:59:59Z'}
    row=NS(id=1,date=day,timezone_name='America/New_York',deleted_at=None,values=values,revision=1)
    episode=NS(date=day,severity=11,started_at='2025-11-02T12:00:00Z',ended_at='2025-11-02T11:00:00Z')
    q,eligible=analyze([row,row],[episode],[],[],'America/New_York',7,now)
    codes={i['code'] for i in q['issues']}
    assert {'incomplete_observation_coverage','duplicate_daily_observation','invalid_severity','inconsistent_episode_interval'} <= codes
    assert q['explicit_no_episode_days']==0 and eligible==[]


def test_export_rate_limited(clients):
    a,_,_=clients;register(a)
    for _ in range(10):assert a.post('/api/v1/research-export',json=REQUEST).status_code==200
    assert a.post('/api/v1/research-export',json=REQUEST).status_code==429


def test_today_and_other_zones_are_not_completed_matching_days(clients):
    a,_,_=clients;register(a)
    stamp=datetime.now(timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)
    a.post('/api/daily-checkins',json=report(date=stamp.date().isoformat(),event_at=stamp.isoformat(),observed_at=stamp.isoformat()))
    assert a.get('/api/v1/research-quality').json()['observed_days']==0
    data=report();row=a.post('/api/daily-checkins',json=data)
    assert row.status_code==201
    q=a.get('/api/v1/research-quality?timezone_name=America%2FNew_York').json()
    assert q['observed_days']==0 and q['other_timezone_reports']>=1


def test_missing_legacy_episode_timestamp_is_flagged_and_blocks_conflicting_negative(clients):
    a,_,_=clients;register(a);data=report()
    a.post('/api/daily-checkins',json=data)
    a.post('/api/episodes',json={'date':data['date'],'severity':3})
    q=a.get('/api/v1/research-quality').json()
    assert q['explicit_no_episode_days']==0
    assert {'missing_episode_timestamp','conflicting_daily_observation'} <= {i['code'] for i in q['issues']}


def test_invalid_episode_intervals_cannot_leave_no_episode_reports_conflict_free():
    now=datetime(2025,11,3,12,tzinfo=timezone.utc)
    day='2025-11-02'
    row=NS(id=1,date=day,timezone_name='UTC',deleted_at=None,revision=1,
        values={'date':day,'timezone_name':'UTC','status':'no_migraine',
            'event_at':day+'T12:00:00Z','observed_at':day+'T12:00:00Z',
            'status_recorded_at':'2025-11-03T01:00:00Z'})
    e=NS(date=day,severity=3,started_at=day+'T12:00:00Z',ended_at=day+'T11:00:00Z')
    q,_=analyze([row],[e],[],[],'UTC',7,now)
    assert q['explicit_no_episode_days']==0
    assert 'conflicting_daily_observation' in {i['code'] for i in q['issues']}


def test_creation_availability_must_match_original_server_timestamp(clients):
    a,_,factory=clients;register(a)
    row=a.post('/api/daily-checkins',json=report(stress=0)).json()
    # Simulate inconsistent storage, not a supported user edit: even an internally
    # consistent journal/current pair cannot rewrite the original creation anchor.
    with factory() as s:
        current=s.get(DailyCheckin,row['id'])
        revision=s.query(CheckinRevision).filter_by(checkin_id=row['id']).one()
        earlier=(datetime.fromisoformat(current.created_at)-timedelta(hours=1)).isoformat()
        revision.recorded_at=earlier
        revision.values={**revision.values,'status_recorded_at':earlier}
        current.values={**current.values,'status_recorded_at':earlier}
        s.commit()
    q=a.get('/api/v1/research-quality').json()
    assert 'unverifiable_revision_history' in {i['code'] for i in q['issues']}
    assert q['eligible_observations']==0
    assert a.post('/api/v1/research-export',json=REQUEST).json()['daily_revisions']==[]


def test_later_backdated_corrections_cannot_rewrite_exported_historical_availability(clients):
    from research.revision_contract import RevisionBundle
    from research.revision_dataset import features_at, build_revision_dataset
    a,_,_=clients;register(a)
    data=report(stress=0,status='unknown')
    row=a.post('/api/daily-checkins',json=data).json()
    before=a.post('/api/v1/research-export',json=REQUEST).json()
    original=a.get(f"/api/daily-checkins/{row['id']}/history").json()[0]
    cutoff=datetime.now(timezone.utc)
    def reconstruct(export):
        return RevisionBundle(account_key='local-account',captured_at=export['exported_at'],
            provenance={'source_kind':'consented','source_reference':'synthetic-test',
                'consent_reference':'synthetic-protocol','provenance_verified':True},
            daily_revisions=export['daily_revisions'])
    historical=features_at(reconstruct(before),cutoff)[0]
    assert historical['stress']==0
    assert a.put(f"/api/daily-checkins/{row['id']}",json={**data,'stress':9,'expected_revision':1}).status_code==200
    after=a.post('/api/v1/research-export',json=REQUEST).json()
    assert [r['values']['stress'] for r in after['daily_revisions']]==[0,9]
    assert after['daily_revisions'][0]['recorded_at']==before['daily_revisions'][0]['recorded_at']
    assert after['daily_revisions'][0]['values']==before['daily_revisions'][0]['values']
    assert features_at(reconstruct(after),cutoff)[0]==historical
    # Server availability fields are never accepted from the client.
    assert a.put(f"/api/daily-checkins/{row['id']}",json={**data,'expected_revision':2,
        'status_recorded_at':original['recorded_at']}).status_code==422
    assert a.get(f"/api/daily-checkins/{row['id']}/history").json()[0]==original
    assert a.post('/api/v1/research-export',json={**REQUEST,'cutoff':cutoff.isoformat()}).status_code==422
    # Neither unknown daily status nor absent external outcome coverage is a label.
    assert build_revision_dataset(reconstruct(after),cutoff,cutoff+timedelta(days=1))[0]==[]
    assert a.delete(f"/api/daily-checkins/{row['id']}?expected_revision=2").status_code==204
    assert a.get(f"/api/daily-checkins/{row['id']}/history").json()[0]==original
    assert a.post('/api/v1/research-export',json=REQUEST).json()['daily_revisions']==[]
