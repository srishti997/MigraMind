"""Exercise the additive migration only in a new synthetic temporary database."""
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import pytest

from sqlalchemy import create_engine
from app.deployment import database_ready


def test_migration_010_preserves_records_and_refuses_destructive_downgrade(tmp_path):
    path = tmp_path/'synthetic-migration.sqlite'
    backend = Path(__file__).resolve().parents[1]
    env = {**os.environ, 'APP_ENV':'development', 'DATA_MODE':'local',
        'SESSION_IDLE_TIMEOUT_ENABLED':'false', 'PYTHON_DOTENV_DISABLED':'1',
        'DATABASE_URL':'sqlite:///'+path.as_posix()}
    def migrate(direction, version):
        return subprocess.run([sys.executable,'-B','-m','alembic',direction,version],
            cwd=backend,env=env,capture_output=True,text=True,timeout=60)
    result = migrate('upgrade','009')
    assert result.returncode == 0, result.stderr
    engine = create_engine(env['DATABASE_URL'])
    try: assert not database_ready(engine)
    finally: engine.dispose()
    with sqlite3.connect(path) as connection:
        connection.execute("INSERT INTO users VALUES(1,'synthetic@example.test','Synthetic','synthetic-unused-hash','2026-01-01')")
        connection.execute("INSERT INTO contacts(name,relationship,phone,owner_id) VALUES('Synthetic preserved','Friend','+12025550100',1)")
        connection.execute("INSERT INTO login_sessions(user_id,token_digest,csrf_token,expires_at) VALUES(1,'synthetic-digest','synthetic-csrf','2099-01-01T00:00:00+00:00')")
        names = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('alembic_version','sqlite_sequence')")]
        columns = {name:[row[1] for row in connection.execute('PRAGMA table_info('+name+')')] for name in names}
        before = {name:connection.execute('SELECT * FROM '+name).fetchall() for name in names}
    result = migrate('upgrade','head')
    assert result.returncode == 0, result.stderr
    def verify():
        with sqlite3.connect(path) as connection:
            for name in names:
                quoted_columns = ','.join('"'+column.replace('"','""')+'"' for column in columns[name])
                assert connection.execute('SELECT '+quoted_columns+' FROM "'+name+'"').fetchall() == before[name]
            info = {row[1]:row for row in connection.execute('PRAGMA table_info(login_sessions)')}
            assert info['last_activity_at_ms'][2:4] == ('BIGINT',0)
            assert connection.execute('SELECT last_activity_at_ms FROM login_sessions').fetchall() == [(None,)]
            assert connection.execute('SELECT version_num FROM alembic_version').fetchall() == [('010',)]
            assert connection.execute('PRAGMA foreign_key_check').fetchall() == []
    verify()
    engine = create_engine(env['DATABASE_URL'])
    try: assert database_ready(engine)
    finally: engine.dispose()
    # Existing repository migrations are forward-only; no column/data is dropped.
    result = migrate('downgrade','009')
    assert result.returncode != 0 and 'Keep the additive activity column' in result.stderr
    verify()
    assert migrate('upgrade','head').returncode == 0
    verify()


@pytest.mark.parametrize('start_revision', [None, '009'])
def test_fresh_or_ordered_upgrade_starts_actual_app_with_idle_disabled(tmp_path, start_revision):
    path = tmp_path/'synthetic-startup.sqlite'
    backend = Path(__file__).resolve().parents[1]
    env = {**os.environ, 'APP_ENV':'development', 'DATA_MODE':'local',
        'DATABASE_URL':'sqlite:///'+path.as_posix(), 'SESSION_IDLE_TIMEOUT_ENABLED':'false',
        'PYTHON_DOTENV_DISABLED':'1', 'PYTHONDONTWRITEBYTECODE':'1'}
    for version in ([start_revision,'head'] if start_revision else ['head']):
        result = subprocess.run([sys.executable,'-B','-m','alembic','upgrade',version],
            cwd=backend,env=env,capture_output=True,text=True,timeout=60)
        assert result.returncode == 0, result.stderr
    with sqlite3.connect(path) as connection:
        assert connection.execute('SELECT version_num FROM alembic_version').fetchall() == [('010',)]
        assert 'last_activity_at_ms' in {row[1] for row in connection.execute('PRAGMA table_info(login_sessions)')}
        assert connection.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0
        assert connection.execute('PRAGMA foreign_key_check').fetchall() == []
    # Startup uses this new file only; health/readiness, auth and the off switch are real.
    script = '''
from fastapi.testclient import TestClient
from app.main import app, security, engine
assert security.session_idle_timeout_enabled is False
try:
 with TestClient(app,headers={'Origin':'http://localhost:5173'}) as client:
  assert client.get('/api/health').status_code == 200
  assert client.get('/api/ready').status_code == 200
  anonymous = client.get('/api/auth/session').json()
  assert anonymous['user'] is None
  client.headers['X-CSRF-Token'] = anonymous['csrf_token']
  response = client.post('/api/auth/register',json={'email':'startup@example.test','display_name':'Synthetic startup','password':'Synthetic-startup-password-123'})
  assert response.status_code == 201
  state = response.json()
  assert set(state) == {'user','csrf_token','expires_at','demo_mode'}
  client.headers['X-CSRF-Token'] = state['csrf_token']
  assert client.get('/api/account').status_code == 200
  assert client.post('/api/auth/activity',json={'expected_last_activity_at_ms':0}).status_code == 409
  assert client.post('/api/auth/logout').status_code == 204
  assert client.get('/api/account').status_code == 401
finally:
 engine.dispose()
'''
    result = subprocess.run([sys.executable,'-B','-c',script],cwd=backend,env=env,
        capture_output=True,text=True,timeout=60)
    assert result.returncode == 0, result.stderr
