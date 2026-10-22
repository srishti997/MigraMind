import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app, Base, db
@pytest.fixture
def client():
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory=sessionmaker(bind=engine)
    def override():
        with factory() as s: yield s
    app.dependency_overrides[db]=override
    from app.main import auth
    auth.limiter.clear()
    with TestClient(app, headers={'Origin':'http://localhost:5173'}) as c:
        c.headers['X-CSRF-Token']=c.get('/api/auth/session').json()['csrf_token']
        registered=c.post('/api/auth/register',json={'email':'fixture@example.test','password':'Synthetic-password-123','display_name':'Demo'})
        assert registered.status_code==201
        c.headers['X-CSRF-Token']=registered.json()['csrf_token']
        c.user_id=registered.json()['user']['id']
        yield c
    app.dependency_overrides.clear()
def test_episode_lifecycle(client):
    data={'date':'2026-10-19','severity':5,'duration':90,'trigger':'Stress','notes':'Synthetic'}
    r=client.post('/api/episodes',json=data); assert r.status_code==201
    id=r.json()['id']; assert len(client.get('/api/episodes').json())==1
    assert client.put(f'/api/episodes/{id}',json={**data,'severity':2}).json()['severity']==2
    assert client.delete(f'/api/episodes/{id}').status_code==204
    assert client.get('/api/episodes').json()==[]
    assert client.delete(f'/api/episodes/{id}').status_code==404

def test_sos_preferences_persist_and_old_clients_preserve_new_fields(client):
    values={'help_message':'Synthetic: please text before visiting.','emergency_number':'999'}
    assert client.put('/api/support/preferences',json=values).status_code==200
    saved=client.get('/api/support/preferences').json()
    for key,value in values.items():assert saved[key]==value
    assert client.put('/api/support/preferences',json={'communication_method':'sms'}).status_code==200
    saved=client.get('/api/support/preferences').json()
    for key,value in values.items():assert saved[key]==value
    p={'name':'Synthetic','support':'Ask first','avoid':'Noise','communication':'Text','environment':'Synthetic chosen environment'}
    assert client.put('/api/profile',json=p).status_code==200
    client.put('/api/profile',json={k:v for k,v in p.items() if k!='environment'})
    assert client.get('/api/profile').json()['environment']==p['environment']
    exported=client.get('/api/export').json()
    assert exported['profiles'][0]['environment']==p['environment']
    assert exported['support_preferences'][0]['help_message']==values['help_message']
    assert 'location' not in exported['support_preferences'][0]
    reset=client.post('/api/support/preferences/reset').json()
    assert reset['emergency_number']=='112' and reset['help_message']!=values['help_message']

@pytest.mark.parametrize('value',[{'emergency_number':'tel:112'},{'emergency_number':'1'},{'emergency_number':'1234567'},
    {'help_message':''},{'help_message':'x'*401},{'location':{'latitude':12.34,'longitude':56.78}}])
def test_sos_validation_and_no_location_storage(client,value):
    assert client.put('/api/support/preferences',json=value).status_code==422

def test_006_migration_preserves_owned_and_unassigned_preferences(tmp_path):
    import os,subprocess,sys,sqlite3
    from pathlib import Path
    path=tmp_path/'sos-migration.db';cwd=Path(__file__).resolve().parents[1]
    env={**os.environ,'DATABASE_URL':f'sqlite:///{path.as_posix()}'}
    def upgrade(version):subprocess.run([sys.executable,'-m','alembic','upgrade',version],cwd=cwd,env=env,check=True,capture_output=True)
    upgrade('005')
    with sqlite3.connect(path) as c:
        c.execute("INSERT INTO users VALUES(1,'synthetic@example.test','Synthetic','synthetic-not-a-real-hash','2026-10-19T00:00:00Z')")
        c.execute("INSERT INTO profiles(id,name,support,avoid,communication,owner_id) VALUES(1,'Synthetic legacy','Ask first','Noise','Text',NULL),(2,'Synthetic owner','Ask me','Fragrance','Text first',1)")
        c.execute('INSERT INTO support_preferences(id,owner_id) VALUES(1,NULL),(2,1)')
        c.execute("INSERT INTO attack_sessions(id,started_at,ended_at,active_slot,owner_id) VALUES(1,'2026-10-19T00:00:00Z',NULL,1,1)")
        before=c.execute('SELECT id,name,support,avoid,communication,owner_id FROM profiles ORDER BY id').fetchall()
    upgrade('head')
    with sqlite3.connect(path) as c:
        assert c.execute('SELECT id,name,support,avoid,communication,owner_id FROM profiles ORDER BY id').fetchall()==before
        assert c.execute('SELECT environment FROM profiles').fetchall()==[('',),('',)]
        assert c.execute('SELECT owner_id,emergency_number FROM support_preferences ORDER BY id').fetchall()==[(None,'112'),(1,'112')]
        assert all(row[0] for row in c.execute('SELECT help_message FROM support_preferences'))
        assert c.execute('SELECT owner_id,active_slot,ended_at FROM attack_sessions').fetchone()==(1,1,None)
        assert c.execute('PRAGMA foreign_key_check').fetchall()==[]
