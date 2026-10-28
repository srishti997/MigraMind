"""Synthetic-only boundary/configuration regressions; no live DB connection."""
import logging
import asyncio
import traceback
import os
import subprocess
import sys
from datetime import timedelta

import pytest
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.main import app, LoginSession
from app.security import SecuritySettings, PrivateBoundary
from app.auth import Limiter, now
from test_auth import clients, register
from test_research_quality import REQUEST


PRODUCTION = {'APP_ENV': 'production', 'CORS_ORIGINS': 'https://app.example.test',
    'ALLOWED_HOSTS': 'api.example.test',
    'DATABASE_URL': 'postgresql+psycopg://synthetic:synthetic@localhost/synthetic?sslmode=verify-full'}


@pytest.mark.parametrize('changes', [
    {'APP_ENV': 'Production'}, {'APP_ENV': 'prod'}, {'CORS_ORIGINS': ''},
    {'CORS_ORIGINS': '*'}, {'CORS_ORIGINS': 'http://app.example.test'},
    {'CORS_ORIGINS': 'https://user:synthetic@app.example.test'},
    {'CORS_ORIGINS': 'https://app.example.test/path'},
    {'CORS_ORIGINS': 'https://app.example.test:bad'},
    {'CORS_ORIGINS': 'https://app.example.test?token=synthetic'},
    {'ALLOWED_HOSTS': ''}, {'ALLOWED_HOSTS': '*'}, {'ALLOWED_HOSTS': 'https://api.example.test'},
    {'ALLOWED_HOSTS': 'api\nexample.test'}, {'ALLOWED_HOSTS': '.example.test'},
    {'ALLOWED_HOSTS': 'example..test'}, {'ALLOWED_HOSTS': '-example.test'},
    {'ALLOWED_HOSTS': '[not-an-address]'},
    {'SESSION_HOURS': '0'}, {'SESSION_HOURS': '169'}, {'SESSION_HOURS': 'synthetic'},
    {'DATABASE_URL': 'sqlite:///synthetic.db'},
    {'DATABASE_URL': 'postgresql+psycopg://synthetic:private-value@localhost/synthetic'},
    {'DATABASE_URL': 'postgresql+psycopg://synthetic:private-value@localhost/synthetic?sslmode=require'},
])
def test_invalid_production_settings_fail_closed_without_values(changes):
    with pytest.raises(RuntimeError) as error:
        SecuritySettings.load({**PRODUCTION, **changes})
    assert 'private-value' not in str(error.value)


def test_explicit_production_and_local_settings():
    settings = SecuritySettings.load(PRODUCTION)
    assert settings.production and settings.origins == ('https://app.example.test',)
    assert 'synthetic:synthetic' not in repr(settings)
    local = SecuritySettings.load({})
    assert not local.production and local.database_url == 'sqlite:///./migramind.db'
    assert SecuritySettings.load({'CORS_ORIGINS': ' http://localhost:5173, http://127.0.0.1:5173 '}).origins == local.origins


@pytest.mark.parametrize('missing', ['CORS_ORIGINS', 'ALLOWED_HOSTS', 'DATABASE_URL'])
def test_required_production_settings_cannot_be_omitted(missing):
    environment = {k: v for k, v in PRODUCTION.items() if k != missing}
    with pytest.raises(RuntimeError):
        SecuritySettings.load(environment)


