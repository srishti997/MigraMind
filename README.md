# MigraMind

Mobile-first migraine tracking and caregiver preferences. React + TypeScript + Vite + Tailwind CSS, FastAPI, SQLAlchemy, Alembic and PostgreSQL. All seeded records are synthetic. This is an account-isolated local prototype with cookie authentication. Do not host publicly or enter real health information before production security and privacy review. See [Sprint 6 authentication and privacy](docs/authentication-privacy.md) for current behavior and limitations; older sprint verification below is historical.

## Run locally (PowerShell)

Start PostgreSQL using Docker Desktop:

```powershell
Copy-Item .env.example .env
# Set a private POSTGRES_PASSWORD in the root .env before starting Docker.
docker compose up -d
cd backend
python -m venv .venv
./.venv/Scripts/python -m pip install -r requirements.txt
Copy-Item .env.example .env
# This template defaults to SQLite. For PostgreSQL, set DATABASE_URL in backend/.env
# using your local database credentials before running migrations.
./.venv/Scripts/python -m alembic upgrade head
./.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

If Docker is unavailable, omit the environment copy: the default database is `backend/migramind.db` (SQLite). Or set `DATABASE_URL=sqlite:///./migramind.db` in `.env`. Run the same migration command, then create an account in the browser. Do not seed for normal use: legacy seed records remain unassigned and are deliberately hidden from new accounts.

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. API documentation: http://127.0.0.1:8000/docs. The Vite proxy routes `/api` to the backend. `frontend/.env.example` describes the optional API origin for separate hosting. CORS origins are configurable through `backend/.env`.

## Verify

```powershell
cd frontend
npm test
npm run build
cd ../backend
./.venv/Scripts/python -m pytest -q
```

API tests use an isolated in-memory database and cover episode lifecycle, invalid input, contact updates/deletion and profile persistence. Frontend tests cover timezone-safe calendar dates and leap-year alignment.

## Behavior and boundaries

- Diary: add, read notes, edit and delete episodes. Calendar highlights records and filters entries by date. Overview calculates descriptive statistics from diary entries, not medical predictions.
- Contacts: add, edit, delete and initiate calls with `tel:` links. Desktop dialing depends on an installed calling handler. Demo numbers must be replaced before use.
- Caregiver profile: saved personal support preferences; viewable in Attack Mode. No automatic sharing or messaging.
- Attack Mode: low-light colors, large controls, support preferences, and user-initiated calling. It does not dispatch emergency services or send SOS notifications.
- No AI model or diagnostic/recommendation service is connected. No medical advice is generated.
- Backend request access logs are disabled by the documented launch command. SQL logging is disabled. Do not log request bodies or add health details to telemetry. Infrastructure logging needs a separate review before production.
- Sprint 6 adds account authentication and server-side user isolation. Encryption at rest, managed backup/retention, account recovery, MFA and production deployment remain outstanding. Bind to loopback and use synthetic records only.
- SQLite is the locally verified fallback; PostgreSQL configuration and migrations are provided. A working Docker daemon is required to verify PostgreSQL.

## Structure

`frontend/src/main.tsx`: UI and API client; `style.css`: responsive styles plus Tailwind import; `utils.ts`: calendar utilities. `backend/app/main.py`: validated APIs and SQLAlchemy models; `backend/alembic`: versioned schema; `backend/seed.py`: synthetic fixtures.
## Verification in this workspace

Production frontend build passed. Frontend tests: 2 passed. Backend tests: 3 passed (one upstream TestClient deprecation warning). SQLite migration and synthetic seeding succeeded. Live frontend HTTP, proxied API health, and create/read/delete smoke checks passed. npm audit reported zero vulnerabilities after updating Vitest. Browser rendering, assistive-technology behavior, actual phone dialing and PostgreSQL were not verified in this environment. No browser automation tool was available; Docker daemon was unavailable.

## Appearance

Choose **Warm Day** or **Gentle Dark** using the Appearance selector in the header or Settings. The preference is stored only on this device; Attack Mode temporarily uses its own dim palette. Opening the episode form during Attack Mode keeps that palette. Shared semantic tokens are centralized in `frontend/src/style.css`. The specified muted base color is retained, with a darker readable text token used to meet 4.5:1 contrast on warm backgrounds. Mobile navigation wraps, calendar columns shrink to available width, and reduced-motion preferences are respected.

