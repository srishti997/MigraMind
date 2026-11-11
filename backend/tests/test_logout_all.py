"""Session revocation tests: fictional accounts and isolated SQLite engines only."""
from dataclasses import replace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from app.auth import Authentication, PasswordConfirmation, digest
from app.main import Base, User, LoginSession, SharingConsent, Contact, Episode
from app.security import SecuritySettings
from test_auth import clients, register, login, PASSWORD, ORIGIN

PATH = '/api/auth/logout-all'


def test_logout_all_revokes_every_session_without_deleting_records(clients):
    a, b, factory = clients
    user = register(a)
    assert login(b).status_code == 200
    replay = {'Cookie': f"migramind_session={b.cookies.get('migramind_session')}",
              'X-CSRF-Token': b.headers['X-CSRF-Token']}
    current_replay = {'Cookie': f"migramind_session={a.cookies.get('migramind_session')}",
                      'X-CSRF-Token': a.headers['X-CSRF-Token']}
    assert a.post('/api/contacts', json={'name':'Synthetic contact','relationship':'Friend','phone':'+12025550100'}).status_code == 201
    assert a.post('/api/episodes', json={'date':'2026-01-01','severity':4,'duration':60,'trigger':'Unknown','notes':'Synthetic diary'}).status_code == 201
    with factory() as s:
        before = s.query(Contact).filter_by(owner_id=user['id']).count()
        anonymous = LoginSession(token_digest=digest('synthetic-anonymous-session'), csrf_token='synthetic', expires_at='2099-01-01T00:00:00+00:00')
        s.add(anonymous); s.commit()
    result = a.post(PATH, json={'password': PASSWORD})
    assert result.status_code == 204 and not result.content
    assert 'max-age=0' in result.headers['set-cookie'].lower()
    assert 'httponly' in result.headers['set-cookie'].lower()
    for client in (a, b):
        assert client.get('/api/account').status_code == 401
        assert client.get('/api/contacts').status_code == 401
    assert a.get('/api/account', headers=replay).status_code == 401
    assert a.get('/api/account', headers=current_replay).status_code == 401
    assert a.post(PATH, json={'password': PASSWORD}, headers=replay).status_code == 401
    with factory() as s:
        assert s.get(User, user['id']) is not None
        assert s.query(Contact).filter_by(owner_id=user['id']).count() == before == 1
        assert s.query(Episode).filter_by(owner_id=user['id']).one().notes == 'Synthetic diary'
        assert s.query(LoginSession).filter_by(user_id=user['id']).count() == 0
        assert s.query(LoginSession).filter_by(user_id=None).count() == 1
    assert login(a).status_code == 200


def test_wrong_password_does_not_revoke_any_session_or_expose_input(clients, caplog):
    a, b, factory = clients
    register(a); assert login(b).status_code == 200
    wrong = 'Synthetic-wrong-password-456'
    response = a.post(PATH, json={'password': wrong})
    assert response.status_code == 400
    assert response.json() == {'detail': 'Password confirmation failed'}
    assert 'set-cookie' not in response.headers
    assert wrong not in response.text + caplog.text
    assert wrong not in repr(PasswordConfirmation(password=wrong))
    assert a.get('/api/account').status_code == b.get('/api/account').status_code == 200
    with factory() as s: assert s.query(LoginSession).filter(LoginSession.user_id.is_not(None)).count() == 2


@pytest.mark.parametrize('headers', [{'X-CSRF-Token':''}, {'Origin':''}, {'Origin':'https://attacker.example.test'}])
def test_logout_all_requires_csrf_and_origin(clients, headers):
    a, b, _ = clients
    register(a); assert login(b).status_code == 200
    assert a.post(PATH, json={'password':PASSWORD}, headers=headers).status_code == 403
    assert a.get('/api/account').status_code == b.get('/api/account').status_code == 200


def test_logout_all_requires_authentication(clients):
    a, _, _ = clients
    assert a.post(PATH, json={'password':PASSWORD}).status_code == 401
    a.cookies.clear()
    assert a.post(PATH, json={'password':PASSWORD}).status_code == 401


def test_logout_all_cannot_target_another_account(clients):
    a, b, factory = clients
    user = register(a); other = register(b, 'other@example.test')
    for field in ('user_id', 'owner_id', 'email'):
        response = a.post(PATH, json={'password':PASSWORD, field: other['id']})
        assert response.status_code == 422 and PASSWORD not in response.text
    assert a.post(PATH, json={'password':PASSWORD}).status_code == 204
    assert b.get('/api/account').json()['id'] == other['id']
    with factory() as s:
        assert s.get(User, user['id']) and s.get(User, other['id'])
        assert s.query(LoginSession).filter_by(user_id=other['id']).count() == 1


