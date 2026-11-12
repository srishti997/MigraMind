# Phase 8: session idle timeout audit and design

## Phase 8C: stabilization and PR-readiness verdict (2026-11-11)

**Verdict: READY WITH DOCUMENTED LIMITATIONS — for PR review with enforcement disabled, not activation or deployment.** Verified `security/session-idle-timeout`; local `main` and HEAD are `7ca2cdddf5f2be214cdb8d7b92cd09c6a8b9e3c0`. Reviewed all tracked differences against that main plus every untracked Phase 8 file. Started with the expected 20 Phase 8A/B paths. Runtime implementation, frontend, migration 010 and previous migrations are unchanged in Phase 8C. Only two backend test files and these two reports receive stabilization changes; the combined intended PR changeset now has **21 paths**.

No remaining deterministic application fix was identified in this review. Fixed one obsolete migration-test expectation and added two synthetic startup cases. The prior Edge focus failure is **not resolved or explained** by subsequent passes. Its uncertainty, five unexecuted provisioning cases and human/platform/operational gates remain documented below. Default `SESSION_IDLE_TIMEOUT_ENABLED=false` and production/demo opt-in rejection are preserved. No existing environment was enabled.

### Bounded Edge focus investigation

Kept the original `manual-accessibility-fixture.pw.ts` regression unchanged. Ran these predeclared groups against a new isolated Vite instance, intercepted synthetic APIs, temporary browser profiles, one worker, **retries=0**, original **30s test / 5s expectation** limits:

| Diagnostic group | Runs / result | Wall time |
| --- | --- | --- |
| Original Edge cancellation scenario | **10/10 passed** | 86.87s |
| Original Chrome scenario | **5/5 passed** | 24.80s |
| Controlled Enter interleaving, Edge | **5/5 passed** | 28.30s |
| Controlled Enter interleaving, Chrome | **5/5 passed** | 24.47s |
| File-backed original trace, one per browser | **2/2 passed** | 6.10s Edge / 4.53s Chrome |
| File-backed interleaving trace, one per browser | **2/2 passed** | 5.59s Edge / 4.62s Chrome |

Total: **29 diagnostic scenarios**, 17 original and 12 controlled interleavings; **87 Edit/Cancel cycles** because each scenario exercises three dates. The forced variant waits for the select to receive focus **between Enter keydown and keyup**, testing the suspected keyboard/effect ordering instead of adding a sleep. It exists only in the temporary test copy. It does not replace, skip or weaken the original regression. Final normal browser suites restored the exact uninstrumented repository file and also passed the original scenario once in each browser.

Inspected `DailyCheckin`'s asynchronous load, keyed form replacement, `[editing, formKey]` focus effect, disabled fieldset and cancellation-opener fallback. Value-free traces captured focus, Enter/Tab, click, submit and navigation events without control values, typed text, record contents, credentials or request headers. Persisted traces from four runs each show:

```text
Edit button → status select → Cancel button → original Edit button → next Delete button
```

Each file-backed run had three status-focus events, **zero submit events**, one initial navigation and **zero query/reload navigations** during the interaction; the existing test also asserted zero writes and unchanged fictional reports. No BODY-focus/native-submit/navigation defect was reproduced under these conditions. This does not rule out other asynchronous, native-control or environment interleavings and does not establish why the Phase 8B Edge run navigated or lost its control. **No speculative Daily Status code change or timeout increase was made.** Keep the earlier failure as an open intermittent/manual verification item.

Evidence-tool limitation: the first 25 runs attached trace bodies inline, but the list reporter did not persist those attachments as files. The runs themselves passed. Corrected only temporary instrumentation to write attachments explicitly, then performed the four additional bounded runs above. This is an evidence-collection correction, not a test retry-until-green. All diagnostic instrumentation/variants were removed from the temporary source before final normal suites; no trace helper or output was added to the repository.

### Migration, startup and authentication verification

Added two cases to `backend/tests/test_session_idle_migration.py`: a completely fresh `upgrade head`, and ordered **009 → head**. Each uses its own new temporary SQLite path and then starts the **actual application** in a subprocess with enforcement explicitly false. Tests verify revision 010, nullable activity-column availability, foreign-key integrity, an initially empty user table, health/readiness 200, synthetic registration and authenticated read, disabled activity refusal, current logout and subsequent unauthorized read. No existing database is opened or copied; schema commands are restricted to those new pytest targets. Existing 010 preservation/idempotency and forward-only downgrade-refusal tests remain intact.

Found a deterministic **test** regression in the previously unexecuted non-provisioning part of `test_deployment.py`: upgrading from 008 to current head and requesting downgrade to 008 now stops at migration **010**, but the assertion still required migration 009's error text. The initial targeted run produced **1 failed / 3 passed** (52.25s pytest / 55.53s wall). Updated only the expected refusal/comment to 010's message; retained all row, marker and version preservation assertions. The final full safe backend suite includes and passes that case. Migration code and application behavior were not changed.

Contract review and passing regressions confirm:

- Disabled bootstrap/login responses have **four** top-level keys: `user`, `csrf_token`, `expires_at`, `demo_mode`. Corrected the earlier report's inaccurate five-key count; no API change was required.
- Enabled metadata and frontend calculations agree on aware server time, integer milliseconds, `min(absolute, activity + 30m)` and strict expiry boundaries. Absolute expiry remains immutable. Partial/invalid metadata fails safely; normal disabled responses do not activate the UI.
- Only explicit authenticated CSRF/Origin-protected activity can advance state. The last-observed precondition rejects stale/replayed refreshes; reads, retries and visibility/timers never renew it. Locked rechecks prevent a waiting refresh from recreating a revoked row or advancing an expired session.
- Current logout, password-confirmed global logout, account isolation and preserved records remain covered. Frontend generation checks and the latched privacy lock reject late responses, changed account/binding and unauthorized activity; no draft is persisted or silently saved.
- The real browser fixture accepts **no database path**. It creates its own unique temporary directory, sets the new SQLite URL before importing the app, disables dotenv, constructs the empty synthetic schema, and enables the flag only in that local child process. Nonce-guarded loopback controls supply an accelerated clock. No existing user/profile/backup/secret input is accepted. Real API tests create fictional accounts, exercise actual cookie/CSRF/storage behavior and clean up only their owned fixture directory.

### Final checks and exact outcomes

All execution was on this Windows machine, using `%TEMP%/migramind-idle-stabilization-3mmjjon1`. Source copies exclude private environment/database/data/backup/export files; installed isolated Python 3.13.12 dependencies were reused read-only, Node dependencies copied after package-lock byte comparison. No package install or developer-environment upgrade. Backend subprocesses use `DATABASE_URL=sqlite://` or an explicitly new synthetic file, `PYTHON_DOTENV_DISABLED=1`, private TEMP/TMP and enforcement false except the separate approved real-browser fixture child.

| Final check | Actual outcome |
| --- | --- |
| Full feasible backend/offline research | **302 passed / 5 deselected**, 109.91s pytest / 112.81s wall; no final failures |
| Full frontend unit suite | **109 passed / 17 files**, 72.85s suite / 74.66s wall |
| Normal intercepted Chrome/Edge browser suites | **60 passed**, 68.32s wall; desktop 1280×850, narrow 320×850; original tests, retries=0 |
| Real frontend-to-new-temporary-backend | **4 passed**, 10.7s suite / 11.79s wall; two actual-API scenarios in each installed Chrome/Edge |
| TypeScript build check | **Passed**, 5.55s wall |
| Local production bundle | **Passed**, 6.15s wall / 4.70s Vite |
| Synthetic production bundle | **Passed**, 6.95s wall / 5.75s Vite |
| Final documentation / integrity | **71 local links / 42 source references** verified; 136 tested source/configuration files match; 17 starting source files unchanged; only 21 intended paths; whitespace check passed |

The backend total expands the earlier 289 by two startup cases and 11 safe deployment-module cases. The **five deselections call provisioning** and remain unexecuted locally under the safety boundary:

```text
test_empty_marker_is_not_synthetic_attestation_and_provision_is_non_destructive
test_existing_records_are_never_marked_or_erased_by_provisioning
test_readiness_and_liveness_actual_app_and_demo_permissions
test_sqlite_backup_restore_on_synthetic_target_only
test_uninitialized_demo_cannot_start_and_check_validates_port
```

No other backend test was deselected. Existing hosted-setting validation, value-free readiness/liveness errors, blocked-body behavior, public tracked deployment-template checks and safe migration ordering were run. No actual hosted service or production database was contacted. The browser coverage is the selected 60 intercepted + four real Phase 8 scenarios, not every browser file/built-demo harness. The 29 focus diagnostics are separate repeat executions and are not added to the normal browser total.

The two production modes use the package's existing build steps directly: one locked `tsc -b` check followed by local and synthetic `vite build`, avoiding npm configuration reads/install. Frontend code did not change between those modes. Temporary outDir warnings are expected; no existing directory was emptied. Existing Starlette/httpx deprecation and Git line-ending notices remain. No final test timeout or hidden retry. The sole assertion failure in this Phase 8C task was the obsolete migration-test expectation above, corrected before final suites.