def test_validation(client):
    assert client.post('/api/episodes',json={'date':'bad','severity':11,'duration':-1}).status_code==422
def test_support(client):
    contact={'name':'Demo','relationship':'Friend','phone':'+12025550123'}
    r=client.post('/api/contacts',json=contact); assert r.status_code==201
    id=r.json()['id']
    assert client.put(f'/api/contacts/{id}',json={**contact,'name':'Updated'}).json()['name']=='Updated'
    assert client.delete(f'/api/contacts/{id}').status_code==204
    p={'name':'Alex','support':'Quiet please','avoid':'Noise'}
    assert client.put('/api/profile',json=p).status_code==200
    assert client.get('/api/profile').json()['support']=='Quiet please'
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.main import AttackSession

def test_attack_session_persistence_and_idempotency(client):
    assert client.get('/api/attack-sessions/current').json() is None
    first = client.post('/api/attack-sessions/start').json()
    assert datetime.fromisoformat(first['started_at']).utcoffset().total_seconds() == 0
    assert first['ended_at'] is None
    assert client.post('/api/attack-sessions/start').json() == first
    # Each request opens a new database session; this confirms persisted state.
    assert client.get('/api/attack-sessions/current').json() == first
    ended = client.post(f"/api/attack-sessions/{first['id']}/end").json()
    assert datetime.fromisoformat(ended['ended_at']) >= datetime.fromisoformat(first['started_at'])
    assert client.post(f"/api/attack-sessions/{first['id']}/end").json() == ended
    second = client.post('/api/attack-sessions/start').json()
    assert second['id'] != first['id']
    assert client.post(f"/api/attack-sessions/{first['id']}/end").json() == ended
    assert client.get('/api/attack-sessions/current').json() == second
    assert len(client.get('/api/attack-sessions').json()) == 2
    assert client.post('/api/attack-sessions/99999/end').status_code == 404

def test_communication_preferences(client):
    p = {'name':'Demo','support':'Dim room','avoid':'Noise','communication':'Text first'}
    assert client.put('/api/profile',json=p).status_code == 200
    assert client.get('/api/profile').json()['communication'] == 'Text first'
    # Older profile clients must not erase newly saved communication preferences.
    client.put('/api/profile',json={k:v for k,v in p.items() if k != 'communication'})
    assert client.get('/api/profile').json()['communication'] == 'Text first'

def test_database_prevents_duplicate_active_sessions(client):
    from app.main import db
    from sqlalchemy import select
    client.post('/api/attack-sessions/start')
    generator=client.app.dependency_overrides[db]()
    s=next(generator)
    try:
        s.add(AttackSession(owner_id=client.user_id,started_at='2026-10-19T12:00:00+00:00',active_slot=1))
        try:
            s.commit()
            assert False, 'Database must reject duplicate active session'
        except IntegrityError:
            s.rollback()
        assert len(s.scalars(select(AttackSession)).all()) == 1
    finally:
        generator.close()