Redesign verification: production build, two frontend tests and three backend tests passed. Text palette contrast pairs were checked at 4.5:1 or higher. Updated frontend modules and existing proxied APIs returned HTTP 200. Actual browser layout, screen-reader behavior and device-specific dialing still require manual inspection.

## Sprint 2: attack assistance

Enter Attack Mode from the header. The dedicated dark view provides immediate Exit and India 112 emergency calling, trusted-contact selection, a user-initiated call link, and a prepared SMS link. SMS text is previewable before opening the device app. No delivery, dispatch or monitoring status is simulated. The platform-specific SMS body delimiter is covered by tests; actual iOS/Android app handoff remains a manual check. Do not place test calls to emergency numbers.

The collapsible support card uses saved caregiver preferences (what helps, what to avoid, and communication preferences), available without another login prompt in this local prototype. Edit them through Caregiver profile and save. Empty contacts, loading failures and session API failures have distinct states; emergency calling remains available even if the API fails.

Start/end tracking is explicit. Entering/leaving Attack Mode does not start/end a session. UTC ISO timestamps persist in the database. Repeated start requests return the existing active session, protected by a unique database slot; repeated end requests preserve the original end timestamp. Reloading the interface reads the persisted status. Sessions and diary entries remain separate; no episode is fabricated from a session.

Additive migration `002` adds communication preferences and the attack_sessions table. Existing diary/contact/profile records are preserved. For an existing checkout, run from backend:

```powershell
./.venv/Scripts/python -m alembic upgrade head
```

Session API routes:

- GET `/api/attack-sessions/current`: most recent session, active or ended, or null.
- GET `/api/attack-sessions`: recorded session timestamps.
- POST `/api/attack-sessions/start`: start or return the current active session.
- POST `/api/attack-sessions/{id}/end`: explicitly end a session, idempotently.

