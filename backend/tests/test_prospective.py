"""Only synthetic reports and isolated databases; never open the user's database."""
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import subprocess
import sys
import pytest
from test_auth import clients, register, PASSWORD
from app.main import DailyCheckin, CheckinRevision


def report(**changes):
    stamp=(datetime.now(timezone.utc)-timedelta(days=2)).replace(hour=12,minute=0,second=0,microsecond=0)
    return {'date':stamp.date().isoformat(),'timezone_name':'UTC','status':'no_migraine',
        'event_at':stamp.isoformat(),'observed_at':stamp.isoformat(),**changes}


def test_creation_idempotency_duplicates_and_no_episode_semantics(clients):
    a,b,_=clients;register(a)
    data=report();r=a.post('/api/daily-checkins',json=data);assert r.status_code==201
    row=r.json();assert row['retrospective'] and row['day_complete']
    assert a.post('/api/daily-checkins',json=data).json()['id']==row['id']
    assert len(a.get('/api/daily-checkins').json())==1
    assert len(a.get(f"/api/daily-checkins/{row['id']}/history").json())==1
    assert a.post('/api/daily-checkins',json=report(status='migraine')).status_code==409
    quality=a.get('/api/v1/collection-quality').json()
    assert quality['observed_days']==1 and quality['explicit_no_episode_days']==1
    assert quality['unknown_days']==29 and quality['forecasting_justified'] is False
    assert quality['missing_fields']['stress']==1
    assert a.get('/api/episodes').json()==[]
    assert a.get('/api/wellness').json()==[]


def test_status_conflicts_and_unknown_do_not_rewrite_diary(clients):
    a,b,_=clients;register(a)
    data=report();row=a.post('/api/daily-checkins',json=data).json()
    episode={'started_at':data['event_at'],'timezone_name':'UTC','severity':0}
    assert a.post('/api/episodes',json=episode).status_code==201
    assert a.get('/api/daily-checkins').json()[0]['episode_discrepancy']=='no_migraine_with_diary_episode'
    quality=a.get('/api/v1/collection-quality').json()
    assert quality['explicit_no_episode_days']==0 and quality['discrepancies']==1
    assert a.put(f"/api/daily-checkins/{row['id']}",json={**data,'status':'unknown','expected_revision':1}).status_code==200
    assert a.get('/api/v1/collection-quality').json()['unknown_days']==30
    assert len(a.get('/api/episodes').json())==1


def test_corrections_tombstone_history_export_and_account_erasure(clients):
    a,b,factory=clients;user=register(a)
    register(b,'surviving-checkin@example.test')
    survivor=b.post('/api/daily-checkins',json=report(stress=3)).json()
    data=report(stress=0);row=a.post('/api/daily-checkins',json=data).json();id=row['id']
    updated=a.put(f'/api/daily-checkins/{id}',json={**data,'stress':5,'expected_revision':1})
    assert updated.status_code==200 and updated.json()['created_at']==row['created_at']
    assert a.put(f'/api/daily-checkins/{id}',json={**data,'expected_revision':1}).status_code==409
    assert a.delete(f'/api/daily-checkins/{id}?expected_revision=1').status_code==409
    assert a.delete(f'/api/daily-checkins/{id}?expected_revision=2').status_code==204
    assert a.delete(f'/api/daily-checkins/{id}?expected_revision=2').status_code==204
    assert a.get('/api/daily-checkins').json()==[]
    deleted=a.get('/api/daily-checkins?include_deleted=true').json()[0]
    assert deleted['values'] is None and deleted['revision']==3
    revisions=a.get(f'/api/daily-checkins/{id}/history').json()
    assert [r['action'] for r in revisions]==['creation','correction','deletion']
    assert [r['values']['stress'] if r['values'] else None for r in revisions]==[0,5,None]
    assert a.post('/api/daily-checkins',json=data).status_code==409
    assert a.put(f'/api/daily-checkins/{id}',json={**data,'expected_revision':3}).status_code==410
    quality=a.get('/api/v1/collection-quality').json()
    assert quality['correction_count']==1 and quality['deleted_reports']==1 and quality['unknown_days']==30
    exported=a.get('/api/export').json()
    assert exported['schema_version']==5 and len(exported['checkin_revisions'])==3
    assert a.request('DELETE','/api/account',json={'password':PASSWORD,'confirmation':'DELETE'}).status_code==204
    with factory() as s:
        assert s.query(DailyCheckin).filter_by(owner_id=user['id']).count()==0
        assert s.query(CheckinRevision).filter_by(owner_id=user['id']).count()==0
    assert b.get('/api/daily-checkins').json()[0]['values']['stress']==3
    assert len(b.get(f"/api/daily-checkins/{survivor['id']}/history").json())==1