### Reproduction and review evidence

From the new filtered backend source, with the same explicit development/local, default-off, dotenv-disabled and private-temp environment used in earlier phases:

```text
<isolated-python> -B -m pytest -q -ra -k "not empty_marker_is_not_synthetic_attestation_and_provision_is_non_destructive and not existing_records_are_never_marked_or_erased_by_provisioning and not readiness_and_liveness_actual_app_and_demo_permissions and not sqlite_backup_restore_on_synthetic_target_only and not uninitialized_demo_cannot_start_and_check_validates_port" --basetemp <new-root>/backend-final-data -p no:cacheprovider
node node_modules/vitest/vitest.mjs run --maxWorkers=1
node node_modules/typescript/bin/tsc -b
node node_modules/vite/bin/vite.js build --outDir <new-root>/local-dist
node node_modules/vite/bin/vite.js build --outDir <new-root>/synthetic-dist
```

Vite builds respectively set `VITE_DATA_MODE=local` / `synthetic`, empty `VITE_API_URL`. Test/build caps were backend 900s, frontend 360s, TypeScript/build 180s each, migration/startup subprocesses 60s. Browser normal suites reuse the Phase 8B isolated fixture/temporary configuration, random loopback ports, nonce, proxy-free readiness checks, temporary profiles and finally-owned-process cleanup; each subprocess cap is 600s. Focus groups use `playwright.focus.config.mjs`, `--project edge|chrome`, `-g` for the original or controlled title, and `--repeat-each 10|5|1`, with a 360s group cap. Temporary configs are not deployment settings.

Retained evidence includes `focus-results.json`, `focus-traced-results.json`, four file-backed focus traces, `focus-trace-summary.json`, the initial migration failure, `backend-final-result.json`, `frontend-results.json`, `browser-final-results.json` and per-command logs. No diagnostic stdout/body records credentials, tokens or form values. Evidence artifacts remain outside the repository.

Reviewed the **entire 21-path changeset**, including new untracked files omitted by `git diff --stat`: four backend runtime files, migration 010, three backend test files, six frontend runtime/style files, five frontend test/fixture files and the two reports. Inspected intended text for credential-shaped literals/private-key headers and artifact extensions without printing candidate values. No such credential flag or database/WAL/SHM/backup/log/temp/dependency artifact was found in the changeset. Seventeen literal locations are explicitly synthetic fixture credentials/hashes/markers, not real accounts; account domains/phone fixtures are fictional. This is a scoped source review, **not an ignored-file, private-secret-store or full Git-history scan**.

All production locks, package manifests, workflow/deployment templates/settings, previous migrations and migration 010 are unchanged from the approved starting state. Runtime/feature code and existing browser tests are unchanged in Phase 8C. This phase changes only:

- `backend/tests/test_deployment.py` — align the current-head refusal expectation.
- `backend/tests/test_session_idle_migration.py` — add fresh and ordered migration/startup cases.
- `docs/SESSION_IDLE_TIMEOUT_PLAN.md` — final evidence/verdict and four-key correction.
- `docs/RELEASE_READINESS.md` — final summary and blockers.

### Required fixes and activation blockers

The identified deterministic assertion defect is fixed; no additional known code fix is required for **review of the disabled-by-default PR**. Before merge, the existing CI and separately authorized provisioning-specific coverage must pass. Earlier Phase 8B failures remain historical evidence; today's passing tests do not erase them.

**Before activation or real-health/public use:** investigate/accept the unresolved historical Edge focus uncertainty with human keyboard/assistive-technology review; approve warning duration, unsaved-entry policy, focus/zoom/contrast and physical-device/sleep/resume behavior; complete Linux and live PostgreSQL/cross-host clock/parallel-worker checks; review schema 010 adoption, coordinated worker cutover, legacy reauthentication and rollback/session invalidation. Reverting enforcement without invalidating retained sessions can restore absolute-only access. Production/demo opt-in remains rejected, not an implemented hosting path. Existing storage/copy encryption, recovery/password change, abuse, retention/restore and research/clinical gates remain open.

No existing database, account, health record, backup, export, secret or user browser profile was read/copied/migrated/modified. No production/default activation, lock/configuration/OS change, commit, push, PR, merge or deployment. **READY WITH DOCUMENTED LIMITATIONS is a PR-review verdict only.**

## Historical Phase 8B and earlier evidence

## Phase 8B: frontend integration and synthetic verification (2026-11-11)

Verified `security/session-idle-timeout` at `7ca2cdd`, with the **nine expected uncommitted Phase 8A paths**. Preserved all seven backend/migration/test files byte-for-byte and extended, rather than replaced, the two reports. **`SESSION_IDLE_TIMEOUT_ENABLED=false` remains the backend default**; production/demo opt-in rejection is unchanged. No existing environment or user-facing serving configuration was enabled, and migration 010/earlier migrations, locks and deployment settings were not altered.

### Actual contract and smallest frontend integration