Emergency guidance sources: [India ERSS](https://112.gov.in/) and [NHS headache warning signs](https://www.nhs.uk/symptoms/headaches/). The interface offers access to urgent help without diagnosing symptoms or requiring AI approval. This prototype is not a medical device or monitored emergency service.

### Sprint 2 verification

Production build passed; 11 frontend tests, 7 backend tests and 2 Playwright browser tests passed. Tests cover contact selection/absence, support preferences, API failure, safe link targets, keyboard entry/exit and dialog focus, session persistence and idempotency, database duplicate prevention, and migration preservation. Browser checks covered all pages at 320/390/768/1280px, no horizontal overflow, large controls, urgent controls in the initial viewport, and reduced motion. No call/SMS links were activated.

Run browser checks while the frontend is running:

```powershell
cd frontend
npm run test:e2e
```

Playwright uses installed Windows Chrome by default. Set `MIGRAMIND_BROWSER` to another Chromium executable path if needed. Browser tests intercept API requests with synthetic fixtures; backend persistence is tested separately. Test screenshots/output are ignored by Git. Manual checks remain: iOS/Android SMS composer/dialer behavior, screen readers, real-device font scaling/landscape and comfort during use. PostgreSQL remains unverified without a Docker daemon. No authentication or multi-user security is added by this sprint.

## Sprint 3: smart tracking and data foundation

Sprint 2 was verified before changes: its existing 7 backend, 11 frontend and 2 browser tests passed. Attack Mode, contact/SMS links, saved support card, emergency access and persistent sessions remain available.

### Try the new tracking experience

Open http://127.0.0.1:5173/ and refresh:

1. **Migraine diary → Log an episode**: only a start time is required for a new timed entry. Severity is optional and accepts 0–10. Expand **Optional details** to enter end time, pain location, symptoms, activity impact, observed factors, medication names/times, notes or an existing session link. Edit/delete controls and **View entry details** are available for each episode. Medication logging gives no recommendations.
2. **Wellness → Daily check-in**: log any combination of sleep hours/quality, stress, hydration estimate, missed meals, screen hours or optional cycle observations. Blank stays unknown; zero and No are explicit values. One check-in per local date; edit the existing entry instead of duplicating it.
3. **Early symptoms → Log early symptom**: save a symptom and onset time independently of migraine attacks. These records are not classified as proven prodromes or triggers.
4. **Calendar**: dates mark episodes and wellness check-ins. Selecting a date lists all its episodes and check-in, with add/edit controls. Known episodes spanning midnight appear on each affected date; unknown ends are not extrapolated. Timed episodes are shown in your device timezone, while date-only legacy entries retain their recorded date.
5. **Overview**: review recorded headache days, onset frequency, average reported severity and average known duration for the last 30 calendar days (today plus the previous 29). A chart and accessible data table use stored episode counts. No data, unknown measurements and zero recorded episodes are distinguished. Missing logs do not prove headache-free days. There are no causal or predictive claims.
6. **Settings → Export my records (JSON)**: download a schema-versioned export of episodes, wellness, early symptoms, sessions, contacts and caregiver preferences. Keep the file private. Export occurs only after a user action.

### Schema and time semantics

Migration `003` preserves existing records, makes severity/duration nullable, and adds episode start/end timestamps, IANA timezone, pain location, symptom list, functional impact, optional medication observations and related-session ID. New tables `wellness` and `early_symptoms` keep daily exposures and potential early symptoms separate from episodes. Observation records retain their creation time; onset times are separate. Session links are validated against existing sessions and do not start/end them.

New timestamp inputs require explicit offsets at the API boundary, normalize to UTC, and retain an IANA timezone. Browser inputs use the device timezone shown in the form. Existing exact timestamps are preserved when unchanged, including the repeated hour at a daylight-saving transition. Invalid/nonexistent local times are rejected. Legacy dates/durations have no fabricated precise start or end. Known start/end determine duration; otherwise a reported duration may be supplied or left unknown.

Headache days are distinct local dates overlapped by entries with severity above zero; zero is a valid no-pain report, and unrated entries cannot establish headache days. An exact midnight endpoint does not add the following day. Entries with unknown end times count only their onset date. Frequency and averages use episode onset dates in the reporting window; known overlapping headache days may include an onset before the window. Severity averages exclude missing values and include explicit zeroes. Duration averages exclude unknown values. Wellness alone cannot establish an attack-free observation period.

Run migrations before starting the updated backend:

```powershell
cd backend
./.venv/Scripts/python -m alembic upgrade head
```

The automatic downgrade for migration 003 is intentionally disabled because converting unknown values back to mandatory measurements or dropping advanced data would lose information. Export and review data before any manual downgrade.

Additional APIs:

- GET/POST `/api/wellness`; PUT/DELETE `/api/wellness/{id}`.
- GET/POST `/api/early-symptoms`; PUT/DELETE `/api/early-symptoms/{id}`.
- GET `/api/insights?timezone_name=Asia%2FKolkata` (optional `as_of=YYYY-MM-DD` for a reproducible 30-day window).
- GET `/api/export` returns downloadable JSON with no-store caching.
- Existing `/api/episodes` POST/PUT accept advanced fields and continue to accept legacy date/severity/duration input.

At completion of Sprint 3, this was a single-user local prototype; Sprint 6 now adds authentication and ownership (see current guidance above). Both servers bind to loopback; do not publicly expose the API or use real health records without production access controls. No AI predictions, diagnosis, medication recommendations or causal inference were added. No health payloads are written to application logs.

### Final Sprint 3 validation

Production build passed. Backend: 25 tests passed, with the existing upstream TestClient deprecation warning. Frontend: 16 tests passed. Browser: 4 tests passed, including all navigation pages at 320/390/768/1280px, keyboard/reduced-motion regression checks, synthetic tracking/calendar/export flows, and preservation of the later repeated-hour timestamp during daylight saving. A newly started attack session can be linked from the diary without reloading. Backend dependency checks passed. Live frontend/proxied APIs/export returned valid responses, and the local SQLite database is at migration 003. No real calls/messages were made and browser fixtures were synthetic. PostgreSQL and real-device screen-reader/dialer/SMS behavior remain unverified.

## Sprint 4: forecasting research foundation

The local data audit found no suitable real longitudinal training dataset. Application/demo records were not used for training. No public deployment or clinical forecasting claim was made, and the database remains at migration 003 without schema/data changes.

- [Data audit and protocol](docs/FORECASTING_AUDIT.md): collected/missing fields, exact next-24-hour onset target, timezone/overlap/unknown handling, leakage barriers, sample gates and evaluation definitions.
- [Experiment guide](docs/ML_EXPERIMENTS.md): private local input contract, read-only audit, preparation, optional offline fitting, dataset requirements and validation work still needed.
- `backend/research/`: versioned snapshot/coverage contract, point-in-time features, purged chronological splits, training-only preprocessing, historical-frequency baseline, logistic regression, optional XGBoost adapter, metrics and local CLI.
- `GET /api/v1/forecast`: explicit insufficient-data/model-unavailable contract with null probability and no model activation path. It never changes Attack Mode, contact actions, or emergency access.
- **Overview → AI Insights — In Development**: quiet research explanation with no mock risk percentages, styled with existing theme tokens.

Read-only audit from `backend`:

```powershell
./.venv/Scripts/python -m research.cli --audit-db --account-id YOUR_ACCOUNT_ID --output-dir ../.research/local-audit
```

Only aggregate status/reporting is emitted; no feature rows or probabilities are printed. The current outcome is `insufficient_data`, `trained: false`, `model_served: false`. The optional ML dependencies are in `backend/requirements-ml.txt`; the tested environment is locked in `backend/requirements-ml.lock.txt`. XGBoost is absent and its adapter reports dependency unavailability. Synthetic model fits occur only inside automated tests and are not presented as research performance.

All research inputs and sensitive derived outputs belong in ignored local `research-data/` or `.research/`, never a public site or repository. The application still lacks verified observation coverage and immutable historical snapshots, so a final diary export alone cannot support leakage-safe retrospective training. The guide describes prospective collection and review requirements rather than inventing clinical data or negative labels.

Sprint 4 verification: **46 backend tests, 18 frontend tests and 4 browser tests passed**, as did the production build and dependency checks. The live versioned forecasting response reports insufficient data with null probability. Existing records and migration 003 are unchanged. Refresh http://127.0.0.1:5173/ and open Overview to inspect the research-status card. No application-data model training or public deployment occurred.

## Sprint 5: adaptive support assistance

See [the support implementation and verification guide](docs/ADAPTIVE_SUPPORT.md).

- **Caregiver profile → Your support choices**: saved preferred contact/method, ordered support actions, accessibility settings, optional feedback use, fixed/adaptive ordering, and explicit reset.
- **Attack Mode**: preference-first highlighted action, explainable feedback ordering for unpinned actions, stable alternatives and independent sticky emergency access. No automatic call/SMS dispatch.
- **Saved support card**: explicit review/redaction before copy or native sharing. No automatic transmission or delivery claim.
- **Support feedback**: optional after an ended session, skippable, reviewable and deletable. No feedback request during an active session or unknown session status.
- **Offline evaluation**: task completion, interactions, preference alignment and recommendation-change summaries, separating simulated fixtures from real-study outcomes. No real-user performance claim.

Migration **004** adds structured support choices and session/action feedback tables while preserving all existing records. From `backend`, run `./.venv/Scripts/python -m alembic upgrade head`. Existing schema-3 exports now include the two new collections additively. Forecasting remains unavailable and is not used for support ordering. The application is still a single-user local prototype.

Final Sprint 5 verification: **56 backend tests, 29 frontend tests and all 6 browser tests passed**, along with the production build and Python dependency checks. Coverage includes existing forecasting research, diary/timezone regressions, preference loading/persistence/reset, feedback ordering/opt-in/CRUD, no active-session prompts, failed-session-status handling, sharing consent, 320px large-text layout, emergency visibility, keyboard focus and reduced motion. The native share/clipboard handlers were mocked; call/SMS links were inspected without activation. All live support/status/export APIs returned valid responses with no-store caching. The local SQLite database is at migration 004. Existing upstream TestClient deprecation warning remains.


## Source repository hygiene

Only source, tests, migrations, documentation, lockfiles and configuration templates belong in Git. Local environments, credentials, databases/journals, uploads, private exports, datasets, model artifacts, caches and editor files are ignored. `.env.example` files are safe placeholders; replace values only in ignored local `.env` files. Docker requires an explicitly configured local `POSTGRES_PASSWORD`. Do not force-add ignored files or publish local health records.

## Sprint 6: accounts and health data privacy

Registration/login/logout, Argon2id hashing, rotating HttpOnly cookie sessions, session-bound CSRF tokens and origin checks, authentication rate limits, and per-account CRUD/insights/export are implemented. **Account** contains display-name settings, sign-out, explicit/revocable future caregiver consent, and password-confirmed account deletion. **Settings** exports the current account's records, identity and consent history; no password hashes or sessions are exported. There are no public caregiver links or automatic sharing actions.

Migration **005** preserves old records with **unassigned ownership**. New accounts cannot view or claim them; account deletion leaves them intact. Back up privately before migrating and never commit a database or export. Warm Day, Gentle Dark and Attack Mode remain available. Emergency calling is user-initiated and available even at sign-in.

Preview: **http://127.0.0.1:5173**. To test isolation, register synthetic A in a normal browser and B in a separate browser profile/incognito window; ordinary tabs share cookies. Add records to A, verify B stays empty, export each account, then delete B with its password and `DELETE`. See [full architecture, migration safety, configuration and test instructions](docs/authentication-privacy.md).

No public deployment or production-grade security claim. PostgreSQL, real-device telephony, screen readers and independent security review remain unverified. See the privacy document for the full list of limitations. No commit or push is performed as part of Sprint 6.

Sprint 6 verification: **66 backend tests, 32 frontend unit tests and 7 browser tests passed**; production build and Python dependency check passed. SQLite migration 005 preserved all eight legacy tables against a private pre-migration backup. The seven browser tests include two real synthetic accounts with cleanup; no phone/SMS actions were activated. One existing upstream TestClient deprecation warning remains.

## Sprint 8: personalized descriptive pattern insights

Open **Insights** for account-specific recorded onset charts, data-sufficiency indicators, missing-data warnings, wellness summaries, explicit comparison denominators, and separate symptom/attack timestamp tables. Warm Day/Gentle Dark themes and accessible Attack Mode are preserved. No forecasting, diagnosis, causal claims or medication recommendations are added.

Migration **007** adds an optional whole-day episode observation and its server confirmation timestamp to wellness records. Old rows remain unknown; missing diary/check-in dates never become episode-free days. Only completed, explicitly confirmed episode-free observations can enter supported comparisons. Daily wellness recording time is never presented as exposure onset time. Back up privately, then run `./.venv/Scripts/python -m alembic upgrade head` from `backend`.

See [pattern-insights methods, exclusions and manual verification](docs/PATTERN_INSIGHTS.md). The authenticated endpoint is `/api/pattern-insights`; it requires the existing session-bound header on reads. Charts have accessible tables/text, comparisons require at least three values per group as an engineering display safeguard, and sparse groups show **Not enough information yet**. All results remain descriptive and limited by retrospective reporting and missing data.

Sprint 8 verification: **97 backend tests and 49 frontend tests passed; 12 Playwright tests passed in the preceding browser verification**; production build passed. Tests use synthetic fixtures, including a real local API check with two temporary accounts. SQLite migration 007 preserved existing values and ownership against a private backup. One upstream TestClient deprecation warning remains. PostgreSQL, screen-reader/device comfort, large-history performance and real-world data quality remain unverified; no clinical validation is claimed. Preview at **http://127.0.0.1:5173** after signing in and choosing Insights.


## Personalized AI data foundation

Overview > **AI Insights - In Development** > **Your data readiness** > **Review data readiness** shows account-only observation coverage, missingness and established prospective-label counts. The read-only `/api/v1/data-readiness` service prepares current features with strict pre-cutoff availability and an elapsed-24-hour horizon. Null severity stays unknown; zero stays a valid rating; missing dates never become migraine-free days.

No model is trained or served. Current editable records cannot reconstruct immutable historical features or verified prospective labels, so training/evaluation remain blocked. No migration or user-record update is needed; preparation captures are temporary and are not saved as historical evidence. The local audit CLI now requires an explicit `--account-id` and cannot pool accounts. See [schema, leakage rules, readiness criteria and future evaluation plan](docs/PERSONALIZED_AI_FOUNDATION.md).

## Sprint 9: daily status and prospective collection

Open **Daily status** or Overview > **Check in today**. Save migraine occurred, explicitly no migraine, or unknown/not sure. Sleep, stress, hydration, routine changes and early symptoms are optional. Missing entries never become migraine-free dates. Daily reports remain separate from diary episodes and older wellness records; discrepancies are shown for review. Expand timing to backdate a report; retrospective versions are labeled.

Migration **008** adds account-owned daily reports and durable revision snapshots without changing existing records. From `backend`, run `./.venv/Scripts/python -m alembic upgrade head` after a private backup. Server creation/correction times remain distinct from user-reported event/observation instants and IANA timezone. Edits require the current revision. Deletion creates a tombstone and retains private history until account deletion; Settings export schema 5 includes that history. Deleted dates are reserved and cannot currently be restored. No migration was applied to the existing workspace health database during this sprint.

Today's negative reports stay provisional even after midnight: explicitly edit/save after the day ends to confirm the completed day. AI Insights > **Daily collection quality** shows observed/unknown dates, completed nonconflicting no-episode days, same-day versus retrospective reports, missing fields, corrections and discrepancies. Same-day collection is not a verified prospective forecast label. The existing readiness panel keeps its separate legacy-source calculations. **Insufficient evidence for forecasting** remains the outcome regardless of counts; no model training or deployment occurs.

See [collection schema, API, timestamp semantics, retention, limitations and leakage-safe evaluation requirements](docs/PROSPECTIVE_COLLECTION.md). The new audit trail covers the new daily reports; legacy wellness/symptom/episode edits have no fabricated historical versions. Multiple differently timed observations per day, PostgreSQL execution, screen-reader/device validation, large-history behavior and production consent/backup-retention controls remain future work. Use only synthetic records in this local prototype.

Sprint 9 verification, repeated during pre-commit review on 2026-10-22: **127 backend tests passed, 0 failed; 56 frontend unit tests passed, 0 failed; all 14 Playwright tests passed, 0 failed; production build passed**. Python dependency checks and `git diff --check` passed. One existing upstream TestClient deprecation warning remains. Browser integration used fresh isolated synthetic SQLite databases; the existing `backend/migramind.db` SHA-256 checksum remained unchanged. Earlier implementation verification failures and their resolutions are recorded in the collection guide. No model training or automatic merge is included.

## Sprint 10: ML research baseline (offline only)

The [revision-aware research guide and dataset specification](docs/ML_RESEARCH_BASELINE.md) describes a research-schema-2 builder, strict historical feature availability, next-24-hour onset labels, verified no-episode interval coverage, chronological purging, historical-frequency/logistic and naive baselines, and reproducible reports. Inputs must be single-account, consented and reviewed, or explicitly synthetic. No application schema, API or frontend prediction changes are included.

Sprint 9 numeric revisions are reconstructable, but daily status is not verified onset and missing logs are never negatives. The account adapter supplies no verified outcomes; real research remains blocked on research consent, complete onset/coverage journals and provenance review. Unknown, incomplete, withdrawn, conflicting and historically unverifiable outcomes are excluded. Sample/class gates are engineering stop rules, not clinical readiness. Synthetic fitting requires explicit opt-in and is software verification only. No real health data was used for fitting and no model is deployed.

Sprint 10 correction policy: complete independent observation coverage is required for both classes, with separate onset evidence for positives and explicit no-episode coverage for negatives. Historical decisions freeze per window; dataset-as-of metadata and fixed candidate-grid splits prevent future-dependent selection. See the research guide for verification results and limitations.


## Sprint 11: research data quality

Overview > AI Insights > **Research data quality** reviews the last 30 completed local days, separating explicit episode/no-episode reports, unknown and missing days, optional omissions, conflicts and history issues. **Daily status > Review yesterday** prepares the existing form; saving remains explicit and creates the existing revision history. Nothing is automatically corrected or treated as a verified forecast outcome.

A separately confirmed **local research-preparation download** includes selected numeric observations and complete eligible correction histories, with scope, timestamps, quality flags and provenance. It excludes deleted chains, identity and free text. This is private health data, not automatically de-identified, clinically validated or ready for model training. The consent is for this download only; no research enrollment or external sharing occurs. No migration or new dependency is required. See [schema, consent, missingness, limitations and verification](docs/RESEARCH_DATA_QUALITY.md).