def test_logout_all_uses_existing_reauthentication_budget(clients):
    a, _, _ = clients
    register(a)
    for _ in range(9): assert a.post(PATH, json={'password':'Synthetic-wrong'}).status_code == 400
    assert a.post(PATH, json={'password':PASSWORD}).status_code == 429
    assert a.get('/api/account').status_code == 200


def test_commit_failure_rolls_back_and_does_not_expire_cookie(clients):
    a, b, factory = clients
    register(a); assert login(b).status_code == 200
    def fail_commit(session):
        raise OperationalError('synthetic commit failure', {}, Exception('synthetic'))
    event.listen(factory.class_, 'before_commit', fail_commit)
    try: response = a.post(PATH, json={'password':PASSWORD})
    finally: event.remove(factory.class_, 'before_commit', fail_commit)
    assert response.status_code == 503 and 'set-cookie' not in response.headers
    assert a.get('/api/account').status_code == b.get('/api/account').status_code == 200


def make_app(factory, settings=None):
    application = FastAPI()
    def db():
        with factory() as session: yield session
    instance = Authentication(application, db, User, LoginSession, SharingConsent, Contact, [], settings=settings)
    return application, instance


def test_revocation_is_shared_and_survives_fresh_engine_and_app(tmp_path):
    # This new file contains synthetic records only, never the application database.
    url = 'sqlite:///' + (tmp_path / 'synthetic-sessions.sqlite').as_posix()
    engine1 = create_engine(url, connect_args={'check_same_thread':False})
    engine2 = create_engine(url, connect_args={'check_same_thread':False})
    Base.metadata.create_all(engine1)
    application1, _ = make_app(sessionmaker(bind=engine1))
    application2, _ = make_app(sessionmaker(bind=engine2))
    try:
        with TestClient(application1, headers={'Origin':ORIGIN}) as a, TestClient(application2, headers={'Origin':ORIGIN}) as b:
            a.headers['X-CSRF-Token'] = a.get('/api/auth/session').json()['csrf_token']
            register(a); assert login(b).status_code == 200
            replay = {'Cookie': f"migramind_session={b.cookies.get('migramind_session')}", 'X-CSRF-Token': b.headers['X-CSRF-Token']}
            assert a.post(PATH, json={'password':PASSWORD}).status_code == 204
            assert b.get('/api/account').status_code == 401
    finally: engine1.dispose(); engine2.dispose()
    engine3 = create_engine(url, connect_args={'check_same_thread':False})
    try:
        fresh_app, _ = make_app(sessionmaker(bind=engine3))
        with TestClient(fresh_app, headers={'Origin':ORIGIN}) as fresh:
            assert fresh.get('/api/account', headers=replay).status_code == 401
    finally: engine3.dispose()


def test_shared_demo_rejects_global_logout(clients):
    a, _, factory = clients
    # Instantiate only the auth routes over the synthetic fixture; no demo provisioning.
    from app.deployment import DEMO_EMAIL
    user = register(a, DEMO_EMAIL)
    settings = replace(SecuritySettings.load(), synthetic_demo=True)
    application, _ = make_app(factory, settings)
    with TestClient(application, headers={'Origin':ORIGIN}) as demo:
        demo.cookies.update(a.cookies); demo.headers['X-CSRF-Token'] = a.headers['X-CSRF-Token']
        assert demo.post(PATH, json={'password':PASSWORD}).status_code == 403
        assert demo.get('/api/account').json()['id'] == user['id']


def test_logout_all_expires_production_cookie_with_matching_attributes(clients):
    _, _, factory = clients
    settings = replace(SecuritySettings.load(), production=True, origins=('https://demo.example.test',))
    application, _ = make_app(factory, settings)
    with TestClient(application, base_url='https://demo.example.test', headers={'Origin':'https://demo.example.test'}) as client:
        client.headers['X-CSRF-Token'] = client.get('/api/auth/session').json()['csrf_token']
        register(client)
        response = client.post(PATH, json={'password':PASSWORD})
        assert response.status_code == 204
        cookie = response.headers['set-cookie'].lower()
        for attribute in ('__host-migramind_session=', 'secure', 'httponly', 'samesite=lax', 'path=/', 'max-age=0'):
            assert attribute in cookie
        assert 'domain=' not in cookie