def test_additive_migration_preserves_existing_data(tmp_path):
    import os, subprocess, sys, sqlite3
    from pathlib import Path
    database = tmp_path / 'migration.db'
    env = {**os.environ, 'DATABASE_URL': f'sqlite:///{database.as_posix()}'}
    cwd = Path(__file__).resolve().parents[1]
    def migrate(version):
        subprocess.run([sys.executable,'-m','alembic','upgrade',version],cwd=cwd,env=env,check=True,capture_output=True)
    migrate('001')
    with sqlite3.connect(database) as connection:
        connection.execute("INSERT INTO profiles VALUES (1, 'Demo', 'Quiet', 'Noise')")
        connection.execute("INSERT INTO contacts VALUES (1, 'Demo', 'Friend', '+12025550123')")
        connection.execute("INSERT INTO episodes VALUES (1, '2026-10-19', 5, 60, 'Unknown', 'Synthetic')")
    migrate('head')
    with sqlite3.connect(database) as connection:
        assert connection.execute('SELECT support, communication FROM profiles').fetchone() == ('Quiet','')
        assert connection.execute('SELECT COUNT(*) FROM episodes').fetchone()[0] == 1
        assert connection.execute('SELECT owner_id FROM episodes').fetchone()[0] is None
        assert connection.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0
        assert connection.execute('SELECT COUNT(*) FROM contacts').fetchone()[0] == 1
        assert connection.execute('SELECT COUNT(*) FROM attack_sessions').fetchone()[0] == 0

def timed_episode(**changes):
    return {'started_at':'2026-10-18T23:30:00+05:30','ended_at':'2026-10-19T01:30:00+05:30','timezone_name':'Asia/Kolkata','severity':6,'pain_location':'Left temple','symptoms':['Nausea'],'functional_impact':'Some activities limited','medications':[{'name':'Synthetic medication','taken_at':'2026-10-19T00:00:00+05:30'}],**changes}

def test_advanced_episode_crud_timestamps_multiple_per_day(client):
    sid=client.post('/api/attack-sessions/start').json()['id']
    data=timed_episode(attack_session_id=sid)
    r=client.post('/api/episodes',json=data)
    assert r.status_code==201,r.text
    row=r.json()
    assert row['started_at']=='2026-10-18T18:00:00+00:00'
    assert row['ended_at']=='2026-10-18T20:00:00+00:00'
    assert row['date']=='2026-10-18' and row['duration']==120
    assert row['timezone_name']=='Asia/Kolkata'
    assert row['medications'][0]['taken_at']=='2026-10-18T18:30:00+00:00'
    assert client.post('/api/episodes',json=timed_episode(severity=0)).status_code==201
    assert len([r for r in client.get('/api/episodes').json() if r['date']=='2026-10-18'])==2
    changed=client.put(f"/api/episodes/{row['id']}",json=timed_episode(severity=0,ended_at=None)).json()
    assert changed['severity']==0 and changed['duration'] is None
    assert client.get('/api/attack-sessions/current').json()['ended_at'] is None
    assert client.delete(f"/api/episodes/{row['id']}").status_code==204

def test_optional_unknown_episode_values(client):
    row=client.post('/api/episodes',json={'started_at':'2026-10-19T01:00:00Z','timezone_name':'Asia/Kolkata'}).json()
    assert row['severity'] is None and row['duration'] is None
    assert row['medications']==[] and row['symptoms']==[]
    legacy=client.post('/api/episodes',json={'date':'2026-10-19','severity':4,'duration':60}).json()
    assert legacy['started_at'] is None and legacy['timezone_name'] is None

@pytest.mark.parametrize('changes',[
    {'started_at':'2026-10-19T01:00:00'},
    {'ended_at':'2026-10-17T00:00:00Z'},
    {'severity':-1},{'severity':11},{'timezone_name':'Not/AZone'},
    {'timezone_name':None},{'medications':[{'name':'Demo','taken_at':'2026-10-19T00:00:00'}]},
    {'medications':[{'name':'','taken_at':'2026-10-19T00:00:00Z'}]},
    {'attack_session_id':99999},{'symptoms':['x'*101]},
])
def test_advanced_validation(client,changes):
    assert client.post('/api/episodes',json=timed_episode(**changes)).status_code==422

