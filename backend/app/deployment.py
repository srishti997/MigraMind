"""Small operational boundaries: no health payloads or configuration in probes/logs."""
import logging
from sqlalchemy import text
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

SCHEMA_REVISION = '010'
FIXTURE_VERSION = 'synthetic-demo/v1'
DEMO_EMAIL = 'demo@synthetic.example.test'


def operation_event(event):
    if event not in {'startup_ready', 'startup_blocked', 'readiness_unavailable', 'demo_write_blocked'}:
        raise ValueError('Unknown operational event')
    logging.getLogger('migramind.operations').warning('{"event":"%s"}', event)


def database_ready(engine, synthetic_demo=False):
    try:
        with engine.connect() as connection:
            if engine.dialect.name == 'postgresql':
                connection.execute(text("SET LOCAL statement_timeout = '3000ms'"))
            if connection.scalar(text('SELECT 1')) != 1:
                return False
            if connection.execute(text('SELECT version_num FROM alembic_version')).scalars().all() != [SCHEMA_REVISION]:
                return False
            if synthetic_demo:
                markers = connection.execute(text('SELECT fixture_version FROM demo_deployments WHERE id=1')).scalars().all()
                if markers != [FIXTURE_VERSION]:
                    return False
                users = connection.execute(text('SELECT email FROM users')).scalars().all()
                if users != [DEMO_EMAIL]:
                    return False
        return True
    except Exception:
        return False


class DemoBoundary:
    def __init__(self, app, enabled=False, probe=None):
        self.app, self.enabled, self.probe = app, enabled, probe

    async def __call__(self, scope, receive, send):
        if not self.enabled or scope['type'] != 'http':
            return await self.app(scope, receive, send)
        path = scope['path']
        if scope['method'] not in ('GET', 'HEAD', 'OPTIONS') and path not in (
            '/api/auth/login', '/api/auth/logout', '/api/v1/research-export'):
            operation_event('demo_write_blocked')
            return await JSONResponse({'detail': 'Synthetic demonstration is read-only. Do not submit real health information.'},
                status_code=403)(scope, receive, send)
        if path.startswith('/api/') and path not in ('/api/health', '/api/ready') and not await run_in_threadpool(self.probe):
            return await JSONResponse({'detail': 'Demonstration unavailable'}, status_code=503)(scope, receive, send)

        async def tagged_send(message):
            if message['type'] == 'http.response.start':
                message = {**message, 'headers': [*message.get('headers', []),
                    (b'x-migramind-data-mode', b'synthetic')]}
            await send(message)
        await self.app(scope, receive, tagged_send)
