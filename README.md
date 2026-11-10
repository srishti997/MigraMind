# MigraMind

A migraine diary and support prototype that keeps missing days unknown and makes research-data limitations visible. Built with **React, TypeScript and FastAPI**, it combines account-isolated tracking, daily revision history, descriptive insights and user-controlled support tools.

**Demo status:** a local, read-only synthetic demonstration. No clinically validated forecasting model or migraine risk score is served. Synthetic results demonstrate software behavior only; do not enter real health information.

## What to look at in 30 seconds

| Product behavior | Technical value |
| --- | --- |
| Diary, daily status and calendar | Exact instants plus IANA zones; unknown, zero and explicitly reported no migraine stay distinct |
| Private daily-report history | Server availability differs from event time; revision checks prevent lost updates |
| Accounts and support tools | Owner isolation, cookie/CSRF boundaries, guarded phone links and independent emergency access |
| Descriptive insights and research review | Missingness stays visible; preparation exports require explicit confirmation |
| Offline research baseline | Fixed-grid chronological splits, availability purging and training-only preprocessing; no model deployed |

Start with the [five-minute walkthrough and final checks](docs/PORTFOLIO_READINESS.md), [architecture diagram](docs/PROJECT_ARCHITECTURE.md), [claim-to-source evidence](docs/PROJECT_EVIDENCE_MATRIX.md), or [interview preparation](docs/INTERVIEW_PREPARATION.md). Personal contributions and tool assistance require the presenter's confirmation.

## Run the synthetic demo locally (PowerShell)

Prerequisites: Python 3.13, Node.js 22 with npm and a current Chromium browser. This review used Node 22.17.1 and npm 11.5.1. SQLite is sufficient; Docker and PostgreSQL are not required for the local demonstration. The quickstart was reproduced from a clean source copy with fresh dependency environments on this Windows setup. Separate-machine and other-platform installations remain unverified.

From the repository root in a new terminal:

```powershell
python -m venv backend/.venv
./backend/.venv/Scripts/python -m pip install -r backend/requirements-ml.lock.txt
if ($LASTEXITCODE) { throw 'Dependency installation failed' }
cd backend
$demoRoot = Join-Path ([IO.Path]::GetTempPath()) ('migramind-demo-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $demoRoot | Out-Null
$env:APP_ENV='development'
$env:DATA_MODE='synthetic'
$env:DEMO_ACKNOWLEDGEMENT='synthetic-only-no-real-health-data'
$env:DATABASE_URL='sqlite:///' + (Join-Path $demoRoot 'migramind-synthetic-demo.sqlite').Replace('\','/')
$env:CORS_ORIGINS='http://127.0.0.1:5185'
$env:ALLOWED_HOSTS='127.0.0.1,localhost'
$env:PORT='8015'
./.venv/Scripts/python -m alembic upgrade head
if ($LASTEXITCODE) { throw 'Migration failed' }
./.venv/Scripts/python -m app.demo provision
if ($LASTEXITCODE) { throw 'Provisioning failed' }
./.venv/Scripts/python -m app.serve
```

Provisioning prompts privately for a fresh demo-only password and refuses a nonempty target. Never point it at an existing personal/research database. The base [Python lock](backend/requirements.lock.txt) is sufficient for runtime; the ML lock above also supports the offline regression suite.

In a second new terminal, from the repository root:

```powershell
cd frontend
npm.cmd ci
if ($LASTEXITCODE) { throw 'Frontend installation failed' }
$env:VITE_API_URL=''
$env:VITE_DATA_MODE='synthetic'
$env:MIGRAMIND_API_PROXY='http://127.0.0.1:8015'
npm.cmd run build
if ($LASTEXITCODE) { throw 'Build failed' }
node node_modules/vite/bin/vite.js preview --host 127.0.0.1 --port 5185 --strictPort
```

Open **http://127.0.0.1:5185**. Sign in as `demo@synthetic.example.test` with the private password. Start with **Explore daily status** and **Show example calendar**: fixtures are fixed in January 2026, so current 30/90-day insights may correctly be empty. The fixture includes three daily statuses, one episode and saved caregiver notes; it has no contacts, wellness, early symptoms or feedback. History contains creation revisions, not fabricated corrections. Follow the [timed walkthrough](docs/PORTFOLIO_READINESS.md#five-minute-demonstration).

Stop both terminals with Ctrl+C. Rehearse from a new empty target next time; there is no browser reset. Vite preview is for this loopback rehearsal only. For configuration, editable-development boundaries and operations, see the [runbook](docs/OPERATIONS_RUNBOOK.md) and [authentication/privacy guide](docs/authentication-privacy.md).

## Verify

Use a fresh terminal so demo settings do not affect editable tests:

```powershell
cd backend
$env:APP_ENV='development'
$env:DATA_MODE='local'
$env:DATABASE_URL='sqlite://'
./.venv/Scripts/python -m pytest -q
./.venv/Scripts/python -m pip check
cd ../frontend
node node_modules/vitest/vitest.mjs run --maxWorkers=1
npm.cmd audit
```

The [Phase 2 release-readiness review](docs/RELEASE_READINESS.md) records current Windows/Ubuntu evidence, safe reproduction commands, accessibility gaps and release blockers. The [portfolio review](docs/PORTFOLIO_READINESS.md) retains the timed demonstration. The [CI workflow and local browser harness](docs/CI.md) run backend/frontend tests, both production builds and the existing editable browser suite using disposable data. Browser suites require **disposable, separately migrated targets**; the default Playwright URL alone does not prove the database is disposable. Use the harness rather than running mutation suites against a personal or reused instance. The dedicated built-demo browser suite remains a separate check because it requires provisioning.

## Source map and limits

- [Frontend workspace](frontend/src/main.tsx), [API client](frontend/src/api.ts), [tracking validation](frontend/src/tracking.ts) and [synthetic guide](frontend/src/DemoGuide.tsx).
- [API/models](backend/app/main.py), [daily revisions](backend/app/prospective.py), [demo boundary](backend/app/deployment.py) and [migrations](backend/alembic/versions).
- [Current revision-aware research baseline](docs/ML_RESEARCH_BASELINE.md), [research presentation](docs/RESEARCH_PRESENTATION.md), [final audit](docs/FINAL_PROJECT_AUDIT.md) and [Sprint 18 remediation](docs/AUDIT_REMEDIATION.md).
- [Historical README/sprint results](docs/SPRINT_HISTORY.md) are archived separately; they are not current verification.

Real-data research remains blocked on suitable independently verified outcomes, genuine study consent/governance and prospective/statistical validation. Hosted PostgreSQL/TLS/roles/backup operations remain unverified. Screen readers, alternate browsers, real-device handoffs and task-based migraine-time comfort need manual review. Support ordering is deterministic; calling, SMS and sharing require user action and establish no delivery or monitoring guarantee. Do not activate emergency or contact links during a demonstration. No clinical, accessibility-certification or production-security claim is made.