def test_wellness_crud_and_unknown_not_zero(client):
    p={'date':'2026-10-19','timezone_name':'Asia/Kolkata'}
    r=client.post('/api/wellness',json=p);assert r.status_code==201,r.text
    row=r.json();assert row['stress'] is None and row['missed_meals'] is None
    assert client.post('/api/wellness',json=p).status_code==409
    changed=client.put(f"/api/wellness/{row['id']}",json={**p,'sleep_hours':7.5,'stress':0,'missed_meals':False,'menstrual_notes':'Synthetic observation'}).json()
    assert changed['stress']==0 and changed['missed_meals'] is False
    assert changed['recorded_at']==row['recorded_at']
    assert len(client.get('/api/wellness').json())==1
    for bad in [{'sleep_hours':25},{'hydration_ml':-1},{'screen_hours':25},{'sleep_quality':11},{'timezone_name':'bad'}]:
        assert client.put(f"/api/wellness/{row['id']}",json={**p,**bad}).status_code==422
    assert client.delete(f"/api/wellness/{row['id']}").status_code==204
    assert client.delete(f"/api/wellness/{row['id']}").status_code==404

def test_early_symptoms_are_separate_and_timezone_aware(client):
    p={'symptom':'Synthetic yawning','onset_at':'2026-10-18T23:30:00-04:00','timezone_name':'America/New_York'}
    r=client.post('/api/early-symptoms',json=p);assert r.status_code==201,r.text
    row=r.json();assert row['onset_at']=='2026-10-19T03:30:00+00:00'
    assert client.get('/api/episodes').json()==[]
    assert client.put(f"/api/early-symptoms/{row['id']}",json={**p,'notes':'Synthetic'}).json()['notes']=='Synthetic'
    assert len(client.get('/api/early-symptoms').json())==1
    assert client.post('/api/early-symptoms',json={**p,'onset_at':'2026-10-19T01:00'}).status_code==422
    assert client.delete(f"/api/early-symptoms/{row['id']}").status_code==204

def test_insights_headache_days_severity_and_known_durations(client):
    empty=client.get('/api/insights?as_of=2026-10-19&timezone_name=Asia/Kolkata').json()
    assert empty['data_status']=='insufficient_data' and empty['episode_count'] is None
    client.post('/api/episodes',json=timed_episode())
    client.post('/api/episodes',json=timed_episode(severity=0,ended_at=None))
    client.post('/api/episodes',json={'date':'2026-10-18','severity':3,'duration':60})
    client.post('/api/episodes',json={'date':'2026-09-19','severity':10,'duration':100})
    client.post('/api/episodes',json={'date':'2026-10-20','severity':10,'duration':100})
    stats=client.get('/api/insights?as_of=2026-10-19&timezone_name=Asia/Kolkata').json()
    assert stats['headache_days']==2 and stats['episode_count']==3
    assert stats['average_severity']==3 and stats['average_duration_minutes']==90
    assert stats['duration_count']==2 and sum(d['episodes'] for d in stats['daily'])==3
    assert len(stats['daily'])==30
    # Same UTC timestamps cross two dates in India, only one date in UTC.
    assert client.get('/api/insights?as_of=2026-10-19&timezone_name=UTC').json()['headache_days']==1
    assert client.get('/api/insights?timezone_name=invalid').status_code==422

def test_no_episodes_recorded_not_confirmed_attack_free(client):
    client.post('/api/wellness',json={'date':'2026-10-19','timezone_name':'Asia/Kolkata'})
    row=client.get('/api/insights?as_of=2026-10-19').json()
    assert row['episode_count']==0 and row['data_status']=='no_episodes_recorded'
    assert row['average_severity'] is None
    client.post('/api/episodes',json={'date':'2026-10-19'})
    assert client.get('/api/insights?as_of=2026-10-19').json()['headache_days'] is None

def test_export_preserves_unknown_values_and_all_record_types(client):
    client.post('/api/episodes',json=timed_episode())
    client.post('/api/wellness',json={'date':'2026-10-19','timezone_name':'Asia/Kolkata'})
    client.post('/api/early-symptoms',json={'symptom':'Synthetic fatigue','onset_at':'2026-10-19T00:00:00Z','timezone_name':'UTC'})
    client.post('/api/attack-sessions/start')
    r=client.get('/api/export');assert r.status_code==200
    assert r.headers['cache-control']=='no-store' and 'attachment' in r.headers['content-disposition']
    data=r.json();assert data['schema_version']==5
    for key in ['episodes','wellness','early_symptoms','attack_sessions']: assert len(data[key])==1
    assert data['wellness'][0]['sleep_hours'] is None
    assert data['episodes'][0]['medications'][0]['name']=='Synthetic medication'
    assert 'active_slot' not in data['attack_sessions'][0]