def test_production_startup_rejects_configuration_before_engine_creation():
    env = {**os.environ, 'APP_ENV': 'production', 'CORS_ORIGINS': '*',
        'DATABASE_URL': 'invalid://synthetic:private-value@localhost/synthetic'}
    result = subprocess.run([sys.executable, '-c', 'import app.main'], env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'CORS_ORIGINS' in result.stderr and 'private-value' not in result.stderr


def test_transport_host_and_error_headers():
    target = FastAPI()
    target.add_middleware(TrustedHostMiddleware, allowed_hosts=['api.example.test'], www_redirect=False)
    target.add_middleware(PrivateBoundary, production=True)

    @target.get('/api/test')
    def route(response: Response):
        response.set_cookie('synthetic-one', 'one')
        response.set_cookie('synthetic-two', 'two')
        return {'synthetic': True}

    with TestClient(target, base_url='https://api.example.test') as c:
        response = c.get('/api/test')
        assert response.status_code == 200
        assert response.headers['strict-transport-security'] == 'max-age=31536000'
        assert response.headers['cache-control'] == 'no-store'
        assert response.headers['x-content-type-options'] == 'nosniff'
        assert response.headers['referrer-policy'] == 'no-referrer'
        assert response.headers['x-frame-options'] == 'DENY'
        assert len(response.headers.get_list('set-cookie')) == 2
        assert c.get('/api/test', headers={'Host': 'attacker.example.test'}).status_code == 400
        # Spoofed forwarding headers do not change the ASGI scheme here.
        assert c.get('http://api.example.test/api/test', headers={'X-Forwarded-Proto': 'https'}).status_code == 400


def test_unexpected_exception_does_not_escape_into_logs(caplog):
    target = FastAPI()
    target.add_middleware(PrivateBoundary)

    @target.get('/api/test')
    def route():
        raise RuntimeError('Synthetic-private-health-token-value')

    with caplog.at_level(logging.DEBUG), TestClient(target) as c:
        response = c.get('/api/test')
    assert response.status_code == 500
    assert response.headers['cache-control'] == 'no-store'
    assert 'Synthetic-private' not in response.text + caplog.text


def test_post_start_failure_has_no_sensitive_exception_context():
    async def exercise():
        async def target(scope, receive, send):
            await send({'type': 'http.response.start', 'status': 200, 'headers': []})
            raise RuntimeError('Synthetic-private-stream-value')
        async def send(message):
            pass
        async def receive():
            return {'type': 'http.request', 'body': b''}
        with pytest.raises(RuntimeError) as error:
            await PrivateBoundary(target)({'type': 'http', 'scheme': 'http'}, receive, send)
        assert 'Synthetic-private' not in ''.join(traceback.format_exception(error.value))
        assert error.value.__context__ is None
    asyncio.run(exercise())


def test_support_consent_also_requires_literal_boolean(clients):
    a, _, _ = clients
    register(a)
    contact = a.post('/api/contacts', json={'name': 'Synthetic', 'relationship': 'Friend', 'phone': '+12025550100'}).json()
    for value in ('true', 1, False):
        result = a.post('/api/account/consents', json={'contact_id': contact['id'], 'scope': 'support_card', 'confirmed': value})
        assert result.status_code == 422


def test_validation_does_not_echo_unknown_sensitive_field_names(clients, caplog):
    a, _, _ = clients
    response = a.post('/api/auth/register', json={'Synthetic-private-key': 'Synthetic-private-value'})
    assert response.status_code == 422
    assert 'Synthetic-private' not in response.text + caplog.text


def test_research_export_auth_csrf_consent_expiry_and_logout(clients):
    a, b, factory = clients
    assert a.post('/api/v1/research-export', json=REQUEST).status_code == 401
    register(a)
    register(b, 'synthetic-security-b@example.test')
    for headers in ({'Origin': 'https://attacker.example.test'}, {'X-CSRF-Token': ''},
                    {'X-CSRF-Token': b.headers['X-CSRF-Token']}):
        assert a.post('/api/v1/research-export', json=REQUEST, headers=headers).status_code == 403
    for confirmed in (False, 'true', 1, None):
        assert a.post('/api/v1/research-export', json={**REQUEST, 'confirmed': confirmed}).status_code == 422
    response = a.post('/api/v1/research-export', json=REQUEST)
    assert response.status_code == 200 and response.headers['content-disposition'].startswith('attachment;')
    assert response.json()['consent']['research_enrollment'] is False
    assert a.post('/api/auth/logout').status_code == 204
    assert a.post('/api/v1/research-export', json=REQUEST).status_code == 401
    with factory() as s:
        s.query(LoginSession).filter(LoginSession.user_id.is_not(None)).update({'expires_at': (now()-timedelta(seconds=1)).isoformat()})
        s.commit()
    assert b.get('/api/export').status_code == 401
    assert b.post('/api/v1/research-export', json=REQUEST).status_code == 401


def test_invalid_expiry_is_unauthorized_not_server_error(clients):
    a, _, factory = clients
    register(a)
    with factory() as s:
        s.query(LoginSession).update({'expires_at': 'synthetic-invalid-time'})
        s.commit()
    assert a.get('/api/episodes').status_code == 401


def test_cors_preflight_and_rebinding_host(clients):
    a, _, _ = clients
    response = a.options('/api/v1/research-export', headers={'Origin': 'https://attacker.example.test',
        'Access-Control-Request-Method': 'POST'})
    assert 'access-control-allow-origin' not in response.headers
    assert a.get('/api/auth/session', headers={'Host': 'attacker.example.test'}).status_code == 400
    assert a.get('/api/health', headers={'Origin': 'http://localhost:5173'}).headers['access-control-allow-origin'] == 'http://localhost:5173'


def test_sliding_rate_limit_expires_each_attempt(monkeypatch):
    clock = [0]
    monkeypatch.setattr('app.auth.time.monotonic', lambda: clock[0])
    limiter = Limiter()
    limiter.check('synthetic', 2)
    clock[0] = 500
    limiter.check('synthetic', 2)
    clock[0] = 901
    limiter.check('synthetic', 2)
    with pytest.raises(Exception) as error:
        limiter.check('synthetic', 2)
    assert error.value.status_code == 429
