"""Validated deployment policy and a value-free ASGI error boundary."""
import os
import re
from ipaddress import IPv6Address
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from fastapi.responses import JSONResponse
from sqlalchemy.engine import make_url


@dataclass(frozen=True)
class SecuritySettings:
    production: bool
    origins: tuple[str, ...]
    hosts: tuple[str, ...]
    session_hours: int
    database_url: str = field(repr=False)
    synthetic_demo: bool = False
    session_idle_timeout_enabled: bool = False

    @classmethod
    def load(cls, environment=None):
        env = os.environ if environment is None else environment
        mode = env.get('APP_ENV', 'development')
        if mode not in ('development', 'production'):
            raise RuntimeError('APP_ENV must be development or production')
        production = mode == 'production'
        data_mode = env.get('DATA_MODE', 'local' if not production else '')
        if data_mode not in ('local', 'synthetic') or (production and data_mode != 'synthetic'):
            raise RuntimeError('Production requires DATA_MODE=synthetic; local development may use local')
        synthetic_demo = data_mode == 'synthetic'
        if synthetic_demo and env.get('DEMO_ACKNOWLEDGEMENT') != 'synthetic-only-no-real-health-data':
            raise RuntimeError('Synthetic demo acknowledgement is required')
        origins = tuple(x.strip() for x in env.get('CORS_ORIGINS', '' if production else
            'http://localhost:5173,http://127.0.0.1:5173').split(',') if x.strip())
        if not origins:
            raise RuntimeError('CORS_ORIGINS requires explicit origins')
        for origin in origins:
            try:
                parsed = urlsplit(origin)
                _ = parsed.port
                valid = (parsed.scheme in ('http', 'https') and parsed.hostname and
                    '*' not in origin and not parsed.username and not parsed.password and
                    not parsed.path and not parsed.query and not parsed.fragment and
                    not any(c.isspace() for c in origin) and
                    (not production or parsed.scheme == 'https'))
            except ValueError:
                valid = False
            if not valid:
                raise RuntimeError('CORS_ORIGINS must contain exact origins; production requires HTTPS')
        hosts = tuple(x.strip().lower() for x in env.get('ALLOWED_HOSTS', '' if production else
            'localhost,127.0.0.1,[::1],testserver').split(',') if x.strip())
        def valid_host(host):
            if host.startswith('[') and host.endswith(']'):
                try:
                    IPv6Address(host[1:-1])
                    return '%' not in host
                except ValueError:
                    return False
            return len(host) <= 253 and re.fullmatch(
                r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*', host) is not None
        if not hosts or not all(valid_host(h) for h in hosts):
            raise RuntimeError('ALLOWED_HOSTS requires explicit hostnames without ports or wildcards')
        try:
            ttl = int(env.get('SESSION_HOURS', '12'))
            if not 1 <= ttl <= 168:
                raise ValueError()
        except ValueError:
            raise RuntimeError('SESSION_HOURS must be an integer from 1 to 168') from None
        idle_flag = env.get('SESSION_IDLE_TIMEOUT_ENABLED', 'false')
        if idle_flag not in ('true', 'false'):
            raise RuntimeError('SESSION_IDLE_TIMEOUT_ENABLED must be true or false')
        idle_enabled = idle_flag == 'true'
        if idle_enabled and (production or synthetic_demo):
            raise RuntimeError('Idle timeout foundation is limited to explicit local development testing')
        database_url = env.get('DATABASE_URL', 'sqlite:///./migramind.db')
        try:
            database = make_url(database_url)
            if synthetic_demo:
                from pathlib import Path
                name = database.database or ''
                if 'DATABASE_URL' not in env or not (
                    (database.get_backend_name() == 'sqlite' and Path(name).name == 'migramind-synthetic-demo.sqlite') or
                    (database.get_backend_name() == 'postgresql' and name.endswith('_synthetic_demo'))):
                    raise ValueError()
            if production and (database.get_backend_name() != 'postgresql' or
                    not database.host or not database.database or
                    database.query.get('sslmode') != 'verify-full'):
                raise ValueError()
        except Exception:
            # Never interpolate a database URL/driver exception containing credentials.
            raise RuntimeError('Invalid DATABASE_URL; production requires PostgreSQL TLS verification; demo requires a dedicated synthetic-demo database name') from None
        return cls(production, origins, hosts, ttl, database_url, synthetic_demo, idle_enabled)


class PrivateBoundary:
    """Suppress exception values before they can reach server traceback logging.

    No exception, request body, path/query, token or health value is logged here.
    Failures after response start abort with a fresh sanitized exception.
    """
    def __init__(self, app, production=False):
        self.app, self.production = app, production

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        started = False

        async def private_send(message):
            nonlocal started
            if message['type'] == 'http.response.start':
                started = True
                policy = {b'cache-control': b'no-store', b'x-content-type-options': b'nosniff',
                    b'referrer-policy': b'no-referrer', b'x-frame-options': b'DENY'}
                if self.production and scope['scheme'] == 'https':
                    policy[b'strict-transport-security'] = b'max-age=31536000'
                # Preserve repeated headers, especially independent Set-Cookie fields.
                headers = [(k, v) for k, v in message.get('headers', []) if k.lower() not in policy]
                message = {**message, 'headers': headers + list(policy.items())}
            await send(message)

        if self.production and scope['scheme'] != 'https':
            return await JSONResponse({'detail': 'HTTPS is required'}, status_code=400)(scope, receive, private_send)
        failed = False
        try:
            await self.app(scope, receive, private_send)
        except Exception:
            # Leave the exception context before raising a sanitized post-start error.
            failed = True
        if failed:
            if started:
                raise RuntimeError('Response could not be completed') from None
            await JSONResponse({'detail': 'The request could not be completed. Try again.'},
                status_code=500)(scope, receive, private_send)
