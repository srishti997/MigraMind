"""Disabled-by-default idle foundation; only new synthetic SQLite files/accounts."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from threading import Event, Lock

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.auth import Authentication, IDLE_TIMEOUT_MS, epoch_ms
from app.main import Base, User, LoginSession, SharingConsent, Contact
from app.security import SecuritySettings
from test_auth import register, login, PASSWORD, ORIGIN

PATH = '/api/auth/activity'
START = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)


class Clock:
    def __init__(self): self.value = START; self.lock = Lock()
    def __call__(self):
        with self.lock: return self.value
    def advance_to(self, milliseconds):
        with self.lock: self.value = START + timedelta(milliseconds=milliseconds)


class Harness:
    def __init__(self, path):
        self.url = 'sqlite:///' + path.as_posix()
        self.clock = Clock(); self.engines = []; self.clients = []
        engine = self.engine(); Base.metadata.create_all(engine)
        self.factory = sessionmaker(bind=engine)
    def engine(self):
        engine = create_engine(self.url, connect_args={'check_same_thread':False, 'timeout':10})
        self.engines.append(engine); return engine
    def client(self, enabled=True, hours=12, clock=None):
        factory = sessionmaker(bind=self.engine())
        app = FastAPI()
        def db():
            with factory() as session: yield session
        @app.exception_handler(SQLAlchemyError)
        async def error(request, exception):
            return JSONResponse(status_code=503, content={'detail':'Session request unavailable'})
        settings = replace(SecuritySettings.load(), session_idle_timeout_enabled=enabled, session_hours=hours)
        Authentication(app, db, User, LoginSession, SharingConsent, Contact, [], settings, clock or self.clock)
        client = TestClient(app, headers={'Origin':ORIGIN})
        self.clients.append(client); return client
    def sign_in(self, client, email='a@example.test'):
        client.headers['X-CSRF-Token'] = client.get('/api/auth/session').json()['csrf_token']
        return register(client, email)
    def activity(self, user_id):
        with self.factory() as session:
            return session.query(LoginSession).filter_by(user_id=user_id).one().last_activity_at_ms
    def set_activity(self, user_id, value):
        with self.factory() as session:
            session.query(LoginSession).filter_by(user_id=user_id).update({'last_activity_at_ms':value})
            session.commit()


@pytest.fixture
def h(tmp_path):
    harness = Harness(tmp_path/'synthetic-idle.sqlite')
    yield harness
    for client in harness.clients: client.close()
    for engine in harness.engines: engine.dispose()


def payload(last=epoch_ms(START)):
    return {'expected_last_activity_at_ms':last}


def clone(h, client, **options):
    other = h.client(**options)
    other.cookies.update(client.cookies)
    other.headers['X-CSRF-Token'] = client.headers['X-CSRF-Token']
    return other


def test_flag_defaults_false_and_opt_in_is_explicit_local_only():
    environment = {'DATABASE_URL':'sqlite://', 'APP_ENV':'development'}
    assert SecuritySettings.load(environment).session_idle_timeout_enabled is False
    assert SecuritySettings.load({**environment, 'SESSION_IDLE_TIMEOUT_ENABLED':'false'}).session_idle_timeout_enabled is False
    assert SecuritySettings.load({**environment, 'SESSION_IDLE_TIMEOUT_ENABLED':'true'}).session_idle_timeout_enabled is True
    from test_security import PRODUCTION
    with pytest.raises(RuntimeError, match='limited to explicit local'):
        SecuritySettings.load({**PRODUCTION, 'SESSION_IDLE_TIMEOUT_ENABLED':'true'})
    with pytest.raises(RuntimeError, match='limited to explicit local'):
        SecuritySettings.load({**environment, 'DATA_MODE':'synthetic', 'DEMO_ACKNOWLEDGEMENT':'synthetic-only-no-real-health-data', 'SESSION_IDLE_TIMEOUT_ENABLED':'true'})


@pytest.mark.parametrize('value', ['','TRUE','1','yes','False'])
def test_invalid_flag_fails_closed(value):
    with pytest.raises(RuntimeError, match='must be true or false'):
        SecuritySettings.load({'SESSION_IDLE_TIMEOUT_ENABLED':value})


@pytest.mark.parametrize('offset,expected', [(IDLE_TIMEOUT_MS-1,200),(IDLE_TIMEOUT_MS,401),(IDLE_TIMEOUT_MS+1,401)])
def test_exact_idle_boundary(h, offset, expected):
    client = h.client(); h.sign_in(client)
    h.clock.advance_to(offset)
    assert client.get('/api/account').status_code == expected
    assert client.post(PATH, json=payload()).status_code == (200 if expected == 200 else 401)


def test_explicit_activity_extends_only_idle_and_retries_do_not_extend(h):
    client = h.client(); user = h.sign_in(client)
    before = client.get('/api/auth/session').json()
    cookie = client.cookies.get('migramind_session')
    h.clock.advance_to(10*60*1000)
    response = client.post(PATH, json=payload())
    assert response.status_code == 200 and 'set-cookie' not in response.headers
    refreshed = response.json()
    assert refreshed['expires_at'] == before['expires_at']
    assert refreshed['last_activity_at_ms'] == epoch_ms(h.clock())
    assert client.cookies.get('migramind_session') == cookie
    assert client.headers['X-CSRF-Token'] == before['csrf_token']
    h.clock.advance_to(11*60*1000)
    assert client.post(PATH, json=payload()).status_code == 409
    assert h.activity(user['id']) == refreshed['last_activity_at_ms']
    h.clock.advance_to(35*60*1000)
    assert client.get('/api/account').status_code == 200
    h.clock.advance_to(40*60*1000)
    assert client.get('/api/account').status_code == 401


def test_bootstrap_reads_and_ordinary_mutations_never_touch(h):
    client = h.client(); user = h.sign_in(client)
    initial = h.activity(user['id'])
    for minutes in (1,10,29):
        h.clock.advance_to(minutes*60*1000)
        assert client.get('/api/auth/session').json()['last_activity_at_ms'] == initial
        assert client.get('/api/account').status_code == 200
    assert client.put('/api/account', json={'display_name':'Synthetic renamed'}).status_code == 200
    assert h.activity(user['id']) == initial
    h.clock.advance_to(IDLE_TIMEOUT_MS)
    assert client.get('/api/account').status_code == 401
    assert client.get('/api/auth/session').json()['user'] is None


def test_absolute_expiry_remains_fixed_and_caps_metadata(h):
    client = h.client(hours=1); h.sign_in(client)
    absolute = client.get('/api/auth/session').json()['expires_at']
    last = epoch_ms(START)
    for minutes in (29,58):
        h.clock.advance_to(minutes*60*1000)
        response = client.post(PATH, json=payload(last))
        assert response.status_code == 200
        last = response.json()['last_activity_at_ms']
        assert response.json()['expires_at'] == absolute
    assert response.json()['idle_expires_at'] == absolute
    h.clock.advance_to(60*60*1000)
    assert client.post(PATH, json=payload(last)).status_code == 401
    assert client.get('/api/account').status_code == 401


@pytest.mark.parametrize('value', [None,-1,'corrupt',epoch_ms(START)+1])
def test_missing_invalid_or_future_activity_fails_closed_when_enabled(h, value):
    client = h.client(); user = h.sign_in(client)
    h.set_activity(user['id'], value)
    assert client.get('/api/account').status_code == 401
    assert client.post(PATH, json=payload()).status_code == 401


@pytest.mark.parametrize('legacy', [False,True])
def test_disabled_preserves_legacy_absolute_behavior_and_response(h, legacy):
    client = h.client(enabled=False); user = h.sign_in(client)
    expected = None if legacy else epoch_ms(START)
    if legacy: h.set_activity(user['id'], None)
    h.clock.advance_to(11*60*60*1000)
    state = client.get('/api/auth/session').json()
    assert set(state) == {'user','csrf_token','expires_at','demo_mode'}
    assert state['user']['id'] == user['id']
    assert client.get('/api/account').status_code == 200
    assert client.post(PATH, json=payload()).status_code == 409
    assert h.activity(user['id']) == expected
    # Explicit enabling, not installing the column, requires legacy reauthentication.
    enabled = clone(h, client)
    assert enabled.get('/api/account').status_code == 401
    assert enabled.get('/api/auth/session').json()['user'] is None
    assert h.activity(user['id']) == expected
    h.clock.advance_to(13*60*60*1000)
    assert client.get('/api/account').status_code == 401


def test_anonymous_session_keeps_one_hour_and_login_rotation_initializes_activity(h):
    client = h.client()
    state = client.get('/api/auth/session').json()
    client.headers['X-CSRF-Token'] = state['csrf_token']
    cookie = client.cookies.get('migramind_session')
    h.clock.advance_to(31*60*1000)
    user = register(client)
    assert client.cookies.get('migramind_session') != cookie
    assert h.activity(user['id']) == epoch_ms(h.clock())
    replay = {'Cookie':f'migramind_session={cookie}', 'X-CSRF-Token':state['csrf_token']}
    assert client.post(PATH, json=payload(), headers=replay).status_code == 401


@pytest.mark.parametrize('headers', [{'X-CSRF-Token':''},{'X-CSRF-Token':'wrong'},{'Origin':''},{'Origin':'https://attacker.example.test'}])
def test_activity_requires_csrf_and_origin(h, headers):
    client = h.client(); user = h.sign_in(client)
    h.clock.advance_to(1000)
    assert client.post(PATH, json=payload(), headers=headers).status_code == 403
    assert h.activity(user['id']) == epoch_ms(START)


def test_anonymous_and_no_cookie_cannot_touch(h):
    client = h.client()
    assert client.post(PATH, json=payload()).status_code == 401
    client.get('/api/auth/session')
    assert client.post(PATH, json=payload()).status_code == 401


@pytest.mark.parametrize('extra', [{'user_id':2},{'owner_id':2},{'timestamp':0},{'expected_last_activity_at_ms':True}])
def test_activity_rejects_owner_and_client_time_overrides(h, extra):
    client = h.client(); user = h.sign_in(client); h.clock.advance_to(1000)
    assert client.post(PATH, json={**payload(),**extra}).status_code == 422
    assert h.activity(user['id']) == epoch_ms(START)


def test_cross_account_and_independent_sessions_stay_isolated(h):
    a = h.client(); user = h.sign_in(a)
    b = h.client(); other = h.sign_in(b, 'other@example.test')
    h.clock.advance_to(20*60*1000)
    assert b.post(PATH, json=payload()).status_code == 200
    assert h.activity(user['id']) == epoch_ms(START)
    assert h.activity(other['id']) == epoch_ms(h.clock())
    independent = h.client(); assert login(independent).status_code == 200
    h.clock.advance_to(IDLE_TIMEOUT_MS)
    assert a.get('/api/account').status_code == 401
    assert b.get('/api/account').status_code == 200
    assert independent.get('/api/account').status_code == 200


def test_refresh_visible_to_independent_and_fresh_instances(h):
    a = h.client(); h.sign_in(a)
    b = clone(h, a)
    h.clock.advance_to(20*60*1000)
    assert a.post(PATH, json=payload()).status_code == 200
    h.clock.advance_to(40*60*1000)
    fresh = clone(h, a)
    for client in (b,fresh):
        state = client.get('/api/auth/session').json()
        assert state['last_activity_at_ms'] == epoch_ms(START+timedelta(minutes=20))
        assert client.get('/api/account').status_code == 200


def test_global_and_current_logout_replay_cannot_revive_or_delete_records(h):
    a = h.client(); user = h.sign_in(a)
    b = h.client(); assert login(b).status_code == 200
    other = h.client(); other_user = h.sign_in(other,'other@example.test')
    replay = clone(h,a)
    with h.factory() as session:
        session.add(Contact(owner_id=user['id'],name='Synthetic preserved',relationship='Friend',phone='+12025550100'))
        session.commit()
    h.clock.advance_to(1000)
    assert a.post('/api/auth/logout-all', json={'password':'Synthetic wrong'}).status_code == 400
    with h.factory() as session:
        rows = session.query(LoginSession).filter_by(user_id=user['id']).all()
        assert len(rows) == 2 and all(row.last_activity_at_ms == epoch_ms(START) for row in rows)
    assert a.post('/api/auth/logout-all', json={'password':PASSWORD}).status_code == 204
    for client in (b,replay):
        assert client.get('/api/account').status_code == 401
        assert client.post(PATH,json=payload()).status_code == 401
    with h.factory() as session:
        assert session.query(Contact).filter_by(owner_id=user['id']).one().name == 'Synthetic preserved'
        assert session.get(User,user['id']) is not None
        assert session.query(LoginSession).filter_by(user_id=user['id']).count() == 0
    assert other.get('/api/account').status_code == 200
    assert h.activity(other_user['id']) == epoch_ms(START)
    assert login(a).status_code == 200
    current_replay = clone(h,a)
    assert a.post('/api/auth/logout').status_code == 204
    assert current_replay.post(PATH,json=payload(epoch_ms(h.clock()))).status_code == 401


def test_same_instant_and_backward_clock_cannot_advance_activity(h):
    client = h.client(); user = h.sign_in(client)
    assert client.post(PATH,json=payload()).status_code == 409
    h.clock.advance_to(1000)
    assert client.post(PATH,json=payload()).status_code == 200
    h.clock.advance_to(999)
    assert client.post(PATH,json=payload(epoch_ms(START)+1000)).status_code == 401
    assert h.activity(user['id']) == epoch_ms(START)+1000


def test_clock_conversion_uses_aware_integer_milliseconds():
    offset = timezone(timedelta(hours=5,minutes=30))
    assert epoch_ms(START.astimezone(offset)) == epoch_ms(START)
    assert epoch_ms(START+timedelta(microseconds=999)) == epoch_ms(START)
    assert epoch_ms(START+timedelta(microseconds=1000)) == epoch_ms(START)+1
    with pytest.raises(ValueError,match='timezone-aware'):
        epoch_ms(START.replace(tzinfo=None))


def test_fractional_clock_metadata_matches_enforced_millisecond_boundary(h):
    client = h.client(); h.sign_in(client)
    with h.clock.lock: h.clock.value = START+timedelta(microseconds=1000999)
    response = client.post(PATH,json=payload())
    assert response.status_code == 200
    deadline = START+timedelta(milliseconds=1000+IDLE_TIMEOUT_MS)
    assert response.json()['idle_expires_at'] == deadline.isoformat()
    h.clock.advance_to(1000+IDLE_TIMEOUT_MS-1)
    assert client.get('/api/account').status_code == 200
    h.clock.advance_to(1000+IDLE_TIMEOUT_MS)
    assert client.get('/api/account').status_code == 401


def test_concurrent_refreshes_serialize_and_only_one_consumes_expected_state(h):
    a = h.client(); user = h.sign_in(a); b = clone(h,a)
    h.clock.advance_to(1000)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda client:client.post(PATH,json=payload()).status_code,(a,b)))
    assert sorted(responses) == [200,409]
    assert h.activity(user['id']) == epoch_ms(h.clock())


@pytest.mark.parametrize('revoke', [False,True])
def test_waiting_refresh_rechecks_expiry_or_revocation_after_lock(h, revoke):
    a = h.client(); user = h.sign_in(a); b = clone(h,a)
    waiting = Event()
    @event.listens_for(h.engines[-1], 'before_cursor_execute')
    def mark(connection,cursor,statement,parameters,context,many):
        if statement == 'BEGIN IMMEDIATE': waiting.set()
    h.clock.advance_to(1000)
    with h.engines[0].connect() as blocker:
        blocker.exec_driver_sql('BEGIN IMMEDIATE')
        if revoke: blocker.exec_driver_sql('DELETE FROM login_sessions WHERE user_id=?',(user['id'],))
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(b.post,PATH,json=payload())
            try:
                assert waiting.wait(5), 'Refresh did not reach its write-lock acquisition'
                if not revoke: h.clock.advance_to(IDLE_TIMEOUT_MS)
            finally: blocker.commit()
            assert future.result(timeout=10).status_code == 401
    with h.factory() as session:
        rows = session.query(LoginSession).filter_by(user_id=user['id']).all()
        assert rows == [] if revoke else len(rows) == 1 and rows[0].last_activity_at_ms == epoch_ms(START)


def test_failed_activity_commit_rolls_back(h):
    client = h.client(); user = h.sign_in(client); h.clock.advance_to(1000)
    # Only intercept the UPDATE, after the locked validity check, in this engine.
    @event.listens_for(h.engines[-1], 'before_cursor_execute')
    def fail(connection,cursor,statement,parameters,context,many):
        if statement.startswith('UPDATE login_sessions'):
            raise SQLAlchemyError('Synthetic failure')
    assert client.post(PATH,json=payload()).status_code == 503
    assert h.activity(user['id']) == epoch_ms(START)
