"""TEST ONLY: real application routes over a fresh synthetic database and clock.

Run only from a filtered source copy with the existing test interpreter/PYTHONPATH.
No database path is accepted. No migrations/provisioning or existing data access.
"""
from datetime import datetime, timedelta, timezone
import importlib
import os
from pathlib import Path
import secrets
import tempfile
from threading import Lock

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
import uvicorn


def main():
    token = os.environ.get('MIGRAMIND_IDLE_TEST_TOKEN', '')
    origin = os.environ.get('MIGRAMIND_IDLE_TEST_FRONTEND', '')
    from urllib.parse import urlsplit
    parsed = urlsplit(origin)
    if len(token) < 24 or parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or not parsed.port or parsed.path:
        raise RuntimeError('Explicit isolated loopback test configuration required')
    port = int(os.environ['MIGRAMIND_IDLE_TEST_PORT'])
    if not 1024 <= port <= 65535: raise RuntimeError('Invalid test port')
    with tempfile.TemporaryDirectory(prefix='migramind-idle-real-') as directory:
        database = Path(directory).resolve()/'synthetic-idle.sqlite'
        if database.exists(): raise RuntimeError('Test database must be new')
        os.environ.update(APP_ENV='development', DATA_MODE='local', SESSION_IDLE_TIMEOUT_ENABLED='true',
            DATABASE_URL='sqlite:///'+database.as_posix(), CORS_ORIGINS=origin,
            ALLOWED_HOSTS='127.0.0.1,localhost', PYTHON_DOTENV_DISABLED='1')
        application = importlib.import_module('app.main')
        clock_lock = Lock()
        stamp = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
        def clock():
            with clock_lock: return stamp
        importlib.import_module('app.auth').now = clock
        application.Base.metadata.create_all(application.engine)
        wrapper = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
        def authorize(request):
            if request.client.host != '127.0.0.1' or not secrets.compare_digest(request.headers.get('x-idle-test-token',''),token):
                raise HTTPException(403,'Isolated fixture access required')
        class Advance(BaseModel):
            minutes: int = Field(strict=True, ge=0, le=720)
        @wrapper.get('/__idle_test__/info')
        def info(request:Request):
            authorize(request)
            return {'fixture':'synthetic-idle-v1','server_time':clock().isoformat()}
        @wrapper.post('/__idle_test__/advance')
        def advance(data:Advance,request:Request):
            nonlocal stamp
            authorize(request)
            with clock_lock: stamp += timedelta(minutes=data.minutes)
            return {'server_time':clock().isoformat()}
        @wrapper.post('/__idle_test__/shutdown')
        def shutdown(request:Request):
            authorize(request); server.should_exit = True
            return {'stopping':True}
        wrapper.mount('/',application.app)
        server = uvicorn.Server(uvicorn.Config(wrapper,host='127.0.0.1',port=port,
            access_log=False,proxy_headers=False,log_level='error'))
        try: server.run()
        finally: application.engine.dispose()


if __name__ == '__main__': main()
