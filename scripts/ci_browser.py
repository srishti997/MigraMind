"""Run the existing editable browser suite only against a new disposable database."""

import argparse
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / 'backend'
FRONTEND = ROOT / 'frontend'


def restart_target_spec(temp_root, run_id, database_path, marker, *, existing_target, symlinked):
    """Offline validation for a proposed fresh synthetic restart target.

    Inputs are observations, not proof of directory ownership or safe cleanup.
    No file is opened, created, migrated or deleted by this function.
    """
    if not isinstance(run_id, str) or re.fullmatch(r'[0-9a-f]{32}', run_id) is None:
        raise ValueError('Synthetic run identifier required')
    if type(existing_target) is not bool or type(symlinked) is not bool:
        raise ValueError('Explicit target observations required')
    if existing_target or symlinked:
        raise ValueError('Existing or linked target refused')
    base, candidate = Path(temp_root), Path(database_path)
    expected_dir = base / ('migramind-restart-' + run_id)
    expected_db = expected_dir / ('synthetic-' + run_id + '.sqlite')
    if not base.is_absolute() or base.resolve() != Path(tempfile.gettempdir()).resolve() or candidate != expected_db:
        raise ValueError('Exact temporary synthetic target required')
    if marker != {'classification':'SYNTHETIC_RESTART_ONLY', 'run_id':run_id}:
        raise ValueError('Synthetic ownership marker required')
    return 'REVIEW_ONLY_NOT_AUTHORIZATION'


def restart_environment(base_environment, database_path, api_port, frontend_port):
    """Construct a restricted child environment; does not run any process."""
    if (type(api_port) is not int or type(frontend_port) is not int
            or api_port == frontend_port or not all(1024 <= p <= 65535 for p in (api_port, frontend_port))):
        raise ValueError('Distinct explicit local ports required')
    candidate = Path(database_path)
    match = re.fullmatch(r'synthetic-([0-9a-f]{32})\.sqlite', candidate.name)
    if (not candidate.is_absolute() or match is None
            or candidate.parent.name != 'migramind-restart-' + match.group(1)
            or candidate.parent.parent.resolve() != Path(tempfile.gettempdir()).resolve()):
        raise ValueError('Exact temporary synthetic database path required')
    allow = {'SYSTEMROOT','WINDIR','PATH','COMSPEC','PATHEXT','SYSTEMDRIVE',
             'PROCESSOR_ARCHITECTURE','NUMBER_OF_PROCESSORS','TEMP','TMP'}
    env = {key:value for key,value in base_environment.items() if key.upper() in allow}
    env.update(APP_ENV='development', DATA_MODE='local',
               DATABASE_URL='sqlite:///' + Path(database_path).as_posix(),
               PYTHON_DOTENV_DISABLED='1', PYTHONDONTWRITEBYTECODE='1',
               CORS_ORIGINS=f'http://127.0.0.1:{frontend_port}', ALLOWED_HOSTS='127.0.0.1',
               VITE_API_URL='', VITE_DATA_MODE='local',
               MIGRAMIND_API_PROXY=f'http://127.0.0.1:{api_port}',
               MIGRAMIND_E2E_BASE_URL=f'http://127.0.0.1:{frontend_port}')
    return env


def require_free_ports(ports):
    for port in ports:
        with socket.socket() as sock:
            if os.name == 'nt':
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            sock.bind(('127.0.0.1', port))