def test_every_endpoint_is_owned_and_csrf_bound(clients):
    a,b,_=clients;register(a);register(b,'checkin-b@example.test')
    data=report(routine_changes='Synthetic private routine')
    row=a.post('/api/daily-checkins',json=data).json();id=row['id']
    assert b.get('/api/daily-checkins?include_deleted=true').json()==[]
    assert b.get('/api/v1/collection-quality').json()['observed_days']==0
    assert b.get(f'/api/daily-checkins/{id}/history').status_code==404
    assert b.put(f'/api/daily-checkins/{id}',json={**data,'expected_revision':1}).status_code==404
    assert b.delete(f'/api/daily-checkins/{id}?expected_revision=1').status_code==404
    assert 'Synthetic private routine' not in b.get('/api/export').text
    for path in ('/api/daily-checkins','/api/v1/collection-quality',f'/api/daily-checkins/{id}/history'):
        assert a.get(path,headers={'X-CSRF-Token':''}).status_code==401
    assert a.post('/api/daily-checkins',json=data,headers={'X-CSRF-Token':''}).status_code==403
    assert a.put(f'/api/daily-checkins/{id}',json={**data,'expected_revision':1},headers={'Origin':'https://invalid.test'}).status_code==403


@pytest.mark.parametrize('changes',[
    {'event_at':'bad'}, {'observed_at':'2025-01-01T12:00:00'}, {'timezone_name':'invalid'},
    {'event_at':'2099-01-01T12:00:00Z'}, {'observed_at':'2099-01-01T12:00:00Z'},
    {'event_at':'2020-01-01T12:00:00Z'}, {'observed_at':'2020-01-01T12:00:00Z'},
    {'status':'missing'}, {'stress':11}, {'owner_id':9}, {'sleep_hours':-1},
])
def test_invalid_reports_are_rejected_without_private_value_echo(clients,changes):
    a,b,_=clients;register(a)
    response=a.post('/api/daily-checkins',json=report(routine_changes='Synthetic sensitive value',**changes))
    assert response.status_code==422 and 'Synthetic sensitive value' not in response.text


def test_dst_fold_instants_are_distinct_and_source_date_is_preserved(clients):
    a,b,_=clients;register(a)
    # A completed historical fall-back day has two 01:30 instants.
    data=report(date='2025-11-02',timezone_name='America/New_York',event_at='2025-11-02T01:30:00-04:00',observed_at='2025-11-02T01:30:00-05:00')
    row=a.post('/api/daily-checkins',json=data).json()
    assert row['values']['event_at']=='2025-11-02T05:30:00+00:00'
    assert row['values']['observed_at']=='2025-11-02T06:30:00+00:00'
    result=a.put(f"/api/daily-checkins/{row['id']}",json={**data,'expected_revision':1,'timezone_name':'UTC'})
    assert result.status_code==422


def test_today_is_provisional_and_other_timezones_are_separate(clients):
    a,b,_=clients;register(a)
    now=datetime.now(timezone.utc)-timedelta(seconds=1)
    data=report(date=now.date().isoformat(),event_at=now.isoformat(),observed_at=now.isoformat())
    row=a.post('/api/daily-checkins',json=data).json()
    assert not row['day_complete'] and not row['retrospective']
    quality=a.get('/api/v1/collection-quality').json()
    assert quality['explicit_no_episode_days']==0 and quality['same_day_observations']==1
    other=a.get('/api/v1/collection-quality?timezone_name=Asia%2FKolkata').json()
    assert other['observed_days']==0 and other['other_timezone_reports']==1
    assert a.get('/api/v1/collection-quality?timezone_name=Invalid').status_code==422


def test_partial_day_negative_never_becomes_complete_without_reconfirmation(clients):
    a,b,factory=clients;register(a)
    data=report();row=a.post('/api/daily-checkins',json=data).json()
    # Simulate a report originally made during the day, now read after midnight.
    with factory() as s:
        stored=s.get(DailyCheckin,row['id'])
        stored.created_at=data['event_at']
        stored.values={**stored.values,'status_recorded_at':data['event_at']};s.commit()
    quality=a.get('/api/v1/collection-quality').json()
    assert quality['explicit_no_episode_days']==0
    current=a.get('/api/daily-checkins').json()[0]
    assert current['day_complete'] and not current['whole_day_confirmed']
    corrected=a.put(f"/api/daily-checkins/{row['id']}",json={**data,'expected_revision':1}).json()
    assert corrected['whole_day_confirmed']
    assert a.get('/api/v1/collection-quality').json()['explicit_no_episode_days']==1


def test_migration_008_preserves_007_synthetic_values(tmp_path):
    import sqlite3
    path=tmp_path/'synthetic.db';cwd=Path(__file__).resolve().parents[1]
    env={**os.environ,'DATABASE_URL':f'sqlite:///{path.as_posix()}'}
    def upgrade(version):subprocess.run([sys.executable,'-m','alembic','upgrade',version],cwd=cwd,env=env,check=True,capture_output=True)
    upgrade('007')
    with sqlite3.connect(path) as s:
        s.execute("INSERT INTO users(id,email,display_name,password_hash,created_at) VALUES(1,'synthetic@example.test','Synthetic','unused','2025-01-01')")
        s.execute("INSERT INTO wellness(id,owner_id,date,timezone_name,recorded_at,stress,episode_observation) VALUES(1,1,'2025-01-01','UTC','2025-01-02T12:00:00Z',0,'no_episode')")
        before=s.execute('SELECT * FROM wellness').fetchall()
    upgrade('head')
    with sqlite3.connect(path) as s:
        assert s.execute('SELECT * FROM wellness').fetchall()==before
        assert s.execute('SELECT * FROM daily_checkins').fetchall()==[]
        assert s.execute('PRAGMA foreign_key_check').fetchall()==[]
