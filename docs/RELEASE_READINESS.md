# Phase 2: release readiness

## Phase 8C: final stabilization and PR-readiness verdict (2026-11-11)

**READY WITH DOCUMENTED LIMITATIONS — disabled-by-default PR review only.** Verified `security/session-idle-timeout` against local `main`/HEAD `7ca2cdd`. All intended Phase 8A/B work is preserved; no runtime/frontend or migration change in this phase. **`SESSION_IDLE_TIMEOUT_ENABLED=false` remains default**, with production/demo opt-in rejected and no existing environment enabled. [Final evidence and activation blockers](SESSION_IDLE_TIMEOUT_PLAN.md#phase-8c-stabilization-and-pr-readiness-verdict-2026-11-11) include the complete changeset review, precise commands and historical failures.

| Phase 8C final validation | Exact result |
| --- | --- |
| Backend/offline research | **302 passed / 5 provisioning-dependent cases deselected**, 109.91s pytest / 112.81s wall |
| Full frontend unit suite | **109 passed / 17 files**, 72.85s suite / 74.66s wall |
| Uninstrumented Chrome/Edge desktop + 320px | **60 passed**, 68.32s wall; retries disabled, original timeouts |
| Real frontend → fresh temporary backend | **4 passed**, 10.7s suite / 11.79s wall |
| TypeScript / local / synthetic builds | Passed, **5.55s / 6.15s / 6.95s wall**, using existing locked build steps |
| Bounded focus diagnostics | **29 passed**: 17 original scenarios + 12 controlled Enter interleavings; separate from normal browser totals |
| Documentation / integrity | **71 local links / 42 source references**, 136 tested source/configuration files matched; 17 starting source files unchanged; 21 intended paths; whitespace check passed |

**Edge uncertainty remains open:** no reproduction in 29 bounded diagnostics or the final normal suites. Four persisted, value-free traces show expected Edit → select → Cancel → Edit → Delete transitions, no submit events or unexpected navigation. The earlier failure is not declared resolved, and Daily Status behavior/tests were not changed to make it pass. Initial inline trace bodies were not persisted by the list reporter; four additional planned file-backed traces corrected evidence collection, without retry/timeout changes.

New migration regressions cover fresh install and ordered 009→010 upgrade, actual startup/readiness/authentication with enforcement off, and existing synthetic-record preservation. One old deployment-module assertion failed because downgrade now stops at 010 rather than 009; corrected only its expected message, retained preservation checks, and included it in the final passing backend suite. The five deselections invoke provisioning and require separately authorized/CI verification; no such script ran locally. Disabled auth responses have four top-level keys, correcting an earlier documentation count only.

Reviewed all **21 intended paths**, including untracked files, for scope, artifacts and credential-shaped literals. No temporary/data/database/backup artifact or such secret flag in the reviewed changeset; fixture literals are explicitly synthetic. No actual secret/data stores or ignored/Git-history scan. Runtime code, migrations, locks, deployment settings and browser tests are preserved. Phase 8C modifies only two backend test files and these two reports. Existing user databases/records/backups/secrets/environments remain untouched.

**Activation/public release remains blocked:** unresolved historical Edge uncertainty, human AT/timing/keyboard/zoom/contrast and physical-device review, Linux/PostgreSQL/cross-host clocks/parallel workers, schema adoption/cutover/rollback and session invalidation, plus existing storage/recovery/abuse/retention/research gates. No known deterministic code fix remains for disabled PR review; CI/provisioning-specific checks are still required before merge. No activation, commit, push, PR, merge or deployment.

## Phase 8B: frontend idle integration — synthetic verification, not activation (2026-11-11)

Verified `security/session-idle-timeout` and the nine expected uncommitted Phase 8A paths. Preserved the seven backend/migration/test files unchanged and both report bodies. The [Phase 8B evidence](SESSION_IDLE_TIMEOUT_PLAN.md#phase-8b-frontend-integration-and-synthetic-verification-2026-11-11) records the UI/API contract, failures, exact synthetic reproduction and remaining gates. **Backend default stays `SESSION_IDLE_TIMEOUT_ENABLED=false`; no existing environment was enabled.**

Only complete enabled backend metadata activates a five-minute warning. **Stay signed in** deliberately posts the last confirmed activity precondition and updates/dismisses only after a valid acknowledgement; passive activity never renews. Stale tabs can explicitly check status without retrying activity. Idle/absolute expiry, revocation or changed account/session binding clears private UI with a latched sign-in flow; bootstrap/late responses cannot restore it. Unsaved forms persist through a confirmed extension but are discarded on closure, with no draft storage/autosave and honest pending-save wording. Warning controls render inside the diary modal when necessary, remain keyboard reachable, restore focus and wrap at 320px without animation.

| Phase 8B final evidence | Actual result / limitation |
| --- | --- |
| Backend/offline-research | **289 passed**, 150.92s pytest / 155.67s wall; six new-target migration cases included, provisioning module excluded |
| Full frontend | **109 passed / 17 files**, 64.62s suite / 65.39s wall |
| Intercepted Chrome/Edge, desktop + 320px | **59 passed / 1 failed** of 60. All **44 new idle executions passed**; one existing Edge Daily Status focus case failed once. Original run remains partially failing. |
| Existing Edge case diagnostic | **1 passed**, 3.8s suite / 4.91s wall, unchanged code/timeouts; intermittent cause unresolved |
| Real frontend → temporary backend | **4 passed**, 9.6s suite / 10.61s wall; two actual API scenarios in each Chrome/Edge, new fictional accounts/private SQLite and accelerated clock |
| Local / synthetic production builds | Both TypeScript + Vite passed, **9.99s / 10.90s wall** |
| Documentation / integrity | **70 local links / 42 source references**, 133 tested source/configuration files matched; seven Phase 8A backend files and previous report bodies preserved; whitespace check passed |

Failures were investigated rather than retried silently: initial browser clocks advanced before bootstrap; a two-tab fixture advanced a shared clock twice; real integration exposed the page consuming its own sign-in BroadcastChannel message. Added ready waits, corrected shared-clock advancement and introduced non-sensitive memory-only sender filtering with regressions. Original and diagnostic failure logs remain. No Playwright retries or timeout increases. Details/counts are in the plan, including the unresolved existing Edge scenario.

All execution used filtered temporary source, reused isolated dependencies, intercepted APIs or a nonce-guarded test wrapper around actual application routes. The wrapper alone enables enforcement in its local child process, accepts no database path, creates a new synthetic schema without provisioning/migration, and cleans its owned data at shutdown. No existing database/account/health/backup/secret/browser-profile access, lock/migration/deployment/OS change, dependency installation or real email/phone action. Seven backend files from Phase 8A remain untouched; 13 frontend/test/report paths are changed in Phase 8B (20 combined worktree paths).

**Rollout gates remain:** backend flag off; existing-data schema 010 adoption/cutover and invalidation require separate review. No additional migration/configuration change is required by this frontend work. Intermittent Edge regression, human AT/keyboard/timing/contrast/zoom, physical devices/sleep-resume, Linux/Safari/Firefox, PostgreSQL/cross-host clocks and operational rollout remain unverified. Storage/recovery/abuse/retention/research gates are unchanged. No public/real-health readiness or clinical claim, commit, push, PR, merge or deployment.

## Phase 8A: approved backend idle foundation — OFF by default (2026-11-11)

Verified `security/session-idle-timeout` at `7ca2cdd`, with only the existing two uncommitted Phase 8 document changes. Preserved both bodies. The [implementation evidence](SESSION_IDLE_TIMEOUT_PLAN.md#phase-8a-approved-backend-foundation-disabled-by-default-2026-11-11) records the approved backend foundation, exact contract, migration/clock/retry semantics, tests and limits. Earlier audit/design statements below are historical.

**`SESSION_IDLE_TIMEOUT_ENABLED=false` by default.** Exact `true` opt-in is restricted by settings validation to local development; production/synthetic-demo opt-in is rejected. No serving configuration was enabled. When opted in, persistent last activity adds a **30-minute idle check** alongside unchanged absolute expiry. Only explicit authenticated Origin/CSRF-protected activity POST advances it, with a server-observed precondition to reject stale retries; reads/bootstrap/ordinary requests never renew it. No frontend code, warning, timer, automatic logout or activity caller changed.

Migration **010** only adds nullable BIGINT `login_sessions.last_activity_at_ms`, without default/backfill/deletion or health changes; readiness expects 010. New code requires that schema even with the behavior flag off. No existing database was accessed/migrated. Off-state legacy NULL sessions retain normal absolute behavior; explicit enabling requires their fresh sign-in. Downgrade follows repository convention and refuses before modifying schema/data; no destructive rollback implemented. Activation/disable-after-activation requires a separate reviewed cutover/invalidation procedure.

| Phase 8A verification | Actual Windows evidence |
| --- | --- |
| Final backend/offline-research suite | **289 passed**, 141.26s pytest / 144.43s wall; includes 39 new idle/migration cases and all six migration cases. Deployment/provisioning module excluded. |
| Focused foundation checks | Corrected run **38 passed**, 65.39s pytest / 69.50s wall; final broader run adds fractional-clock regression |
| Relevant frontend regressions | **21 passed / 3 files**, 42.95s suite / 47.99s wall |
| Local / synthetic production builds | TypeScript + Vite passed, **38.51s / 35.56s wall** |
| Documentation / integrity | **62 local links / 38 source references**, 127 tested source/configuration files matched; both starting document bodies preserved; exactly nine intended changed files; whitespace check passed |
| Failures / follow-ups | Initial focused run: 34 passed, 2 test-helper failures (multiple-session assumption, unquoted reserved column). Corrected once. First broader run: 288 passed; then aligned response precision with stored milliseconds and added regression, final 289 passed. No timeouts/hidden flaky reruns; existing TestClient and temporary Vite outDir warnings remain. |

Only fresh temporary filtered source, synthetic accounts/databases and copied matching dependencies were used; no install, existing app environment mutation, real data/secret/backup/WAL access, provisioning, deployment or OS change. SQLite tests exercise concurrent threads, independent engines/apps, waiting past expiry/revocation, rollback and fresh-instance persistence; live PostgreSQL/parallel-process/Linux/browser/human/device verification remains unperformed. Synthetic migration tests verify preserved table values/NULL state, readiness, downgrade refusal and idempotent upgrade.

**Not ready to activate:** the frontend still lacks idle warning/latched lock/activity integration; host UTC is test-injectable rather than a shared database clock. Schema rollout, clock/policy transitions, migration/rollback, hosted abuse/operations and Phase 8B accessibility/unsaved-entry handling need separate approval/evidence. S7-01/SP4-03 remains operationally open; recovery/change, storage/copies, restore/retention, manual/research gates remain. Public/real-health release is **NO-GO**. Nine intended files only (backend foundation/migration/tests and these two documents); locks, previous migrations, frontend and production configuration files untouched. No commit, push, PR, merge or deployment.

## Phase 8: session idle timeout audit and design (2026-11-11)

Verified clean `security/session-idle-timeout` at **`7ca2cdd`**, the PR #22 merge, also the local `main` HEAD; both ancestry checks passed. No remote fetch/GitHub-state claim. The new [idle-timeout plan](SESSION_IDLE_TIMEOUT_PLAN.md) maps current absolute expiry, session persistence/CSRF/cookies, PR #22 global revocation and frontend lifecycle, with source/test references and proposed acceptance/rollout/rollback requirements. **Audit/design only: no timeout implemented or migration created/run.** Prior evidence is preserved below.

Current sessions have fixed absolute expiry (**12h default, configurable 1–168h; anonymous 1h**) and no persistent activity state or idle renewal. Proposal: retain that ceiling, add one nullable persistent server activity timestamp, use a **30-minute idle interval / five-minute accessible warning**, and count only deliberate foreground activity through a narrowly CSRF-protected operation. These timings are proposals, not policy. Automatic API traffic/bootstrap/polling must not renew sessions. Existing authenticated rows would require sign-in rather than activity backfill; cross-instance locking/clock, frontend latched privacy lock, unsaved-entry disposal and schema/rollback approval are required. Reverting to old code without invalidating sessions could restore access to idle-expired rows.

| Phase 8 validation | Actual Windows evidence |
| --- | --- |
| Existing backend auth/security/global revocation | **65 passed, 1 migration case deselected**, 13.56s pytest / 15.03s wall |
| Temporary current-behavior observations | **2 passed**, 1.36s pytest / 2.28s wall; no activity column, no deadline/cookie renewal, +11h accepted and +13h denied with 12h absolute TTL |
| Relevant frontend unit tests | **21 passed / 3 files**, 10.62s suite / 12.06s wall |
| Documentation / integrity | **54 local links / 34 source references**, 123 tested source/configuration files matched, prior reports preserved; only the two intended documents changed; whitespace check passed |
| Failures / limitations | No test failures/retries; existing TestClient deprecation warning. No new browser/human/device, Linux, build, real parallel-worker/PostgreSQL, migration/provisioning or deployment result. Proposed idle behavior is not tested or implemented. |

New filtered temporary source, synthetic fixtures and fresh temporary databases only; existing isolated dependencies reused read-only, no installs or existing data/secret access. Detailed commands, caps and evidence are in the plan. Only `docs/SESSION_IDLE_TIMEOUT_PLAN.md` and this report change. **Release blockers unchanged:** idle timeout remains S7-01/SP4-03 Medium/open; Phase 7 revoke-all remains implemented. Recovery/change, storage/copies, abuse/hosting, restore/retention, human accessibility/device and research gates remain; public/real-health release is **NO-GO**. Request separate approval for the bounded schema/backend/test implementation slice before proceeding, with no rollout until frontend protections are verified. No commit, push, PR, merge or deployment.

## Phase 7: approved Sign out all sessions implementation (2026-11-11)

Verified `security/session-recovery` at `4b3a45f` and preserved the only starting changes: the two uncommitted Phase 7 documents. The [approved implementation follow-up](SESSION_SECURITY_PLAN.md#approved-follow-up-password-reauthenticated-sign-out-all-sessions-2026-11-11) supersedes only the earlier S7-02 implementation-pending status; the original audit snapshots below remain intact.

Account & Privacy now offers an inline **Sign out all sessions** confirmation requiring the current password. The protected `POST /api/auth/logout-all` uses existing Argon2 verification, authenticated ownership, Origin/CSRF and attempt budgets, then transactionally deletes all session rows for that user, including current, before expiring the cookie. It does not delete the account or health data. The UI clears authentication and returns to fresh sign-in only after confirmed success; cancellation sends nothing and restores focus, and failures are shown without success claims. Shared read-only demo global revocation is explicitly unavailable; ordinary logout remains unchanged. No migration, process-local revocation workaround, rate-limit redesign or production configuration change.

| Approved implementation validation | Actual Windows evidence |
| --- | --- |
| Backend suite | **245 passed, 5 migration cases deselected**, 36.92s pytest / 38.77s wall; deployment/provisioning module excluded. Includes 12 new session-revocation cases. |
| Frontend suite | **91 passed / 15 files**, 45.30s suite / 46.54s wall |
| Affected frontend verification after test-type correction | **15 passed / 2 files**, 7.35s suite / 8.04s wall; overlaps full suite |
| Isolated Playwright | **22 passed**, 22.2s suite / 25.88s wall; installed Chrome/Edge desktop and 320px viewports, mocked API, temporary profiles, retries=0 |
| Local / synthetic production builds | Both passed TypeScript + Vite, **7.61s / 7.48s wall** |
| Documentation / integrity | **59 local links / 37 source references**, 123 tested source/configuration files matched; original uncommitted document bodies preserved; locks, migrations and protected configuration unchanged; diff whitespace passed |
| Failures | First two builds failed TypeScript on eight new unit-test queries using unsupported `exact`; corrected test options, reran affected tests and each build once. No application workaround, timeout increase, unit/backend/browser failure or hidden flaky rerun. Existing TestClient deprecation and temporary Vite outDir warnings remain. |

Backend evidence covers wrong password/auth/CSRF refusal, owner-selector rejection, multi-session/current-cookie replay, other users and saved records remaining intact, failed-commit rollback, existing reauthentication budget and cookie attributes. Independent apps/engines sharing a new synthetic SQLite file and a third fresh engine rejected revoked credentials: durable lookup/deletion, not a memory list. This is not an actual multi-process, Linux or hosted PostgreSQL test. Browser results demonstrate rendered keyboard/focus/cancel/success/failure and reflow behavior with intercepted responses, not real-API or human/device verification.

All tests/builds used a new filtered temporary source tree and synthetic databases only. Existing isolated dependencies were reused read-only; no install, existing data/database/WAL/backup/secret access, migration, provisioning, real account operation, email or deployment. Full API/browser/demo provisioning harnesses were skipped. Exact commands, limits, evidence artifacts, security guarantees and rollback are in the plan.

**Remaining release gates:** S7-02 is addressed for the supported local prototype; **SP4-03 remains partially open** for idle expiry, verified password change/recovery and session inventory. SP4-01/High storage/copies, shared abuse/hosting, restore/retention, offline logout/privacy, human accessibility/device and research gates remain. New logins with a known password can still create sessions; already-authorized requests/rendered data cannot be recalled, and database restore must not resurrect revoked sessions. Real-health/public release remains **NO-GO**. No commit, push, PR, merge or deployment.

## Phase 7: session security and account recovery review (2026-11-11)

Verified clean `security/session-recovery` at **`4b3a45f`**, merge of PR #21, before work. The [session-security and recovery plan](SESSION_SECURITY_PLAN.md) maps actual authentication, cookie/CSRF, expiry, revocation, ownership and missing recovery capabilities, with source references, synthetic reproduction steps and proposed acceptance/rollback criteria. **Audit and planning only; no application changes.** Prior audit and Phase 6 evidence below are preserved.

Confirmed controls: Argon2id; opaque random cookie sessions with stored digests; login/registration rotation; server absolute expiry; production Secure/HttpOnly/host-only/SameSite cookies; Origin/CSRF checks; current-session logout; scoped account/record access. No new Critical/High or cross-account disclosure was confirmed. Missing idle expiry, non-destructive revoke-all and verified password change/recovery refine **SP4-03 / Medium**. Process-local abuse controls and pre-CSRF account-budget pressure refine **SP4-04 / Medium**. Local registration enumeration and mounted private UI after failed logout are **Low**, with prerequisites and bounded evidence in the plan. No reset-token flow exists to validate.

| Phase 7 check | Actual Windows result |
| --- | --- |
| Existing selected backend modules | **100 passed, 2 migration tests deselected**, 17.39s pytest / 18.93s wall |
| Temporary synthetic backend observations | **7 passed**, 3.57s pytest / 5.16s wall |
| Existing frontend authentication/client unit tests | **15 passed / 2 files**, 11.95s suite / 13.86s wall |
| Temporary mocked-frontend logout observation | **1 passed**, 3.89s suite / 5.15s wall |
| Failures / retries | Initial backend and observation collections had 5 and 1 errors respectively because the temporary copy omitted research Python source. Added that source to the temporary copy; one rerun each passed under unchanged limits. No product/dependency fix or hidden rerun. Existing Starlette/httpx deprecation warning remains. |

Tests used new filtered temporary source, in-memory fixture databases and fictional accounts only; prior isolated Python dependencies were reused read-only, and matching locked Node dependencies copied. No installs, existing database/account/token/secret access, actual browser profile, migration, provisioning, external service or email. No fresh Linux, browser, build, load, deployment or physical-device result is claimed; full browser/demo harnesses that provision/migrate were excluded. Exact command shapes, logs, limits and observations are in the plan.

**Real-health/public release remains NO-GO:** SP4-01/High storage/copies, SP4-03 account compromise/recovery, SP4-04/06 hosted abuse/operations, retention/restore erasure and the human accessibility/device/research gates remain open. Proposed first implementation is password-reauthenticated **sign out all sessions**, including current, without deleting health records or changing ordinary logout semantics. It requires separate approval; idle expiry, password change/verified recovery and other remediation are not implemented. Only `docs/SESSION_SECURITY_PLAN.md` and this report change. No commit, push, PR, merge or deployment.

## Phase 6: approved synthetic authenticated-backup prototype (2026-11-10)

Verified `security/data-protection` at `07ae0b1`, merged PR #20, with only the existing Phase 6 documentation edits before work. The user separately approved a **synthetic-only** proof of concept under [prototypes/synthetic_encrypted_backup](../prototypes/synthetic_encrypted_backup/README.md). The [plan follow-up](DATA_PROTECTION_PLAN.md#approved-synthetic-only-encrypted-prototype-follow-up-2026-11-10) preserves the earlier design/drill evidence and records exact implementation, dependencies, runs and limits.

Uses PyCA **cryptography 50.0.2 / AES-256-GCM**, fresh 256-bit memory-only key and 96-bit nonce, 128-bit tag, exact-header authenticated metadata and strict bounded format/schema validation. Generates random fictional JSON only; accepts no input/key/destination paths. Recovery validates fully before staging, then atomically publishes a **new-only** fixed sandbox name via hard link; existing targets are never replaced. Keys are not printed/persisted and references/files are dropped/cleaned at context exit; this is intentionally not durable key recovery or secure memory erasure.

| Prototype verification | Actual result / limit |
| --- | --- |
| Final Windows | **19 tests passed**, zero failed/skipped; Python **3.13.12**, **0.736s suite / 1.683s wall**. Demo and `pip check` passed in new standalone venv. |
| Final WSL | **19 tests passed**, zero failed/skipped; Python **3.10.12**, **0.223s suite / 0.418s wall**. Demo and `pip check` passed in a new venv without system ensurepip installation. Not application Python 3.13/CI validation. |
| Covered failures | Wrong key, metadata/nonce/ciphertext/tag tampering, truncation/size/version/contract validation, authenticated malformed payloads, no pre-validation staging, existing-target preservation, injected I/O failures and concurrent publication. |
| Dependencies | Only prototype requirements added: cryptography **50.0.2**, cffi **2.1.1**, pycparser **3.11**, conditional typing_extensions **4.16.0**. Official PyPI metadata/artifact hashes and actual library/OpenSSL versions retained; application locks unchanged. |
| Initial setup issue | Windows verified-wheel launcher triggered pip's self-modification guard before installing dependencies. Corrected module invocation, retained the failure, then succeeded; no protection disabled or version substituted. |
| Development evidence | Initial WSL 17 tests passed, then two cases/stronger assertions were added; intermediate and final Windows 19-test runs passed. A fresh final WSL environment was created when the initial temporary one was unavailable. No cryptographic assertion failed or was rerun to hide a failure. |

Only four prototype files and these two Phase 6 reports change. No application integration, existing file/data/DB/WAL/backup/export/browser/secret access, production dependency/configuration change, migration, OS encryption change, credential change or cloud deployment. No commit, push, PR or merge. **SP4-01/High and public/real-data release remain blocked:** SQLite consistency, durable/recoverable key custody, trusted operator provenance, retention/restore erasure, session revocation, actual storage/hosting protection and other security/manual/research gates are unverified. Passing an ephemeral JSON AEAD experiment does not secure MigraMind's existing databases or copies.

## Historical Phase 6 design and earlier release evidence

## Phase 6: data protection design and safe validation (2026-11-10)

Verified clean `security/data-protection` at **`07ae0b1`**, merged PR #20, before work. The new [data-protection and backup plan](DATA_PROTECTION_PLAN.md) maps confirmed storage mechanisms versus unknown OS/cloud copies, defines the local and future-hosting threat models, and provides adoption, acceptance, recovery/rollback and approval steps. **Design only; no encryption enabled, key created, existing data moved or application/deployment configuration changed.**

Recommended local layers: active full-disk encryption on covered volumes, an owner-approved durable nonsynced private root, inherited restricted permissions, controlled exports, separately encrypted/authenticated portable backups and independent recovery custody. Full-disk encryption does not protect plaintext after an unlocked application or sync/export client reads it. Future hosting separately requires encrypted volumes/snapshots/WAL/backups, verified TLS, KMS and restricted runtime/backup/restore identities. None was implemented here.

| Phase 6 evidence | Actual result / limit |
| --- | --- |
| Synthetic file backup/recovery | Same **12 JSON-only cases passed on Windows and WSL**, covering exact snapshot/restore, corruption/truncation detection, contract/path/overwrite refusal and source preservation. Not SQLite, encrypted-archive or disaster-recovery validation; no database file created/opened. |
| Windows permissions | New temporary root DACL restricted to current OS SID and SYSTEM, protected inheritance, inherited child sentinel and owner write/read verified. Separate read-only ACL probe **blocked** by missing `SeSecurityPrivilege`; no privilege/policy changes or effective-denial pass claimed. |
| WSL permissions | New fixture directory **0700**, JSON **0600**, umask **0077**; non-root owner write to separate **0400** probe denied as expected. No different-identity test or actual private-path inspection. Python 3.10 standard-library drill is not project Python 3.13 validation. |
| Checksum threat demonstration | Replacing both a synthetic copy and its unkeyed digest manifest was accepted by a hash-only check. Checksums alone do not authenticate backups; provenance/authentication remains a design requirement. |
| Documentation/integrity | Source/reference review and final documentation/scope checks only; no application tests, migrations, provisioning, encryption/key exercise or existing-data inspection. Earlier phase test counts remain historical. |

**SP4-01 / High remains open**, as do copy retention/erasure (SP4-05), actual hosted operations (SP4-06) and the other security/privacy/manual/research release gates. Real-data/public release remains blocked. Actual device encryption/sync/backup coverage, authenticated encrypted recovery, SQLite/WAL consistency, independent identities and recovery on another device remain unverified. Only `docs/DATA_PROTECTION_PLAN.md` and this report change; no audit history, code, dependencies/locks, migrations, existing backups, secrets or production settings were modified. No commit, push, PR, merge or deployment. Any implementation requires separate approval.

## Historical Phase 5 and earlier evidence

## Phase 5: P1-only installer remediation (2026-11-10)

**Approved P1 implementation:** README and the backend/browser CI jobs now bootstrap exact **pip 26.3** before unchanged locked application installs and assert its installed version. README refuses an existing `.venv`; existing developer environments were not upgraded. Bootstrap/install commands use isolated pip configuration, explicit official PyPI, disabled version checks, noninteractive/no-cache operation and bounded network retries/timeouts. No application, lock, migration, production deployment setting or data change; no P2/P3/P4 work. The [Phase 5 audit evidence](SECURITY_PRIVACY_AUDIT.md#phase-5-approved-p1-installer-remediation-2026-11-10) preserves the earlier audit/planning snapshots and reports every failure/retry.

Independently verified publication on `pypi.org`, listing on the intended simple index, actual wheel download and SHA-256, wheel Python requirement **>=3.10**, and successful installation on supported **Windows Python 3.13.12**. Both new base/ML environments report **pip 26.3**, outside all five reviewed affected ranges. Fresh 26.3 metadata reports no advisory entries; this concerns the installer, not a blanket runtime-security result.

| Phase 5 check / gate | Actual result |
| --- | --- |
| New Windows base / ML installation | Both succeeded; **35 / 42 exact pins**, compatibility and import checks passed. Requirement/lock bytes and hashes unchanged; both bootstrap reports match the verified public wheel hash. |
| New ML environment tests | **233 passed, 5 migration cases deselected**; entire deployment/provisioning module excluded. **36.49s pytest / 38.78s wall**. Not the full historical 254-test suite. |
| New base environment tests | **53 authentication/security tests passed, 1 migration case deselected**, **12.63s pytest / 14.23s wall**; overlap with ML suite. **4 readiness regressions passed** separately. |
| Frontend / builds | **85 tests passed**; local and synthetic TypeScript/Vite builds passed (**10.37s / 9.15s wall**). Copied matching locked npm dependencies, not a new npm installation. |
| Static workflow / README | YAML/policy and **9 Python-job Bash run-block syntax** checks passed; README PowerShell syntax and refusal of a synthetic existing-environment sentinel passed. No workflow commands or full README migration/provisioning sequence executed. |
| Import verification failure | Initial ML verification hit its **90s cap**; one instrumented diagnostic rerun passed in **7.03s under the same cap**, with no reinstall/version change. Original cause unproven; retained as a limitation. |
| Linux / actual GitHub CI | **Pending.** WSL provides Python **3.10.12**, no discovered system Python 3.13. Two new venv attempts failed; diagnostic confirms missing **ensurepip**. No system packages installed; Docker server unavailable. Bash parsing is not Linux install evidence. Actual GitHub Actions jobs were not triggered. |
| Other tooling / retries | Two temporary evidence-collector encoding errors were corrected with UTF-8/ASCII-safe handling; initial WSL log retrieval failed before the same-process diagnostic reproduction. No app tests/builds failed or were rerun. Pip bootstrap/lock installs each succeeded first invocation; logs recorded **zero network retry/resume messages**. |

**P1 status: implemented and Windows-validated, rollout incomplete.** Supported-version Linux/actual CI validation remains a release-sign-off gate; old pip 25.3 environments remain affected unless separately remediated. The full integration browser harness requires migration and the built-demo harness requires provisioning, so neither was run under this task's explicit prohibition. No existing user-data target was substituted.

**SP4-01 remains High/open.** Storage/copy encryption, backups/retention, hosted operations, account recovery/abuse defenses, human accessibility/device and research/clinical gates remain unchanged. No public deployment or real-health use is authorized. Detailed command shapes, timing/caps, artifact provenance, original failures and private temporary evidence paths are in the audit. Only README, CI workflow and these two reports are intended changed files. No commit, push, PR, merge, provisioning or deployment.

## Historical Phase 4 gates and planning

## Phase 4 security and privacy gates (2026-11-10)

The **audit-only** [Phase 4 security/privacy audit](SECURITY_PRIVACY_AUDIT.md#phase-4-security-and-privacy-audit) reviewed clean `audit/security-privacy` at `bf62f41` (PR #19 merged), including its manual-accessibility fixture and Daily Status focus fix. No product/configuration fix was implemented. Earlier Sprint 14 security results in that file are preserved as historical evidence, not current dependency/toolchain assurance.

| Release boundary | Current security/privacy gate |
| --- | --- |
| Guided local synthetic demonstration | Retain loopback-only operation, fictional data, isolated temporary paths and no real telephone/device-handler activation during QA. Manual accessibility/device gates remain open. Current account isolation tests are bounded evidence, not a security certification. |
| Clean installation toolchain | **Open: SP4-02 / High.** The reused fresh Python environment still has pip 25.3; current metadata flags five distinct installer advisories. All 35/42 application pins match and their metadata reports no advisories, but that excludes pip. Approve a reviewed bootstrap/toolchain correction and fresh validation separately; no installer was upgraded here. Historical successful installation does not close this security gate. |
| Public hosting, including a synthetic demo | **Blocked: SP4-04/06 / Medium.** Abuse/resource limits, trusted proxy/client identity, actual TLS/headers/CSP, secrets, restricted runtime/database grants, private monitoring and encrypted recovery need operator/security/privacy verification. The nginx CSP also blocks the built inline theme bootstrap (SP4-08 / Low); the app still renders, but hosted compatibility sign-off is pending. No live deployment was assessed. |
| Real health-data / participant use | **Blocked: SP4-01 / High; SP4-03/05 / Medium.** Application-unencrypted files/copies, account compromise/session recovery and all-copy retention/withdrawal remain unresolved. Membership enumeration exists in local writable registration (SP4-07 / Low); synthetic/production registration remains disabled. No private DB, OS encryption/sync settings, secrets or existing backup was inspected. |
| Research or clinical claims | **Blocked as before.** No validated score/diagnosis is served. Genuine enrollment, independent outcome/coverage verification, governance and prospective/clinical validation remain required; export consent and synthetic tests do not supply them. |

Actual Phase 4 checks: **123 selected backend tests passed, 3 migration cases deliberately deselected; 6 additional isolated checks passed; 85 frontend unit tests passed; 25 mocked browser cases passed in each of Chrome and Edge; both production builds passed.** A separate Chrome built-page check confirmed the CSP violation and continued render. `pip check`, 35/42 installed-pin verification and route inventory passed (54 API registrations, 49 authenticated, five intended public). npm reported zero known advisories; 42/42 exact-version PyPI application metadata queries returned no advisory entries. Installer advisories are reported separately, with aliases deduplicated. See the audit for commands, timings, temporary-tooling errors, safe reproduction, source references and limitations.

Only the two audit documents changed. No application behavior, database, migration, dependency lock, production configuration, secret or existing virtual environment was modified. No provisioning, live backend, deployment, commit, push, PR or merge was performed. Human/device, hosted PostgreSQL/TLS/grants, actual storage/backup controls, independent penetration testing and clinical/privacy approvals remain unverified.

### Remediation planning follow-up - approval pending

The [two-High-finding remediation plan](SECURITY_PRIVACY_AUDIT.md#remediation-planning-for-the-two-high-findings---not-implemented) adds a source-based storage/copy inventory, encryption threat/compatibility comparison, advisory-by-advisory workflow applicability, proposed file changes, validation and rollback. **Both High findings remain open. No remediation was implemented.** The planning follow-up used only static source/report review and public documentation/metadata; prior test results above were not rerun.

| Proposed decision | Release consequence / approval boundary |
| --- | --- |
| P1 first: explicit installer bootstrap, candidate **pip 26.3**, in README and backend/browser CI setup; leave app locks unchanged | Metadata currently lists no advisories for this candidate, but fresh Windows/Linux installation, pin/import/test verification and actual CI installer checks remain pending. Recorded pip 25.3 matches all five advisory ranges; vendor severity is one Low/four Moderate, while the audit's High is the overall conditional toolchain priority. This blocks clean-toolchain/public-packaging sign-off, not an established remote exploit in the running API. |
| P2: local volume/ACL/nonsynced-path policy plus encrypted portable copies and separate key/recovery custody | OS encryption protects covered offline disks, not unlocked apps, plaintext sync/exports or recipient copies. Actual device encryption, active DB path, sync scope and existing backups remain unknown and were not inspected. No existing data move, key creation or OS change is authorized. Real-data and hosted storage-protection gates remain open. |
| P3/P4: SQLCipher/field encryption or hosted storage/KMS design only under separate approval | Native driver/schema/analytics/history/backup/recovery and migration risks need synthetic rehearsal and a target-specific cutover/rollback plan. Do not alter production's synthetic-only boundary, migration files or application features merely to claim encryption. Neither approach is needed to demonstrate fictional data locally. Other hosting/privacy/manual/research gates remain unchanged. |

## Historical Phase 2 and Phase 3 evidence

Assessment: 2026-11-09, `test/release-readiness`, starting at `87ca919db30c5a5675d0888833d4e66355e5a855` (PR #17 merged). Scope: a **local synthetic portfolio demonstration**, not public deployment, real health-data collection or clinical use. This report supplements the historical [portfolio review](PORTFOLIO_READINESS.md), [security audit](SECURITY_PRIVACY_AUDIT.md), [deployment review](DEPLOYMENT_READINESS.md) and [CI guide](CI.md).

**Phase 3 update — 2026-11-10 (Asia/Calcutta):** PR #18 is merged at `1b5da97`; current work is on `test/manual-accessibility`. The [manual accessibility checklist and device matrix](MANUAL_ACCESSIBILITY.md) cover all 12 destinations and provide a database-free paused review session. **No human screen-reader, actual browser-zoom or physical-device verification is claimed.** On this Windows host, 82 unit tests passed; Chrome and Edge each passed 17 existing mocked cases plus a separate 6-case fixture/pattern batch (23 distinct selected cases per browser). Width/touch probes observed all 12 destinations at 640/320px, two themes and emulated mobile orientations; these are not 200%/400% browser zoom or real Android/iOS tests. Firefox/WebKit were unavailable in checked locations. No new browser test failed or was retried in this phase.

**A11Y-01 / P2 approved follow-up:** Daily status cancellation now restores its actual initiating Edit/Review yesterday control, or the new status select when that control is unavailable. The keyed form previously removed the focused Cancel button, leaving BODY active. [Red/green regression evidence and exact validation](MANUAL_ACCESSIBILITY.md#approved-daily-status-focus-fix) document both new browser cases failing before the fix in Chrome and Edge, then passing afterward. The final unit suite is **85 passed** and both production builds passed; **25 selected cases passed in each of Chrome and Edge** with no post-fix failure or retry. Human keyboard/screen-reader confirmation, actual zoom, contrast and physical-device gates remain pending. No data, API, styling or production configuration behavior changed. The initial Phase 3 results above and Phase 2 results below remain historical, including the earlier flaky timeout and fresh-install/pip limitations.

## Decision and priorities

The supported release boundary is a guided, loopback-only, synthetic demonstration. Public or real-health use remains blocked. Passing tests establish bounded software behavior, not clinical validation, accessibility conformance or production security.

**Latest installation result:** the [follow-up investigation](#fresh-windows-install-investigation) completed a fresh Windows Python 3.13.12/ML-lock install and **254 backend tests in that new environment**. The earlier failed attempts below remain recorded, with their transport errors and pip cleanup mechanism explained. Other release gates remain open.

**Latest accessibility result:** the two approved fixes are implemented and verified: the login `tel:112` link now measures **48px high**, and Attack Mode destination navigation focuses the appropriate heading while ordinary exits restore entry/opener focus. **82 frontend tests, 17 selected browser tests and both production builds passed.** The [approved-fix validation](#approved-accessibility-fixes-and-validation) records expected pre-fix failures, an initial test-typing build error and outstanding human/device checks. The earlier [emergency review](#pr-18-emergency-navigation-and-accessibility-review) remains historical evidence.

| Priority / scope | Finding, evidence and impact | Required next step / disposition |
| --- | --- | --- |
| P0: real health-data / public release blocker | SQLite, downloads and local backups are plaintext. The checkout is on a OneDrive path; ignored files are excluded from Git, **not** necessarily from cloud synchronization. Account authorization does not protect files from the OS user, malware, extensions or cloud backup access. See `app/security.py`, `app/auth.py`, `.gitignore`, and the privacy guide. | Keep all demonstrations fictional; place temporary data outside the checkout. Real use requires storage/backup/key management, access control, retention, incident handling and governance review. No real database was opened for this review. |
| P0: research / clinical release blocker | `/api/v1/forecast` remains unavailable; fixed synthetic observations and offline metrics do not validate forecasting, diagnosis or treatment. Local download consent is not research enrollment. Existing research and outcome-verification gates remain open. | Preserve existing disclaimers and research gates. No model, claim or clinical policy change is proposed. |
| P1: public release blocker | A fixed demo email with one operator-chosen password is a shared demonstration identity. Login limits are process-local; no MFA, account recovery, independent penetration test or operational abuse controls are established. Session/login/logout/export operations still write operational records in a health-read-only demo. | Keep access local and password private; do not reuse personal credentials. Public identity, abuse and availability controls require a separate approved design. “Read-only” refers to health/account editing, not a byte-immutable database. |
| P1: hosted release blocker | Existing production guards require explicit synthetic acknowledgement, dedicated database name, PostgreSQL verified TLS, exact HTTPS origins/hosts. nginx/systemd, database roles, certificate forwarding, encrypted restore and monitoring have not been exercised here. Vite preview is a rehearsal server. | Do not publish the preview server or relax guards. Execute the existing operations runbook on an approved host before any hosted claim. Ubuntu CI is not deployment verification. |
| P1: broad accessibility release gate | Existing tests cover selected properties; there is no installed axe/pa11y/Lighthouse audit engine. Screen readers, actual tab order through every form/error, 200–400% zoom, all rendered color combinations and migraine-time comfort remain unverified. | Complete the manual checklist below before claiming broad accessibility. This does not prevent a clearly bounded guided desktop demo. |
| P1: portability gate / installer risk | The fresh Windows install gate is now **verified within the follow-up's bounds**: Python 3.13.12, unchanged locks, new venv and 254 backend tests. Earlier transfer failures exposed pip 25.3's Windows open-handle cleanup defect; interrupted-download handling remains an installer risk. Ubuntu CI is separate evidence. WSL returned `Wsl/EnumerateDistros/Service/E_ACCESSDENIED`; no interactive Linux demo, second personal machine, Firefox, WebKit or physical mobile device was tested. | Retain bounded, isolated retries and the transport evidence; no pip patch/upgrade is included. Rehearse the Linux synthetic-demo commands on a separate approved Linux system. Do not extend the Windows result to the exact earlier 3.13.11 interpreter or another machine. |
| P2: test gap addressed | Existing keyboard checks did not traverse all 12 workspace destinations with focus, landmark and visible-control-name assertions. | Added one Playwright regression at 320/1280px using mocked synthetic read-only responses; no application changes. |
| P2: guided-demo presentation limitation | January 2026 fixtures intentionally produce empty recent-window insights; contacts, wellness, early symptoms and feedback are empty. A long mobile navigation list and empty states can dominate a five-minute tour. | Start with the fixed-date guide, explain missingness, and use the timed walkthrough. Do not fabricate recent observations or forecasts. Existing documentation already discloses fixture limits. |
| P2: login emergency target — resolved in automated checks | The original 19px inline target is now a scoped 48px-high padded link. Its `tel:112` destination, text, native link semantics, visible focus, colors and responsive layout are preserved. | User-approved CSS fix, three parameterized browser regressions / 12 theme-mode-width variants. No live telephone handler was invoked; physical-device comfort remains manual. |
| P2: support-route focus — resolved in automated checks | Explicit route intent now prevents the Attack Mode return-focus effect from overriding destination-heading focus. Contact setup and caregiver edit, including same-page revisits, pass new unit/browser checks. | Ordinary exits still restore the entry control; contact and episode modal exits restore their connected opener. Human screen-reader/context-change review remains required. |
| P2: supply-chain / maintenance limitation | Locks pin app packages but Python locks have no artifact hashes. CI actions use commit SHAs and read-only permissions; Python/Node minor selectors can resolve to newer patch versions. Advisory scans do not cover every runtime/OS/browser component. | Review runtime patch policy and scan dependencies at each release; do not interpret lock reproducibility as complete supply-chain assurance. No dependency changes made. |
| P3: optional copy polish | `frontend/src/SupportCard.tsx` renders the literal separator `Caregiver guide ? saved personal preferences`. This looks like a copy/encoding defect but does not change support behavior. | Defer a copy-only product change for approval; this phase permits tests/documentation only. |

## Inspection and changes

Reviewed README quickstart, backend requirements/locks and environment templates; `security.py`, `auth.py`, demo/deployment/startup guards; Vite, package scripts/lock, both Playwright configurations and all browser suites; CI, operations, security, research, portfolio and release documentation. Test fixtures use new in-memory or temporary SQLite targets. The CI browser harness checks free ports, migrates only its new temporary target, verifies its own server logs plus HTTP 200, disables loopback proxy use and stops its child processes in `finally`.

Isolation is an operator responsibility outside the harness: `load_dotenv()` and the development fallback `sqlite:///./migramind.db` can select an existing local database if settings are omitted. Always set the temporary `DATABASE_URL` explicitly before migrations/startup; a demo-like filename or a read-only UI alone is not proof of fictional provenance. Never copy existing `.env` files into the audit copy. `VITE_*` values are public build inputs, so must never contain secrets.

The initial audit's test/documentation changes were:

- `frontend/e2e/product-quality.pw.ts`: traverse every workspace destination with keyboard Enter at 320/1280px, assert current navigation state, one main landmark, focused heading with visible outline, a bounded visible-control-name heuristic, no page overflow and no writes. This is not a complete accessible-name implementation or an unmocked CRUD journey.
- This report and a README link to it. Historical sprint reports remain historical; their old counts are not current results.

The later approved accessibility follow-up adds only scoped login-link styling, navigation/return-focus handling and focused regressions, described below. No unrelated functionality, emergency number, SOS workflow, production configuration, migration, dependency lock, credential or existing database change is included. No commit, push, PR, merge, deployment or provisioning against a pre-existing user-data target is performed.

## Validation evidence

### Current Windows candidate

Local host: Windows, Python **3.13.11**, Node **22.17.1**. The npm wrapper reports **11.5.1**; the explicit Node/npm CLI path used by this phase's verifier reports **10.9.2**. A tracked-source copy (including the changed test) was created in a new system temporary directory; ignored databases, `.env`, environments and `node_modules` were not copied. This is testing **on the same machine**, not another-machine testing. Existing installed Chrome is used for local Playwright; GitHub uses the locked Playwright Chromium download.

The initial sandboxed pip attempt failed with `WinError 10013` (network access blocked), not a dependency-resolution verdict. An approved new-copy attempt with pip cache disabled failed after 537.7s with `ConnectionResetError(10054)` while downloading SciPy. A cache-permitted retry with a 120-second network timeout failed after 516.3s: DNS resolution errors while resuming that download, ending in a Windows `WinError 32` file-lock error. None is counted as a successful Python installation. **A complete fresh Windows Python/ML install was not reproduced in that initial audit.** The [fresh-install follow-up](#fresh-windows-install-investigation) below records the subsequent investigation separately; these initial failures remain historical facts.

The remaining Python checks in the **initial audit** used the existing environment, whose installed versions exactly match all **35 base / 42 ML pins**. The frontend used a successful fresh `npm ci` with a new cache in the isolated copy. All databases used by tests/startup remain new and disposable regardless of dependency-environment provenance. The subsequent new-environment results are recorded separately below.

The first fallback backend run reported **240 passed, 14 setup errors**, one warning: `PermissionError [WinError 5]` opening the shared `%TEMP%/pytest-of-srish` directory. No assertion failure was reported in that run. A rerun uses a uniquely named, previously nonexistent `--basetemp` beneath this audit's new directory; no shared directory was deleted or permissions changed. The reproduction commands also select a new pytest target. Never reuse `--basetemp` for a directory containing wanted files: pytest owns/clears that target.

| Check | Initial audit result and execution boundary (follow-up below) |
| --- | --- |
| Fresh source / dependencies | Fresh venv creation passed; full Python installation **incomplete** for the transport reasons above. Fresh `npm ci` passed in 137.1s. |
| Backend / offline ML | **254 passed**, zero failed/skipped, one existing Starlette/httpx deprecation warning, 305.95s on rerun; existing matching Python environment, isolated source and new pytest root |
| Python compatibility / lock comparison | `pip check` passed; installed metadata matches all 35 base and 42 ML pins; no dependencies installed into the existing environment |
| Readiness regressions | **4 passed** using `python -m unittest discover -s scripts -p test_ci_browser.py -v` |
| Frontend unit tests | **80 passed / 14 files**, 85.07s; fresh npm installation |
| Production builds | Both TypeScript/Vite `local` and `synthetic` builds passed (command wall times 15.2s / 14.7s) in the temporary source copy |
| Candidate standard browser suite | **22 passed**, 2.0m, including added all-destination keyboard/label/focus test; `scripts/ci_browser.py --api-port 18001 --frontend-port 15174`, existing matching Python environment, fresh npm installation, new editable SQLite, Chrome **156.0.8078.79**; forced ANSI Vite logs also passed readiness |
| Built synthetic demonstration | Fresh dedicated SQLite migrations, fictional fixture initialization and `app.serve --check` passed. Reinitialization exited 1 as expected, with the fresh fixture database's SHA-256 unchanged. API/direct and proxied `/api/ready` and frontend root returned 200. **3 browser tests passed**, 21.9s, against `app.serve` + built Vite preview at 18015/15185. |
| Dependency advisories | `npm audit --json`: zero vulnerabilities, exit 0. OSV batch query: **42 pinned Python packages**, zero known advisory entries; package metadata only was submitted. Does not scan OS/runtime/browser or prove package authenticity. |
| Documentation / diff | README + this report: **30 relative file targets exist**; external sites and every Markdown fragment were not exhaustively checked. `git diff --check` passed; tracked change scope is README, this report and one browser test. No migrations, locks, configuration, existing records or credentials are included. |
| Cleanup | Browser harness completed cleanup; demo wrapper's `finally` stopped both process trees. A final exclusive-bind check confirmed all four review ports (18001/15174/18015/15185) were free. No existing server was stopped. New synthetic log/database/screenshot artifacts remain in the task's temporary directory for review. |

The fixture check used an automatically generated private password passed only to child environments. The current interactive Windows `getpass` prompt was **not** retested; the previous portfolio review's interactive result is historical evidence, not a new pass. That initial Windows demo startup used the existing matching Python environment, so startup alone did not close the fresh Python installation gate. The separate follow-up below subsequently verified a new Python environment.

Private local artifacts: `%TEMP%/migramind-release-byqz3jsa/` (fresh source/npm, failed install logs, successful checks, new fixture and screenshots). `%TEMP%/migramind-release-2_u_ku5p/` contains the initial sandbox-denied attempt. Neither directory is an existing user-data source, a release artifact or a directory to reuse for real data. The one-off verification wrappers remain outside Git; reproducible checked-in commands and the existing harness are described below.

### Fresh Windows install investigation

Follow-up on the same Windows host, using a **new** `%TEMP%/migramind-install-investigation-lp7xirsl/` source copy, virtual environment, pip temporary directory and test root. No existing venv was installed into, upgraded, repaired or deleted. No user database, secret, migration, application configuration or dependency lock was changed. Only this report changes in the follow-up; the README/browser-test changes above predate it. No provisioning CLI, server startup or deployment was run.

#### Cause and evidence

This was **transport failure plus an installer cleanup defect**, not a demonstrated application dependency conflict:

1. The original commands were `python -m pip install -r requirements-ml.lock.txt` with `PIP_NO_CACHE_DIR=1`, then the same unchanged lock with `--timeout 120` and `PIP_NO_CACHE_DIR=false`, inside the former disposable copy. Neither command bounded total execution or pip's separate resume attempts. Logs show compatible-wheel selection and download, then a reset or DNS errors; no resolver conflict, compiler failure or application import failure was reported.
2. The earlier `WinError 10013` was a sandbox socket-access denial. The other logs establish `ConnectionResetError(10054)` and `getaddrinfo` error 11001 during package transport. They do not identify the specific remote server, DNS service, proxy, firewall or other component responsible; no such component is blamed without evidence.
3. Both the preserved failed temporary environment and the fresh environment use **pip 25.3**, with byte-identical `pip/_internal/network/download.py` (SHA-256 `1e0b05bd390f0dd820d3351e868b1efc9fb9e36fbd474169ca2a51c39061c403`). Its incomplete-download path calls `os.remove()` while the enclosing writer is still open. That can mask the intended incomplete-download exception with Windows sharing violation 32. The same control flow is visible in the [upstream pip 25.3 source](https://github.com/pypa/pip/blob/25.3/src/pip/_internal/network/download.py#L171-L232).
4. A deterministic **zero-network** probe invoked that installed cleanup path with one simulated failed resume and a new one-byte file held open by the same process. It raised `PermissionError`, errno 13, **winerror 32**; after closing the handle, renaming and reading the file succeeded. No unrelated process or antivirus lock is needed to reproduce the symptom. This establishes the cleanup mechanism, not the origin of the earlier network interruption. Pip itself was not patched or upgraded.
5. Fresh probes resolved `pypi.org` and `files.pythonhosted.org`; official SciPy 1.18.1 metadata returned 200 and listed `scipy-1.18.1-cp313-cp313-win_amd64.whl` (36,622,841 bytes, Python `>=3.12`). A 1,024-byte range request returned **206** and a ZIP signature. Writing, flushing, renaming and reading a new 65,536-byte file in the private temporary directory passed. These point-in-time checks do not prove permanent network reliability or an absence of all external locks.
6. Both locks contain only exact package pins; all **35 base pins** are an identical subset of the **42 ML pins**. No repository pip configuration, custom-index directive, editable dependency or source-build requirement was found. The controlled install used official HTTPS PyPI, binary wheels, no cache, ignored pip configuration and no inherited pip/Python option overrides. TLS verification remained enabled.

#### Bounded attempt and results

The approved process resolved `python` to `C:/Users/srish/.jupyter/.ipynb/python.exe`, **Python 3.13.12 x64**, rather than the earlier Miniconda **3.13.11**. This satisfies the documented Python 3.13 family but is **not an exact patch/interpreter rerun** of the original attempt or another-machine test. The fresh venv has system-site packages disabled. The installer is its newly seeded pip 25.3, not the application's existing venv.

| Check | Follow-up result |
| --- | --- |
| Network / private file probes | Passed, 1.75s; no diagnostic retry loop; hard cap 75s |
| New venv / installer version | Created in 19.10s; pip 25.3 confirmed; venv creation cap 90s |
| ML lock installation | **Exit 0**, 357.79s; all 42 packages installed into the new venv; hard cap **600s** |
| Artifact / lock integrity | The install report lists 42 artifacts, all from `files.pythonhosted.org`; the downloaded SciPy SHA-256 matches official metadata (`559ed65f60c1af5a03f3912605a1b5114f522c7c32fb23c3376ae8f03219fe28`). Both repository lock hashes still match the source-copy baseline. This is a provenance check, not a general package-security claim. |
| Retry policy | Socket timeout **20s**, `--retries 1`, `--resume-retries 0`; **one** ML install invocation, no outer install retries; base-only fallback was not needed |
| Compatibility | `pip check`: exit 0, 5.21s |
| Pins / imports | Exit 0, 44.81s: all 42 installed versions match the unchanged ML lock, including all 35 base pins; 17 runtime/ML module imports originate inside the new venv; `app.main` imports from the new source copy with `DATABASE_URL=sqlite://`; no existing database is opened |
| Backend suite in the new venv | **254 passed**, zero failed/skipped, **one existing Starlette/httpx deprecation warning**, **290.85s** pytest duration (296.52s command wall time); exit 0, no timeout; hard cap **900s** |
| Pip cleanup probe | Expected `WinError 32` reproduced with zero network requests; closing the owned handle allowed rename/read; no existing files deleted |

The 17 third-party imports were `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `psycopg`, `pydantic`, `httpx`, `pytest`, `argon2`, `tzdata`, `numpy`, `scipy`, `sklearn`, `joblib`, `cloudpickle`, `narwhals` and `threadpoolctl`. Installation writes, caches and logs stayed within the new target. `PYTHONDONTWRITEBYTECODE=1`, a private `TEMP`/`TMP`, explicit in-memory application URL and a previously nonexistent pytest base directory isolated verification. Existing backend fixture tests create only fictional, disposable data.

Disabling resumes bounds work; it is **not a fix for pip's open-handle cleanup defect**. A fresh directory likewise does not cure a network outage. A successful complete download simply avoids that error path. No timeout was used to conceal a failed test, and no dependency pins were changed to make installation pass.

#### Exact commands and safe reproduction

Actual command shapes, run from the new source copy, with `<fresh-python>` equal to the **new** `ml-venv/Scripts/python.exe` and `<source>` its new `source` directory:

```text
<base-python> -I -m venv <new-root>/ml-venv
<fresh-python> -I -m pip --version
<fresh-python> -I -m pip --isolated --disable-pip-version-check --no-input --no-cache-dir install --index-url https://pypi.org/simple --only-binary=:all: --timeout 20 --retries 1 --resume-retries 0 -r <source>/backend/requirements-ml.lock.txt --report <new-root>/ml-install-report.json
<fresh-python> -I -m pip check
<fresh-python> -I <new-root>/verify.py <new-root>/ml-venv <source>/backend/requirements-ml.lock.txt <source>/backend
<fresh-python> -m pytest -q -ra --basetemp <new-root>/pytest-<new-uuid>
<fresh-python> -I -B %TEMP%/migramind-pip-lock-probe.py <new-root>
```

The verification wrapper set `PIP_CONFIG_FILE=NUL`, removed inherited `PIP_*`/`PYTHON*` options and `VIRTUAL_ENV` from **child environments only**, and set `APP_ENV=development`, `DATA_MODE=local`, `DATABASE_URL=sqlite://`. No persistent environment setting was edited. Download/unpack `TEMP`/`TMP` pointed to `<new-root>/pip-temp`; test `TEMP`/`TMP` pointed to `<new-root>/runtime-temp`. Subprocesses had explicit wall-clock caps: install 600s, imports 90s and backend tests 900s. On timeout only the wrapper's own child tree would be terminated; no timeout occurred in these completed checks.

To reproduce without reusing an existing environment, run this bounded Windows scaffold from the repository root with a Python 3.13 interpreter. It creates a tracked-source copy only; it never copies ignored `.env`, venv or database files. The final assertion requires all 42 pin checks and verifies the imports in that new environment. Test output goes to private logs; check the printed path/results before drawing conclusions.

```powershell
@'
from pathlib import Path
import os, sys, tempfile, subprocess, shutil, uuid
repo = Path.cwd()
root = Path(tempfile.mkdtemp(prefix="migramind-install-recheck-"))
source = root / "source"
source.mkdir()
for name in filter(None, subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")):
    original = repo / name
    if original.is_file():
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, target)
assert not list(source.rglob(".env")) and not list(source.rglob("*.db")) and not list(source.rglob("*.sqlite"))
scratch = root / "scratch"
scratch.mkdir()
env = {k: v for k, v in os.environ.items()
       if not k.upper().startswith(("PIP_", "PYTHON")) and k.upper() != "VIRTUAL_ENV"}
env.update(PIP_CONFIG_FILE=os.devnull, TEMP=str(scratch), TMP=str(scratch),
           PYTHONDONTWRITEBYTECODE="1", APP_ENV="development", DATA_MODE="local", DATABASE_URL="sqlite://")
print("New target:", root, "Base:", sys.executable, sys.version, flush=True)
def run(label, args, cwd, seconds):
    with (root / (label + ".log")).open("w", encoding="utf-8") as log:
        child = subprocess.Popen([str(a) for a in args], cwd=cwd, env=env,
                                 stdout=log, stderr=subprocess.STDOUT,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            code = child.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           check=False, timeout=20)
            child.wait(timeout=20)
            raise
    print(label, "exit", code, flush=True)
    assert code == 0, str(root / (label + ".log"))
venv = root / "ml-venv"
run("venv", [sys.executable, "-I", "-m", "venv", venv], root, 90)
python = venv / "Scripts/python.exe"
lock = source / "backend/requirements-ml.lock.txt"
run("install", [python, "-I", "-m", "pip", "--isolated", "--disable-pip-version-check",
    "--no-input", "--no-cache-dir", "install", "--index-url", "https://pypi.org/simple",
    "--only-binary=:all:", "--timeout", "20", "--retries", "1", "--resume-retries", "0",
    "-r", lock, "--report", root / "install-report.json"], source, 600)
run("pip-check", [python, "-I", "-m", "pip", "check"], source, 60)
verify = root / "verify.py"
verify.write_text("""from pathlib import Path
from importlib.metadata import version
import importlib, sys
venv, lock, backend = map(Path, sys.argv[1:])
pins = [s.split('==') for s in lock.read_text(encoding='utf-8-sig').splitlines() if s.strip() and not s.startswith('#')]
assert len(pins) == 42 and all(version(n) == v for n, v in pins)
assert Path(sys.prefix).resolve() == venv.resolve() and sys.prefix != sys.base_prefix
for name in ['fastapi','uvicorn','sqlalchemy','alembic','psycopg','pydantic','httpx','pytest','argon2','tzdata','numpy','scipy','sklearn','joblib','cloudpickle','narwhals','threadpoolctl']:
    module = importlib.import_module(name)
    assert Path(module.__file__).resolve().is_relative_to(venv.resolve())
sys.path.insert(0, str(backend))
import app.main
assert Path(app.main.__file__).resolve().is_relative_to(backend.resolve())
assert app.main.security.database_url == 'sqlite://'
print('42 pins, 17 third-party imports, isolated app.main import passed')
""", encoding="utf-8")
run("imports", [python, "-I", verify, venv, lock, source / "backend"], source, 90)
testroot = root / ("pytest-" + uuid.uuid4().hex)
assert not testroot.exists()
run("backend", [python, "-m", "pytest", "-q", "-ra", "--basetemp", testroot], source / "backend", 900)
'@ | python -I -
if ($LASTEXITCODE) { throw 'Check the new target logs; verification did not complete' }
```

This scaffold uses one private scratch directory for pip/test temporary files; the executed investigation used separate private directories. Both keep all test data outside existing installations. The installer options bound request retries; the wrapper supplies the separate total deadline. Keep logs if a transfer fails again; do not clear shared temp directories, disable antivirus/TLS, reuse a partially installed venv or alter locks based solely on a transport error.

Logs and machine-readable evidence for the executed investigation are outside Git under `%TEMP%/migramind-install-investigation-lp7xirsl/`: `results.json`, `network-and-file-probes.log`, `install-ml.log`, `ml-install-report.json`, `pip-check.log`, `pins-and-imports.log`, `backend-tests.log`, `pip-lock-probe.json` and `artifact-check.json`. The temporary investigation/probe wrappers also remain outside Git. The probe creates its own previously nonexistent file and refuses to reuse its output names; use a new probe directory when repeating it. The reproduction scaffold was syntax-checked, not executed a second time. Remaining limits: same Windows host only; the exact original 3.13.11 interpreter was not retried; the source of the earlier resets/DNS failures is unidentified; pip's interrupted-download cleanup issue remains present; Linux desktop, hosting and the accessibility/governance gates below are unchanged. Earlier frontend/browser results were not rerun or newly claimed in this follow-up.

### Rendered visual review

Playwright captured all 12 workspace destinations at **1280px and 390px**, plus desktop login, mobile Attack Mode, SOS and dark settings: **28 views**, zero recorded page errors and zero overflow flags for the 24 workspace views. The agent inspected eight contact sheets covering those 24 actual screenshots and the four additional images with the image viewer. Captures are synthetic and ignored at `.research/release-readiness/`; originals/logs are also in the task's system temporary directory. No patient data is pictured.

Warm/dark appearance, screen hierarchy, the fixed January calendar, read-only notes and empty-state explanations were visible without a confirmed layout-blocking defect in these views. The mobile navigation and repeated guide push content far down the page; caregiver preferences and sparse insights are particularly long. The login emergency target and caregiver separator follow-ups are prioritized above. This is agent visual inspection of automatically rendered images, **not human manual browser interaction**, screen-reader testing, a colorimeter/whole-page contrast audit or a physical-device comfort assessment. No call, SMS, clipboard/share or location action was activated during visual capture (browser tests separately use mocked device APIs).

### Independently inspected Ubuntu CI

Read-only GitHub API and downloaded job logs confirm [PR #17 CI](https://github.com/srishti997/MigraMind/actions/runs/42604412009) at `1b95c38d0c0d607f9de3c96d992576d16141dbaa` and [main merge CI](https://github.com/srishti997/MigraMind/actions/runs/42605010506) at `87ca919db30c5a5675d0888833d4e66355e5a855` completed successfully. Merge-job logs report:

| Check | Actual Ubuntu result |
| --- | --- |
| Backend / offline ML | 254 passed, one warning, 45.26s; `pip check` passed |
| Frontend | 80 passed in 14 files |
| Both production bundles | local and synthetic build steps succeeded |
| Readiness regressions | 4 tests passed |
| Disposable editable Chromium suite | 21 passed, 52.5s |
| Runtime | Ubuntu 24.04.5, Python 3.13.18, Node 22.23.4, npm 10.9.9 |

Those runs precede this phase's added test. They verify Linux dependency installation, test/build execution and loopback backend/Vite startup in ephemeral CI, with dependency caches permitted. They do **not** verify a manually installed Linux desktop, a provisioned Linux synthetic demo, public hosting or this uncommitted test on GitHub. No workflow was triggered by this review.

## Workflow coverage and boundaries

| Requested workflow | Existing evidence exercised | Limits |
| --- | --- | --- |
| Authentication | `test_auth.py`, `authentication.pw.ts`, `security.pw.ts`: real isolated API registration/login, two-account isolation, stale tabs, CSRF/Origin, logout, consent and deletion | Fictional accounts only; no recovery/MFA or external identity provider |
| Daily status | `test_prospective.py`, `prospective.pw.ts`: keyboard report, revision conflicts/history, tombstones, research quality | No actual participant or prospective outcome verification |
| Migraine diary | `test_api.py`, `test_audit_remediation.py`; `tracking.pw.ts`, `patterns.pw.ts`: strict validation, historical preservation, timestamps/DST, optional values | Browser form CRUD is mocked; backend CRUD/validation uses isolated real SQLite |
| Calendar | `tracking.pw.ts`, `product-quality.pw.ts`: month/day selection, unknown vs recorded days, three timezone boundaries; dedicated demo fixture navigation | Not an exhaustive locale/timezone matrix |
| Insights | `test_pattern_insights.py`, `patterns.pw.ts`; built-demo summary/pattern failure and retry checks | Mocked supported/sparse cases plus real synthetic empty-window responses; no clinical inference |
| Wellness / early symptoms | `test_api.py` CRUD, unknown/zero and timezone checks; `tracking.pw.ts` form save/edit/delete and export | Browser API mocked; no longitudinal real-user study |
| Trusted contacts | Backend ownership/phone validation and CRUD; assistance/support browser safe-link checks | No actual phone call, SMS, delivery or emergency-system interaction |
| Caregiver profile | Backend account isolation/persistence; `support.pw.ts` preference save/reload; demo disabled-save checks | Browser editable preferences mocked; no caregiver identity/authorization workflow |
| Support feedback | `test_api.py`, `test_support.py`, `support.pw.ts`: optional feedback lifecycle, active-session suppression, explicit opt-in ordering | Browser API/share/clipboard mocked; deterministic support ordering is not clinical effectiveness |
| Partial failures / exports | Existing frontend tests and demo suite retry checks, account-change guards, consent/download and blocked writes | No network chaos campaign or third-party delivery verification |

The standard browser suite mixes real-API and mocked tests as identified above. A green browser count must not be described as end-to-end persistence coverage of every screen.

## Accessibility audit

| Area | Automated / source evidence | Manual work remaining |
| --- | --- | --- |
| Keyboard and focus | Skip link, Enter navigation, page/research destination focus, modal focus trap/Escape/return, Attack Mode entry/exit; added all-destination check. CSS supplies 3px `:focus-visible` outlines. | Natural sequential Tab/Shift+Tab order across every populated form, validation/retry and disclosure; Space activation beyond existing research-tour checks; focus visibility under forced colors/zoom |
| Labels / semantics | Role-based locators, main/navigation landmarks, field labels, modal semantics; existing and new bounded control-name checks | Screen-reader names, reading order, status/error announcements, SVG semantics and all dynamic states with NVDA/VoiceOver |
| Contrast | Existing test calculates three semantic text/background token pairs in warm and dark themes against 4.5:1 | All actual text, disabled controls, borders, selected days, focus rings and non-text contrast; token checks are not whole-page contrast measurement |
| Motion / size | CSS `prefers-reduced-motion` and saved preference; existing browser assertions for no animation/transition, larger-text/simplified support and emergency visibility | Vestibular/photophobia comfort, OS settings, zoom/reflow at 200–400%, text spacing and large-font device settings |
| Responsive layout | Browser overflow assertions at 320/390/768/1280px across existing suites; built-demo all-screen checks at 320/768/1280px | Real phones/tablets, landscape, mobile keyboards, touch accuracy, longer/localized data and alternate browser engines |

No dedicated automated accessibility engine was found in package scripts or the lock. No accessibility certification, human screen-reader pass or physical-device pass is claimed. The earlier screenshot review is agent visual inspection of Playwright-rendered images, separate from these manual tasks. The PR #18 checks below add bounded login/emergency evidence, not accessibility certification.

### PR #18 emergency navigation and accessibility review

This section records the **pre-approval review**, before the two fixes below. Scope: `test/release-readiness`, same Windows host, preserved working tree. Only the report changed during that review. The earlier README/browser-test edits remained intact. The successful fresh Windows Python **3.13.12** installation, **42 verified pins** and **254 passing backend tests** are separate evidence above; they were not rerun or replaced by the frontend reviews. The exact earlier 3.13.11 interpreter, unexplained historical transport interruptions and pip 25.3 incomplete-download cleanup defect remain limitations. Source line references and 19px/focus observations in this historical section describe the pre-fix snapshot.

#### Exact destinations and intended behavior

| Entry / source | Destination and behavior | Semantics, safety and verification boundary |
| --- | --- | --- |
| Login / registration / connection-error page, [Authentication.tsx](../frontend/src/Authentication.tsx#L26) | Literal **`tel:112`**, including before authentication and when bootstrap fails. No HTTP redirect, application help route, `target` or click handler is attached. | Native `<a href>` outside the form; accessible name **Emergency call · 112 (India)**. Nearby wording identifies India, says the user initiates the call and nothing is dispatched automatically, and disclaims medical-device/monitored-service status. Natural Tab/Enter and intercepted pointer activation are checked below. |
| Attack Mode emergency action, [AttackMode.tsx](../frontend/src/AttackMode.tsx#L16) | **`tel:<saved-number>`** for a known preference matching 2–6 ASCII digits; otherwise **`tel:112`**. Fixtures confirmed `112`, saved `999`, malformed-value fallback and unavailable-preference fallback. | Native link with large target; remains independent of session/contacts/recommendation availability. Labels distinguish India/default from saved number; unavailable-preference copy asks the user to confirm the local number. This syntax guard does not verify regional correctness or reachability. |
| **SOS / Get help**, [AttackMode.tsx](../frontend/src/AttackMode.tsx#L29) | Opens inline `#help-request`; **does not call or navigate to an external site**. | Native button with `aria-expanded`/`aria-controls`; focuses the SOS heading. Close returns focus to the SOS button. It is not an emergency-dispatch button or a modal requiring its own tab trap. |
| Trusted-contact calls and SMS, [SOSMessage.tsx](../frontend/src/SOSMessage.tsx#L37), [assistance.ts](../frontend/src/assistance.ts#L17) | `tel:<normalized-contact-number>` and `sms:<normalized-number>?body=<encoded-message>`; iOS uses `&body=`. The directory's call actions use the same number guard. | Malformed values cannot produce web/script URI schemes; number formatting is syntax-only. Opening a composer is not sending a message. Text/location requires explicit preparation; no delivery/monitoring guarantee. No contact call/SMS was actually handed off during review. |
| **Emergency guidance → Guidance sources**, [AttackMode.tsx](../frontend/src/AttackMode.tsx#L39) | **`https://112.gov.in/`** and **`https://www.nhs.uk/symptoms/headaches/`**, each with `target="_blank"`, `rel="noreferrer"`. These are information links, not telephone actions. | Native disclosures and links; no health values, tokens or query parameters are embedded. `noreferrer` requests referrer suppression and opener isolation under browser semantics. The labels do not explicitly warn about a new tab; optional copy/accessibility follow-up, not a demonstrated destination defect. External responses/redirects/content were not exercised or clinically reviewed here. |
| **View caregiver guide / My support card** | Opens saved-preference disclosure within Attack Mode and focuses its summary; does not send data. | Source and existing SOS tests cover summary focus; sharing remains a separate explicit review/copy/share action. |
| **Set up a trusted contact / Review or edit outside Attack Mode**, [main.tsx](../frontend/src/main.tsx#L82) | Leaves Attack Mode for **Trusted contacts** / **Caregiver profile** inside the workspace. No external navigation or automatic persistence. | Destination renders, but the focused-probe finding below shows header focus overriding destination-heading focus. |
| **Exit Attack Mode / Log an episode / Review support feedback** | Exit returns to the workspace and its entry control; diary action opens the existing form (or read-only notice in demo mode); optional post-session feedback opens its workspace page. | Leaving the view does not end an active session. Starting/ending sessions and saving forms are separate explicit API writes in editable mode; no such operation is necessary to follow an emergency link. Existing mocked tests cover exit/modal/feedback flows. |

A `tel:` URI requests the browser/device's registered calling handler. It may open a dialer, app chooser or web-based handler, or initiate a call, depending on the platform; an additional confirmation screen is **not guaranteed**. The app does not automatically activate it on load. See [MDN telephone-link behavior](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/a#linking_to_telephone_numbers) and [noreferrer semantics](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/noreferrer). Do not infer successful OS handoff, call completion or emergency-service contact from DOM assertions.

#### Historical findings and proposals before approval

| Priority | Exact file / evidence / impact | Minimal proposed correction requiring approval |
| --- | --- | --- |
| P2: login emergency target | [Authentication.tsx:26](../frontend/src/Authentication.tsx#L26), [style.css:202](../frontend/src/style.css#L202), [style.css:393](../frontend/src/style.css#L393): the link is `display:inline`, measured **19px high**, whereas neighboring authentication buttons have a 48px minimum height. Keyboard semantics and focus work, but the small target is harder to use with touch/motor difficulty during urgency. This is a usability finding, **not a declared WCAG target-size failure**; spacing/exceptions/full conformance were not audited. | Add a narrowly scoped `.auth-panel .emergency-action` style with inline-flex alignment, padding and a 48px minimum height matching neighboring controls; keep `href="tel:112"`, link semantics and India/no-dispatch wording. Add a login target-size/focus regression. No URL or clinical-content change is proposed. |
| P2: emergency-support route focus | [main.tsx:34](../frontend/src/main.tsx#L34), [main.tsx:53](../frontend/src/main.tsx#L53), [main.tsx:82](../frontend/src/main.tsx#L82): keyboard activation of contact setup and caregiver edit displays the right destination, but `document.activeElement` is **Enter Attack Mode**, not its `<h1>`. The page-heading effect runs before the unconditional Attack Mode return-focus effect, which overrides it. A screen-reader/keyboard user can miss the destination change and must traverse header controls again. Emergency dialing itself remains available. | Distinguish explicit **Exit Attack Mode** return focus from navigation to another destination. Keep entry-button focus for ordinary exit; focus the destination heading for contact/profile handoffs, including revisiting the same destination. Add regression assertions for both handoffs and retain existing exit/modal focus assertions. |
| P3: optional external-link announcement | `AttackMode.tsx:39`: guidance links explicitly request a new tab but their accessible labels do not say so. Browser behavior/assistive-technology announcement remains a manual check. | Consider visible “opens in a new tab” text or an associated description without changing destinations or `rel`; seek approval before product copy changes. |

No incorrect `http:` destination, `javascript:` injection or automatic dialing was confirmed for the login emergency action. The small target and route-focus defect were recorded for approval, then fixed only after the user's subsequent explicit authorization, as documented below. Existing source disclaimers and emergency destinations are retained.

#### Non-destructive checks in this review

Checks use a new `%TEMP%/migramind-emergency-review-kjhyxvex/` tracked-source copy with a **copy of the previously locked npm installation**; dependency lock hashes matched before reuse. This is not a new npm-install claim. Only a loopback Vite server was started at **15381**, with an unused discard-port API proxy and **all browser API requests mocked**. No backend, database, migration or provisioning command was run. Fake writes in existing unit/support browser tests affect fixture memory only.

The focused probe installs a capture-phase guard that prevents default telephone/SMS/external-HTTP activation **before** keyboard or pointer events can invoke their native handlers. Out-of-origin HTTP requests are also blocked. This safety interception is confined to the temporary review harness, not product code. It validates event reachability/destination, not a real dialer, new tab, clipboard, geolocation or service delivery. Existing SOS/support tests separately mock device APIs.

| Check | Result / limits |
| --- | --- |
| Frontend unit suite | **80 passed / 14 files**, 168.25s (173.35s command wall time), using `node node_modules/vitest/vitest.mjs run --maxWorkers=1` |
| Existing mocked browser subset | Initial invocation: **11 passed, 1 failed**, 1.2m (73.44s command wall time). The responsive assistance test exhausted its unchanged **30s total test budget** while querying the SMS link's bounding box; that link is present in the failure snapshot, and no layout assertion failed. A **single unchanged rerun at the same 30s limit passed**, 4.4s test / 5.6s suite duration (6.45s command wall time). All 12 selected scenarios therefore have passing executions, but the initial group was **not a clean pass**; cause of that transient timeout is not isolated. No timeout increase, assertion relaxation or product/test-source change was applied. |
| Focused login probe | **12 variants**: 320/390/1280px × warm/dark × anonymous local/server-attested-synthetic modes. Each has literal `tel:112`, native link semantics outside the form, natural Tab reachability, Enter and pointer activation captured before default, a solid **3px** focus ring, **7.492:1** computed emergency text/background contrast, **19px** target height, and no horizontal overflow. Visibility was checked **after keyboard focus**, not as a universal initial-viewport guarantee. Separate failed-bootstrap fixture retained the emergency link. The earlier six-variant probe is retained separately. |
| Focused Attack Mode / SOS / source links | Four fixtures confirmed `tel:112`, saved `tel:999`, malformed-preference fallback and unavailable-preference fallback, plus heading → Exit → emergency Tab order. Emergency targets measured **105–127.5px** high at 320px. SOS heading/close-return focus and guidance href/target/rel checks passed. Confirmation captured/prevented **36** telephone/external-link activations across login and Attack Mode; zero actual external request attempts, zero mutation requests and zero page errors in that probe. No native handoff/new-tab behavior is claimed. |
| Route-focus observation | Both contact setup and caregiver edit render the right page but leave focus on **Enter Attack Mode**; this is a confirmed unresolved finding, not an accessibility pass |
| Isolation / preservation / cleanup | All tracked source-file SHA-256 values matched the pre-review baseline, including the existing README/browser-test work, locks, migrations and configuration. Only the untracked review report was intentionally updated. Vite process-tree cleanup completed, and an exclusive-bind check confirmed port 15381 free. Temporary logs/screenshots remain for review; no database or existing server was used. |

The selected checked-in browser files are `assistance.pw.ts`, `sos.pw.ts`, `support.pw.ts` and `product-quality.pw.ts`. Commands run from the disposable `source/frontend`:

```text
node node_modules/vitest/vitest.mjs run --maxWorkers=1
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 15381 --strictPort
node node_modules/@playwright/test/cli.js test e2e/assistance.pw.ts e2e/sos.pw.ts e2e/support.pw.ts e2e/product-quality.pw.ts --config playwright.config.mjs --output <new-root>/browser-results
node node_modules/@playwright/test/cli.js test e2e/assistance.pw.ts --grep "responsive pages and attack assistance avoid horizontal overflow" --config playwright.config.mjs --output <new-root>/browser-rerun
```

The Node probe and lifecycle wrappers remain temporary; `frontend-unit.log`, `mocked-browser.log`, `responsive-rerun.log`, `emergency-probe-confirmation.json`, `results.json` and the source-hash baseline are retained outside Git under the path above. The first probe's `width` field describes element width; the confirmation separately records `viewportWidth`, eliminating that logging ambiguity without changing product code. The agent visually inspected warm/dark synthetic login and caregiver-route focus screenshots at 320px; this is **not human keyboard/screen-reader testing**. No native emergency number was activated, and no external guidance page was opened. The earlier full **22 browser / 3 built-demo / 4 readiness-regression** results remain earlier evidence; this review does not claim those complete suites were rerun.

#### Manual verification gates still open

- **Keyboard-only:** human Tab/Shift+Tab traversal from login through error/retry, registration, every populated form and disclosure; native links activate with **Enter**, buttons also with **Space**. Check that no required control needs a mouse, no focus is obscured, and escape/return works without accidental activation. Automated `.focus()` followed by Enter does not establish natural tab order everywhere.
- **Screen readers:** NVDA with intended Windows browser, and VoiceOver/Safari if supported; landmarks, heading order, labels, SVG announcements, field errors, loading/status announcements, `aria-expanded`, SOS/support-card reading order and new-tab expectations. Browser role locators and control-name heuristics are not screen-reader testing.
- **Focus management:** the support-route issue is now fixed in automated checks below; human inspection still covers login/logout, session expiry, validation failure, retry, modal close, Attack Mode entry/exit, SOS open/close, guide transitions, research navigation and any new-tab return. Preserve visible focus under zoom and forced-color settings.
- **Contrast and resizing:** inspect all rendered text, borders, icons, disabled/selected states and focus rings in warm, dark and Attack Mode, not only three token pairs or the emergency text pair. Test 200–400% zoom, text spacing, large-font settings and reflow. No whole-application contrast or accessibility conformance pass is claimed.
- **Responsive / comfort:** real phones/tablets, landscape, software keyboards, longer content, touch-target spacing, migraine-time comfort and reduced-motion preferences; Firefox/WebKit and physical-device behavior remain untested here. The approved login target fix passes automated checks below; real-device comfort is still unverified.
- **Handler behavior and safety:** OS/registered `tel:`/`sms:` handling and source-link tab behavior remain unverified. Use a safely stubbed handler or an authorized non-emergency test arrangement; **never call 112 or another real emergency service for QA**. No simulated test establishes delivery, emergency response or clinical suitability.

These gates remain open for broad accessibility/release sign-off. A guided local synthetic demonstration must disclose its limitations; public hosting, real health data and clinical/research use remain blocked under the existing gates. The subsequent authorization covers only the two fixes below, not publication or deployment.

### Approved accessibility fixes and validation

The user explicitly approved the login target and destination/return-focus fixes on the existing branch. This follow-up changes exactly:

- `frontend/src/style.css`: a single `.auth-panel .emergency-action` rule adds inline-flex alignment, 48px minimum height, 12px/16px padding and the existing small-radius token. No font, palette, global emergency styling, number, text or href changes.
- `frontend/src/main.tsx`: records whether Attack Mode is handing off to a destination. Route handoffs focus the destination `<h1>` (main landmark fallback), including a revisit to the same page. Ordinary exits restore the connected entry control. Modal close restores its connected initiating control. The existing contact/profile/feedback navigation callbacks share this focus intent; their destinations, persistence and SOS behavior are unchanged. Focus is transition-driven, with no timer or trap.
- `frontend/src/AttackMode.test.tsx`: two parameterized unit cases exercise contact setup and caregiver edit, first and repeated same-page navigation, Tab away from the heading, ordinary Attack Mode exit, and contact-dialog Escape/return. Existing episode-dialog focus tests remain intact.
- `frontend/e2e/accessibility-fixes.pw.ts`: five browser regressions: three viewport cases cover 12 local/synthetic × warm/dark login variants; two cases cover both navigation flows, repeated destinations, ordinary exits and contact-dialog close. The login tests verify a native link, unchanged accessible name/href, at least 48px height, natural Tab/Enter, visible focus and no horizontal overflow. A capture listener prevents the real `tel:112` handler from opening during activation tests.
- `docs/RELEASE_READINESS.md`: current statuses, before/after evidence, actual failures/results and remaining manual gates. Existing `README.md` and `product-quality.pw.ts` work from earlier turns is preserved unchanged.

All execution used a new `%TEMP%/migramind-a11y-fixes-8dmhwlr9/` source/dependency copy. The previously locked npm dependency directory was copied; no packages were installed or locks updated. API responses are mocked, and the only server is disposable loopback Vite at 15382 with an unused API-proxy target. No backend, database, migration, provisioning, actual call, external guidance navigation or production service was used.

| Verification | Actual result |
| --- | --- |
| Regression sensitivity / before | All **5 new browser cases failed as expected** against the original `main.tsx`/`style.css` substituted only in the disposable copy: three measured **19px instead of ≥48px**, two found destination headings unfocused. This intentional negative control is not a flaky run or a failing final candidate. |
| Final frontend unit suite | **82 passed / 14 files**, zero failed/skipped, **41.38s** (42.16s command wall time), after correcting the test-query typing issue below |
| Candidate browser suite | **17 passed**, **25.8s** (26.83s wall time), first candidate invocation with default timeouts and no retries. Includes all 5 new cases and the existing 12 mocked assistance/SOS/support/product-quality scenarios. No browser failure or timeout in this candidate run. |
| Production builds | Both TypeScript/Vite builds passed: **local 8.09s** command wall time (Vite 2.82s); **synthetic 7.87s** (Vite 2.81s). Output stays in temporary local/synthetic directories. |
| Focused accessibility measurements / after | All **12 login variants measured 48px high**, with unchanged **7.492:1** emergency text/background contrast, unchanged native accessible name/`tel:112`, visible solid 3px focus and no horizontal overflow. Both contact/profile routes now have the correct destination **H1** as `document.activeElement`. |
| Safety / neighboring flows | Four emergency-number/default/fallback fixtures, SOS heading/close-return focus, source-link href/target/rel and existing exit/modal/feedback tests passed. The focused probe prevented **36** telephone/external activations, with zero actual external request attempts, zero API mutation requests and zero page errors. Existing support tests use in-memory mock writes/device APIs only. |
| Visual inspection | Agent inspected actual 320px warm/dark synthetic-login screenshots and caregiver destination focus: the padded control fits and heading focus is visible. This is screenshot inspection, not human screen-reader, touch or physical-device testing. |
| Cleanup / preservation | Vite process trees stopped; port 15382 was free after cleanup. Final source hashes matched the intended candidate, including unchanged backend, migrations, locks, production configuration and the earlier README/browser-test edits. Existing venvs and user data were not opened or modified. |

**Unexpected failure, corrected:** the first unit run passed 82 tests, but both initial production builds rejected three new unit-test queries with **TS2769**: `exact` is a Playwright option, not a Testing Library `ByRoleOptions` member. Removing that unsupported option preserves Testing Library's existing exact string-name matching. The entire 82-test unit suite and both production builds were rerun successfully against the corrected test source. Initial build logs are retained; this was a test typing mistake, not a product failure or dependency change. The browser-tested product/CSS/browser-regression bytes did not change during that correction.

**Flakiness record:** the preceding review's 30-second responsive-test timeout and its single unchanged successful rerun remain recorded above. It was not erased, converted to a clean batch pass or fixed by increasing timeouts. In the current candidate, that same responsive case passed as part of the 17-test batch without rerun; no new browser flakiness was observed. Expected negative-control failures and the corrected TypeScript errors are separately classified.

Commands, from the disposable copy's `frontend`, using the existing Node/npm CLI entry point:

```text
node node_modules/vitest/vitest.mjs run --maxWorkers=1
node <npm-cli.js> run build -- --outDir <new-root>/local-dist       # VITE_DATA_MODE=local
node <npm-cli.js> run build -- --outDir <new-root>/synthetic-dist   # VITE_DATA_MODE=synthetic
node node_modules/@playwright/test/cli.js test e2e/accessibility-fixes.pw.ts e2e/assistance.pw.ts e2e/sos.pw.ts e2e/support.pw.ts e2e/product-quality.pw.ts --config playwright.config.mjs --output <new-root>/browser-candidate
```

For the negative control, only the new browser file ran against pre-fix files in the temporary copy, then the candidate bytes were restored before all candidate checks. Logs include `browser-before-fix.log`, `browser-candidate.log`, `frontend-unit-final.log`, `build-local-final.log`, `build-synthetic-final.log`, `accessibility-probe.json`, initial build-error logs and final source hashes under the artifact directory above. Test/build command wall limits were bounded; none expired. No verification wrapper is committed.

These results close the two confirmed findings **within automated coverage**, not the manual accessibility gates. Human keyboard/screen-reader behavior, all rendered contrast states, forced colors, 200–400% zoom/reflow, real-device touch/comfort, alternate engines and safely controlled OS handler behavior remain outstanding. No axe/pa11y/Lighthouse engine was added or claimed. The prior fresh Python **254 backend / 42 pins**, full **22-browser / 3 built-demo / 4 readiness-regression** results remain earlier evidence; backend/data-dependent and complete browser suites were not rerun for these frontend-only changes. No clinical, public-hosting or production-readiness claim is introduced.

## Reproduce safely

Use a new source copy and fresh terminal. Never copy `.env` or a database from a working installation. Do not run mutation suites against a reused server. The browser harness refuses occupied ports and removes only its own temporary test database. The commands below do not apply migrations to an existing database or invoke destructive reset/downgrade tools. Stop on any failed command.

### Windows checks

From the repository root in PowerShell, create an archive of tracked HEAD; copy the candidate test explicitly until it is committed:

```powershell
$releaseRoot = Join-Path ([IO.Path]::GetTempPath()) ('migramind-release-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $releaseRoot | Out-Null
git archive --format=zip --output="$releaseRoot/source.zip" HEAD
if ($LASTEXITCODE) { throw 'Archive failed' }
Expand-Archive -LiteralPath "$releaseRoot/source.zip" -DestinationPath "$releaseRoot/source"
Copy-Item frontend/e2e/product-quality.pw.ts "$releaseRoot/source/frontend/e2e/product-quality.pw.ts"
Set-Location "$releaseRoot/source"
python -m venv backend/.venv
if ($LASTEXITCODE) { throw 'venv failed' }
$python = (Resolve-Path backend/.venv/Scripts/python.exe).Path
$env:PIP_NO_CACHE_DIR='1'
$env:npm_config_cache=Join-Path $releaseRoot 'npm-cache'
& $python -m pip install -r backend/requirements-ml.lock.txt
if ($LASTEXITCODE) { throw 'pip installation failed' }
$env:APP_ENV='development'; $env:DATA_MODE='local'; $env:DATABASE_URL='sqlite://'
Set-Location backend
if (Test-Path (Join-Path $releaseRoot 'pytest-new')) { throw 'Use a fresh pytest target' }
& $python -m pytest -q --basetemp (Join-Path $releaseRoot 'pytest-new')
if ($LASTEXITCODE) { throw 'Backend tests failed' }
& $python -m pip check
if ($LASTEXITCODE) { throw 'Dependency compatibility failed' }
Set-Location ../frontend
npm.cmd ci
if ($LASTEXITCODE) { throw 'npm installation failed' }
node node_modules/vitest/vitest.mjs run --maxWorkers=1
if ($LASTEXITCODE) { throw 'Frontend tests failed' }
$env:VITE_API_URL=''
foreach ($mode in @('local','synthetic')) {
  $env:VITE_DATA_MODE=$mode
  npm.cmd run build
  if ($LASTEXITCODE) { throw "Build failed: $mode" }
}
$env:PLAYWRIGHT_BROWSERS_PATH=Join-Path $releaseRoot 'browsers'
node node_modules/@playwright/test/cli.js install chromium
if ($LASTEXITCODE) { throw 'Chromium installation failed' }
# Alternatively use a current installed Chrome, as in this phase's local run:
# $env:MIGRAMIND_BROWSER='C:/Program Files/Google/Chrome/Application/chrome.exe'
Set-Location ..
& $python -m unittest discover -s scripts -p test_ci_browser.py -v
if ($LASTEXITCODE) { throw 'Readiness tests failed' }
& $python scripts/ci_browser.py --api-port 18000 --frontend-port 15173
if ($LASTEXITCODE) { throw 'Browser tests failed' }
Set-Location frontend
npm.cmd audit --json
if ($LASTEXITCODE) { throw 'Review dependency audit results' }
```

These commands are the reproducible procedure, not a claim that every line completed successfully in the initial audit. Its full Python installation stopped at the transport failures recorded above; feasible subsequent checks used the existing matching Python environment, argument-array subprocess calls (Node/npm CLI 10.9.2) and the installed Chrome alternative. The separate follow-up completed a new Python installation using the bounded installer commands documented above. No global package installation is required.

### Linux checks

Prerequisites: Git, Python 3.13 with venv support, Node 22/npm, and Playwright's Chromium OS libraries. The following reproduces the CI paths locally; installing OS libraries with `--with-deps` requires a separately approved disposable runner/admin environment, as used by CI. It was **not** run in local WSL.

```bash
set -eu
release_root=$(mktemp -d -t migramind-release-XXXXXXXX)
mkdir "$release_root/source"
git archive HEAD | tar -x -C "$release_root/source"
cp frontend/e2e/product-quality.pw.ts "$release_root/source/frontend/e2e/product-quality.pw.ts"
cd "$release_root/source"
python3.13 -m venv backend/.venv
release_python="$release_root/source/backend/.venv/bin/python"
export PIP_NO_CACHE_DIR=1 npm_config_cache="$release_root/npm-cache"
"$release_python" -m pip install -r backend/requirements-ml.lock.txt
export APP_ENV=development DATA_MODE=local DATABASE_URL=sqlite://
(cd backend && "$release_python" -m pytest -q --basetemp "$release_root/pytest-new" && "$release_python" -m pip check)
(cd frontend && npm ci && node node_modules/vitest/vitest.mjs run --maxWorkers=1)
(cd frontend && VITE_API_URL='' VITE_DATA_MODE=local npm run build)
(cd frontend && VITE_API_URL='' VITE_DATA_MODE=synthetic npm run build)
export PLAYWRIGHT_BROWSERS_PATH="$release_root/browsers"
(cd frontend && node node_modules/@playwright/test/cli.js install chromium)
"$release_python" -m unittest discover -s scripts -p test_ci_browser.py -v
"$release_python" scripts/ci_browser.py --api-port 18000 --frontend-port 15173
(cd frontend && npm audit --json)
```

### Synthetic demo startup and five-minute rehearsal

The [README PowerShell startup](../README.md#run-the-synthetic-demo-locally-powershell) creates a new dedicated target and is the Windows operator procedure. The private `getpass` prompt requires an interactive console. For automated verification only, this review generates a fresh random demo-only password in the child-process environment; it is not printed, committed or stored in documentation. No real records are seeded. The initializer refuses every nonempty application table; no reset/delete option exists.

Linux equivalent, **after** the isolated source installation above, from `$release_root/source/backend` in a fresh terminal with `release_root` set to that newly created directory (not an existing installation):

```bash
set -eu
demo_root=$(mktemp -d -t migramind-demo-XXXXXXXX)
export APP_ENV=development DATA_MODE=synthetic
export DEMO_ACKNOWLEDGEMENT=synthetic-only-no-real-health-data
export DATABASE_URL="sqlite:///$demo_root/migramind-synthetic-demo.sqlite"
export CORS_ORIGINS=http://127.0.0.1:5185 ALLOWED_HOSTS=127.0.0.1,localhost PORT=8015
unset DEMO_PASSWORD
./.venv/bin/python -m alembic upgrade head
./.venv/bin/python -m app.demo provision # private interactive demo-only password
./.venv/bin/python -m app.serve --check
./.venv/bin/python -m app.serve
```

In a second terminal inside that **same fresh copy's** `frontend` directory:

```bash
set -eu
export VITE_API_URL='' VITE_DATA_MODE=synthetic MIGRAMIND_API_PROXY=http://127.0.0.1:8015
npm run build
node node_modules/vite/bin/vite.js preview --host 127.0.0.1 --port 5185 --strictPort
```

Verify `http://127.0.0.1:8015/api/ready` and `http://127.0.0.1:5185/api/ready` return HTTP 200; the frontend root is `http://127.0.0.1:5185/`, not `/api/health`. Match the host spelling, ports, CORS origin and proxy exactly. Do not increase timeouts or bypass readiness when they disagree. The synthetic fixture is January 2026; use the guide instead of today's calendar. Follow the existing [timed walkthrough](PORTFOLIO_READINESS.md#five-minute-demonstration):

1. 0:00–0:35: explain diary/support purpose, synthetic/read-only boundary, sign in with `demo@synthetic.example.test` and the private password.
2. 0:35–1:20: Explore daily status; distinguish migraine/no migraine/unknown and view a creation revision.
3. 1:20–2:05: Show example calendar, inspect the fixed episode and diary; blank days stay unknown.
4. 2:05–3:35: Explore descriptive insights, explain empty recent windows, Review research features; no prediction or clinical validation is available. Research download is optional and requires explicit local consent.
5. 3:35–4:30: inspect appearance, saved caregiver notes and Attack Mode; exit with keyboard. Do not activate emergency/contact/share/location actions.
6. 4:30–5:00: show account isolation/history/availability-aware research tests and CI; disclose hosting/research/accessibility limits and sign out.

The built-demo suite can be run only while this **new isolated fixture** is served: set `MIGRAMIND_DEMO_BASE_URL`, a private `MIGRAMIND_DEMO_PASSWORD`, and `MIGRAMIND_BROWSER` to the installed Chromium executable; run `node node_modules/@playwright/test/cli.js test --config playwright.demo.config.mjs` from `frontend`. The password is a process environment value, not a literal command saved in shell history. On Linux, resolve the downloaded executable with `node --input-type=module -e "import {chromium} from '@playwright/test'; console.log(chromium.executablePath())"` with the same `PLAYWRIGHT_BROWSERS_PATH`. Stop both servers with Ctrl+C; rehearse next time with a new empty target. Do not point these tests at personal data or delete an ambiguous directory.

## Remaining release sign-off

- Human keyboard/screen-reader, zoom, contrast and real-device checks above, including error/retry and populated editable forms. Automated screenshots do not replace them.
- The approved login emergency target and support-route focus fixes pass their automated regressions; human accessibility review is still open. Keep the earlier browser timeout and successful unchanged rerun, and the subsequent corrected test-typing build error, visible in the validation record.
- Fresh interactive Linux synthetic-demo rehearsal and any intended alternate browser; patch-level runtime and OS review.
- The follow-up closes the bounded fresh Windows Python/ML-lock installation check on 3.13.12. The exact earlier 3.13.11 interpreter was not rerun, the source of the transport failures remains unidentified, and pip's incomplete-download cleanup defect remains present; preserve these limits when reproducing or presenting results.
- Public deployment, PostgreSQL/TLS/roles, backups/recovery, monitoring and independent security review remain separate unapproved work.
- No real health-data/research/clinical release until the existing governance and validation gates are independently met.
- Review this candidate's documentation/test diff and rerun its added browser test in GitHub if publication is later authorized. No publication action is part of this phase.
