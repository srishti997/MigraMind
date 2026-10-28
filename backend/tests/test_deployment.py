"""Synthetic-only deployment/provisioning checks; never open the app's private DB."""
import asyncio
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.deployment import DemoBoundary, database_ready, operation_event, SCHEMA_REVISION, DEMO_EMAIL
from app.demo import provision
from app.security import SecuritySettings
from test_security import PRODUCTION

BACKEND = Path(__file__).resolve().parents[1]
ACK = 'synthetic-only-no-real-health-data'


@pytest.mark.parametrize('changes', [
    {'DATA_MODE': ''}, {'DATA_MODE': 'local'}, {'DATA_MODE': 'real'},
    {'DEMO_ACKNOWLEDGEMENT': ''}, {'DEMO_ACKNOWLEDGEMENT': 'yes'},
    {'DATABASE_URL':'postgresql+psycopg://synthetic:synthetic@localhost/ordinary?sslmode=verify-full'},
])
def test_hosted_demo_requires_explicit_mode_ack_and_dedicated_target(changes):
    with pytest.raises(RuntimeError):
        SecuritySettings.load({**PRODUCTION, **changes})


def demo_database(tmp_path):
    path = tmp_path/'migramind-synthetic-demo.sqlite'
    environment = {**os.environ, 'APP_ENV':'development', 'DATA_MODE':'synthetic',
        'DEMO_ACKNOWLEDGEMENT':ACK, 'DATABASE_URL':'sqlite:///'+path.as_posix(),
        'CORS_ORIGINS':'http://localhost:5173', 'ALLOWED_HOSTS':'testserver,localhost,127.0.0.1'}
    result = subprocess.run([sys.executable,'-m','alembic','upgrade','head'], cwd=BACKEND,
        env=environment,capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    engine = create_engine(environment['DATABASE_URL'])
    return path, environment, engine, sessionmaker(bind=engine)


def test_empty_marker_is_not_synthetic_attestation_and_provision_is_non_destructive(tmp_path):
    from app.main import User, DailyCheckin
    _, env, engine, factory = demo_database(tmp_path)
    assert database_ready(engine) and not database_ready(engine, True)
    with factory() as session:
        provision(session, 'Synthetic-demo-password-123', SecuritySettings.load(env))
    assert database_ready(engine, True)
    with factory() as session:
        assert session.query(User).one().email == DEMO_EMAIL
        assert session.query(DailyCheckin).count() == 3
        with pytest.raises(ValueError, match='nonempty'):
            provision(session, 'Synthetic-demo-password-123', SecuritySettings.load(env))
        assert session.query(DailyCheckin).count() == 3
    with engine.begin() as connection:
        connection.execute(text("UPDATE demo_deployments SET fixture_version='invalid'"))
    assert not database_ready(engine, True)
    engine.dispose()


def test_existing_records_are_never_marked_or_erased_by_provisioning(tmp_path):
    from app.main import User, DemoDeployment
    _, env, engine, factory = demo_database(tmp_path)
    with factory() as session:
        session.add(User(email='synthetic-existing@example.test',display_name='Synthetic existing',
            password_hash='unused synthetic hash',created_at='2026-01-01'))
        session.commit()
        with pytest.raises(ValueError, match='nonempty'):
            provision(session, 'Synthetic-demo-password-123', SecuritySettings.load(env))
        assert session.query(User).one().display_name == 'Synthetic existing'
        assert session.query(DemoDeployment).count() == 0
    engine.dispose()


def test_readiness_failure_is_value_free():
    class BrokenEngine:
        def connect(self):
            raise RuntimeError('Synthetic private credential health value')
    assert database_ready(BrokenEngine(), True) is False


def test_public_liveness_is_db_independent_and_readiness_failure_is_private(monkeypatch, caplog):
    from app import main
    class BrokenEngine:
        def connect(self):raise RuntimeError('Synthetic-private-database-secret')
    monkeypatch.setattr(main, 'engine', BrokenEngine())
    with TestClient(main.app) as client:
        assert client.get('/api/health').json()=={'status':'ok'}
        response=client.get('/api/ready')
    assert response.status_code==503 and response.json()=={'status':'unavailable'}
    assert response.headers['cache-control']=='no-store'
    assert 'Synthetic-private' not in response.text+caplog.text


def test_demo_blocks_body_ingestion_and_logs_only_fixed_event(caplog):
    reached = []
    async def target(scope, receive, send):
        reached.append(True)
    async def exercise():
        async def receive():
            raise AssertionError('Blocked request body must not be read')
        messages=[]
        async def send(message):messages.append(message)
        await DemoBoundary(target, enabled=True, probe=lambda:True)(
            {'type':'http','method':'POST','path':'/api/daily-checkins'},receive,send)
        assert messages[0]['status'] == 403
    asyncio.run(exercise())
    assert not reached
    assert 'demo_write_blocked' in caplog.text and 'credential' not in caplog.text
    with pytest.raises(ValueError):operation_event('Synthetic private payload')


def test_readiness_and_liveness_actual_app_and_demo_permissions(tmp_path):
    _, env, engine, factory = demo_database(tmp_path)
    with factory() as session:
        provision(session, 'Synthetic-demo-password-123', SecuritySettings.load(env))
    script = '''
import json
from fastapi.testclient import TestClient
from app.main import app, engine
from app.auth import hasher
from sqlalchemy import text
def snapshot():
 with engine.connect() as c:
  names=c.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('login_sessions','sqlite_sequence') ORDER BY name")).scalars().all()
  return {name:c.execute(text('SELECT * FROM '+name+' ORDER BY 1')).fetchall() for name in names}
before=snapshot()
type(hasher).check_needs_rehash=lambda self,value:True
with TestClient(app, headers={'Origin':'http://localhost:5173'}) as client:
 assert client.get('/api/health').json()=={'status':'ok'}
 assert client.get('/api/ready').json()=={'status':'ready'}
 state=client.get('/api/auth/session').json()
 assert state['demo_mode'] is True
 client.headers['X-CSRF-Token']=state['csrf_token']
 assert client.post('/api/auth/register',json={}).status_code==403
 login=client.post('/api/auth/login',json={'email':'demo@synthetic.example.test','password':'Synthetic-demo-password-123'})
 assert login.status_code==200
 client.headers['X-CSRF-Token']=login.json()['csrf_token']
 assert len(client.get('/api/daily-checkins').json())==3
 for method,path in [('POST','/api/episodes'),('PUT','/api/account'),('DELETE','/api/account')]:
  assert client.request(method,path,json={'notes':'Synthetic blocked payload'}).status_code==403
 # Inventory every installed mutating route, including future additions and unknown paths.
 for route in app.routes:
  for method in getattr(route,'methods',set())-{'GET','HEAD','OPTIONS'}:
   if route.path in ('/api/auth/login','/api/auth/logout','/api/v1/research-export'):continue
   path=route.path.replace('{id}','1')
   assert client.request(method,path,json={}).status_code==403,(method,path)
 assert client.post('/api/unknown-admin-write',json={}).status_code==403
 for path in ('/api/profile','/api/support/preferences','/api/support/recommendations'):
  assert client.get(path).status_code==200
 assert snapshot()==before
 assert client.get('/api/export').json()['synthetic_demo'] is True
 assert client.post('/api/v1/research-export',json={'confirmed':False,'scope':'local_research_preparation','timezone_name':'UTC','days':30}).status_code==422
 exported=client.post('/api/v1/research-export',json={'confirmed':True,'scope':'local_research_preparation','timezone_name':'UTC','days':30})
 assert exported.status_code==200 and exported.json()['synthetic_demo'] is True
 assert exported.json()['training_eligible'] is False
 assert client.post('/api/auth/logout').status_code==204
 assert client.get('/api/daily-checkins').status_code==401
 assert snapshot()==before
 # A damaged fixture cannot cause GET handlers to recreate application records.
 with engine.begin() as connection:
  connection.execute(text('DELETE FROM profiles'))
  connection.execute(text('DELETE FROM support_preferences'))
 damaged=snapshot()
 state=client.get('/api/auth/session').json()
 client.headers['X-CSRF-Token']=state['csrf_token']
 login=client.post('/api/auth/login',json={'email':'demo@synthetic.example.test','password':'Synthetic-demo-password-123'})
 assert login.status_code==200
 client.headers['X-CSRF-Token']=login.json()['csrf_token']
 for path in ('/api/profile','/api/support/preferences','/api/support/recommendations'):
  assert client.get(path).status_code==503
 assert snapshot()==damaged
print('demo integration passed')
'''
    result = subprocess.run([sys.executable,'-c',script],cwd=BACKEND,env=env,capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    assert 'Synthetic blocked payload' not in result.stderr
    with engine.begin() as connection:connection.execute(text("UPDATE alembic_version SET version_num='008'"))
    assert database_ready(engine, True) is False
    engine.dispose()


def test_009_preserves_008_records_and_is_idempotent(tmp_path):
    path=tmp_path/'migration.sqlite'
    env={**os.environ,'APP_ENV':'development','DATA_MODE':'local','DATABASE_URL':'sqlite:///'+path.as_posix()}
    def migrate(target):
        result=subprocess.run([sys.executable,'-m','alembic','upgrade',target],cwd=BACKEND,env=env,capture_output=True,text=True)
        assert result.returncode==0,result.stderr
    migrate('008')
    with sqlite3.connect(path) as connection:
        connection.execute("INSERT INTO users VALUES(1,'synthetic-preserved@example.test','Synthetic preserved','unused','2026-01-01')")
        before=connection.execute('SELECT * FROM users').fetchall()
    migrate('head');migrate('head')
    with sqlite3.connect(path) as connection:
        assert connection.execute('SELECT * FROM users').fetchall()==before
        assert connection.execute('SELECT * FROM demo_deployments').fetchall()==[]
        assert connection.execute('SELECT version_num FROM alembic_version').fetchone()[0]==SCHEMA_REVISION
    refused=subprocess.run([sys.executable,'-m','alembic','downgrade','008'],cwd=BACKEND,env=env,capture_output=True,text=True)
    assert refused.returncode!=0 and 'do not erase demo provenance automatically' in refused.stderr
    with sqlite3.connect(path) as connection:
        assert connection.execute('SELECT * FROM users').fetchall()==before
        assert connection.execute('SELECT version_num FROM alembic_version').fetchone()[0]==SCHEMA_REVISION
        assert connection.execute('SELECT * FROM demo_deployments').fetchall()==[]


def test_sqlite_backup_restore_on_synthetic_target_only(tmp_path):
    path, env, engine, factory = demo_database(tmp_path)
    with factory() as session:provision(session, 'Synthetic-demo-password-123', SecuritySettings.load(env))
    engine.dispose()
    restored=tmp_path/'restored.sqlite'
    with sqlite3.connect(path) as source, sqlite3.connect(restored) as destination:
        source.backup(destination)
        for table in ('users','daily_checkins','checkin_revisions','episodes','demo_deployments','alembic_version'):
            assert source.execute(f'SELECT * FROM {table}').fetchall()==destination.execute(f'SELECT * FROM {table}').fetchall()
        assert destination.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    # This tests consistent local backup/restore, NOT encryption or off-host retention.


def test_uninitialized_demo_cannot_start_and_check_validates_port(tmp_path):
    _, env, engine, factory = demo_database(tmp_path)
    script='from fastapi.testclient import TestClient; from app.main import app; client=TestClient(app); client.__enter__()'
    blocked=subprocess.run([sys.executable,'-c',script],cwd=BACKEND,env=env,capture_output=True,text=True)
    assert blocked.returncode!=0 and 'startup_blocked' in blocked.stderr
    with factory() as session:provision(session, 'Synthetic-demo-password-123', SecuritySettings.load(env))
    valid=subprocess.run([sys.executable,'-m','app.serve','--check'],cwd=BACKEND,env=env,capture_output=True,text=True)
    assert valid.returncode==0,valid.stderr
    invalid=subprocess.run([sys.executable,'-m','app.serve','--check'],cwd=BACKEND,env={**env,'PORT':'invalid'},capture_output=True,text=True)
    assert invalid.returncode!=0 and 'PORT must be' in invalid.stderr
    missing_mode={k:v for k,v in env.items() if k!='APP_ENV'}
    refused=subprocess.run([sys.executable,'-m','app.serve','--check'],cwd=BACKEND,env=missing_mode,capture_output=True,text=True)
    assert refused.returncode!=0 and 'APP_ENV explicitly' in refused.stderr
    engine.dispose()


def test_deployment_templates_keep_boundaries_explicit():
    root=BACKEND.parent
    service=(root/'deploy/migramind-demo.service.example').read_text()
    proxy=(root/'deploy/nginx-demo.conf.example').read_text()
    assert '-m app.serve --check' in service and 'NoNewPrivileges=true' in service
    assert 'proxy_pass http://127.0.0.1:8015' in proxy
    assert 'proxy_set_header X-Forwarded-Proto https' in proxy and 'access_log off' in proxy
    assert 'proxy_cache off' in proxy and 'Content-Security-Policy' in proxy
    assert not (root/'deploy/demo.env.example').read_text().split('DATABASE_URL=')[1].splitlines()[0]
