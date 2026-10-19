"""Synthetic accounts only; no outbound calling/messaging services exist."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app, Base, db, auth, User, LoginSession, Episode, Contact

PASSWORD='Synthetic-password-123'
ORIGIN='http://localhost:5173'

@pytest.fixture
def clients():
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    @event.listens_for(engine,'connect')
    def foreign_keys(connection,_): connection.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    factory=sessionmaker(bind=engine)
    def override():
        with factory() as s: yield s
    app.dependency_overrides[db]=override;auth.limiter.clear()
    with TestClient(app,headers={'Origin':ORIGIN}) as a, TestClient(app,headers={'Origin':ORIGIN}) as b:
        for client in (a,b): client.headers['X-CSRF-Token']=client.get('/api/auth/session').json()['csrf_token']
        yield a,b,factory
    app.dependency_overrides.clear();auth.limiter.clear();engine.dispose()

def register(c,email='a@example.test'):
    r=c.post('/api/auth/register',json={'email':email,'password':PASSWORD,'display_name':'Synthetic account'})
    assert r.status_code==201
    c.headers['X-CSRF-Token']=r.json()['csrf_token'];return r.json()['user']

def login(c,email='a@example.test',password=PASSWORD):
    c.headers['X-CSRF-Token']=c.get('/api/auth/session').json()['csrf_token']
    r=c.post('/api/auth/login',json={'email':email,'password':password})
    if r.status_code==200:c.headers['X-CSRF-Token']=r.json()['csrf_token']
    return r

def test_registration_login_logout_and_hash(clients):
    a,b,factory=clients
    before=a.cookies.get('migramind_session');user=register(a,'A@example.test')
    assert user['email']=='a@example.test' and a.cookies.get('migramind_session')!=before
    with factory() as s:
        row=s.get(User,user['id']);assert row.password_hash.startswith('$argon2id$')
        assert PASSWORD not in row.password_hash
        assert not s.query(LoginSession).filter_by(token_digest=a.cookies.get('migramind_session')).first()
    cookie=a.get('/api/auth/session').request.headers['cookie']
    assert a.post('/api/auth/logout').status_code==204
    assert a.get('/api/episodes').status_code==401
    assert b.get('/api/episodes',headers={'Cookie':cookie}).status_code==401
    assert login(a,password='wrong').status_code==401
    unknown=login(b,email='unknown@example.test',password='wrong')
    assert unknown.status_code==401 and unknown.json()==login(a,password='wrong').json()
    assert login(a).status_code==200
    assert a.get('/api/account').json()['id']==user['id']
    assert a.put('/api/account',json={'display_name':'Updated'}).json()['display_name']=='Updated'

def test_csrf_cookie_and_origin(clients):
    a,b,_=clients
    cookie=a.get('/api/auth/session').headers.get('set-cookie')
    # Initial bootstrap sets the HttpOnly cookie; inspect the original attributes on a fresh client.
    b.cookies.clear();r=b.get('/api/auth/session');cookie=r.headers['set-cookie'].lower()
    assert 'httponly' in cookie and 'samesite=lax' in cookie and 'path=/' in cookie
    assert 'csrf_token' in r.json() and 'token_digest' not in r.text
    payload={'email':'csrf@example.test','password':PASSWORD,'display_name':'Synthetic'}
    assert a.post('/api/auth/register',json=payload,headers={'X-CSRF-Token':''}).status_code==403
    assert a.post('/api/auth/register',json=payload,headers={'Origin':'https://evil.example'}).status_code==403
    assert a.post('/api/auth/register',json=payload,headers={'X-CSRF-Token':r.json()['csrf_token']}).status_code==403
    register(a)
    assert a.post('/api/attack-sessions/start',headers={'X-CSRF-Token':'invalid'}).status_code==403
    assert a.post('/api/auth/logout',headers={'Origin':'null'}).status_code==403
    assert a.get('/api/episodes').headers['cache-control']=='no-store'

@pytest.mark.parametrize('kind',['invalid','expired'])
def test_expired_invalid_sessions(clients,kind):
    a,_,factory=clients;register(a)
    if kind=='invalid':a.cookies.set('migramind_session','invalid')
    else:
        with factory() as s:
            s.query(LoginSession).update({'expires_at':'2000-01-01T00:00:00+00:00'});s.commit()
    assert a.get('/api/episodes').status_code==401
    assert a.post('/api/attack-sessions/start').status_code==401
    assert a.get('/api/auth/session').json()['user'] is None

def test_auth_rate_limiting_and_duplicate_registration(clients):
    a,b,_=clients;register(a)
    assert b.post('/api/auth/register',json={'email':'a@example.test','password':PASSWORD,'display_name':'Synthetic'}).json()['detail']=='Unable to create an account with those details'
    for _ in range(12):r=login(b,password='wrong')
    assert r.status_code==429 and r.headers['retry-after']=='900'

def test_production_cookie_and_password_validation_redaction(clients,monkeypatch):
    from fastapi import FastAPI
    from app.auth import Authentication
    from app.main import SharingConsent
    a,_,_=clients
    bad=a.post('/api/auth/register',json={'email':'bad','password':'secret','display_name':'Synthetic'})
    assert bad.status_code==422 and 'secret' not in bad.text and 'input' not in bad.text
    monkeypatch.setenv('APP_ENV','production')
    production=FastAPI()
    Authentication(production,db,User,LoginSession,SharingConsent,Contact,[])
    production.dependency_overrides[db]=app.dependency_overrides[db]
    with TestClient(production,base_url='https://testserver') as c:
        cookie=c.get('/api/auth/session').headers['set-cookie']
        assert '__Host-migramind_session=' in cookie and 'Secure' in cookie and 'HttpOnly' in cookie
        assert 'Domain=' not in cookie

def test_all_health_routes_require_authentication(clients):
    a,_,_=clients
    for route in app.routes:
        path=getattr(route,'path','')
        if not path.startswith('/api/') or path=='/api/health' or path.startswith('/api/auth/'):continue
        path=path.replace('{id}','1')
        for method in route.methods:
            r=a.request(method,path,json={} if method not in ('GET','HEAD') else None)
            assert r.status_code==401,(method,path,r.status_code)

def test_cross_user_crud_references_insights_and_exports(clients):
    a,b,factory=clients;ua=register(a);ub=register(b,'b@example.test')
    entries={
      'episodes':{'date':'2026-10-19','severity':7,'notes':'Synthetic A only'},
      'wellness':{'date':'2026-10-19','timezone_name':'Asia/Kolkata','sleep_hours':6},
      'early-symptoms':{'symptom':'Synthetic yawning','onset_at':'2026-10-19T00:00:00+05:30','timezone_name':'Asia/Kolkata'},
      'contacts':{'name':'Synthetic contact A','phone':'+12025550100','relationship':'Friend'}}
    rows={}
    for resource,payload in entries.items():
        r=a.post('/api/'+resource,json=payload);assert r.status_code==201
        rows[resource]=r.json()
        assert b.get('/api/'+resource).json()==[]
        assert b.put(f'/api/{resource}/{r.json()["id"]}',json=payload).status_code==404
        assert b.delete(f'/api/{resource}/{r.json()["id"]}').status_code==404
        own=b.post('/api/'+resource,json=payload);assert own.status_code==201
        assert own.json()['owner_id']==ub['id']
    assert b.post('/api/contacts',json={**entries['contacts'],'owner_id':ua['id']}).status_code==422
    a.put('/api/profile',json={'name':'A only','support':'Synthetic support','avoid':'Synthetic avoidance'})
    assert b.get('/api/profile').json()['name']!='A only'
    assert a.put('/api/support/preferences',json={'preferred_contact_id':rows['contacts']['id'],'communication_method':'sms'}).status_code==200
    assert b.get('/api/support/preferences').json()['preferred_contact_id'] is None
    assert b.put('/api/support/preferences',json={'preferred_contact_id':rows['contacts']['id']}).status_code==422
    sa=a.post('/api/attack-sessions/start').json()
    assert b.get('/api/attack-sessions/current').json() is None
    assert b.post(f'/api/attack-sessions/{sa["id"]}/end').status_code==404
    sb=b.post('/api/attack-sessions/start').json();assert sa['id']!=sb['id']
    assert b.post('/api/episodes',json={**entries['episodes'],'attack_session_id':sa['id']}).status_code==422
    a.post(f'/api/attack-sessions/{sa["id"]}/end');b.post(f'/api/attack-sessions/{sb["id"]}/end')
    feedback={'session_id':sa['id'],'action_id':'support_card','helpful':True}
    fa=a.post('/api/support/feedback',json=feedback).json()
    assert b.post('/api/support/feedback',json=feedback).status_code==404
    assert b.get('/api/support/feedback').json()==[]
    assert b.delete(f'/api/support/feedback/{fa["id"]}').status_code==404
    consent=a.post('/api/account/consents',json={'contact_id':rows['contacts']['id'],'scope':'support_card','confirmed':True}).json()
    assert b.get('/api/account/consents').json()==[]
    assert b.delete(f'/api/account/consents/{consent["id"]}').status_code==404
    assert b.post('/api/account/consents',json={'contact_id':rows['contacts']['id'],'scope':'support_card','confirmed':True}).status_code==404
    assert b.get('/api/support/recommendations').json()['contact_id']==rows['contacts']['id']+1
    export=b.get('/api/export');assert export.status_code==200
    data=export.json();assert data['account']['email']=='b@example.test'
    assert data['support_feedback']==[] and data['sharing_consents']==[]
    for key in ('password_hash','token_digest','csrf_token','owner_id'):assert key not in export.text
    assert {r['id'] for r in data['episodes']}!={rows['episodes']['id']}
    assert len(data['attack_sessions'])==1 and data['attack_sessions'][0]['id']==sb['id']
    assert b.get('/api/insights?as_of=2026-10-19').json()['episode_count']==1
    b.post('/api/support/preferences/reset')
    assert a.get('/api/support/preferences').json()['communication_method']=='sms'

def test_account_deletion_revokes_sessions_and_preserves_other_and_unclaimed_data(clients):
    a,b,factory=clients;ua=register(a);ub=register(b,'b@example.test')
    a.post('/api/episodes',json={'date':'2026-10-19'});b.post('/api/episodes',json={'date':'2026-10-19'})
    c=a.post('/api/contacts',json={'name':'Synthetic','phone':'+12025550100','relationship':'Friend'}).json()
    a.get('/api/profile');a.put('/api/support/preferences',json={'preferred_contact_id':c['id']})
    consent=a.post('/api/account/consents',json={'contact_id':c['id'],'scope':'support_card','confirmed':True}).json()
    assert a.delete(f'/api/account/consents/{consent["id"]}').status_code==204
    assert a.get('/api/account/consents').json()[0]['revoked_at']
    session=a.post('/api/attack-sessions/start').json();a.post(f'/api/attack-sessions/{session["id"]}/end')
    a.post('/api/support/feedback',json={'session_id':session['id'],'action_id':'support_card','helpful':True})
    with factory() as s:
        s.add(Episode(date='2020-01-01',severity=1,duration=10,trigger='Unknown',notes='Unassigned synthetic'));s.commit()
    assert a.get('/api/export').json()['episodes'][0]['date']!='2020-01-01'
    with TestClient(app,headers={'Origin':ORIGIN}) as other:
        assert login(other).status_code==200
        assert a.request('DELETE','/api/account',json={'password':'wrong','confirmation':'DELETE'}).status_code==400
        assert a.request('DELETE','/api/account',json={'password':PASSWORD,'confirmation':'no'}).status_code==400
        assert a.request('DELETE','/api/account',json={'password':PASSWORD,'confirmation':'DELETE'}).status_code==204
        assert other.get('/api/account').status_code==401
    with factory() as s:
        assert s.get(User,ua['id']) is None and s.get(User,ub['id']) is not None
        assert s.query(Episode).filter_by(owner_id=ua['id']).count()==0
        assert s.query(Episode).filter_by(owner_id=None).count()==1
        assert s.query(LoginSession).filter_by(user_id=ua['id']).count()==0
    assert len(b.get('/api/episodes').json())==1

def test_004_migration_preserves_all_legacy_tables_and_links(tmp_path):
    import os, subprocess, sys, sqlite3
    from pathlib import Path
    path=tmp_path/'legacy.db';cwd=Path(__file__).resolve().parents[1]
    env={**os.environ,'DATABASE_URL':f'sqlite:///{path.as_posix()}'}
    def upgrade(version):subprocess.run([sys.executable,'-m','alembic','upgrade',version],cwd=cwd,env=env,check=True,capture_output=True)
    upgrade('004')
    with sqlite3.connect(path) as c:
        c.execute("INSERT INTO contacts VALUES(1,'Synthetic','Friend','+12025550100')")
        c.execute("INSERT INTO profiles VALUES(1,'Synthetic','Quiet','Noise','Text')")
        c.execute("INSERT INTO attack_sessions VALUES(1,'2026-10-19T00:00:00+00:00',NULL,1)")
        c.execute("INSERT INTO episodes(date,severity,duration,trigger,notes,pain_location,symptoms,functional_impact,medications,attack_session_id) VALUES('2026-10-19',5,60,'Unknown','Synthetic','','[]','','[]',1)")
        c.execute("INSERT INTO wellness(date,timezone_name,recorded_at) VALUES('2026-10-19','Asia/Kolkata','2026-10-19T00:00:00+00:00')")
        c.execute("INSERT INTO early_symptoms(symptom,onset_at,timezone_name,recorded_at,notes) VALUES('Synthetic','2026-10-19T00:00:00+00:00','Asia/Kolkata','2026-10-19T00:00:00+00:00','')")
        c.execute("INSERT INTO support_preferences(id,preferred_contact_id) VALUES(1,1)")
        c.execute("INSERT INTO support_feedback VALUES(1,1,'support_card',1,'2026-10-19T01:00:00+00:00')")
        tables=['episodes','wellness','early_symptoms','contacts','profiles','attack_sessions','support_preferences','support_feedback']
        before={t:c.execute('SELECT * FROM '+t).fetchall() for t in tables}
    upgrade('head')
    with sqlite3.connect(path) as c:
        for table in tables:
            after=c.execute('SELECT * FROM '+table).fetchall()
            assert [r[:-1] for r in after]==before[table]
            assert all(r[-1] is None for r in after)
        assert c.execute('PRAGMA foreign_key_check').fetchall()==[]
        assert c.execute('SELECT COUNT(*) FROM users').fetchone()[0]==0
