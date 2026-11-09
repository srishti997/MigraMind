# Continuous integration

The [GitHub Actions workflow](../.github/workflows/ci.yml) runs on pull requests
and pushes to `main`. It uses GitHub-hosted Ubuntu 24.04 runners, Python 3.13 and
Node 22, matching the runtime families documented in the README. Patch releases
within those runtime families may advance; application dependencies come from the
existing exact Python locks and npm lockfile.

## Jobs and boundaries

| Job | Existing configuration reused | Checks |
| --- | --- | --- |
| Backend and offline ML | `backend/requirements-ml.lock.txt`, existing pytest fixtures | `pip check`, full `pytest -q -ra`; ML dependencies are installed so the offline regressions can run |
| Frontend | `frontend/package-lock.json`, npm `test` and `build` scripts | One-worker Vitest run; TypeScript/Vite production builds with `VITE_DATA_MODE=local` and `synthetic` |
| Browser | Base Python lock, npm lock, `frontend/playwright.config.mjs`, existing `frontend/e2e` tests | Locked Playwright Chromium; fresh editable SQLite target; real API and Vite integration plus existing mocked browser scenarios |

Only `contents: read` is granted. Checkout does not persist Git credentials.
Actions are pinned to full commit SHAs, resolved from their official v6 tags on
2026-11-09. Package caches are keyed by their lockfiles; databases, environments,
build output and browser results are not cached or uploaded. Superseded runs are
cancelled, and each job has a finite timeout. No deployment, repository write,
secret, external database service or `pull_request_target` event is configured.

The backend process imports with `APP_ENV=development`, `DATA_MODE=local` and
`DATABASE_URL=sqlite://`. Its existing fixtures use memory/temporary databases.
Existing backend deployment tests retain their direct, isolated tests of the
provisioning **function**; the workflow and harness invoke no provisioning CLI,
seed script or demo initialization command.

The dedicated `test:demo` browser suite is intentionally omitted: it requires a
provisioned synthetic fixture. Both frontend build modes are checked without
provisioning. Browser execution covers the existing editable suite, including its
mocked synthetic-UI checks. This does not replace the separately rehearsed built
demo, PostgreSQL, real-device, accessibility or production-readiness checks.

## Disposable browser execution

[scripts/ci_browser.py](../scripts/ci_browser.py) is shared by CI and local runs.
It always replaces inherited database, environment, API-proxy and browser-target
settings with its own local test settings. It migrates only a newly generated
SQLite path under the operating-system temporary directory. Test accounts and
fictional records are created by the existing browser tests, not a seeder.

The helper defaults to loopback ports **8000 and 5173**. If a port is occupied, it
refuses to proceed; it never connects to or stops that existing server. Locally,
choose different free ports with `--api-port 18000 --frontend-port 15173`.
Existing tests explicitly use `http://127.0.0.1:5173` as an API Origin; the temporary
API allows that Origin alongside the selected frontend origin without changing
the tests or application configuration files.
It waits for API and frontend readiness and cleans up its server process groups,
temporary database, logs and browser output on success or failure. Failures retain
the test output and server-log tails in the console. Existing product tests also
write ignored `.research` screenshots; these are not cached or uploaded. Ordinary cancellation invokes
cleanup when Python receives the interruption; forced runner termination relies
on the disposable GitHub runner being discarded.

From a fresh development terminal after installing the locked dependencies:

```powershell
# From frontend; install the Chromium revision belonging to the locked Playwright.
node node_modules/@playwright/test/cli.js install chromium
cd ..
./backend/.venv/Scripts/python scripts/ci_browser.py
```

CI uses `install --with-deps chromium` to include Linux system packages. The helper
resolves Chromium through the installed Playwright package and passes its path via
the existing `MIGRAMIND_BROWSER` override. For a local run with an already installed
Chrome, explicitly set that variable to its executable; no browser is downloaded
automatically by the helper. Do not run the raw browser suite against a personal
instance as a substitute for the disposable helper.

## Verification and remaining limits

Local verification on 2026-11-09 used Windows, Python 3.13.11, Node 22.17.1 and
npm 11.5.1 with the existing locked environment:

| Check | Local result |
| --- | --- |
| Backend / offline ML | **254 passed**, no failures/skips; 317.69s. Existing Starlette/httpx deprecation warning. `pip check` passed. |
| Frontend | **80 passed across 14 files**, no failures/skips; 178.39s with `--maxWorkers=1`. |
| Production builds | Both local and synthetic TypeScript/Vite builds passed through the existing npm script, with output in fresh temporary directories. |
| Browser harness | **21 passed** using existing Chrome and alternate loopback ports 18000/15173. The helper's temporary targets and server processes were cleaned up. |
| Safety / failure handling | Occupied default ports were refused. A forced browser-command failure propagated as nonzero, cleaned the temporary database/processes and left a temporary guard file's hash unchanged. Deliberately inherited production/synthetic/database/remote-target settings were replaced with isolated local settings. |
| Workflow | Official actionlint **v1.7.12** passed, with its release checksum verified before execution. ShellCheck/Pyflakes were unavailable and disabled for this local lint invocation; Python syntax was checked separately. |
| Scope / preservation | Exactly four intended text files; lock-version matching, documentation links, syntax and diff checks passed. All 10 migration-source hashes match the historical manifest. No application, lockfile, migration, production configuration or secret changes. |

The initial PowerShell npm wrapper stripped arguments after `--`: its frontend run
passed without the requested worker limit, but its first build invocation failed.
The final run invoked the npm CLI through Node to preserve the exact CI arguments;
both builds and the one-worker frontend run passed. No application assertion was
changed. The workflow uses Bash on Ubuntu rather than that PowerShell wrapper.

The workspace database was never a test target. Its current hash differs from the
older Sprint 18 manifest, which is not a baseline for this task; no byte-equality
claim is made for that live file. Isolation and unchanged bytes were verified
directly with the separate temporary guard fixture instead. Existing services on
the default local ports were left running and untouched.

The hosted workflow itself cannot run until the user approves publication; no
commit, push, PR or Actions run is performed by this change. No provisioning CLI or
seed script was run. The existing backend provisioning-function unit tests ran
only against their temporary fixtures as part of the full backend suite.

The first approved GitHub run must verify Ubuntu dependency-wheel availability,
action execution/cache restore, Chromium's Linux system packages, the POSIX cleanup
path and the actual pull-request/push triggers. WSL was inaccessible and no Docker
daemon was available locally. Local Windows results and static
workflow validation do not establish those hosted results. No clinical, research,
deployment or accessibility claim follows from a green workflow.

References: [Playwright's CI setup](https://playwright.dev/docs/ci-intro),
[checkout](https://github.com/actions/checkout),
[setup-python](https://github.com/actions/setup-python), and
[setup-node](https://github.com/actions/setup-node).
