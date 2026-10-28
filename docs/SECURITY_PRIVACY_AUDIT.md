# Sprint 14: security and privacy hardening audit

Assessment: 2026-10-28, branch `feat/security-privacy-hardening`. Scope: FastAPI/React prototype, authentication, diary/observations/history, research downloads, deployment configuration and dependency metadata. Reviewed [authentication/privacy](authentication-privacy.md), [collection](PROSPECTIVE_COLLECTION.md), [offline baseline](ML_RESEARCH_BASELINE.md), [research quality](RESEARCH_DATA_QUALITY.md), [Park findings](PARK_DATASET_AUDIT.md), [pilot proposal](PROSPECTIVE_PILOT_PROTOCOL.md) and [readiness gates](RESEARCH_READINESS_GATE.md) before changes.

**Outcome: targeted fixes implemented and synthetically tested; real health-data hosting, research recruitment and clinical prediction remain NO-GO.** This is a repository review, not penetration testing, legal certification, HIPAA compliance, research approval or proof of production security. No production service, researcher contact, participant recruitment, patient-data collection or model was introduced. No existing health database was migrated or used as a fixture. Publication requires the separately authorized final security review; merging remains a separate, unauthorized action.

## Threat model and boundaries

Assets: account credentials, opaque session/CSRF tokens, health observations and episode history, contacts/support preferences, revision journals, consent receipts and private downloads. Actors include anonymous clients, a malicious account holder guessing another record ID, an external website attempting CSRF/CORS abuse or local DNS rebinding, a misconfigured proxy/operator, and a compromised dependency/build source. A database/host administrator, browser extension, stolen unlocked device or downloaded-file recipient is outside application ownership enforcement and needs separate controls.

| Boundary | Controls reviewed / remaining trust |
| --- | --- |
| Browser to API | Cookie session, in-memory CSRF token, exact origins, source Host, TLS in production, session expiry/logout. CORS is not authentication. A trusted frontend origin or XSS can act with its user's authority. |
| API to database | Session-derived owner on all health handlers, foreign object checks, parameterized ORM, no SQL echo, hidden parameters, transactional revisions and account erasure. Authentication does not encrypt files or constrain privileged offline CLI/database access. |
| App to research preparation | Explicit authenticated POST and literal consent, fixed local-download scope, allowlisted numeric history, no independently verified outcomes and no research enrollment. Caregiver consent is separate. |
| Download to device | Fixed attachment filename, no-store, object URL revocation, explicit user action. Browser cache settings do not erase saved downloads, OS backups, screenshots or shared copies. |
| Deployment/configuration | Environment settings are server-controlled; browser `VITE_` values are public. Proxy trust, DNS/certificates, managed secrets, frontend hosting headers and production database operations require review. |
| Dependencies/tooling | Exact lockfiles plus advisory checks; tooling runs locally with dependency metadata only. Registry/advisory integrity, platform binaries and compromised build systems are not proved safe by a zero-result scan. |

## Confirmed findings and prioritized changes

Severity is a qualitative impact/likelihood assessment for a hypothetical exposed deployment, not evidence of an actual compromise. The prototype was not deployed to reproduce attacks. No confirmed exploitable critical application defect was established. Critical/high advisory flags were investigated before lower-priority tightening.