def wait_ready(url, process, log_path, startup_marker):
    opener = build_opener(ProxyHandler({}))
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError('A temporary verification server exited before readiness')
        # An unrelated server winning a port race must not satisfy readiness.
        # Check our own server's successful-bind log before requesting its URL.
        # Vite inserts ANSI styling inside the URL (notably around the port).
        startup_log = re.sub(r'\x1b\[[0-9;]*m', '',
                             log_path.read_text(encoding='utf-8', errors='replace'))
        if startup_marker not in startup_log:
            time.sleep(.25)
            continue
        try:
            with opener.open(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (URLError, TimeoutError):
            pass
        time.sleep(.25)
    raise RuntimeError('Temporary verification server readiness timed out')


def stop(process):
    if process.poll() is not None:
        return
    if os.name == 'nt':
        # Include the virtual-environment launcher's children, not just its PID.
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name == 'nt':
            process.kill()
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api-port', type=int, default=8000)
    parser.add_argument('--frontend-port', type=int, default=5173)
    args = parser.parse_args()
    ports = (args.api_port, args.frontend_port)
    if len(set(ports)) != 2 or any(not 1024 <= port <= 65535 for port in ports):
        parser.error('Use two distinct ports between 1024 and 65535')
    api_origin = f'http://127.0.0.1:{args.api_port}'
    frontend_origin = f'http://127.0.0.1:{args.frontend_port}'
    node = shutil.which('node')
    if node is None:
        raise RuntimeError('Node.js is required')
    require_free_ports(ports)  # Never use, migrate or stop an existing local server.
    browser = os.environ.get('MIGRAMIND_BROWSER')
    if not browser:
        browser = subprocess.check_output(
            [node, '--input-type=module', '-e',
             "import {chromium} from '@playwright/test'; console.log(chromium.executablePath())"],
            cwd=FRONTEND, text=True).strip()
    if not Path(browser).is_file():
        raise RuntimeError('Chromium is missing; install it with the locked Playwright CLI')

    with tempfile.TemporaryDirectory(prefix='migramind-ci-') as directory:
        target = Path(directory).resolve()
        assert target.parent == Path(tempfile.gettempdir()).resolve()
        env = {**os.environ, 'APP_ENV': 'development', 'DATA_MODE': 'local',
               'DATABASE_URL': 'sqlite:///' + (target / 'editable.sqlite').as_posix(),
               # Retain the Origin used explicitly by existing API browser tests.
               'CORS_ORIGINS': frontend_origin + ',http://127.0.0.1:5173,http://localhost:5173',
               'ALLOWED_HOSTS': '127.0.0.1,localhost,testserver',
               'VITE_API_URL': '', 'VITE_DATA_MODE': 'local',
               'MIGRAMIND_API_PROXY': api_origin,
               'MIGRAMIND_E2E_BASE_URL': frontend_origin,
               'MIGRAMIND_BROWSER': str(Path(browser).resolve())}
        processes, logs = [], []
        try:
            subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'],
                           cwd=BACKEND, env=env, check=True)
            commands = [
                ([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1',
                  '--port', str(args.api_port), '--no-access-log'], BACKEND),
                ([node, 'node_modules/vite/bin/vite.js', '--host', '127.0.0.1',
                  '--port', str(args.frontend_port), '--strictPort'], FRONTEND),
            ]
            for index, (command, cwd) in enumerate(commands):
                log = (target / f'server-{index}.log').open('w', encoding='utf-8')
                logs.append(log)
                processes.append(subprocess.Popen(
                    command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=os.name != 'nt',
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0))
            wait_ready(api_origin + '/api/ready', processes[0],
                       target / 'server-0.log', 'Uvicorn running on ' + api_origin)
            wait_ready(frontend_origin, processes[1],
                       target / 'server-1.log', frontend_origin + '/')
            subprocess.run([node, 'node_modules/@playwright/test/cli.js', 'test',
                            '--config', 'playwright.config.mjs',
                            '--output', str(target / 'browser-results')],
                           cwd=FRONTEND, env=env, check=True)
        except Exception:
            for index in range(len(logs)):
                logs[index].flush()
                print((target / f'server-{index}.log').read_text(
                    encoding='utf-8', errors='replace')[-4000:], file=sys.stderr)
            raise
        finally:
            for process in reversed(processes):
                stop(process)
            for log in logs:
                log.close()


if __name__ == '__main__':
    main()
