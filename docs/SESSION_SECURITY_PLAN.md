# Phase 7: session security and account recovery plan

## Approved follow-up: password-reauthenticated sign out all sessions (2026-11-11)

**Current status:** the user approved only the narrowly scoped S7-02 implementation. Verified `security/session-recovery` at `4b3a45f`; the only starting changes were this untracked plan and the modified release-readiness report. Both audit documents were preserved and extended. The original audit-only text below is a **historical snapshot**, not a statement that this approved follow-up is unimplemented. No idle timeout, password change/reset, rate-limit redesign, schema or deployment change was added.

### Implemented behavior and security properties

- [`PasswordConfirmation`](../backend/app/auth.py#L46) accepts only the existing password (1–128 characters), excludes it from model repr, and forbids extra identity/owner fields. [`POST /api/auth/logout-all`](../backend/app/auth.py#L148) requires the existing authenticated session, exact allowed Origin and session CSRF before reauthentication. It verifies with the existing Argon2 implementation and reuses the existing IP/account attempt budgets without altering their limits or algorithms. Invalid confirmation returns only `Password confirmation failed` (400); missing/invalid authentication is 401, CSRF/Origin refusal 403, extra fields 422, exhausted budget 429. No account/session details or password are returned/logged by the new handler.
- The server deletes **every `LoginSession` row for the session-derived current user**, including the caller, in one database transaction. Only after a successful commit does it expire the current cookie and return **204**. It does not delete or update the user, password hash or health records. Failed verification performs no deletion. A failed commit rolls back through the existing request-session/error boundary, returns 503 in the tested application and does not expire the cookie.
- Revocation is persistent database state, not a worker-local list or frontend flag. Every subsequent protected request performs the existing database lookup. Two independently instantiated auth apps with separate engines sharing a **new synthetic SQLite file** observed revocation, and a third fresh app/engine after disposing the first two still rejected replay. This tests fresh-instance persistence, not an actual multi-process load test or production PostgreSQL execution. Workers must share the authoritative session database; independent database copies would not share revocation. No migration is needed.
- [`AccountSettings.tsx`](../frontend/src/AccountSettings.tsx#L16) adds a small inline confirmation form. Opening focuses the labeled current-password field; Enter confirms, Tab reaches confirm/cancel, cancellation restores the initiating button and sends no request. The password is an uncontrolled, masked input, cleared immediately on submission and discarded on cancellation/unmount; it is not placed in React state, browser storage or logs. Request/verification memory is transient, not a secure-memory-erasure guarantee. Pending controls prevent repeated submission; safe failures show the existing alert and leave a blank focused field for retry, without reporting success.
- [`Authentication.tsx:17`](../frontend/src/Authentication.tsx#L17) reuses the existing logout lifecycle only after the successful server response: clear memory-held authentication/generation, notify same-origin tabs, unmount the private workspace and bootstrap fresh anonymous CSRF before showing sign-in. Ordinary Sign out still calls the original current-session endpoint. Other devices fail on their next authenticated API request; this does not remotely erase already displayed content.
- **Shared read-only synthetic demo:** the action is labeled unavailable and not rendered as a button. Its existing frontend and server demo write allowlists remain closed; the auth handler also explicitly refuses synthetic mode. Ordinary demo logout remains available. This avoids allowing one visitor with the shared demo password to sign out every other visitor. No demo/production configuration or broad write allowance changed.

### Regression coverage and actual results

All execution was on this Windows machine using a **new temporary filtered source tree**, fictional records and new in-memory/temporary databases. Existing Phase 5 Python 3.13.12 dependencies were reused read-only; matching locked Node dependencies were copied after package-lock byte comparison. No install, existing app environment mutation, existing SQLite/WAL/account/health/backup/export/browser-profile/secret access, migration or provisioning occurred. Existing synthetic CRUD/erasure tests operate only on their own fixtures. No external service or telephone handler was contacted.

| Check | Actual result / scope |
| --- | --- |
| Initial focused backend run | **11 passed**, 5.66s pytest / 7.12s wall; later extended with saved-diary/current-cookie replay and production-cookie checks |
| Final existing backend suite plus new tests | **245 passed, 5 migration cases deselected**, 36.92s pytest / 38.77s wall. Deployment/provisioning module excluded. Includes **12** new revocation cases. |
| Full frontend unit suite | **91 passed / 15 files**, 45.30s suite / 46.54s wall; six new tests (four account form, two auth lifecycle) |
| Affected frontend tests after type-check correction | **15 passed / 2 files**, 7.35s suite / 8.04s wall; overlaps the full suite, not 15 additional distinct tests |
| Chrome + Edge isolated browser checks | **22 passed**, 22.2s suite / 25.88s wall, retries **0**. New cancel/success/failure scenarios ran in each installed browser at 1280×850 and 320×850 (**12 executions**); five existing manual-fixture scenarios ran once per desktop browser (**10 executions**). All API traffic intercepted; these are automated UI checks, not human/physical-device or real-API browser verification. |
| Final local production build | TypeScript + Vite **passed**, 7.61s wall / 3.00s Vite |
| Final synthetic production build | TypeScript + Vite **passed**, 7.48s wall / 2.59s Vite; not a deployment |
| Documentation / integrity | **59 local links / 37 source-line references checked**, **123 copied source/configuration files identical** to tested counterparts; both original uncommitted document bodies preserved; requirements/locks, migrations, CI and deployment settings unchanged; `git diff --check` passed |

[`test_logout_all.py`](../backend/tests/test_logout_all.py) covers correct/wrong password, password non-echo/repr, missing authentication (anonymous and no cookie), CSRF and missing/untrusted Origin, multiple sessions, current and independent cookie replay, forbidden owner selectors, other-account and anonymous-session preservation, saved account/contact/diary preservation, subsequent login, existing reauthentication limits, failed commit rollback, independent/fresh database engines, demo refusal and matching production cookie-expiry attributes. Password confirmation does not opportunistically rehash or change a password.

[`AccountSettings.test.tsx`](../frontend/src/AccountSettings.test.tsx) covers confirmation, keyboard order, cancellation/focus/password disposal, required password, pending controls, failure/retry and demo behavior. [`Authentication.test.tsx`](../frontend/src/Authentication.test.tsx) checks the authenticated CSRF/password request and successful return to fresh sign-in, plus refusal without false success. [`session-revocation.pw.ts`](../frontend/e2e/session-revocation.pw.ts) uses the existing isolated manual-accessibility fixture to exercise actual rendered UI with intercepted API responses. It does not establish server-side revocation; the backend tests do that separately.

**Failures and retries:** both first production-build attempts exited 1 during TypeScript checking (**4.77s local / 3.80s synthetic**): eight new React Testing Library queries incorrectly used Playwright's unsupported `exact` option. Removed that option from those unit-test queries; string role names already match exactly. No product/dependency workaround. Reran only the affected 15 unit tests and each build once with unchanged caps; all passed. The initial full unit suite had passed because Vitest does not perform this TypeScript check. No unit/backend/browser assertion failed, no flaky test was silently rerun, and Playwright retries were disabled. The existing Starlette/httpx TestClient deprecation warning remains; Vite's warning about temporary output directories outside the project is expected and no existing directory was emptied.

The first integrity check incorrectly included generated temporary TypeScript incremental-build metadata in its source comparison. Restricted it to the copied source/configuration file types and reran the checker successfully; no application/build/test rerun or repository artifact change was needed. Historical audit line references below describe the pre-implementation source; the implementation references above describe the current files.

### Safe reproduction commands and evidence

Evidence root: `%TEMP%/migramind-session-implementation-z5svrlxj`, containing only copied source/dependencies, synthetic test artifacts, temporary build output, logs and JSON command/results. Initial copies of the two uncommitted audit documents were retained there to verify preservation. Test caps: focused backend 180s, broad backend 600s, full/affected frontend 360s, each build 180s, Playwright 300s. No package/network retries or installation were performed.

Use a **new filtered copy**, excluding actual `.env`, database/WAL/SHM, backups/exports, secrets, datasets and browser profiles. Before importing the app, use the audit environment described below: `APP_ENV=development`, `DATA_MODE=local`, `DATABASE_URL=sqlite://`, `SESSION_HOURS=12`, `PYTHON_DOTENV_DISABLED=1`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=<new-copy>/backend`, private TEMP/TMP and no inherited app credentials/configuration. From copied backend:

```text
<isolated-python> -B -m pytest -q -ra --ignore=tests/test_deployment.py -k "not migration" --basetemp <new-root>/backend-all-data -p no:cacheprovider
```

From copied frontend with matching copied locked dependencies and empty `VITE_API_URL`:

```text
node node_modules/vitest/vitest.mjs run --maxWorkers=1
node node_modules/vitest/vitest.mjs run src/AccountSettings.test.tsx src/Authentication.test.tsx --maxWorkers=1
node <npm-cli.js> run build -- --outDir <new-root>/local-dist
node <npm-cli.js> run build -- --outDir <new-root>/synthetic-dist
```

Builds respectively use `VITE_DATA_MODE=local` / `synthetic`. Browser checks launch only copied Vite on a new loopback port, verify HTTP 200 and `/@vite/client` using a proxy-free readiness client (30s limit), then run `node node_modules/@playwright/test/cli.js test --config playwright.session-review.config.mjs`. That **temporary-only** config extends existing Playwright configuration with four Chrome/Edge desktop/narrow projects, workers=1, retries=0, private output, and only `session-revocation.pw.ts` plus desktop `manual-accessibility-fixture.pw.ts`. `MIGRAMIND_E2E_BASE_URL` supplies the temporary URL. Every API request is intercepted before navigation; foreign origins and native emergency handlers are blocked by the fixture. Browser profiles/output are temporary. The server is terminated/waited in a finally block. No personal service or persistent browser context is used.

### Remaining limits and rollback

**S7-02's local-prototype implementation is addressed within this scope**, not the whole SP4-03 finding. Server idle expiry, verified password change/reset, identity verification, session inventory, shared abuse defenses and S7-06 offline-logout privacy locking are still absent. No rate-limit behavior was redesigned. All other storage, recovery/restore, hosted operations, research and manual accessibility gates remain. Real-health/public release is still NO-GO.

Deletion revokes sessions present at the committed transaction boundary. It cannot stop a new/concurrent login by someone who knows the still-valid password, undo requests already authorized before commit, retract exports, or erase another device's already-rendered content. A lost success response leaves the UI reporting an unconfirmed failure; its next protected request discovers revocation, and retry may need a fresh login. Do not interpret a transport error as proof the transaction failed. Existing error handling is reused; no general offline lock was added.

No actual parallel-worker stress/restart process, PostgreSQL/hosting, Linux, cross-device, screen-reader, human keyboard/contrast/zoom or real email/recovery verification was performed. API-dependent browser tests and built-demo/provisioning harnesses were skipped because they migrate/provision or delete synthetic accounts; bounded backend tests and fully intercepted browser fixtures supply the stated evidence instead. No new advisory/network scan or fresh dependency-install claim.

Rollback, if separately requested: revert the additive route/UI/tests, leaving ordinary logout unchanged. No migration is involved. Already-revoked sessions must stay revoked; users sign in again. Never restore tokens, old database snapshots or password hashes to undo revocation. Existing user data and the original audit documents remain preserved. No commit, push, PR, merge or deployment.

## Historical Phase 7 audit-only snapshot

Assessment: **2026-11-11, Asia/Calcutta**. Starting branch `security/session-recovery`, clean HEAD **`4b3a45f`**, merge of PR #21 (`security/data-protection`). Confirmed the merged data-protection plan and synthetic encrypted-backup prototype. This is an **audit and remediation proposal only**. No application fix, API, configuration, schema, dependency or account change is implemented.

## Decision and scope

MigraMind has useful authentication and account-isolation controls. It is still a **supervised, fictional local prototype**, not an approved public health-data service. No new Critical/High finding or cross-account disclosure was confirmed in this review. That is bounded evidence, not penetration-test certification. Existing [security/privacy findings](SECURITY_PRIVACY_AUDIT.md), [storage/copy protection](DATA_PROTECTION_PLAN.md) and manual/research gates remain open.

The smallest recommended first implementation is a separately approved, password-reauthenticated **sign out all sessions** operation. Ordinary sign out correctly affects the current session; it should retain that behavior. Account deletion must not become the recovery workaround. Account recovery, idle expiry and abuse defenses need separate decisions and verification.

| Priority / finding | Severity and prerequisite | Release decision |
| --- | --- | --- |
| S7-01: no server idle expiry | Medium; someone can use an unattended, unlocked authenticated browser | Participant-facing session protection gate; accept only as an explicit supervised synthetic-demo limitation |
| S7-02: no non-destructive revoke-all | Medium; another session/device is compromised while the owner still has credentials | Compromise-response gate before real-health use |
| S7-03: no verified password change/recovery | Medium; forgotten/compromised password or loss of the last usable session | Recovery/identity-policy gate before participant use; not an implemented reset-token vulnerability |
| S7-04: limited abuse/availability controls | Medium; reachable writable auth service, shared IP, restart/multiple workers or targeted account attempts | Public-hosting blocker; no load-exhaustion attack was attempted |
| S7-05: registration membership disclosure | Low; writable local registration and a candidate email | Requires an enrollment/privacy decision before any real-user registration |
| S7-06: failed logout leaves private UI mounted | Low; logout request fails while someone can see/use the unlocked device | Shared-device/manual failure-flow gate; no claim that the server accepted logout |

S7-01/02/03 refine **SP4-03**, S7-04 refines **SP4-04**, and S7-05/06 add specific observations. They do not replace or lower prior findings. No remediation is approved by this document.

## What actually happens

A session is a temporary server-held permission to use one account. The browser carries an opaque random cookie, not a password or JWT. The server stores a digest of that cookie. A separate CSRF value binds requests to the mounted UI; it is not a password-reset or one-time recovery token.

| Flow | Implemented behavior and evidence | Missing behavior / limit |
| --- | --- | --- |
| Bootstrap | [`auth.py:110`](../backend/app/auth.py#L110): `GET /api/auth/session` returns the valid session's public account, CSRF and deadline; otherwise creates an anonymous one-hour session and removes expired rows. Anonymous creation is IP-limited. | A valid bootstrap does not refresh the deadline, rotate the cookie or verify activity. The public endpoint returns session state, not health records. |
| Register | [`auth.py:119`](../backend/app/auth.py#L119): normalized email, display name, 12–128-character password; extra fields forbidden. Existing anonymous-session CSRF and exact Origin required. Hash, insert, replace previous browser session and sign in. Duplicate insert returns generic 400. | Basic email syntax is not proof of ownership. No verification message, enrollment invitation or recovery address validation. Synthetic-demo mode disables registration. |
| Password storage | [`auth.py:16`](../backend/app/auth.py#L16): Argon2id, time cost 3, memory 65,536 KiB, parallelism 2. Unknown-user login checks a dummy hash; wrong known/unknown passwords return the same 401 detail. Password fields suppress repr. | No constant-time end-to-end claim, compromised-password screening, MFA or hash-work concurrency bound. Database/host compromise is outside HTTP ownership enforcement. |
| Login | [`auth.py:130`](../backend/app/auth.py#L130): validate body, IP/account budget, Origin/CSRF, verify password; opportunistically rehash on successful local login if needed. Issue a fresh cookie/CSRF and delete the previous browser session row. | Rehashing is not a password change. Login does not revoke independently issued sessions. Synthetic mode permits only the provided fictional account and skips hash updates. |
| Session creation / cookie | [`auth.py:68–105`](../backend/app/auth.py#L68): independent `token_urlsafe(32)` session and CSRF values; SHA-256 digest of the high-entropy session identifier stored. Cookie is HttpOnly, SameSite=Lax, Path=/, no Domain; production adds Secure and `__Host-`. Max-Age matches server TTL (anonymous one hour). | Development cookies intentionally permit local HTTP; unsuitable for remote exposure. CSRF is stored in the session table and returned to the UI. Cookie security does not stop an unlocked browser, XSS or malicious extensions. |
| Expiry | [`security.py:64`](../backend/app/security.py#L64), [`auth.py:75`](../backend/app/auth.py#L75): server absolute lifetime defaults to 12 hours, configurable integer 1–168. Invalid, naive or expired deadlines fail closed. | No idle clock, sliding refresh, refresh token or background activity renewal. [`LoginSession`](../backend/app/main.py#L41) has no last-seen or issued-at field. Expired-row cleanup is lazy; expiry is enforced even before cleanup. |
| Read/write authorization | [`auth.py:20`](../backend/app/auth.py#L20), [`auth.py:86`](../backend/app/auth.py#L86): user derived from valid session; GET/HEAD require matching session-bound CSRF (401 on mismatch); mutations require matching CSRF plus exact allowed Origin (403). Owned queries and referenced IDs are independently scoped. | CSRF does not defend against code executing at a trusted origin. CORS is not authorization; non-browser clients can forge Origin but still need credentials/session authority. |
| Logout | [`auth.py:141`](../backend/app/auth.py#L141): protected POST deletes current session, commits, expires matching cookie; replay of that session fails. | Other independent sessions remain active. No session inventory, revoke-other/all control, session count cap or administrator recovery flow. A refused or unreceived request is not successful logout. |
| Account update / deletion | [`auth.py:145–160`](../backend/app/auth.py#L145): update accepts display name only. Deletion verifies password and typed DELETE, deletes owned records and all this user's sessions transactionally; other accounts and unassigned legacy rows stay intact. | Deletion is destructive, not routine recovery; it cannot erase old external copies. No password-change endpoint. Restoring an old database could restore session rows; backup restore must invalidate sessions under a future approved procedure. No existing backup was inspected. |
| Frontend lifecycle | [`Authentication.tsx:12–17`](../frontend/src/Authentication.tsx#L12): bootstrap gates screens; timer hides private UI at the supplied absolute deadline; session change and persisted pageshow re-bootstrap; confirmed logout clears state and reboots anonymous CSRF before sign-in. [`api.ts`](../frontend/src/api.ts#L1) uses credentialed no-store/no-referrer requests, memory-only CSRF and generation checks against stale responses. | Timers, sleep/resume and cross-tab delivery are browser-dependent; server expiry remains authoritative. No idle lock. No offline logout guarantee (S7-06). |
| Cross-tab / browser storage | [`sessionEvents.ts`](../frontend/src/sessionEvents.ts#L1): BroadcastChannel change signal, fallback random localStorage marker; no identity/health/token payload. Appearance preferences use localStorage. | Does not notify another device or erase already seen content. No physical-device, extension or browser-profile inspection performed. |

All protected account/health route families were reviewed through `main.py`, `tracking_routes.py`, `support_routes.py`, `prospective.py` and `research_quality.py`. Existing route-inventory, mutation CSRF, bidirectional ownership and account-erasure tests exercise diary, wellness, early symptoms, contacts, caregiver profile, support/attack preferences and feedback, daily status/history, insights and exports. No caller-supplied owner override or cross-account record access was confirmed. Privileged database/CLI access remains a separate trust boundary; these tests do not certify arbitrary future endpoints.

### Recovery features: absent, not tested as if implemented

There is no forgot-password, reset-password, change-password, emailed recovery, verified-email enrollment, recovery-code, MFA or staff-assisted identity-verification flow in the reviewed route/UI contracts. Therefore reset-token generation, digest storage, one-time consumption, token expiry, reset throttling, enumeration-safe reset responses and password-change session revocation are **not implemented / not applicable to current reset testing**, rather than passed checks. The CSRF token must never be repurposed for recovery. The synthetic backup's ephemeral encryption key is unrelated to account recovery and cannot recover a lost password.

## Findings and safe reproduction

All steps below refer exclusively to a **new filtered source copy** and the in-memory `clients` fixture in [`test_auth.py:13`](../backend/tests/test_auth.py#L13). Set `DATABASE_URL=sqlite://` and `PYTHON_DOTENV_DISABLED=1` before importing the app. Never point these instructions at an existing service, database, account or browser profile. `a`, `b`, `factory`, `register`, `login` and `PASSWORD` refer to that synthetic fixture/helpers; do not print cookies or session/CSRF values.

### S7-01 — Medium: absolute lifetime does not limit inactivity

Evidence: session lookup only compares `expires_at` with current UTC time; schema has no activity field. The temporary test registered a fictional user, saved the bootstrap deadline, replaced only the copied module's `now()` with the original time plus six hours, and observed account GET **200**, unchanged bootstrap deadline and no new cookie. At plus thirteen hours, account GET was **401** with default 12-hour TTL. No sleep or real clock setting was needed.

Risk: an unattended unlocked browser remains usable within its absolute lifetime. There is no demonstrated expiry bypass. Proposed fix: define an approved idle period plus immutable absolute ceiling, enforce both on the server, then add an accessible client privacy lock. Acceptance must include boundary times, sleep/resume, clock error, multiple tabs/devices, concurrent touches and exclusion of background polling from meaningful user activity. Existing rows need an explicit conservative cutover; a new last-activity field/migration needs separate approval. Do not merely extend/reuse absolute expiry as an idle clock.

### S7-02 — Medium: no non-destructive compromise-response revocation

Safe reproduction: `register(a)`, `login(b)` with the same fictional identity, `a.post('/api/auth/logout')` → **204**; A account GET → **401**, B account GET → **200**. Existing tests also confirm login rotation invalidates the prior cookie/CSRF and deletion revokes every session for that user. This is expected single-session logout, not a broken current-session logout.

Risk: a copied or independent compromised session can survive until its deadline. Deleting all health records is not an acceptable substitute. Recommended first task and its acceptance/rollback are below. Successful revocation cannot retract already rendered/exported data or requests already authorized before the transaction.

### S7-03 — Medium: no verified password change or account recovery

Evidence: auth route inventory and display-name-only `AccountUpdate`; a temporary authenticated PUT including a password field returned **422**, rather than changing a password. No recovery routes or UI were found. No email was sent.

Risk: password loss has no supported recovery; knowledge of a compromised password cannot be invalidated through an ordinary password-change operation. No claim of insecure reset-token handling is made because that flow does not exist. First approve authenticated password change with current-password verification and atomic all-session revocation. Future lost-password recovery requires a proven identity channel: an arbitrary registration email is currently unverified and is not sufficient evidence of account ownership. Never infer identity from health details or an active caregiver consent receipt.

Future reset acceptance: high-entropy purpose-bound token stored as a digest, short explicit TTL, atomic one-time use, generic externally visible requests, bounded request/verification attempts, safe configured link origin (not untrusted Host), no token/referrer/log leakage, password-hash update plus all-session revocation in one transaction, no automatic login, race/replay/expired/wrong-user tests using a fake outbox only. SMTP, identity policy, schema, contracts and retention need separate approval. Recovery does not restore deleted health records or encryption keys.

### S7-04 — Medium: throttle availability and deployment limitations

Evidence: [`Limiter`](../backend/app/auth.py#L51) is a locked process-local map of sliding 900-second deques. Login/registration and account deletion share **30/IP**, **10/normalized-account** budgets. They count successful attempts too; successful login does not clear the budget. Bootstrap of an absent/expired session uses the IP budget. Login/register call `attempts()` **before CSRF**, but after FastAPI body validation. A rejected account check can already have consumed the IP budget. 429 returns a fixed `Retry-After: 900`, not an exact earliest retry deadline. There is no permanent lockout or per-user persisted lock flag.

Bounded reproduction: registration consumes one account attempt. Nine well-formed login POSTs for that same fictional email with an empty CSRF header each return **403**. The legitimate next login then returns **429**. This proves pressure on the account budget before CSRF, not a CSRF bypass or account takeover. A separate standalone Limiter test allowed one request, rejected the second with limit=1, then allowed a request to a new instance: state is not shared/persistent. No restart, multiworker run, flood or expensive concurrent hashing experiment was performed.

Threat prerequisites: an attacker needs a reachable auth service and a candidate account identifier; can submit non-browser requests. Shared demo clients can also collide unintentionally. Every check scans current keys under one lock; state cardinality and Argon2 work need bounds. Restart/multiple workers reset/multiply limits. [`serve.py:29`](../backend/app/serve.py#L29) uses one loopback worker; its proxy trust does not itself establish a trusted real-client-IP policy. The nginx body/rate controls are templates, not verified deployed defenses. Existing SP4-04 parser/body/unbounded-read risks remain.

Proposed design: inexpensive bounded ingress/IP/body/time limits before expensive work, explicit trusted-proxy identity, bounded account pressure with an anti-lockout policy, and shared state for multiple workers. Moving all throttling after CSRF would expose anonymous bootstrap/CSRF work and is not a complete fix. Validate rejection ordering, rolling-window boundaries, shared NAT fairness, reauthentication/delete interactions, restart/workers, malicious header spoofing and synthetic load under a separately approved test plan. No load or external-service testing was performed here.

### S7-05 — Low: local registration distinguishes an existing email

Safe reproduction: create a fictional account, then submit the same email from a second synthetic client → **400**; submit a fresh fictional email with otherwise identical valid fields → **201**. Generic error wording does not hide the status distinction. Existing tests confirm known/unknown wrong-password login returns the same **401** detail and uses a dummy hash; timing equivalence was not measured.

Risk requires reachable writable registration. Synthetic-demo registration is disabled, so this does not expose a real-user list in the supported fictional demo. Before participant registration, choose invitation/enrollment or a verified out-of-band confirmation design with uniform externally visible responses. Do not change status codes alone and claim enumeration solved. Compatibility includes current client handling of immediate registration/sign-in and email ownership policy.

### S7-06 — Low: unsuccessful logout does not hide mounted private content

Evidence: [`Authentication.tsx:16`](../frontend/src/Authentication.tsx#L16) awaits the logout request before clearing user/CSRF/UI. [`AccountSettings.tsx:9`](../frontend/src/AccountSettings.tsx#L9) catches errors and displays an alert. A temporary mocked frontend test bootstrapped a fictional account, rejected logout with a synthetic network error, caught that rejection and confirmed the private workspace remained mounted. A separate backend observation returned **403** for logout without CSRF, **200** for the still-valid account, then **204/401** for correct logout/account read. These are distinct checks, not an end-to-end browser/network failure test.

Risk: someone at an unlocked screen can still view private content after an unsuccessful sign-out attempt. The UI does not falsely report success; no server-revocation bypass was shown. Propose an explicit local privacy lock on logout failure with truthful wording that server logout is unconfirmed and a retry path. Avoid immediately bootstrapping back into the still-valid cookie session. HttpOnly cookies cannot safely be cleared by JavaScript; define server retry and subsequent-unlock semantics first. Acceptance: offline, 403, 500, lost response after server commit, retry and recovery without private content reappearing or an unhandled promise. No product fix is made here.

## Proposed implementation order, acceptance and rollback

| Order | Exact proposed scope (approval required) | Acceptance | Compatibility / rollback |
| --- | --- | --- | --- |
| 1: revoke all | Add `POST /api/auth/logout-all` in `backend/app/auth.py`, current-password-only extra-forbidden input, existing authenticated Origin/CSRF gate and bounded reauthentication attempts. Transactionally delete **all** rows for the session-derived user, including current session, then expire its cookie and return 204. Add explicit Account Settings action and confirmed-success clearing through existing lifecycle hooks. Do not accept a caller-supplied owner ID. | Two sessions plus a cloned current credential all fail subsequent protected requests; unrelated user's and anonymous sessions remain valid; wrong password/CSRF/Origin revokes nothing; next valid login works; no health deletion. Tests cover cookie attributes, rollback on DB error, old-response guards and UI success/failure. | Existing ordinary logout unchanged; existing table suffices, no migration proposed. Decide explicitly whether the new auth action is allowed in the backend `DemoBoundary` and frontend demo allowlist; never broaden general demo writes. Revert additive route/UI if needed; users reauthenticate. Never restore revoked session rows from backup as rollback. |
| 2: logout privacy UX | Small `Authentication.tsx`/`AccountSettings.tsx` failure-path design from S7-06, unit and mocked-browser tests. | Private UI hidden on failure; server revocation status accurately described; no silent re-bootstrap/unlock; accessible retry. | Local clearing is not remote revocation. Revert code if necessary without claiming earlier attempts succeeded; do not alter emergency access. |
| 3: authenticated password change | Dedicated extra-forbidden contract, current-password verification, current password policy, generic errors and bounded reauth; atomically update Argon2 hash and revoke all sessions; require fresh sign-in. | Old password and every old session fail; new password works; bad input/reauth causes no change; concurrent transaction and other-account isolation verified. | Separate API/UI approval; opportunistic rehash remains separate. Never roll back by restoring old password hashes or live tokens; corrective change/recovery requires a verified procedure. |
| 4: idle expiry | Approved last-activity schema and server enforcement, client lock and bounded update policy; retain absolute ceiling. | S7-01 cases plus synthetic migration/cutover, races, DB-write load, background polls and demo-mode behavior. | Migration/config approval required. Define old-row policy and safe rollback that preserves the absolute ceiling; no real-data migration in this task. |
| Parallel before exposure | Shared/bounded ingress and account abuse controls, verified recovery/enrollment design, independent storage/restore and deployment review. | S7-03/04/05 acceptance and existing security/research/manual gates; fake services and isolated data first. | No unsolicited SMTP, proxy trust change or infrastructure rollout. Avoid production-only assumptions in local/demo tests. |

Revoke-all invalidates sessions present at the transaction boundary; a new concurrent login using a still-known password can establish another session. It therefore mitigates stolen-session risk, not stolen-password persistence. Password change/identity recovery remains necessary. Revocation cannot undo already-authorized in-flight actions or erase rendered/downloaded records. Durable backup restore must prevent revoked/expired identities from becoming valid again; the JSON encryption prototype does not establish that guarantee.

## Actual validation and reproduction environment

All execution was on **this Windows machine**. A new temporary filtered source copy held tracked Python application/test/research source and frontend source only. No `.env`, database/WAL/SHM, export, backup, private key, browser profile or user dataset was copied/read. No default API server was started. Existing fixture schemas were created in new in-memory SQLite engines (not Alembic migrations), overridden into TestClient and disposed after use. Tests may delete their own fictional users only.

Read-only reuse: the earlier isolated Phase 5 base environment (`%TEMP%/migramind-phase5-pip-6u5o2bro/base-venv`) supplies Python 3.13.12/dependencies; no package/environment upgrade or new-install claim. Frontend dependencies were copied from that phase's temporary source only after package-lock bytes matched current Git source. No npm install, advisory network query or external contact occurred. Child environment was restricted to OS execution variables plus the explicit settings below. Python ran with `-B`; test caches/output were confined to the new temporary root.

| Check | Actual result |
| --- | --- |
| Branch/base/initial tree | `security/session-recovery`, `4b3a45f` merged PR #21, clean before changes |
| Existing selected backend tests | **100 passed, 2 migration tests deselected**, 17.39s pytest / 18.93s wall; auth, security, prospective, research-quality and account-foundation modules |
| Temporary backend observations | **7 passed**, 3.57s pytest / 5.16s wall; S7-01/02/04/05, absent password contract and failed/correct logout |
| Existing frontend auth/client tests | **15 passed, 2 files**, 11.95s suite / 13.86s wall |
| Temporary frontend logout observation | **1 passed**, 3.89s suite / 5.15s wall |
| Documentation / integrity | **50 local links, 33 source-line references checked**, historical release text preserved, **107 copied source/configuration files identical** to repository counterparts; `git diff --check` passed. Initial link validation caught an incorrect launcher line reference, corrected before the final check. Only the two intended documents differ from Git. |
| Dependency warning | Existing Starlette/httpx TestClient deprecation warning in backend runs; no dependency change |
| Browser / Linux / deployment / email | Not run. No real-device, hosted TLS/proxy/cookie integration, reset delivery or load-test assurance claimed |

**Failure and retry disclosure:** first existing-backend collection exited 2 with **five collection errors**, and the first observation collection exited 2 with **one**, all `ModuleNotFoundError: research`: the temporary-copy script omitted `backend/research/*.py`. No tests ran in either attempt (5.27s / 2.71s wall). Added only tracked research Python source to the temporary copy and reran each once with the same 600s/180s caps; results above. No package/application change, timeout increase or silent retry-until-green. Frontend runs passed first invocation (240s cap each).

Evidence directory for this run: `%TEMP%/migramind-session-review-ox6zi4fp`, with backend/final/observation/frontend logs, JSON command/results and the temporary observation source. These are synthetic test artifacts, not data backups. Observation tests are deliberately outside Git; no application test file is changed.

### Exact safe command shapes

Start only from a new filtered source copy, with the copied backend as working directory. `AUDIT_ROOT` and `AUDIT_PYTHON` below are placeholders for the **new** temporary root and the reused isolated interpreter; do not use the normal application environment or URL. Clear unrelated application environment values, including demo/production and Vite settings, before setting:

```powershell
$env:APP_ENV = 'development'
$env:DATA_MODE = 'local'
$env:DATABASE_URL = 'sqlite://'
$env:SESSION_HOURS = '12'
$env:PYTHON_DOTENV_DISABLED = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = "$AUDIT_ROOT/source/backend"
$env:TEMP = $AUDIT_ROOT
$env:TMP = $AUDIT_ROOT
& $AUDIT_PYTHON -B -m pytest -q -ra tests/test_auth.py tests/test_security.py tests/test_prospective.py tests/test_research_quality.py tests/test_account_foundation.py -k 'not migration' --basetemp "$AUDIT_ROOT/pytest-data-new" -p no:cacheprovider
# Temporary observation module only after constructing the synthetic cases above:
& $AUDIT_PYTHON -B -m pytest -q -ra tests/test_phase7_observations.py --basetemp "$AUDIT_ROOT/observations-new" -p no:cacheprovider
```

In the copied frontend with matching copied dependencies, `CI=true`, `VITE_DATA_MODE=local`, empty `VITE_API_URL`, and TEMP/TMP still inside the new root:

```text
node node_modules/vitest/vitest.mjs run src/Authentication.test.tsx src/api.test.ts --maxWorkers=1
node node_modules/vitest/vitest.mjs run src/phase7-observation.test.tsx --maxWorkers=1
```

Temporary observations assert the **current limitations**, not the desired future fixes. They are not regression coverage for unimplemented remediation. Their safe fixture steps are specified above; retain them only as local audit evidence until an approved implementation adds appropriate repository regressions.

## Remaining gates and limitations

- Existing **SP4-01 / High storage/copy protection** is still open. Encrypted synthetic JSON round trips do not protect current databases, copies or session restoration. Existing installer remediation evidence and its Linux/CI limitations remain historical, not revalidated here.
- No human/physical-device or fresh browser verification, real deployment, network advisory refresh, email delivery, distributed/concurrency load test, filesystem encryption/ACL inspection, backup inspection or existing-data access. Full integration/demo harnesses were skipped because they provision/migrate; no migration or provisioning command was run. A production build was not rerun for documentation-only changes.
- Existing CSRF/ownership/cookie tests and code review support the stated controls; no broad guarantee of absence of XSS, timing leakage, session races or account-isolation defects is made. Existing secret files/Git history were not scanned because that could expose sensitive material.
- Define the intended real-user identity and recovery operator, required idle/absolute lifetimes, shared-device policy, multi-device revocation scope, proxy/client-IP policy, reset channel and consent/retention obligations before implementation. No current real user needs to disclose records or credentials for those decisions.

**Approval boundary:** only this plan and the release-readiness link/evidence are changed. All application behavior, auth contracts, dependencies/locks, migrations, deployment settings and existing data remain untouched. No commit, push, PR, merge or deployment. Request separate approval for task 1 (password-reauthenticated sign out all sessions) before any remediation; subsequent items remain separately scoped.