def test_headache_overlap_midnight_and_deduplication(client):
    # An episode before the window that overlaps its first day still counts that headache day.
    client.post('/api/episodes',json=timed_episode(started_at='2026-09-19T23:00:00Z',ended_at='2026-09-21T00:00:00Z',timezone_name='UTC'))
    client.post('/api/episodes',json=timed_episode(started_at='2026-09-20T12:00:00Z',ended_at='2026-09-20T13:00:00Z',timezone_name='UTC'))
    stats=client.get('/api/insights?as_of=2026-10-19&timezone_name=UTC').json()
    assert stats['headache_days']==1  # Sep 20, excluding the midnight endpoint on Sep 21.
    assert stats['episode_count']==1

def test_forecast_v1_is_unavailable_without_probability_or_emergency_effects(client):
    response=client.get('/api/v1/forecast')
    assert response.status_code==200 and response.headers['cache-control']=='no-store'
    body=response.json()
    assert body['api_version']=='v1' and body['status']=='insufficient_data'
    assert body['probability'] is None and body['model_version'] is None
    assert body['clinically_validated'] is False and body['emergency_actions_affected'] is False
    assert client.get('/api/attack-sessions/current').json() is None
    # Query parameters cannot activate an unvalidated model or bypass readiness.
    assert client.get('/api/v1/forecast?data_ready=true').json()['probability'] is None

def test_forecast_service_stays_unavailable_even_if_future_data_review_passes():
    from app.forecasting import ForecastServiceV1
    status=ForecastServiceV1().status(data_ready=True)
    assert status.status=='model_unavailable' and status.probability is None

def ended_support_session(client):
    row=client.post('/api/attack-sessions/start').json()
    assert client.post(f"/api/attack-sessions/{row['id']}/end").status_code==200
    return row['id']

def test_support_choices_persist_reset_without_erasing_caregiver_or_feedback(client):
    contact=client.post('/api/contacts',json={'name':'Synthetic contact','relationship':'Friend','phone':'+12025550123'}).json()
    values={'preferred_contact_id':contact['id'],'communication_method':'sms','preferred_actions':['prepare_sms','support_card'],
        'large_text':True,'reduce_motion':True,'simplified_view':True,'use_feedback':True,'ranking_mode':'adaptive'}
    response=client.put('/api/support/preferences',json=values);assert response.status_code==200,response.text
    assert client.get('/api/support/preferences').json()['preferred_actions']==values['preferred_actions']
    client.put('/api/profile',json={'name':'Demo','support':'Quiet','avoid':'Noise','communication':'Text first'})
    session=ended_support_session(client)
    client.post('/api/support/feedback',json={'session_id':session,'action_id':'prepare_sms','helpful':True})
    reset=client.post('/api/support/preferences/reset').json()
    assert reset['preferred_contact_id'] is None and reset['preferred_actions']==[]
    assert reset['use_feedback'] is False and reset['large_text'] is False
    assert client.get('/api/profile').json()['support']=='Quiet'
    assert len(client.get('/api/support/feedback').json())==1

def test_support_preference_validation_and_deleted_contact(client):
    assert client.put('/api/support/preferences',json={'preferred_contact_id':999}).status_code==422
    assert client.put('/api/support/preferences',json={'preferred_actions':['prepare_sms','prepare_sms']}).status_code==422
    assert client.put('/api/support/preferences',json={'preferred_actions':['emergency_call']}).status_code==422
    contact=client.post('/api/contacts',json={'name':'Synthetic','relationship':'Friend','phone':'12345'}).json()
    client.put('/api/support/preferences',json={'preferred_contact_id':contact['id']})
    client.delete(f"/api/contacts/{contact['id']}")
    assert client.get('/api/support/preferences').json()['preferred_contact_id'] is None

