"""Guard ordering and unchanged budgets; temporary synthetic fixtures only."""
import pytest
from fastapi.testclient import TestClient

from app.auth import digest, hasher
from app.main import app, auth, User, LoginSession
from test_auth import clients, register, login, PASSWORD, ORIGIN


def budgets():
    return {key: tuple(window) for key, window in auth.limiter.windows.items()}


def payload(route, email='target@example.test'):
    data = {'email': email, 'password': PASSWORD}
    if route == 'register':
        data['display_name'] = 'Synthetic account'
    return data


@pytest.mark.parametrize('route', ['login', 'register'])
@pytest.mark.parametrize('guard', [
    'missing_origin', 'invalid_origin', 'missing_csrf', 'invalid_csrf',
    'mismatched_csrf', 'missing_session', 'invalid_session', 'expired_session',
])
def test_rejected_guards_leave_all_budgets_and_records_unchanged(clients, monkeypatch, route, guard):
    a, b, factory = clients
    if guard == 'missing_origin': a.headers.pop('Origin')
    elif guard == 'invalid_origin': a.headers['Origin'] = 'https://untrusted.example.test'
    elif guard == 'missing_csrf': a.headers.pop('X-CSRF-Token')
    elif guard == 'invalid_csrf': a.headers['X-CSRF-Token'] = 'synthetic-invalid'
    elif guard == 'mismatched_csrf': a.headers['X-CSRF-Token'] = b.headers['X-CSRF-Token']
    elif guard == 'missing_session': a.cookies.clear()
    elif guard == 'invalid_session':
        a.cookies.clear(); a.cookies.set('migramind_session', 'synthetic-invalid')
    else:
        with factory() as s:
            s.query(LoginSession).filter_by(token_digest=digest(a.cookies.get('migramind_session'))).update(
                {'expires_at': '2000-01-01T00:00:00+00:00'})
            s.commit()
    before = budgets()
    with factory() as s:
        counts = (s.query(User).count(), s.query(LoginSession).count())
    def forbidden_work(*args, **kwargs):
        pytest.fail('Rejected security guards must not perform password work')
    monkeypatch.setattr(type(hasher), 'hash', forbidden_work)
    monkeypatch.setattr(type(hasher), 'verify', forbidden_work)
    response = a.post('/api/auth/' + route, json=payload(route))
    assert response.status_code == 403
    assert response.json()['detail'] == (
        'Request origin is not allowed' if guard.endswith('origin') else 'Refresh the page and try again')
    assert budgets() == before
    with factory() as s:
        assert (s.query(User).count(), s.query(LoginSession).count()) == counts


@pytest.mark.parametrize('route', ['login', 'register'])
@pytest.mark.parametrize('attacker_ip', ['testclient', '198.51.100.8'])
def test_rejected_requests_cannot_poison_target_or_shared_ip(clients, route, attacker_ip):
    a, b, _ = clients
    register(a, 'target@example.test'); register(b, 'other@example.test')
    auth.limiter.clear()
    with TestClient(app, client=(attacker_ip, 50000)) as attacker:
        for _ in range(10):
            response = attacker.post('/api/auth/' + route,
                json=payload(route, ' TARGET@example.test '),
                headers={'Origin': 'https://untrusted.example.test'})
            assert response.status_code == 403
    assert budgets() == {}
    assert login(a, 'target@example.test').status_code == 200
    assert login(b, 'other@example.test').status_code == 200
    assert len(auth.limiter.windows[('account', digest('target@example.test'))]) == 1
    assert len(auth.limiter.windows[('account', digest('other@example.test'))]) == 1


def test_valid_guards_preserve_success_failure_duplicate_and_normalized_accounting(clients):
    a, b, _ = clients
    auth.limiter.clear()
    register(a, ' TARGET@example.test ')
    assert b.post('/api/auth/register', json=payload('register')).status_code == 400
    known = login(b, 'target@example.test', 'synthetic-wrong')
    unknown = login(b, 'absent@example.test', 'synthetic-wrong')
    assert known.status_code == unknown.status_code == 401
    assert known.json() == unknown.json() == {'detail': 'Email or password is incorrect'}
    assert login(a, 'target@example.test').status_code == 200
    assert len(auth.limiter.windows[('account', digest('target@example.test'))]) == 4
    assert len(auth.limiter.windows[('account', digest('absent@example.test'))]) == 1
    assert len(auth.limiter.windows[('ip', 'testclient')]) == 5


@pytest.mark.parametrize('route', ['login', 'register'])
@pytest.mark.parametrize('kind,limit', [('ip', 30), ('account', 10)])
def test_validly_submitted_requests_still_obey_exhausted_budgets(clients, monkeypatch, route, kind, limit):
    a, _, _ = clients
    auth.limiter.clear()
    key = (kind, 'testclient' if kind == 'ip' else digest('target@example.test'))
    for _ in range(limit): auth.limiter.check(key, limit)
    def forbidden_work(*args, **kwargs):
        pytest.fail('Exhausted budgets must reject before password work')
    monkeypatch.setattr(type(hasher), 'hash', forbidden_work)
    monkeypatch.setattr(type(hasher), 'verify', forbidden_work)
    response = a.post('/api/auth/' + route, json=payload(route))
    assert response.status_code == 429 and response.headers['retry-after'] == '900'
    assert response.json() == {'detail': 'Too many attempts. Try again later.'}
    assert len(auth.limiter.windows[key]) == limit
    if kind == 'account': assert len(auth.limiter.windows[('ip', 'testclient')]) == 1
    else: assert ('account', digest('target@example.test')) not in auth.limiter.windows
    before = budgets()
    assert a.post('/api/auth/' + route, json=payload(route), headers={'Origin': ''}).status_code == 403
    assert budgets() == before  # Guards retain precedence even when already throttled.


@pytest.mark.parametrize('route', ['login', 'register'])
@pytest.mark.parametrize('malformed', ['json', 'schema'])
def test_malformed_requests_do_not_charge_budgets(clients, route, malformed):
    a, _, _ = clients
    before = budgets()
    response = (a.post('/api/auth/' + route, content='{', headers={'Content-Type': 'application/json'})
        if malformed == 'json' else a.post('/api/auth/' + route, json={'email': 'bad', 'password': 'synthetic'}))
    assert response.status_code == 422
    assert budgets() == before


@pytest.mark.parametrize('route', ['/api/auth/logout-all', '/api/account'])
def test_existing_protected_dependency_failures_still_do_not_charge(clients, route):
    a, _, _ = clients
    register(a)
    before = budgets()
    method = 'DELETE' if route == '/api/account' else 'POST'
    assert a.request(method, route, json={'password': PASSWORD}, headers={'Origin': ''}).status_code == 403
    assert budgets() == before
    a.cookies.clear()
    assert a.request(method, route, json={'password': PASSWORD}).status_code == 401
    assert budgets() == before
