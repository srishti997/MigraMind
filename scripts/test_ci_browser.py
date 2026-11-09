"""Readiness regressions; use only ephemeral loopback HTTP servers and log files."""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from ci_browser import wait_ready


@contextmanager
def http_server(status=200):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            self.send_response(status)
            self.end_headers()
            self.wfile.write(b'{"status":"ready"}')

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


class ReadinessTests(unittest.TestCase):
    def test_colored_vite_url_reaches_http_with_or_without_trailing_slash(self):
        with http_server() as (origin, requests), tempfile.TemporaryDirectory() as directory:
            port = origin.rsplit(':', 1)[1]
            log = Path(directory) / 'vite.log'
            # Vite colors the URL and makes the port bold within it on CI.
            log.write_text(f'Local: \x1b[36mhttp://127.0.0.1:\x1b[1m{port}\x1b[22m/\x1b[39m\n')
            for suffix in ('', '/'):
                with self.subTest(suffix=suffix), \
                     patch('ci_browser.time.monotonic', side_effect=[0, 0, 61]), \
                     patch('ci_browser.time.sleep'), \
                     patch.dict('os.environ', {
                         **{key: 'http://127.0.0.1:9' for key in
                            ('HTTP_PROXY', 'http_proxy', 'HTTPS_PROXY', 'https_proxy',
                             'ALL_PROXY', 'all_proxy')}, 'NO_PROXY': '', 'no_proxy': ''}):
                    wait_ready(origin + suffix, Mock(poll=lambda: None), log, origin + '/')
            self.assertEqual(requests, ['/', '/'])

    def test_missing_startup_marker_does_not_probe_another_server(self):
        with http_server() as (origin, requests), tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / 'vite.log'
            log.write_text('Vite is still starting\n')
            with patch('ci_browser.time.monotonic', side_effect=[0, 0, 61]), \
                 patch('ci_browser.time.sleep'), \
                 self.assertRaisesRegex(RuntimeError, 'readiness timed out'):
                wait_ready(origin, Mock(poll=lambda: None), log, origin + '/')
            self.assertEqual(requests, [])

    def test_non_200_response_is_not_ready(self):
        for status in (404, 503):
            with self.subTest(status=status), http_server(status) as (origin, requests), \
                 tempfile.TemporaryDirectory() as directory:
                log = Path(directory) / 'api.log'
                marker = 'Uvicorn running on ' + origin
                log.write_text(marker + '\n')
                with patch('ci_browser.time.monotonic', side_effect=[0, 0, 61]), \
                     patch('ci_browser.time.sleep'), \
                     self.assertRaisesRegex(RuntimeError, 'readiness timed out'):
                    wait_ready(origin + '/api/ready', Mock(poll=lambda: None), log, marker)
                self.assertEqual(requests, ['/api/ready'])

    def test_exited_process_is_not_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, 'exited before readiness'):
                wait_ready('http://127.0.0.1:9/', Mock(poll=lambda: 1),
                           Path(directory) / 'unused.log', 'unused')


if __name__ == '__main__':
    unittest.main()