def test_support_no_contacts_and_cold_start_are_explained(client):
    body=client.get('/api/support/recommendations').json()
    assert body['recommended_action']=='support_card'
    assert body['contact_id'] is None
    assert {a['id'] for a in body['actions']}=={'call_contact','prepare_sms','support_card'}
    assert [a['available'] for a in body['actions']]==[True,False,False]
    contact=client.post('/api/contacts',json={'name':'Demo','relationship':'Friend','phone':'12345'}).json()
    body=client.get('/api/support/recommendations').json()
    assert body['recommended_action']=='call_contact' and body['contact_id']==contact['id']
    assert all(a['explanation'] for a in body['actions'])
    assert body['feedback_ranking_enabled'] is False

def test_feedback_optional_after_end_crud_and_export(client):
    active=client.post('/api/attack-sessions/start').json()
    payload={'session_id':active['id'],'action_id':'support_card','helpful':True}
    assert client.post('/api/support/feedback',json=payload).status_code==409
    client.post(f"/api/attack-sessions/{active['id']}/end")
    response=client.post('/api/support/feedback',json=payload);assert response.status_code==201,response.text
    row=response.json();assert row['session_id']==active['id'] and row['action_id']=='support_card'
    assert client.post('/api/support/feedback',json=payload).status_code==409
    assert client.post('/api/support/feedback',json={**payload,'action_id':'emergency_call'}).status_code==422
    assert client.post('/api/support/feedback',json={**payload,'action_id':'call_contact','helpful':'yes'}).status_code==422
    assert client.post('/api/support/feedback',json={**payload,'session_id':999}).status_code==404
    assert client.get('/api/export').json()['support_feedback'][0]['helpful'] is True
    assert client.delete(f"/api/support/feedback/{row['id']}").status_code==204
    assert client.get('/api/support/feedback').json()==[]
    assert client.delete(f"/api/support/feedback/{row['id']}").status_code==404

def test_feedback_for_old_session_blocked_during_another_active_session(client):
    old=ended_support_session(client);client.post('/api/attack-sessions/start')
    assert client.post('/api/support/feedback',json={'session_id':old,'action_id':'call_contact','helpful':False}).status_code==409

def test_feedback_ranking_opt_in_minimum_evidence_pins_and_fixed_baseline(client):
    contact=client.post('/api/contacts',json={'name':'Demo','relationship':'Friend','phone':'12345'}).json()
    for i in range(3):
        sid=ended_support_session(client)
        assert client.post('/api/support/feedback',json={'session_id':sid,'action_id':'prepare_sms','helpful':True}).status_code==201
        if i==1:
            client.put('/api/support/preferences',json={'use_feedback':True})
            assert client.get('/api/support/recommendations').json()['recommended_action']=='call_contact'
    client.put('/api/support/preferences',json={'use_feedback':False})
    assert client.get('/api/support/recommendations').json()['recommended_action']=='call_contact'
    client.put('/api/support/preferences',json={'use_feedback':True})
    ranked=client.get('/api/support/recommendations').json()
    assert ranked['recommended_action']=='prepare_sms'
    assert '3 of 3' in ranked['actions'][0]['explanation']
    assert client.get('/api/support/recommendations?policy=fixed').json()['recommended_action']=='call_contact'
    client.put('/api/support/preferences',json={'use_feedback':True,'preferred_actions':['call_contact'],'preferred_contact_id':contact['id']})
    assert client.get('/api/support/recommendations').json()['recommended_action']=='call_contact'
    client.put('/api/support/preferences',json={'communication_method':'call','use_feedback':True})
    assert client.get('/api/support/recommendations').json()['recommended_action']=='call_contact'
    # Removing evidence must remove its influence without retraining a model.
    for f in client.get('/api/support/feedback').json():client.delete(f"/api/support/feedback/{f['id']}")
    client.put('/api/support/preferences',json={'use_feedback':True})
    assert client.get('/api/support/recommendations').json()['recommended_action']=='call_contact'

def test_support_recommendation_reads_do_not_dispatch_or_start_sessions(client):
    for _ in range(3):assert client.get('/api/support/recommendations').status_code==200
    assert client.get('/api/attack-sessions').json()==[]
    assert client.get('/api/support/feedback').json()==[]
    assert client.get('/api/v1/forecast').json()['probability'] is None