[`IdleSession.tsx`](../frontend/src/IdleSession.tsx#L11) activates only on the complete backend-enabled metadata contract: `server_time`, `last_activity_at_ms`, `idle_expires_at`, existing `expires_at` and the memory-held session CSRF binding. Normal disabled responses have no idle metadata, so no warning, activity request or idle timer is introduced there. Shared demo metadata is not accepted for idle testing; validated backend configuration already refuses that combination. No separate frontend environment flag or new API behavior was invented.

The client validates finite times, safe integer activity, `idle_expires_at = min(expires_at, last_activity_at_ms + 30 minutes)` and the unchanged absolute ceiling. Deadlines are anchored to `performance.now()` **before** the request, conservatively subtracting round-trip latency. Acknowledged absolute time can never be moved later by a refresh. Visibility/focus/timer checks can shorten/close on evidence of suspended monotonic time or backward wall-clock change; they never renew the server session. This is conservative handling, not a guarantee against every OS/browser clock anomaly.

Only the native **Stay signed in** button calls:

```text
POST /api/auth/activity
credentials: include; existing X-CSRF-Token header
body: {"expected_last_activity_at_ms": <last server-confirmed value>}
```

The browser supplies its real Origin under the existing backend policy. Pending controls prevent duplicate submission. The warning stays present until a successful response passes metadata, deadline and generation checks; no optimistic extension. Typing, navigation, polling, renders, visibility changes, timers and automatic retries do **not** send activity. This deliberately chooses the smallest explicit-continuation integration; typing alone does not renew the session. There is no keystroke/content tracking or health payload in this request.

403/network/5xx failures keep the last confirmed deadline and show a truthful static failure. A stale 409 offers **Check session status**, an explicit no-touch `GET /api/auth/session`; it never fetches-and-retries activity automatically. A check updates metadata only for the same account **and same CSRF session binding**; changed identity/binding or anonymous state closes the private workspace. A new activity attempt requires another deliberate click using the newly confirmed precondition. The fixed absolute ceiling remains even after a successful activity response and cannot be dismissed as if extended.

[`api.ts`](../frontend/src/api.ts#L5) adds typed HTTP status errors and expiry signaling for the new auth/activity route, retaining existing safe message handling and stale-response generation checks. [`Authentication.tsx`](../frontend/src/Authentication.tsx#L19) latches the enabled-mode privacy lock: expire/revoke/identity-change closes and unmounts private content, clears memory authentication and prepares sign-in CSRF without displaying bootstrap's user. **Retry connection and late success responses cannot unlock it.** Explicit successful sign-in is required. Ordinary disabled-mode absolute expiry and current/global logout behavior remain covered; enabled logout also clears idle state after server-confirmed success. Failed logout is never reported as successful server revocation.

### Unsaved entries, accessibility and tabs

- Warn at approximately **five minutes before the earlier server-confirmed idle/absolute deadline**, without taking focus from diary/check-in input. A named region, polite atomic status, native buttons and pending/failure messages provide keyboard and screen-reader semantics. No repeating second-by-second announcements or animation.
- The warning normally appears as a sticky region. A small empty slot in the existing diary dialog lets it render **inside that dialog's focus trap** when necessary. Controls are explicit `type=button`, so continuation cannot submit the diary. Successful dismissal restores the previously focused connected control, with the existing main landmark as fallback. Scoped CSS wraps buttons at 320px, uses existing theme tokens and 48px targets; reduced-motion checks found no animation.
- Unsaved text remains in the mounted form while warning/confirmation is pending and after a valid extension. At expiry/revocation/privacy lock, the form is unmounted and unsaved UI state discarded. No localStorage/sessionStorage/IndexedDB draft, URL content, clipboard copy, export or automatic save was added. The sign-in explanation says unsaved entries were discarded and warns that a previously pending save may have completed; users must check saved records rather than retry a write blindly. Unmounting is not forensic memory erasure.
- Multiple tabs remain conservative: no activity heartbeat or new deadline broadcast. A stale tab gets the backend's 409 and must explicitly check state before another user-triggered attempt. Expired/locked tabs cannot reopen themselves after another tab's extension. Existing identity-change notifications contain no account, CSRF, credential or health payload.
- Real integration exposed an important notification interaction: `announceSessionChange()` creates a separate BroadcastChannel object, so the announcing page's observer can receive its own message. The new idle lock initially treated that as a remote change after registration. [`sessionEvents.ts`](../frontend/src/sessionEvents.ts#L4) now includes a **memory-only random notification sender marker** and ignores its own messages. This marker is not an authentication/session identifier or security token. Other tabs still receive changes; legacy `changed` messages remain supported. The existing storage fallback remains a random notification marker only. Three focused sender/receiver regressions and real sign-in tests cover the correction.

These are implemented semantics plus automated checks. **No human screen-reader, visual contrast/zoom, physical-device or clinical usability verification is claimed.** Warning timing, interruption tolerance, assistive-technology behavior and sleep/resume on actual devices remain manual gates.

### Final validation and real API evidence

All runs used `%TEMP%/migramind-idle-ui-eqditokj`: a new filtered source tree, matching copied locked Node dependencies and read-only reuse of the earlier isolated Python 3.13.12 ML environment. No install, developer-venv upgrade, existing database/WAL/backup/export/browser-profile/secret access, real account operation or provisioning. Backend tests used `DATABASE_URL=sqlite://`, explicit default-off settings and their own new synthetic fixture files. Existing synthetic migration regressions ran against newly generated databases; migration source did not change.

| Final check | Actual Windows result |
| --- | --- |
| Backend/offline-research suite | **289 passed**, 150.92s pytest / 155.67s wall; provisioning/deployment module excluded, all six synthetic migration cases included |
| Full frontend suite after integration correction | **109 passed / 17 files**, 64.62s suite / 65.39s wall; includes 15 idle and three notification tests |
| Intercepted Chrome/Edge desktop + 320px | **59 passed / 1 failed** of 60, 71.46s wall. **All 44 new idle executions passed**; one existing Edge Daily Status focus scenario failed once. Do not report the original run as 60 green checks. |
| Existing Edge scenario diagnostic reproduction | **1 passed**, 3.8s suite / 4.91s wall, unchanged code and timeouts; intermittent cause not established and initial failure retained |
| Actual frontend → temporary backend | **4 passed**, 9.6s suite / 10.61s wall: two real-API scenarios in each installed Chrome and Edge |
| Local production build | TypeScript + Vite **passed**, 9.99s wall / 2.97s Vite |
| Synthetic production build | TypeScript + Vite **passed**, 10.90s wall / 3.92s Vite; no serving environment enabled |
| Documentation / integrity | **70 local links / 42 source-line references checked**, 133 tested source/configuration files matched, all seven Phase 8A backend files and both prior report bodies preserved; locks/migrations/configuration unchanged and `git diff --check` passed |

The real tests use [`idle-backend.py`](../frontend/test-fixtures/idle-backend.py), a **test-only wrapper around actual application routes**. It accepts no database path: it creates its own new temporary directory and SQLite file, sets local mode and enables the flag **only inside that child process**, disables dotenv, creates the synthetic schema with `Base.metadata.create_all`, and injects a controlled auth clock. Browser registration creates fictional accounts through the real API. There is no migration/provisioning or existing-data copy. Random nonce-protected loopback-only test controls advance time and gracefully stop the server; the nonce is kept in runner memory/environment and not printed or committed. This wrapper is not a production launch or backup tool.

Real evidence covers a check-in draft surviving acknowledged authenticated extension, an independent session's password-confirmed global revocation causing protected UI removal, a diary draft disappearing at idle expiry, a stale/unauthenticated refresh returning 401 and sign-in remaining latched. API requests use actual Vite proxy, cookie, CSRF/Origin validation and SQLite session storage. Backend time and browser clocks are accelerated; this is not a 30-minute wall-clock soak or another-machine test. The wrapper does not validate production launcher/readiness, real TLS/PostgreSQL or migration rollout; those remain separate gates.

Intercepted [`idle-session.pw.ts`](../frontend/e2e/idle-session.pw.ts) covers enabled/disabled modes, actual diary-dialog keyboard continuation/focus/draft preservation, check-in expiry/disposal, 403/409/401/500/network failures, two tabs, warning sign-out, fixed absolute ceiling, 320px reflow and reduced motion. All API traffic is intercepted before navigation; foreign origins/native phone/SMS handlers are blocked. Existing manual-fixture and global-revocation browser files supply the 16 regression executions. [`idle-session-real.pw.ts`](../frontend/e2e/idle-session-real.pw.ts) requires explicit fixture environment and validates the nonce-protected fixture identity before navigation; it skips by default without that setup. No personal browser profile or arbitrary existing localhost backend was attached.

### Failure history and bounded reruns

1. Initial frontend suite **103 passed** and both builds passed. Added conservative suspended-clock and account/session-binding cases; the next full run was **104 passed**, with **32 affected tests passed** after the additional binding cases. These overlap later coverage, not additional distinct final tests.
2. Initial intercepted browser run recorded **3 completed passes and 4 completed 30-second failures**. Tests had advanced virtual time before authentication finished. Stopped only that owned Node runner (exit 4294967295 after 171.35s); remaining checks were not completed. Added explicit authenticated-ready waits. No timeout increase.
3. The corrected intercepted run produced **56 passed / 4 failed** (177.93s wall). Each two-tab fixture advanced Playwright's shared browser-context clock twice, effectively moving 50 minutes. Corrected it to one advance. This was deterministic fixture scheduling, not a passing flaky retry.
4. Initial real API run had **4 failures** (80.89s wall); one bounded Chrome diagnostic also failed (32.45s). Status/path-only logging showed registration succeeded, then the page consumed its own notification and closed; protected requests subsequently got 401. No password/cookie/token/record values were logged. Corrected notification sender filtering, added regressions and reran full frontend/builds and both browser suites under the same limits. **All four real scenarios now pass.**
5. The resulting 60-check intercepted suite retained **one existing Edge Daily Status keyboard/focus failure**: expected status-select focus after Enter was absent and navigation was reported. With no idle metadata, that scenario does not activate the new warning. One bounded diagnostic reproduction passed with no code/timeout change. Cause is **unresolved**; record it as intermittent regression/manual verification work, not as fixed or silently green. No Daily Status behavior or existing browser test was changed to hide it.

All Playwright configurations use **retries=0**, one worker and unchanged 30s test/5s expectation limits. Browser subprocess caps were 600s; readiness was a bounded proxy-free 30s HTTP check. The diagnostic and initial-failure artifacts remain separately named; later runs did not overwrite them. No unit/build/backend assertion failure or package/network retry occurred. Existing Starlette/httpx deprecation, expected temporary external-outDir warnings and Git line-ending notices remain.

### Exact safe reproduction boundary

From a new filtered copied backend, before app import: `APP_ENV=development`, `DATA_MODE=local`, `DATABASE_URL=sqlite://`, `SESSION_HOURS=12`, **`SESSION_IDLE_TIMEOUT_ENABLED=false`**, `PYTHON_DOTENV_DISABLED=1`, `PYTHONDONTWRITEBYTECODE=1`, copied backend `PYTHONPATH` and private TEMP/TMP. No inherited application credentials/configuration. Use the isolated interpreter/dependencies without upgrading them:

```text
<isolated-python> -B -m pytest -q -ra --ignore=tests/test_deployment.py --basetemp <new-root>/backend-data -p no:cacheprovider
node node_modules/vitest/vitest.mjs run --maxWorkers=1
node <npm-cli.js> run build -- --outDir <new-root>/local-dist
node <npm-cli.js> run build -- --outDir <new-root>/synthetic-dist
```

Frontend builds respectively use `VITE_DATA_MODE=local` / `synthetic`, empty `VITE_API_URL`; caps 360s unit, 180s per build, 900s backend. Early/complete unit and build logs/results are separately retained. No new dependency installation/advisory scan is claimed.

For browsers, the isolated runner allocates two new loopback ports, generates an ephemeral control nonce and supplies only child-process `MIGRAMIND_IDLE_TEST_PORT`, `MIGRAMIND_IDLE_TEST_FRONTEND`, `MIGRAMIND_IDLE_TEST_TOKEN`, `MIGRAMIND_IDLE_TEST_BACKEND`, `MIGRAMIND_E2E_BASE_URL` and `MIGRAMIND_API_PROXY`. The fixture is launched from copied frontend with `<isolated-python> -B test-fixtures/idle-backend.py`; it always chooses its own fresh database. Vite binds `127.0.0.1` with `--strictPort`, proxies only to that temporary backend, and must actually serve `/@vite/client`. No setting is written to the repository or an existing environment.

Temporary configs extend the existing Playwright config for Chrome/Edge desktop 1280×850 and narrow 320×850. Desktop matches `idle-session.pw.ts`, `manual-accessibility-fixture.pw.ts` and `session-revocation.pw.ts`; narrow matches only the new idle file. Real projects match only `idle-session-real.pw.ts` at desktop size. Commands:

```text
node node_modules/@playwright/test/cli.js test --config playwright.idle-mock-complete.config.mjs
node node_modules/@playwright/test/cli.js test --config playwright.idle-real-complete.config.mjs
node node_modules/@playwright/test/cli.js test --config playwright.idle-edge-recheck.config.mjs --project edge-desktop -g "Daily Status cancellation restores"
```

Those configuration files live only in the temporary source tree, not production configuration. The runner shuts down its fixture with the nonce, waits/terminates owned processes in finally, and uses temporary browser profiles/output. No existing service is stopped. Successful fixture shutdown disposes the synthetic engine and cleans its owned temporary data directory. Test artifacts outside that directory are retained as evidence.

### Changed paths and remaining rollout gates

Phase 8B changes **13 paths**:

- Application/UI: `frontend/src/IdleSession.tsx`, `frontend/src/Authentication.tsx`, `frontend/src/api.ts`, `frontend/src/main.tsx`, `frontend/src/sessionEvents.ts`, `frontend/src/style.css`.
- Tests/fixture: `frontend/src/IdleSession.test.tsx`, `frontend/src/sessionEvents.test.ts`, `frontend/e2e/idle-session.pw.ts`, `frontend/e2e/idle-session-real.pw.ts`, `frontend/test-fixtures/idle-backend.py`.
- Reports: `docs/SESSION_IDLE_TIMEOUT_PLAN.md`, `docs/RELEASE_READINESS.md`.

The seven existing Phase 8A backend paths (`backend/app/auth.py`, `backend/app/main.py`, `backend/app/security.py`, `backend/app/deployment.py`, `backend/alembic/versions/010_session_activity.py`, `backend/tests/test_session_idle.py`, `backend/tests/test_session_idle_migration.py`) remain unchanged relative to this task's starting tree. Thus the combined worktree has **20 intended paths**, not 20 new Phase 8B changes.

**No additional migration, package or production configuration is needed by the frontend integration.** Phase 8A schema 010 remains a prerequisite for future adoption, and an existing-data migration/activation is still separately gated. Do not turn on enforcement in real/demo environments on the strength of these tests. Resolve/review the intermittent Edge legacy-focus scenario and perform human keyboard/AT/timing/zoom/contrast, real-device/sleep/resume and policy/unsaved-data review. Linux, Firefox/Safari/iOS/Android, live PostgreSQL, cross-host clocks and actual parallel-worker/rollout verification remain unperformed.

The explicit-only continuation policy means people reading or typing must act on the warning; accessibility approval of the proposed duration is still required. Conservative latency/clock handling can close a workspace before a still-valid backend session would expire. A local lock cannot revoke other devices or retract in-flight/exported data; lost save responses remain uncertain. Storage/copy protection, recovery/change, abuse/hosting, retention/restore and research/clinical gates remain unchanged. **No release-readiness or clinical claim is made.** No existing records, credentials, backups, secrets, migrations, locks, deployment settings or OS configuration changed; no commit, push, PR, merge or deployment.

## Historical Phase 8A and earlier evidence

## Phase 8A: approved backend foundation, disabled by default (2026-11-11)

**Current status:** implemented only the separately approved backend foundation. Verified `security/session-idle-timeout` at `7ca2cdd`; the only starting changes were the existing modified release report and this untracked Phase 8 plan. Both document bodies are preserved below as a historical design snapshot. No frontend code, warning, timer, automatic logout, activity caller or serving configuration was changed. **No existing database was accessed or migrated.**

### Feature flag, legacy policy and persistent schema

- [`SecuritySettings`](../backend/app/security.py#L20) adds `session_idle_timeout_enabled=False`. The environment name is **`SESSION_IDLE_TIMEOUT_ENABLED`**, accepts exactly lowercase `true` / `false`, and defaults to **`false`**. Invalid values fail configuration validation. Validated settings reject `true` in production or synthetic-demo mode: this foundation is restricted to explicit local-development testing until frontend/rollout gates are approved. No environment/example/CI/service/demo/production configuration enables it. Duration is a fixed **30 minutes** (`IDLE_TIMEOUT_MS`), not a new adjustable policy setting.
- [`LoginSession.last_activity_at_ms`](../backend/app/main.py#L48) is the single new persistent field: nullable BIGINT UTC epoch milliseconds. [`010_session_activity.py`](../backend/alembic/versions/010_session_activity.py) adds that column to `login_sessions`, with **no default, backfill, account/session deletion, health update or table rebuild in the upgrade**. Old rows remain NULL. Readiness expects revision **010**, so missing schema does not masquerade as ready.
- With the flag **off**, NULL, old or otherwise invalid activity state is ignored: existing absolute lifetime, cookies, bootstrap response shape, login rotation, logout and global revocation retain their behavior. Installing the additive migration alone does not log users out. New authenticated sessions initialize the timestamp at login/registration even when enforcement is off; passive reads never maintain it.
- With explicit local opt-in **on**, authenticated NULL/invalid/future activity is unauthorized; no bootstrap/touch backfill or grace period is invented. Legacy rows require a new sign-in and receive no perpetual validity. Anonymous sessions retain one-hour absolute expiry and NULL activity. This makes activation an explicit reauthentication/cutover decision, not an unannounced default mass logout.
- **Schema compatibility is separate from the flag:** new ORM queries require column 010 even when enforcement is disabled. Future adoption requires a separately approved migration against an owner-verified target; nothing auto-migrates. Running new code against 009 is not supported, and no claim is made that the off switch provides an old-schema adapter.
- The migration follows the repository's **forward-only downgrade convention**: downgrade raises before changing schema/data. Synthetic tests prove refusal leaves revision, records and column unchanged, then a repeated upgrade is a no-op. No destructive downgrade is implemented or required for the upgrade. A reviewed code rollback may retain the additive column, but must also handle schema-readiness compatibility; an older release expecting 009 cannot simply be declared ready against 010.

### Enforced behavior when explicitly enabled in isolated tests

[`auth.py`](../backend/app/auth.py#L89) checks both limits for every authenticated lookup: **T < absolute expiry AND L <= T_ms < L + 1,800,000ms**. L must be a nonnegative integer. Equality at either deadline is expired. Millisecond conversion is integer arithmetic, floors sub-millisecond precision, accepts aware timezones and rejects naive clock values. Reported idle deadlines use that same stored millisecond precision and are capped by the original absolute expiry. The cookie, CSRF and absolute expiry are not refreshed by activity.

`Authentication(..., clock=...)` is an optional test seam; default clock remains the existing aware **host UTC `now()`**, rather than the design's preferred future shared-database clock. This preserves the existing absolute clock and supports deterministic local tests. Separate instances on this machine share the OS clock; the foundation **does not establish cross-host clock consistency**. Future distributed hosting must approve/test its clock authority. A stored activity time ahead of the sampled clock fails closed; wall-clock jumps remain an operational limitation, not a solved monotonic-time guarantee.

[`POST /api/auth/activity`](../backend/app/auth.py#L156) is the only refresh operation. It requires authenticated session, current CSRF and exact Origin. The body is extra-forbidden and contains one strict nonnegative integer precondition:

```json
{"expected_last_activity_at_ms": 1767268800000}
```

That number is an **illustrative synthetic server-observed state value**, not a client-proposed clock or desired deadline. Callers must use the last acknowledged value from enabled login/bootstrap/activity metadata. The server uses its own clock for the replacement. This is a small refinement of the original empty-body proposal: an accepted refresh advances L; replaying its old precondition returns **409** without touching L, so retrying a lost successful request does not keep extending the idle deadline. A same-millisecond/non-advancing request also returns 409. A caller must wait for a **new intentional interaction**, check current state and make a fresh explicit request; no automatic fetch-and-retry loop is authorized or implemented.

Response after commit: `server_time`, unchanged `expires_at`, `last_activity_at_ms`, and capped `idle_expires_at`. Enabled authenticated bootstrap/login additionally supply that metadata; disabled responses keep their original four keys. No new session identifier, password or health value is accepted/returned by activity. Off-state authenticated activity returns **409** without writes; expired/anonymous/revoked authentication is **401**, CSRF/Origin refusal **403**, invalid/extra input **422**, stale/non-advancing precondition **409**. Existing private DB/error handling remains; no login/password rate-limit algorithm or budget was changed for activity.

**Transaction guarantees:** after preliminary read-only authentication, the activity route records the current user ID and ends that read transaction. SQLite acquires `BEGIN IMMEDIATE`; PostgreSQL uses a row-locking query (`FOR UPDATE`). Unsupported dialects fail with 503. It re-reads the cookie-digest session, verifies the same current user, CSRF and both deadlines **after waiting for the lock**, then samples/revalidates the clock again, checks the precondition, updates L and commits before acknowledging. It never inserts/upserts a missing session. Failed commit rolls back. SQLite refreshes serialize across engines; only one concurrent request can consume a given expected state. Existing logout/global deletion serialize with the database write, so a refresh waiting behind committed revocation cannot recreate a row. A transaction already authorized before expiry may finish afterward; this is not retrospective cancellation of in-flight work.

Ordinary reads, bootstrap, account updates, polling and timers **do not refresh** meaningful activity. There is no frontend activity integration or automatic retry. The authenticated endpoint is an intent protocol, **not proof of human presence**: a valid session/CSRF holder or trusted-origin compromise can forge new explicit activity. Shared demo allowlists remain unchanged and still block this endpoint. No production/demo activation is permitted by validated configuration.

### Actual validation and failures

All execution was on **this Windows machine**, from a new filtered temporary source tree: `%TEMP%/migramind-idle-foundation-9umrj19t`. Reused the earlier isolated Python 3.13.12 ML environment read-only and copied matching locked Node dependencies; no install or environment upgrade. Child configuration used `DATABASE_URL=sqlite://`, `APP_ENV=development`, `DATA_MODE=local`, `SESSION_IDLE_TIMEOUT_ENABLED=false`, `SESSION_HOURS=12`, `PYTHON_DOTENV_DISABLED=1`, `PYTHONDONTWRITEBYTECODE=1`, copied-source `PYTHONPATH` and private TEMP/TMP, with unrelated environment/configuration excluded. Tests explicitly construct opted-in instances with an injected clock over new synthetic SQLite files. Existing account/health data, WAL/SHM, backup/export, browser-profile and secret files were never copied/read/modified.

| Check | Actual result |
| --- | --- |
| First focused run | **34 passed / 2 failed**, 49.80s pytest / 54.23s wall; test-helper defects described below |
| Corrected focused run plus two added cases | **38 passed**, 65.39s pytest / 69.50s wall |
| First broad backend run | **288 passed**, 120.62s pytest / 123.52s wall, before the final fractional-deadline refinement |
| Final backend/offline-research suite | **289 passed**, 141.26s pytest / 144.43s wall. Includes **39 new cases**, including the new migration case, and the existing five migration cases. Only `test_deployment.py` excluded to avoid provisioning. |
| Relevant frontend regressions | **21 passed / 3 files**, 42.95s suite / 47.99s wall; no frontend source changes |
| Local production build | TypeScript + Vite **passed**, 38.51s wall / 14.02s Vite |
| Synthetic production build | TypeScript + Vite **passed**, 35.56s wall / 13.22s Vite; no demo database provisioned |
| Documentation / integrity | **62 local links / 38 source-line references checked**; 127 tested source/configuration files matched; both original uncommitted document bodies preserved; exactly nine intended paths; locks, frontend, prior migrations and deployment configuration files unchanged; `git diff --check` passed |

[`test_session_idle.py`](../backend/tests/test_session_idle.py) covers off-by-default validation/production-demo refusal, active/idle/exact boundaries, fixed absolute ceiling, passive traffic, NULL/invalid/future state, old/new sessions with flag off, anonymous lifetime/rotation, CSRF/Origin and owner/time overrides, account/independent-session isolation, fresh instances/engines, global/current revocation and preserved synthetic records, stale retry preconditions, millisecond/offset/backward-clock behavior, simultaneous refreshes, refresh blocked past expiry or committed revocation, and failed-update rollback. [`test_session_idle_migration.py`](../backend/tests/test_session_idle_migration.py) upgrades a **new** database to 009, inserts fictional records, upgrades to 010, compares every pre-existing table/column value, checks NULL/no backfill, foreign keys/readiness, downgrade refusal and repeated upgrade. It never uses an existing MigraMind database or runs provisioning.

**Failure/retry disclosure:** the initial focused run assumed exactly one session where two were intentionally created (`MultipleResultsFound`), and its migration comparison did not quote a reserved column named `values` (`sqlite3.OperationalError`). Corrected the assertions/identifier quoting only, added disabled-nonlegacy and clock-conversion cases, and reran once under the same 240s cap: 38 passed. After the first broad pass, source review found activity response metadata used raw microsecond time while enforcement used stored milliseconds, potentially advertising up to **0.999ms** extra. Corrected metadata to use the persisted precision, added a fractional-clock regression and reran the whole broad suite once: 289 passed. No test timeout, dependency change, hidden retry-until-green or flaky test rerun. Existing Starlette/httpx deprecation and temporary external-Vite-outDir warnings remain.

Exact command shapes, only from the copied backend and explicit isolated interpreter/environment above:

```text
<isolated-python> -B -m pytest -q -ra tests/test_session_idle.py tests/test_session_idle_migration.py --basetemp <new-root>/focused-data -p no:cacheprovider
<isolated-python> -B -m pytest -q -ra --ignore=tests/test_deployment.py --basetemp <new-root>/backend-final-data -p no:cacheprovider
```

Synthetic migration subprocesses run bounded `alembic upgrade 009`, `upgrade head`, expected-refused `downgrade 009` and repeated `upgrade head` with a URL created **only inside pytest's new tmp_path**. These commands are not adoption instructions for an existing database. Initial/final suite logs, command/results JSON and before-change document copies are retained under the temporary evidence root. Caps: focused 240s, broad 900s, each migration subprocess 60s. From copied frontend, with `CI=true`, empty `VITE_API_URL`, and respectively local/synthetic build mode:

```text
node node_modules/vitest/vitest.mjs run src/Authentication.test.tsx src/AccountSettings.test.tsx src/api.test.ts --maxWorkers=1
node <npm-cli.js> run build -- --outDir <new-root>/local-dist
node <npm-cli.js> run build -- --outDir <new-root>/synthetic-dist
```

Frontend/build caps were 180s each. No browser/physical-device/human accessibility, Linux, real parallel-process or live PostgreSQL/migration/lock test was run. Threaded SQLite tests do use separate app instances/connections and real database contention; do not relabel them as distributed-worker or PostgreSQL assurance. Hosted/provisioning harnesses were excluded. No new network advisory/dependency-install check or clinical claim.

### Rollout gates, remaining limitations and next step

- **Not enabled for users.** S7-01/SP4-03 remains open operationally. Before activation, approve/implement the Phase 8B frontend warning, intentional activity coalescing/precondition handling, latched private-content removal, 401 handling for `auth/activity`, accessible focus/live announcements, unsaved-entry disposal and multi-tab behavior. The current frontend does not call activity or honor idle deadlines. No idle UI was added here.
- Review a coordinated schema/cutover and legacy reauthentication policy before touching any existing data. No mixed old/new workers; old code ignores idle state. Explicit off-to-on activation can invalidate old/NULL or inactive sessions by design. Do not silently backfill or claim zero logout impact on activation.
- Disabling after activation or increasing the idle interval can make retained idle-expired rows usable under the older absolute-only policy. Any rollback/policy change needs stopped ingress and separately approved session invalidation, plus compatible readiness/code review. Do not restore revoked sessions from backups or blindly downgrade/drop the column. This task tested **safe downgrade refusal**, not an operational rollback of a real installation.
- Host UTC is injectable but not a distributed trusted clock. Small backward jumps detected as future L fail closed; other wall-clock rollback scenarios can change apparent lifetime. Approve an authoritative clock/clock-correction policy before hosting. Cross-host/PostgreSQL behavior, contention/load/body limits and operator recovery still require isolated evidence; activity adds a short SQLite writer transaction and no new shared rate-limiter was introduced.
- Revocation/expiry do not retract rendered/exported data or actions already authorized. New login with a known password still creates a session. Password change/recovery, inventory, offline privacy lock, storage/copy protection, retention/restore, hosted abuse controls, manual accessibility and research gates remain separate. Public/real-health release is still **NO-GO**.

Exactly nine intended changed files: four backend application files (`auth.py`, `main.py`, `security.py`, schema-readiness `deployment.py`), the new 010 migration, two new backend test modules and these two Phase 8 documents. No previous migration, application lock, frontend, production/demo configuration file or existing data changed. No commit, push, PR, merge, deployment or OS change. Recommended next step is separately approved **Phase 8B frontend integration and synthetic verification**, keeping the flag off and existing databases untouched until all activation gates are reviewed.

## Historical Phase 8 audit and design snapshot

Assessment: **2026-11-11, Asia/Calcutta**. Branch `security/session-idle-timeout` started clean at **`7ca2cdddf5f2be214cdb8d7b92cd09c6a8b9e3c0`**, the merge commit for PR #22. Local `main` and HEAD both pointed to that commit; ancestry checks succeeded for each. This verifies local Git history, not a new GitHub API query or fetch. PR #22's password-confirmed global revocation and tests are present.

**Audit and design only.** No timeout, endpoint, schema/migration, setting, authentication behavior, dependency or deployment change is implemented. Only this document and the release-readiness report change. The [Phase 7 plan](SESSION_SECURITY_PLAN.md), [security/privacy audit](SECURITY_PRIVACY_AUDIT.md) and prior [release evidence](RELEASE_READINESS.md) remain preserved.

## Decision summary

Retain the existing immutable absolute expiry. Propose an additional **30-minute idle limit per authenticated session**, with an accessible **five-minute warning** and explicit continuation before expiry. These durations are **proposals requiring approval and usability verification**, not existing policy, clinical guidance or a compliance claim.

The smallest recommended persistent state is **one nullable `last_activity_at_ms` BIGINT column** on `login_sessions`, representing server-authoritative UTC epoch milliseconds. A migration is necessary: no equivalent state exists today. New authenticated sessions initialize it; existing authenticated rows with NULL require fresh sign-in, not a fabricated activity backfill. Anonymous bootstrap keeps its existing one-hour absolute policy. No migration was created or executed.

Propose one narrowly scoped, CSRF-protected **`POST /api/auth/activity`** for deliberate foreground interaction and the explicit “Stay signed in” action. Ordinary API calls do not touch activity. This supports typing an unsaved diary entry without treating resource refresh or background polling as a person. A valid cookie alone is insufficient; this uses the existing authenticated session, exact Origin and session-bound CSRF. The server cannot prove a human is present: a stolen session plus CSRF, trusted-origin compromise or malicious automation can imitate activity. This control addresses unattended-session exposure, not those threats.

## Confirmed current behavior

| Area | Actual source and behavior |
| --- | --- |
| Session persistence | [`main.py:41`](../backend/app/main.py#L41): `LoginSession` has `id`, nullable `user_id`, `token_digest`, `csrf_token`, `expires_at`. No issued-at, last-seen, last-activity, idle deadline or persistent clock state. The server stores SHA-256 of an opaque random session identifier, not its raw cookie. Local SQLite and the configured database persist session rows; no database was opened for source review. |
| Absolute lifetime | [`security.py:64`](../backend/app/security.py#L64): `SESSION_HOURS` defaults to **12**, accepts integers **1–168**. [`auth.py:103`](../backend/app/auth.py#L103) sets authenticated expiry once at issue and anonymous expiry at one hour. Cookie Max-Age follows that lifetime. |
| Lookup / renewal | [`auth.py:77`](../backend/app/auth.py#L77): query by cookie digest, parse aware `expires_at`, accept only if strictly later than current UTC. Invalid/naive deadlines fail closed. Reads and writes do not renew it. [`bootstrap:114`](../backend/app/auth.py#L114) returns a valid session unchanged; otherwise removes absolutely expired rows and issues an anonymous session. No refresh-token, sliding-refresh or activity endpoint exists. |
| Authentication / rotation | [`auth.py:122`](../backend/app/auth.py#L122): registration/login issue new cookie and CSRF, delete that browser's previous session, and start a new absolute lifetime. They do not refresh an existing authenticated row or revoke independently issued sessions. Password verification uses existing Argon2id; recovery/change remains absent. |
| Cookie / CSRF | [`auth.py:71`](../backend/app/auth.py#L71): HttpOnly, host-only, Path=/, SameSite=Lax; production adds Secure and `__Host-`. [`require_user:89`](../backend/app/auth.py#L89) derives the user from session; GET/HEAD require session-bound CSRF, mutations require CSRF and exact Origin. CSRF is memory-held on the frontend. No client clock or activity assertion currently influences authorization. |
| Revocation | [`logout:144`](../backend/app/auth.py#L144) deletes current row and expires cookie. [`logout-all:148`](../backend/app/auth.py#L148) reauthenticates with current password and transactionally deletes all rows for current user, then expires cookie. Subsequent lookups fail across app instances sharing that database. No worker-local revocation list. Health/account rows remain intact. |
| Middleware / readiness | [`main.py:178`](../backend/app/main.py#L178) redacts validation/DB errors; exact CORS, TrustedHost and private-response/TLS boundary are registered nearby. [`security.py:91`](../backend/app/security.py#L91) supplies private response headers and HTTPS enforcement. [`deployment.py:39`](../backend/app/deployment.py#L39) blocks synthetic-demo writes except explicit allowed routes. Its readiness check requires schema revision **009**; no middleware implements idle expiry. |
| Frontend expiry | [`Authentication.tsx:12–17`](../frontend/src/Authentication.tsx#L12) bootstraps, hides/unmounts private screens at the supplied absolute deadline, rechecks on persisted pageshow and session-change events, and clears after confirmed logout. Its session-ended handler immediately bootstraps again. No idle warning, unsaved-entry recovery or activity signal exists. |
| API failure handling | [`api.ts:9–16`](../frontend/src/api.ts#L9): credentials/CSRF, no-store/no-referrer, stale-response generation checks; non-auth 401 dispatches session-ended. Auth-path 401 is deliberately excluded today. A future activity endpoint must explicitly handle its own expiry response; simply adding the route will not make its 401 hide content. |
| Resource traffic | [`main.tsx:66–84`](../frontend/src/main.tsx#L66) refreshes collections on mount, explicit refresh/retry and after mutations. No `setInterval` polling was found in reviewed application source; current timers include absolute expiry and object-URL cleanup. Bootstrap, pageshow, refetch and future polling must still be excluded from activity. |

**Confirmed finding:** **S7-01 / SP4-03, Medium, remains open.** An unattended unlocked authenticated browser can remain usable until its absolute deadline. Source plus temporary observations confirm account GET still succeeds at +1h/+6h/+11h with default 12h absolute TTL; bootstrap leaves expiry and cookie unchanged. At +13h account GET is 401. There is no demonstrated absolute-expiry bypass. The prerequisite is access to an already authenticated device/session; idle timeout is not a substitute for disk protection or locking the operating system.

The existing tests in [`test_auth.py`](../backend/tests/test_auth.py#L90), [`test_security.py`](../backend/tests/test_security.py#L147), [`test_logout_all.py`](../backend/tests/test_logout_all.py#L19), [`Authentication.test.tsx`](../frontend/src/Authentication.test.tsx#L73) and [`api.test.ts`](../frontend/src/api.test.ts#L1) cover absolute expiry, malformed expiry, CSRF, rotation, stale responses, logout/global revocation, ownership and private-screen gating. They do **not** establish an idle policy. The earlier security-audit statement that revoke-all was absent is historical; PR #22 implemented it as recorded in Phase 7.

## Proposed policy and meaningful activity

Let **E** be existing absolute expiry, **L** the persisted last accepted meaningful-activity time, **I** the approved idle duration and **T** authoritative server/database UTC at the authorization decision. An authenticated session is usable only when **T < E AND T < L + I**. Equality at either deadline is expired. The effective deadline is **min(E, L + I)**. Bootstrap/touch never changes E, rotates the cookie or creates a new authenticated session.

Use one documented clock authority across instances, preferably the shared database's live UTC clock. Persist UTC epoch milliseconds; do not persist `time.monotonic()` values, trust client timestamps, or compare naive local datetimes. Validate/parse the existing aware absolute string separately and fail closed on malformed values. Define/test conversion precision consistently for SQLite and PostgreSQL; do not assume dialect clock functions or row locks behave identically. Database UTC is still a wall clock, not a guarantee against operator clock changes.

| Request / event | Proposed activity treatment |
| --- | --- |
| Successful login/registration | Initialize L with authoritative time and E with the unchanged configured absolute lifetime; new session only |
| Explicit “Stay signed in” | Send authenticated activity POST; extend idle deadline only after server success and only if both limits are still valid |
| Deliberate diary/form input, control activation, foreground route navigation | UI may send the same activity POST from known interaction handlers, without field values, key contents, route history or health payload. This counts work before Save, including keyboard/assistive-technology activation. |
| User-triggered health save/export, navigation GET | The ordinary API request itself never touches L. The initiating UI handler can send activity POST. Complete that check before sending a sensitive mutation if the confirmed deadline is close; never replay a mutation automatically after reauthentication. |
| Bootstrap, health/readiness, resource GET, retry/refetch, render, focus/visibility/pageshow, timers, passive mouse movement, polling | Never activity. Visibility alone is not a user. Revalidate metadata on return; do not renew. No timer-generated keepalive or retry loop. |
| Failed authentication, invalid/expired cookie, missing/wrong CSRF/Origin, malformed activity input | Never activity; never recreate/upsert a deleted session |
| Logout, logout-all, account deletion | Preserve existing revocation semantics; no activity renewal needed |

Activity POST should accept an empty extra-forbidden input, not a user ID, session ID, client time, desired deadline or diary value. Return only the server time and confirmed idle/absolute deadlines needed by this browser (plus existing demo metadata as appropriate); no raw session identifier. Continue to use existing cookie/Origin/CSRF protection and private error handling. Do not reuse or weaken the CSRF token as a recovery mechanism.

Proposed frontend coalescing: at most one automatic interaction signal per **30 seconds**, only when a new qualifying interaction occurs in a visible tab; no trailing timer/hidden-tab resend. Explicit continuation is immediate, with duplicate pending requests disabled. The confirmed deadline, not the most recent local keystroke, drives warnings/locking. Coalescing may mean up to 30 seconds of local interaction is not yet acknowledged; never display an invented extension. If a request fails, stop claiming renewal and retain the last confirmed deadline. Server resource/rate limits need a separate bounded review; do not consume login/password budgets for each keystroke or introduce a new unbounded map as part of this design.

This is an application intent protocol, not proof of human presence. Assistive technology can produce different event patterns; do not use `event.isTrusted` as the sole usability/security test. Explicit keyboard-accessible continuation must always work before expiry. Reading without interaction can reach the warning; its usability must be tested with people. Thirty minutes/five minutes balance exposure and migraine-related pauses only as an initial proposal. Accessibility/identity owners must approve the policy before participant use; no timing-accessibility conformance is claimed.

## Persistent enforcement and concurrency

1. All protected routes use the common session resolver and both deadlines, including downloads, reads, mutations, bootstrap's authenticated branch and global revocation. Anonymous bootstrap remains separate. Expired/NULL/invalid authenticated state cannot be converted into fresh authenticated state; only a new successful login/registration does that.
2. Activity updates must **serialize the authoritative recheck and touch**, not read-valid in one transaction and blindly update later. Recommended first implementation: row lock on PostgreSQL; an explicit short write transaction (such as `BEGIN IMMEDIATE` before the authoritative lookup) on SQLite, since `SELECT FOR UPDATE` is ineffective there. Cheap invalid-request/CSRF checks can precede acquisition, but re-read and revalidate the session/user, CSRF, Origin and both deadlines inside the transaction. Sample live authoritative T **after acquiring the lock**, not when the request began waiting. Do not attempt to begin a second SQLite transaction inside the existing dependency transaction: the activity resolver needs an explicitly owned short transaction/shared validation helper.
3. If valid, update L monotonically, commit, then acknowledge deadlines. Never hold the lock for password hashing, health writes, network calls or UI waiting. Lock/busy/commit failures produce safe failure and no acknowledged extension. A conditional compare-and-update alternative is acceptable only if it proves equivalent clock/deadline/revocation semantics under contention; no unconditional update, `merge`, insert-on-miss or stale-object save.
4. Logout/global revocation and touch serialize via the database. If deletion wins, the touch finds no row and cannot resurrect it. If touch commits first, the following revocation deletes it. A request waiting past either deadline must fail after its locked recheck. Protected requests already authorized before expiry/revocation can complete; this design does not retrospectively cancel committed work or require broad commit-time checks in every health route.
5. Separate authenticated browser sessions each have their own L; one device does not renew another. Tabs sharing one cookie share the same server session. A tab signal may request a no-touch deadline recheck, but it is never authoritative and must not reset form state, disclose health/identity, or renew anything. Reject responses for a different session generation/account. Cross-tab activity synchronization needs a distinct signal from the current identity-change handler, which unmounts the workspace.
6. Reads can authorize from a fresh row/clock snapshot without taking a write lock or changing L. Cleanup is optional housekeeping, never the enforcement mechanism. Workers and restarted instances must share authoritative persistent state; unavailable storage fails closed. No local timer, cache or process-local last-seen map can override a DB decision.
7. With no grace proposed, a persisted activity time later than authoritative T is invalid and fails closed, rather than silently extending access after a backward clock jump. Forward jumps may expire sessions early. Any allowed clock-skew/grace policy requires explicit approval/tests; long backward jumps that do not produce a future L cannot be fully detected with one timestamp. Trusted clock operations remain a hosting gate, not a solved cryptographic property.

## Schema and rollout design — not executed

- **Proposed additive migration:** nullable `last_activity_at_ms` BIGINT on `login_sessions`; no new health fields, no backfill from record timestamps, cookies, mtime or the moment of deployment. No new index is required for lookup by existing unique digest. New authenticated rows must have valid activity state; anonymous rows may remain NULL.
- Existing authenticated NULL rows are rejected and require sign-in. This deliberately invalidates old sessions without deleting accounts/health records or pretending old users were recently active. Bootstrap must return anonymous state for them, not expose their account or renew them. Cleanup of those rows can be separately bounded; enforcement must not depend on deletion. Use synthetic migration tests for schema/data preservation before proposing any real migration execution.
- Schema/model/auth issuer/dual-deadline resolver/activity transaction, settings validation, metadata contract, client warning/expiry behavior and tests must be reviewed together. A proposed `SESSION_IDLE_MINUTES=30` setting would need fail-closed integer/bounds validation and a documented relationship to `SESSION_HOURS`; for an initial approval decision, consider 5–60 minutes with effective deadline always capped by E. This is **not** a current setting, and no configuration file changes here.
- Update the future schema-readiness expectation in `deployment.py` to the approved migration revision and audit provisioning/test assumptions; do not silently advance version **009** today. Do not run provisioning to adopt the feature. Existing in-memory `create_all` tests alone cannot prove safe migration.
- The shared synthetic demo currently blocks activity POST in both API/client allowlists. A future narrow allowance for this auth-only metadata operation needs explicit approval and tests that every health write stays blocked. Do not exempt demo sessions from idle enforcement invisibly or enable logout-all in the shared demo as a shortcut.
- Stop all old workers before enabling the new policy. Mixed old/new instances are unsafe because old code ignores activity state. Do not declare rollout complete while any serving path checks absolute expiry alone. Stage/test only new synthetic databases first; no existing database was inspected to infer its revision or contents.
- With last-activity state, silently increasing I can make a previously idle-expired but uncollected row usable again. Freeze the approved policy for a serving generation; changing its duration requires coordinated worker cutover and invalidation of existing authenticated sessions under a separately approved procedure. Do not recompute a more generous lifetime for old rows. If seamless per-session policy changes are required, revisit the persisted-deadline/policy-version alternative before implementation. Operational clock corrections likewise need a session-invalidation policy; a single activity timestamp cannot detect every wall-clock rollback.
- **Rollback is security-sensitive:** merely reverting code can reactivate NULL/idle-expired sessions whose absolute deadline is still in the future. Stop ingress/workers, explicitly invalidate all existing session rows under a separately approved operator procedure, then serve compatible code requiring fresh login. Never restore revoked sessions from a snapshot. Prefer leaving an unused nullable column in place over destructive downgrade until compatibility is proved. No rollback SQL/migration was created/run here. Database/backup restore must invalidate sessions before serving and remains a separate gate.

## Frontend expiry, warnings and unsaved information

Proposed API metadata on login/bootstrap/activity: immutable `expires_at`, confirmed `idle_expires_at` and `server_time`. Compute the displayed remaining time from the server response and a local monotonic elapsed timer; browser wall-clock changes must not grant renewal. Recheck on visibility/pageshow/network return without activity. Timer throttling/sleep can delay UI actions, so server authorization is always decisive.

- Warn five minutes before the earlier deadline with a stable, polite live-region message and native “Stay signed in”/“Sign out” controls in logical tab order. Announce once per relevant deadline change, not every second; do not steal focus from diary typing or trap keyboard focus. Explain that unsaved information will be discarded on lock and whether continuation can still help. At the absolute limit, continuation cannot extend E; offer sign-in guidance without claiming otherwise. Verify timing adjustments with accessibility reviewers rather than claiming compliance from a timer test.
- Continuation only succeeds after the server confirms both limits are live. A warning, click, local event or optimistic countdown cannot extend a session. A failed/late response does not keep protected content visible past the last confirmed deadline. Once privacy-locked, a delayed successful response must not automatically remount private content.
- On either deadline/expired API response: immediately clear authentication/generation, unmount all private screens/dialogs/drafts, ignore/cancel in-flight health responses and navigate to sign-in. Focus the sign-in heading or explanatory message; announce the reason generically without account/health values. Keep the existing emergency link accessible, without activating it. No protected stale content during reconnect, history navigation or browser restoration.
- **Change needed to the current lifecycle:** an idle lock must be latched. Today session-ended immediately bootstraps and could reopen private UI if another tab extended the shared server session or a pending acknowledgement arrived. Do not use that flow unchanged for a local privacy lock. Expiry must lead to explicit reauthentication; generic bootstrap cannot unlock it. Handle 401 from future `auth/activity` explicitly because current `api.ts` excludes auth-path 401. Distinguish failed CSRF (403), transport/DB failures and confirmed expiry; none warrants a false save or renewal message.
- Same-cookie tabs can avoid stale warnings through a no-touch metadata recheck after another tab's activity signal. Missed signals still lead to a conservative local lock. Reauthentication in one tab rotates the shared cookie and affects other tabs and their drafts; warn/test this behavior rather than bypassing stale-session guards or keeping old private content mounted.
- **Proposed minimal unsaved-entry policy:** do not persist drafts to localStorage, sessionStorage, IndexedDB, URLs, logs or exports. Before expiry, warning + meaningful typing activity give users an opportunity to Save. At expiry discard unsaved health data from mounted state and state that it was not saved. Do not silently submit or replay it after login or carry it into another account. Retaining an encrypted or memory-held recovery draft would expand sensitive-data lifetime/scope and requires separate approval; it is not part of the initial plan.
- For requests already sent before lock, completion is uncertain if the response is lost. After reauthentication explicitly reload saved records; never claim failure means nothing was committed or automatically retry a POST. Test “saved but response lost” separately from “not saved.” No existing record/history should be rewritten by expiry handling.

## Required synthetic acceptance tests — proposed, not run

| Area | Required cases / expected behavior |
| --- | --- |
| Inactivity / initialization | New authenticated L and unchanged E; +I−1ms valid, +I and +I+1ms denied; no requests and repeated bootstrap/resource/polling both expire. Anonymous one-hour behavior unchanged. |
| Active use / warnings | Input/navigation/explicit continue produces authorized activity; new confirmed idle deadline, same E/cookie/CSRF; no field values sent. Continued active use cannot pass E. Passive/hidden/timer/failed signals do not touch. |
| Absolute ceiling | Touch just before E may only grant up to E; at/after E no touch or authenticated bootstrap. Test configured 1h/12h/168h and shorter idle bounds. |
| Persistence / clocks | Independent instances/engines and restarted process over a new synthetic file share L. Fixed millisecond conversion, UTC/timezone/DST, equal deadlines, malformed/NULL/future/negative/overflow timestamps, forward/backward clock jumps and unavailable DB fail safely. PostgreSQL needs its own isolated runner. |
| Concurrent requests | Two touches cannot move L backward; block a touch behind a lock until expiry and prove refusal. GETs never write L. Logout/touch and logout-all/touch in both orders cannot resurrect rows; stale response cannot reopen UI. No in-flight health payload duplicated. |
| Account / session isolation | Same-account independent sessions expire separately; shared-cookie tabs see server policy; other account's touches cannot change it. Extra owner/time/deadline fields rejected. New login rotates old cookie/CSRF and initializes only its new row. |
| CSRF / stale credentials | Missing/wrong auth, Origin/CSRF, old cookie/token, expired session and replayed global-revocation credentials cannot touch. Generic errors/private headers; no password, token, record or SQL leakage. No weakening of read-binding checks. |
| Global revocation | All Phase 7 cases retained; current + independent session rows deleted, records/other accounts intact, next requests/touches fail, fresh legitimate login possible. Failed password confirmation never revokes or renews sessions. Demo global logout remains blocked. |
| Schema / rollback | Upgrade a new synthetic pre-change schema; all user/health/history values unchanged, old authenticated NULL rows unauthorized, anonymous bootstrap usable, new login initialized. Missing schema fails readiness. Simulate old/new mixed code refusal and rollback without token resurrection. No real migration in design phase. |
| Frontend / accessibility | Fake-clock warning and hard lock, keyboard/AT continuation/cancel, focus and live announcements, typing before Save, multiple tabs, stale generation, offline/sleep/resume/back-forward cache, failed/late keepalive, auth-path 401, absolute ceiling and emergency-link availability. No draft survives logout/expiry/account switch; no real handler activation. |

Test through real shared database transactions in disposable files for race/persistence cases, not only mocks or a shared Python object. Preserve current 65 selected auth/security/revocation regressions and relevant UI tests. Human screen-reader, timing, zoom/reflow and interrupted-entry review remains necessary after implementation; passing fake clocks does not complete those gates.

## Alternatives and reasons

| Alternative | Assessment |
| --- | --- |
| Client timer only / process-local last seen | No reliable backend/cross-worker/restart protection; rejected |
| Shorten `SESSION_HOURS` or keep shortening `expires_at` | Confuses fixed absolute and sliding idle limits; cannot preserve the original ceiling safely with only the existing field; rejected |
| Touch every protected request / middleware heartbeat | Bootstrap, refresh or future polling can renew forever; typing may still be misclassified; rejected |
| Touch successful health mutations only | Small backend surface but times out people reading/typing an unsaved diary; not recommended without explicit continuation/activity path |
| Persist an idle deadline instead of last activity | Feasible equivalent single-column design if updates are capped by E and atomically guarded; less direct last-activity semantics and policy-change handling. Choose one, not both, unless a justified requirement appears. |
| Session/device inventory, recovery, encrypted drafts or token replacement | Separate features/threats; defer to approved Phase 7/storage plans, not idle-timeout scope |

## Actual audit validation and safe reproduction

New temporary root: `%TEMP%/migramind-idle-audit-slfo9_4p`. Copied tracked source only with explicit Python/frontend source/configuration suffixes; no environment, database/WAL/SHM, export, backup, secret, dataset or browser-profile copy. Existing temporary Phase 5 Python 3.13.12 dependencies were reused read-only; copied Node dependencies matched current package-lock bytes. No install, external service, GitHub request, live backend, browser handler, migration or provisioning ran.

Environment before app import: `APP_ENV=development`, `DATA_MODE=local`, **`DATABASE_URL=sqlite://`**, `SESSION_HOURS=12`, `PYTHON_DOTENV_DISABLED=1`, `PYTHONDONTWRITEBYTECODE=1`, copied-backend `PYTHONPATH`, private TEMP/TMP, restricted OS execution environment. Existing fixtures create synthetic in-memory schemas; the existing fresh-instance regression creates only a new temporary synthetic SQLite file. Existing CRUD/erasure tests affect their own synthetic fixtures only.

| Check | Actual Windows result |
| --- | --- |
| Existing auth/security/logout-all backend tests | **65 passed, 1 migration case deselected**, 13.56s pytest / 15.03s wall |
| Temporary current-behavior observations | **2 passed**, 1.36s pytest / 2.28s wall: exact session-column inventory; fixed absolute deadline/cookie and successful +1h/+6h/+11h reads, +13h denial. These do not test the proposed timeout. |
| Existing frontend Authentication/AccountSettings/api tests | **21 passed / 3 files**, 10.62s suite / 12.06s wall |
| Documentation / integrity | **54 local links / 34 source-line references checked**, 123 tested source/configuration files matched; prior release text and audit reports preserved; application, locks, migrations and configuration unchanged; `git diff --check` passed |
| Failures / retries | No test failures, timeouts, installs or test reruns. Existing Starlette/httpx TestClient deprecation warning remains. |

Exact commands from copied backend, with a new output root and the isolated interpreter:

```text
<isolated-python> -B -m pytest -q -ra tests/test_auth.py tests/test_security.py tests/test_logout_all.py -k "not migration" --basetemp <new-root>/backend-data -p no:cacheprovider
<isolated-python> -B -m pytest -q -ra tests/test_phase8_observations.py --basetemp <new-root>/observation-data -p no:cacheprovider
```

The temporary observation module (outside Git) imports the existing `clients`/`register` fixture, asserts the five exact session columns, and patches only copied `app.auth.now` to fixed offsets from registration time. It reads synthetic account/bootstrap endpoints and asserts expiry/cookie behavior; it does not manipulate the OS clock or implement an idle algorithm. Logs, commands/results and temporary observation source remain under the new root. From copied frontend, `CI=true`, `VITE_DATA_MODE=local`, empty `VITE_API_URL`:

```text
node node_modules/vitest/vitest.mjs run src/Authentication.test.tsx src/AccountSettings.test.tsx src/api.test.ts --maxWorkers=1
```

Caps were 180s backend, 90s observations and 180s frontend. No fresh Linux, actual parallel-process/PostgreSQL, browser/device/human accessibility, production build, dependency audit or deployment test was run. Those are not necessary to validate a documentation-only diff and no prior results are rebranded as Phase 8 passes. Full migration/provisioning/demo harnesses were excluded under the task's boundaries.

## Approval and release gates

Smallest recommended first implementation approval: **one additive nullable activity column plus shared backend dual-deadline enforcement, the narrowly authenticated activity operation and focused synthetic migration/concurrency/revocation tests**. This is a bounded backend slice, not permission to apply a migration or enable idle timeout for existing users. Do not enable the feature on a serving application until the warning/activity/latched-lock/unsaved-entry frontend is approved, implemented and verified as well. No remediation is implemented now.

Unresolved decisions: confirm 30-minute/five-minute timings and allowed configuration bounds; whether the proposed foreground interaction set meets keyboard/AT needs; unsaved-data loss wording; exact cross-dialect live-clock/locking implementation and clock policy; session invalidation/cutover/rollback operator procedure; shared-demo auth-only allowance; and the frontend latch/re-authentication contract across tabs. Each affects acceptance; none should be silently guessed during rollout.

**Release status unchanged:** S7-01/SP4-03 idle protection remains Medium/open. PR #22's global revocation remains implemented, while verified password change/recovery and inventory remain absent. SP4-01/High storage/copies, hosted/shared abuse defenses, backup restore/retention, offline privacy locking, human accessibility/device and research/clinical gates remain. Public/real-health release is still **NO-GO**. No application, migration, lock, production configuration, OS/data or deployment change; no commit, push, PR or merge. Separate approval is required before implementation.