| ID / severity | Confirmed pre-change behavior and evidence | Fix / scope |
| --- | --- | --- |
| S14-01 — High, deployment misconfiguration | `APP_ENV` was a string equality: misspellings silently selected insecure development cookies. Production accepted default HTTP origins, implicit SQLite configuration, unvalidated Host and HTTP requests. Cookie flags alone did not validate the deployment. | [security policy](../backend/app/security.py) rejects unknown modes, malformed/wildcard origins and invalid TTL; production requires explicit HTTPS origins, explicit hosts and PostgreSQL with `sslmode=verify-full`. [main](../backend/app/main.py) validates before engine creation, enforces trusted hosts and HTTPS, and disables production API docs/OpenAPI. Local loopback HTTP/SQLite stay supported. |
| S14-02 — High privacy impact on unexpected faults; remote exploitability not established | SQL/validation failures had dedicated handlers, but other exceptions could reach the ASGI server's normal traceback logger with exception values. Synthetic injected faults demonstrate the mechanism; this is not a finding of an actual leaked patient record. | Value-free ASGI boundary returns generic JSON for pre-response failures, raises a fresh sanitized exception after response start, and emits no exception/body/path/query/token logs. ORM exception parameter rendering is also disabled. No blanket third-party logger suppression is installed. |
| S14-03 — High build/install supply-chain concern, conditional on malicious packages/index | Installed `pip==25.3` produced five distinct advisory IDs involving archive/URL/path/entry-point handling. Initial OSV output duplicated entries. `pip` is installation tooling, not an exposed health API endpoint. | Local app tooling upgraded to `pip==26.2.2`; README setup now pins this bootstrap upgrade. See [official pip release notes](https://pip.pypa.io/en/stable/news/). No unnecessary runtime dependency added. |
| S14-04 — Medium privacy exposure in validation metadata | The validation handler excluded input values but returned full `loc` and custom message text. An unknown JSON key supplied by the client was reflected in the error location. | Validation responses expose only the source category (`body`/`query`/etc.), generic text and framework error type. Synthetic sensitive-key/value regression verifies neither is echoed. This trades detailed field errors for a stronger privacy boundary. |
| S14-05 — High impact if production frontend is misconfigured | Production builds accepted arbitrary `VITE_API_URL`, including HTTP or credential-bearing URLs; API requests could then be pointed at an unsafe destination by the operator. This is not attacker control of a shipped build. | [build-time guard](../frontend/src/securityConfig.ts) allows empty same-origin or exact HTTPS origin only, with no userinfo/path/query. Frontend requests disable caching/referrers; 5xx bodies cannot be displayed as raw backend messages. |
| S14-06 — Low consent correctness | Caregiver consent accepted coercible `"true"`/`1`; research export already required a literal Boolean. No caregiver transmission endpoint exists. | Caregiver confirmation also uses `StrictBool`; explicit true remains required. Research-export scope/consent and no-upload behavior remain unchanged. |
| S14-07 — Low availability/correctness | Limiter expired an entire key only after its last attempt aged out, leaving older attempts inside mixed-age windows and overblocking legitimate use. | Expire individual attempts at the 15-minute boundary. Limits remain 30/direct IP and 10/account; no forwarding-header trust, distributed store or security-limit relaxation added. |

Additional defense in depth: validated settings omit database URLs from their representation; invalid configuration messages never interpolate URLs/credentials; malformed/naive session expiry is treated as unauthorized rather than an unhandled error. All HTTP responses through the boundary receive `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` and `X-Frame-Options: DENY`; HTTPS production responses additionally receive HSTS `max-age=31536000`. These API headers do not configure the separately hosted frontend document or its CSP.

Error handling follows the principle of generic client failures in [OWASP error-handling guidance](https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html), with an additional health-privacy restriction: raw exception values are not logged for debugging. Operators still need approved, value-free event counters/alerts. The boundary cannot sanitize arbitrary third-party code that logs before raising, infrastructure request logs, or unreviewed future background tasks; those remain deployment review items.

## Dependency evidence and advisory discrepancies

The first PyPI-backed Python scan timed out and supplied no valid result. Retried using `pip-audit`/OSV against installed `backend/.venv/Lib/site-packages`: **43 packages**, **11 advisory entries in two packages**, representing **six unique advisory IDs** (five for pip plus one for certifi). Audit tooling was installed in a separate ignored environment; no app dependency on pip-audit was introduced. Reports contain package metadata only and remain ignored.

The certifi flag needs qualification: OSV marked installed `2026.10.18` for GHSA-6q48-6c7w-9gw2, while the [maintainer advisory](https://github.com/certifi/python-certifi/security/advisories/GHSA-6q48-6c7w-9gw2) lists `2026.10.18` as patched. The [reviewed advisory](https://github.com/advisories/GHSA-6q48-6c7w-9gw2) recommends `2026.10.19` or later and explains the trust-store changes. Therefore this is recorded as a scanner/upstream range discrepancy, **not a confirmed critical flaw in the previous pin**. Conservatively upgraded to `certifi==2026.10.19` in both backend locks and added the same minimum to requirements. No certificates or TLS verification were disabled.

Post-update OSV scan: **43 packages, zero known advisory entries, zero skipped**; `pip check`: no broken requirements. Frontend `npm audit --json`: zero known vulnerabilities, including zero high/critical; metadata reports 232 dependencies (5 production, 228 development, overlapping categories). These are time-bounded registry results, not absence-of-vulnerability or package authenticity guarantees. Pip's vendored components and OS/browser/container libraries are not independently covered by the application package scan. Future installs must use reviewed pins, fresh scans and a trusted registry; updating source lockfiles does not patch other developers' existing environments.

## Authorization, authentication and export assessment

- Opaque random sessions remain hashed in the database, rotated on login/registration, HttpOnly/SameSite=Lax and host-only; production adds Secure and `__Host-`. Absolute server expiry remains 1–168 hours, anonymous bootstrap one hour. Logout revokes the stored session, not just the cookie. Reads also require the session-bound CSRF token to block stale-tab cross-account reads; mutations require matching token and exact Origin.
- Argon2id configuration, dummy verification for unknown users, generic login errors and per-IP/per-account limits remain. There is no new reset, impersonation, staff access or automatic enrollment mechanism. Registration can reveal successful account creation; account verification/recovery/MFA and hash-work concurrency limits remain open.
- Reviewed route registration across `main.py`, `auth.py`, `tracking_routes.py`, `prospective.py`, `support_routes.py` and `research_quality.py`. Health/account operations use `require_user`; record queries/references derive ownership from the session. Public session bootstrap and `/api/health` are deliberate exceptions; development docs are public, production docs disabled. Existing route-inventory and two-account CRUD/history/export tests pass. No cross-account vulnerability was confirmed in reviewed handlers; this is not a full penetration-test assurance.
- Research export still requires strict true, `local_research_preparation` scope, CSRF/Origin, current owner and per-user rate limit. It retains the explicit UI checkbox/download, numeric allowlist, fixed JSON attachment and no-store. No automatic upload, external ML call or sharing introduced. The local consent receipt is not research enrollment or transfer permission; verified outcomes remain empty and training eligibility false. Personal account export remains a separate authenticated workflow.
- React escapes rendered text; no new raw HTML insertion or health telemetry was added. CSRF tokens remain in memory, and the existing cross-tab fallback stores only a random notification marker. Frontend stale-session guards, account clearing, appearance and Attack Mode remain tested. This review does not rule out XSS or malicious extensions; a strict frontend CSP and independent review remain required.

## Configuration and safe reproduction

Development remains explicitly local/synthetic: `APP_ENV=development`, the existing loopback origins, allowed hostnames and SQLite fallback. See the updated [backend template](../backend/.env.example) and [frontend template](../frontend/.env.example). No real `.env` file or credential was inspected, printed or modified. Database URLs are never copied into audit logs.

Production now fails startup unless all of the following hold: exact `APP_ENV=production`; explicit exact HTTPS `CORS_ORIGINS`; explicit hostname-only `ALLOWED_HOSTS` with no wildcard/port; valid integer `SESSION_HOURS`; and explicit PostgreSQL `DATABASE_URL` with database/host and `sslmode=verify-full`. Configure the certificate trust root through approved libpq/institutional mechanisms; verification was not tested against a production database. Loopback defaults are not a deployment recipe. The frontend build rejects nonempty API destinations unless they are exact HTTPS origins; all `VITE_` variables are publicly bundled and must contain no secrets.

For TLS termination, correctly configure the ASGI scheme only through a reviewed proxy trust boundary. The middleware does not trust a request's `X-Forwarded-Proto` directly; the server may process trusted forwarding headers before ASGI. Do not use `--forwarded-allow-ips=*` or expose a proxy-trusted listener directly. This sprint's synthetic server used `--no-proxy-headers`. Host allowlists, database TLS, HSTS and Secure cookies do not provide disk encryption, backup protection or a deployment approval. HTTP production requests receive 400 rather than redirecting a possibly sensitive POST.

Reproduction commands (synthetic environments only):

```powershell
cd backend
./.venv/Scripts/python -m pip install --upgrade pip==26.2.2
./.venv/Scripts/python -m pip install -r requirements.lock.txt
./.venv/Scripts/python -m pip check
./.venv/Scripts/python -m pytest -q
cd ../frontend
npm.cmd test -- --maxWorkers=2
npm.cmd run build
npm.cmd audit --json
# Start separate loopback API/Vite servers against a freshly migrated synthetic DB.
# Include both the UI test origin and existing synthetic fixture origins in CORS_ORIGINS.
$env:MIGRAMIND_E2E_BASE_URL='http://127.0.0.1:5184'
npm.cmd run test:e2e
```

For backend advisory checks, use a separate tooling environment with pip-audit and scan `backend/.venv/Lib/site-packages` with `--vulnerability-service osv`; do not install auditing tools into production just to run tests. All network checks in this sprint transmitted only dependency identifiers/versions or fetched public security guidance, never health records.

## Regression evidence

| Check | Result / scope |
| --- | --- |
| Backend full suite | **233 passed, 0 failed, 0 skipped** in 57.36 seconds; includes 37 new security cases and existing auth/ownership/history/research tests. One pre-existing Starlette/httpx deprecation warning. |
| Frontend unit suite | **65 passed, 0 failed, 0 skipped** in 20.48 seconds, 12 files; private request options, safe 5xx display and production API configuration regressions included. |
| Playwright | **16 passed, 0 failed, 0 skipped** in 34.4 seconds, full suite; fresh isolated synthetic SQLite migration target and loopback ports 8014/5184. Includes new export-CSRF/literal-consent/header/revoked-cookie regression plus existing two-account isolation, logout, history, diary, Insights and mobile/keyboard/Attack Mode flows. |
| Production frontend build | Passed TypeScript and Vite build; no new frontend dependency. |
| Dependency checks | OSV 43 packages, zero known advisories/skips after updates; npm zero known advisories; pip dependency compatibility passed. |
| Documentation / diff scope | Passed: 30 local Markdown links, UTF-8/whitespace checks including all new files, credential-pattern review and exact 18-file source scope at the pre-publication checkpoint; no unrelated files included. Generated databases, environments, audit JSON, logs, builds and browser artifacts are ignored, not source changes. The original local SQLite database and all nine migration-file checksums stayed unchanged during final review. |

New [backend regressions](../backend/tests/test_security.py) cover production fail-closed settings and import failure, HTTPS/spoofed forwarding/Host, generic early/late exceptions without value-bearing context, validation metadata, strict consent, unauthorized export, foreign CSRF, expiry/logout, invalid stored expiry, denied preflight and sliding-window expiry. Existing [auth tests](../backend/tests/test_auth.py) enforce every health route and two-account object isolation; [research tests](../backend/tests/test_research_quality.py) retain history, consent and zero-verified-outcome semantics. Frontend evidence is in [API tests](../frontend/src/api.test.ts) and [browser security regression](../frontend/e2e/security.pw.ts).

Earlier validation: targeted backend run passed 62; first full suite passed 223 before two additional regressions. Initial browser run had **15 passed / 1 failed**: the new test's redundant account creation/login/cleanup exhausted the existing 30-per-IP limiter and cleanup returned 429. The new browser test was narrowed to export security and deletion-cookie replay, with existing browser/backend tests retaining foreign-account and logout coverage; no limiter thresholds or authorization assertions were weakened. A fresh synthetic API with final code then passed all 16. Browser runtime emitted the existing NO_COLOR/FORCE_COLOR environment warning. Private synthetic artifacts from failed runs stay ignored; no real database was involved.

## Remaining risks and production blockers

These are known limitations or potential risks, **not newly proven exploits**:

1. No managed HTTPS deployment, independent penetration test, production PostgreSQL/TLS execution, disk/backup encryption, key management, retention purge/restore-erasure verification or disaster-recovery/incident exercise. Proxy trust and production frontend CSP/security headers require host-specific verification.
2. Authentication throttling is process-local and can reset on restart or be multiplied across workers; high-cardinality keys and expensive password work need shared bounded rate limits, request/body/time limits and resource controls. No tested distributed defense, staff MFA, account verification/recovery or session/device management.
3. Administrators can access files/CLI and alter application-enforced history; no tamper-evident immutable storage. Legacy episode/wellness edits lack full historical versions. Extensive unpaginated histories/exports need load testing and resource limits. No raw-error logs means production monitoring needs approved value-free counters and incident correlation.
4. Private exports and backups persist outside account deletion. No automatic revocation of downloaded files; no claim of automatic de-identification. Browser/OS extensions, physical access and accidental user sharing remain outside app control. Retention/withdrawal controls must map every copy.
5. No durable research enrollment, independently verified onset/coverage journal, appointed institutional PI/controller, approved protocol/ethics/privacy review or lawful transfer grant. Park remains NO-GO for strict next-24-hour onset evaluation; N1-Headache contact/publication routes do not grant access. Sprint 13's pilot remains a proposal, not an approved study.
6. Synthetic tests and point-in-time advisory scans are incomplete evidence. Screen-reader/real-device comfort, production load/concurrency, dependency authenticity, privileged access and cross-account attack testing need independent review. No clinical effectiveness, diagnosis/treatment advice or prediction readiness is asserted.

Required next steps: independent security/privacy review; institutional ownership and threat-model sign-off; deploy only after managed secrets/storage/TLS/proxy, shared abuse defenses, recovery and retention/incident controls are implemented and verified; separately authorize research enrollment/evidence infrastructure and ethics review before any real participant collection. Do not bypass the [research readiness gate](RESEARCH_READINESS_GATE.md) because this test suite passes.

## Changed source files

- Backend: `app/security.py`, `app/main.py`, `app/auth.py`, `tests/test_security.py`, `tests/test_auth.py`, `.env.example`, `requirements.txt`, `requirements.lock.txt`, `requirements-ml.lock.txt`.
- Frontend: `src/securityConfig.ts`, `src/api.ts`, `src/api.test.ts`, `vite.config.ts`, `e2e/security.pw.ts`, `.env.example`.
- Documentation: this audit, `docs/authentication-privacy.md`, `README.md`.

No schema migration, user-record correction, prediction endpoint or production deployment is part of this change. Final review authorizes publication of these intended files after checks, not deployment or automatic merging.

## Final security review (2026-10-28)

Reviewed the complete intended diff against fetched `origin/main`; the branch base matched main. Review identified that the original host validator rejected dangerous delimiters but still accepted malformed labels/control characters. It now validates DNS labels and bracketed IPv6 explicitly; five malformed-host regressions and three omitted-production-setting regressions were added. Valid loopback defaults remain supported.

Fresh final checks passed: backend 233/233, frontend 65/65, Playwright 16/16, production build, pip compatibility, OSV (43 packages, zero advisories or skips), npm audit (zero advisories), and documentation/diff/privacy scope checks. All suites had zero failures and zero skips. Existing upstream Starlette/httpx and browser environment warnings remain. No existing database or migration file changed; no real record was used as a fixture. Synthetic test servers were stopped after review. Reports, logs, temporary tooling and databases remain ignored. Publication does not resolve the production/infrastructure/research blockers listed above.
