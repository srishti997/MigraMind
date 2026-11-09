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
