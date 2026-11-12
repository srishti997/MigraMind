# Phase 9: authentication abuse protection audit and design

## Phase 9A: approved guard-ordering remediation (2026-11-12)

Verified `security/auth-abuse-protection` at PR #23 merge `3edd914`; starting changes were only the two expected uncommitted Phase 9 reports. Both original report bodies were preserved. **The narrowly approved P1 ordering fix is now implemented; the audit/design snapshot below remains historical.** No other proposed remediation is implemented.

### Implemented contract

Only [login and registration](../backend/app/auth.py#L183) change: `previous = session(request, s)` and existing `csrf(request, previous)` now execute **before** `attempts(request, data.email)`. Mode restrictions stay first, and password lookup/hash/verification and session issuance stay after accounting. There is no middleware/dependency restructuring or new helper/limiter architecture.

Request order is now: existing transport/host/demo/CORS middleware → FastAPI JSON/schema validation and database dependency → applicable mode refusal → existing session validity and exact-Origin/session-bound-CSRF guards → unchanged IP then normalized-account budgets → existing password/database work → unchanged session rotation/cookies. Protected endpoints such as global sign-out retain their existing authenticated/CSRF dependency ordering.

- Applicable Origin/CSRF/missing-invalid-expired-session rejections remain **403 with the same guard details**, without appending, clearing or otherwise modifying either budget, performing password work, or creating/deleting users/sessions.
- Validly guarded submissions retain **30/IP and 10/account per 900 seconds**, including successes, incorrect known/unknown passwords and duplicate/new registrations. IP still runs first; an account-throttled request still spends its IP slot. Existing 429 detail and `Retry-After: 900` remain.
- When a request is both guard-invalid and already throttled, the guard's **403 now precedes 429**. This intentional precedence change is necessary to prevent invalid requests spending/examining protected budget accounting. Validly guarded requests retain their previous 429 behavior. No account-existence detail was added.
- Malformed JSON/schema still returns **422 before handler accounting**, including requests that also have invalid guards. Dependency/DB failures before the handler cannot reach `attempts()`; protected authentication/CSRF dependency failures remain uncharged. No new application body-size or ingress limit was added.
- Anonymous bootstrap is intentionally unchanged: a valid session costs nothing; otherwise its existing IP-only budget precedes anonymous session creation. Registration enumeration, shared account budgets, success accounting, CSRF-valid targeting, process-local state and resource bounds remain unchanged.
- Cookie attributes, password hashing/verification, absolute expiry, disabled-by-default idle flag, ordinary/global logout and owner isolation are untouched. No existing production/demo environment was enabled.

### Focused regression evidence

[test_auth_guard_order.py](../backend/tests/test_auth_guard_order.py) adds **31 synthetic cases**, reusing the existing isolated `clients` fixture:

- Sixteen login/register cases cover missing/untrusted Origin, missing/invalid/other-session CSRF, missing/invalid/expired sessions; exact budget snapshots and user/session row counts stay unchanged. Password hash/verify methods are guarded by fail-on-call spies.
- Four bounded poisoning regressions send ten sequential rejected requests per fixture, for login/register and same/different client IPs. No budget key is created; target and unrelated account then log in successfully and each consumes only its own account slot. No load/credential-spraying run.
- One accounting case checks normalized email, successful registration/login, duplicate registration and identical generic known/unknown wrong-password errors with exact IP/account counts.
- Four exhaustion cases retain IP/account limits and reject before password work; invalid guards remain uncharged even when counters are already full.
- Four malformed JSON/schema cases preserve 422 and budgets; two protected dependency cases preserve missing-auth/invalid-Origin rejection before accounting on global logout/account deletion. No actual account deletion occurs in these new tests.

The missing-Origin login case was run against the **old** implementation first: **1 expected failure / 30 deselected**, 3.02s pytest / 4.87s wall. Its 403 response was correct but budget snapshot changed, proving the test detects the defect. After the two-route reorder the focused module passed **31/31**, 7.49s pytest / 9.11s wall. This deliberate red/green run is not a flaky retry; no assertion/timeout/threshold was weakened.

### Actual Phase 9A validation and safe reproduction

All execution was on this Windows machine in new `%TEMP%/migramind-phase9a-elhggdyb`. Prior Phase 9 reports were saved there as documentation-only baselines. Copied tracked permitted backend/frontend source and the new regression; no actual environment, database/WAL/SHM, health record, backup, export, secret or user profile was opened/copied. Reused isolated Python **3.13.12** dependencies read-only and copied matching Node dependencies after package-lock byte comparison; no package installation or environment upgrade.

Backend children received a restricted OS environment plus `APP_ENV=development`, `DATA_MODE=local`, `DATABASE_URL=sqlite://`, `SESSION_HOURS=12`, `SESSION_IDLE_TIMEOUT_ENABLED=false`, `PYTHON_DOTENV_DISABLED=1`, `PYTHONDONTWRITEBYTECODE=1`, copied backend `PYTHONPATH` and private TEMP/TMP. Fixtures alone create/dispose new in-memory or pytest-temporary synthetic databases. No existing service/database, migration/provisioning command, external request or emergency handler was used.

| Check | Exact Phase 9A outcome |
| --- | --- |
| Old-code regression | **1 expected failure / 30 deselected**, 3.02s pytest / 4.87s wall; 120s cap |
| Final focused module | **31 passed**, 7.49s pytest / 9.11s wall; 120s cap |
| Broader safe backend/offline research | **314 passed / 8 deselected**, 103.31s pytest / 106.18s wall; 600s cap; includes the same 31 regressions |
| Full frontend | **109 passed / 17 files**, 113.44s suite / 116.30s wall; 360s cap |
| TypeScript | **Passed**, 8.64s wall; 180s cap |
| Local production bundle | **Passed**, 5.77s Vite / 7.36s wall; 180s cap |
| Synthetic production bundle | **Passed**, 5.60s Vite / 6.89s wall; 180s cap |
| Final documentation/integrity | **65 local links / 38 source references** verified; **137 tested source/declaration files** match; both original Phase 9 report bodies preserved; exact two-route reorder and four intended paths confirmed; `git diff --check` passed |

No unexpected final failure, timeout, retry or assertion adjustment. The initial red case intentionally exercised pre-fix code; only the two route orders changed between red and green. Existing Starlette/httpx deprecation and temporary external-outDir warnings remain. Build checks used the package's existing `tsc -b` and Vite steps directly, with new temporary outputs, empty `VITE_API_URL` and respective `VITE_DATA_MODE=local`/`synthetic`; no existing directory was emptied. Shared TypeScript checking precedes both modes, with unchanged frontend source.

From the new filtered source and explicit environment above:

```text
# Copied backend; every basetemp must be a new path owned by this run.
<isolated-python> -B -m pytest -q -ra tests/test_auth_guard_order.py --basetemp <new-root>/focused-data -p no:cacheprovider
<isolated-python> -B -m pytest -q -ra --ignore=tests/test_deployment.py -k "not migration" --basetemp <new-root>/backend-data -p no:cacheprovider
# Copied frontend with matching copied dependencies.
node node_modules/vitest/vitest.mjs run --maxWorkers=1
node node_modules/typescript/bin/tsc -b
node node_modules/vite/bin/vite.js build --outDir <new-root>/local-dist
node node_modules/vite/bin/vite.js build --outDir <new-root>/synthetic-dist
```

The **eight migration-named cases were deselected**, and the entire deployment/provisioning module was excluded rather than invoking its scripts. This is not the complete CI backend suite. No browser, Linux, live proxy, real restart/multiworker, load or fresh-dependency/security scan was run; no cross-platform/production readiness claim. Evidence outside Git: original report baselines, `red.json`/`red.log`, `backend-results.json`, focused/backend logs, `frontend-results.json` and frontend/TypeScript/build logs. Prior Phase 9 audit results below are separate historical runs.

### Remaining boundary and rollback

**A9-01 is addressed for requests rejected by existing guards**, not all authentication denial of service. An attacker can obtain a legitimate anonymous session/CSRF and target an account; shared NAT/account budgets, successful-attempt accounting, cross-worker/restart limits, resource/cardinality bounds and registration membership disclosure remain open. Invalid-guard traffic no longer receives this handler's IP limiter: parsing/session lookup/guard work still needs approved ingress/resource defenses. Do not claim P1 closes SP4-04/S7-04 or enables public/real-health use.

Only the two route sequences, new regression module and two existing reports change. No migration, schema, dependency, persistent throttle, production/deployment setting, recovery flow, idle behavior or UI change. If separately authorized, rollback reverts the route ordering and corresponding regression expectations; no database/session/password restoration is needed. Such rollback reintroduces invalid-request budget poisoning. Further abuse-policy/durability/enrollment changes still require approval.

## Historical Phase 9 audit and design — before approved P1 implementation

Assessment: **2026-11-12, Asia/Calcutta**. Starting branch `security/auth-abuse-protection` was clean and identical to local `main`, **`3edd914dabd36a5fdcd22abb41fc4e53a6e8453f`**, merge of PR #23. Local Git ancestry was verified; no remote fetch or GitHub status check was performed. **Audit/design only: no authentication, configuration, migration or dependency change is implemented.**

## Decision and scope

A rate limiter is a temporary budget for requests. MigraMind has separate IP and normalized-account budgets, but rejected login/registration requests can spend them **before** the server checks Origin/CSRF. A person who knows a candidate email can therefore block its next login without knowing a password or owning an anonymous session. This is an availability issue, not a demonstrated password bypass or health-record disclosure.

The smallest first implementation should move existing login/register session and Origin/CSRF checks before `attempts()`, with focused regressions. This needs separate approval. It removes the verified invalid-request budget poisoning, **not** targeted denial by an attacker who obtains a valid anonymous session/CSRF pair. Shared/persistent throttling and enrollment privacy remain separate decisions. Public or real-health release remains **NO-GO**; existing [security/privacy](SECURITY_PRIVACY_AUDIT.md), [session security](SESSION_SECURITY_PLAN.md), [idle-timeout](SESSION_IDLE_TIMEOUT_PLAN.md) and [release gates](RELEASE_READINESS.md) are not superseded.

| Finding | Severity / prerequisites | Decision |
| --- | --- | --- |
| A9-01: rejected Origin/CSRF requests consume shared account/IP budgets | **Medium**; reachable writable local authentication API and candidate identifier; no cookie/password needed | Highest-priority verified fix; public-auth availability blocker |
| A9-02: process-local, shared-across-action throttling | **Medium**; reachable service, restart/multiple workers or attacker with a valid anonymous session | Public-hosting blocker; not a persistence failure of login sessions |
| A9-03: registration distinguishes membership | **Low**; writable local registration, candidate email and valid anonymous Origin/CSRF context | Enrollment/privacy decision before real-user registration |
| A9-04: incomplete resource and cardinality bounds | **Medium**; exposed/direct API or sufficiently many clients/identifiers; no resource-exhaustion attack attempted | Public-hosting/resource-control gate; mostly source evidence |

A9-01/02/04 refine existing **SP4-04 / S7-04**; A9-03 confirms **S7-05**. These are not four new unrelated vulnerabilities or reasons to lower existing findings. No Critical/High issue, account compromise or cross-account disclosure was established by these bounded observations.

## Implemented request and accounting order

Evidence refers to this merged source snapshot; earlier reports' line numbers and claims may describe historical code.

1. **Transport/middleware:** [PrivateBoundary](../backend/app/security.py#L112) rejects insecure production HTTP and sanitizes unexpected errors/headers. The [application](../backend/app/main.py#L181) adds private response handling, host validation, demo boundary and CORS. A rejected host, demo write or CORS preflight never enters an auth handler. CORS is not a substitute for server-side Origin validation: ordinary POST requests can reach handlers even when browsers cannot read their response. The [demo boundary](../backend/app/deployment.py#L39) rejects registration/global revocation/account deletion; demo login rejects non-demo identifiers before accounting. These exceptions matter: the local registration finding is not an open-registration claim about the read-only demo.
2. **Parsing/body validation:** FastAPI parses JSON and validates [Credentials/Registration](../backend/app/auth.py#L33) before executing login/register. Email is length-bounded (3–254 before normalization), stripped and lowercased, with simple `@`/whitespace checks; password is 1–128 for login and 12–128 for registration, display name 1–100, extra fields forbidden. It is not email-ownership verification or full email canonicalization. Invalid bodies return value-free **422** via [main.py](../backend/app/main.py#L181); they do not spend auth budgets. Parsing happens before the limiter and string limits are not HTTP byte limits.
3. **Login/register accounting:** [attempts](../backend/app/auth.py#L144) first checks `('ip', request.client.host or 'unknown')`, limit **30**, then `('account', sha256(normalized_email))`, limit **10**, both per **900 seconds**. Origin, cookie/session and CSRF have not yet been checked. These are global per-process namespaces, not endpoint-specific or IP/account-pair keys.
4. **Session and guards:** [register](../backend/app/auth.py#L183) / [login](../backend/app/auth.py#L194) then look up a valid session and run [csrf](../backend/app/auth.py#L109): exact allowed Origin, existing unexpired session and matching `X-CSRF-Token`. No guard-rejected request hashes/verifies a password or creates a user/session, but its counters remain charged.
5. **Password/database work:** registration hashes with [Argon2id](../backend/app/auth.py#L17), inserts/flushes and returns generic 400 on duplicate integrity failure; success is 201. Login looks up the normalized email and verifies the stored or dummy Argon2id hash. Missing-user and wrong-password responses are the same **401** detail. Successful local login can rehash if parameters changed. Argon2 settings are time cost 3, memory 65,536 KiB, parallelism 2. A dummy hash reduces an obvious missing-user fast path; it does not establish constant-time end-to-end behavior.
6. **Session issuance:** [issue](../backend/app/auth.py#L135) replaces the previous browser session, creates new random cookie/CSRF values, stores the cookie digest and fixed expiry in the database, commits, and sets HttpOnly/SameSite=Lax cookies (Secure/`__Host-` in production). Successful login/register **also consume** budgets; success does not reset failures. Existing independent sessions remain valid. Phase 8 idle protection remains disabled by default.

### Other endpoints sharing the limiter

| Request | Exact relevant behavior |
| --- | --- |
| `GET /api/auth/session` | [bootstrap](../backend/app/auth.py#L148): valid existing session returns without accounting or renewal. Otherwise checks IP budget **only**, deletes absolutely expired session rows and creates a one-hour anonymous row. New session creation can be denied by unrelated auth traffic on that IP. |
| `POST /api/auth/logout` | [logout](../backend/app/auth.py#L204): authenticated session and Origin/CSRF dependency first; delete current row and cookie; no `attempts()` call. |
| `POST /api/auth/logout-all` | [global revocation](../backend/app/auth.py#L209): `require_user` and Origin/CSRF run before handler; demo refusal, then shared IP/account accounting, then password verification and persistent all-session deletion. Invalid guards here do **not** consume budgets. Wrong password does; throttling can block this incident-response action. |
| `DELETE /api/account` | [deletion](../backend/app/auth.py#L225): authenticated Origin/CSRF dependency before shared accounting, password/confirmation and owned-data deletion. Reviewed statically; existing tests erase synthetic fixture records only. No real deletion performed. |
| Collection/research throttles | Same Limiter object, distinct `collection`/research key namespaces; [collection wiring](../backend/app/main.py#L319). Not an auth-budget reset or durable abuse store. |

For protected endpoints, dependencies can reject authentication/CSRF before body-validation errors are returned. Do not generalize login/register's body-first handler accounting to all mutations. No password reset, forgot-password, email verification, recovery token or password-change endpoint is implemented in [auth.py](../backend/app/auth.py#L183); no recovery enumeration/token vulnerability was invented. The frontend explicitly discloses missing recovery.

## Limiter state, keys, boundaries and IP trust

[Limiter](../backend/app/auth.py#L66) is a Python `defaultdict(deque)` plus thread lock owned by each Authentication instance. It is **not** a database table, external shared store or durable lockout. Separate workers/instances each have their own limits; restart loses counters. Existing database session revocation persists independently of this state. A fresh Authentication instance against the same synthetic session factory accepted a login that the first instance had throttled.

Each check scans every key, removes timestamps **<= now − 900**, deletes empty keys, then counts and appends only if under the limit. Time is process-monotonic, so wall-clock jumps do not change these windows. No timer cleanup or maximum key count exists; old keys remain until another check. Scanning every live key under one lock is O(number of keys); high-cardinality memory/CPU impact is a source-derived concern, not a measured outage. `clear()` is a test utility, not a protected public reset endpoint, and does not itself acquire the lock.

If IP rejects, account is untouched. If IP passes but account rejects, the IP timestamp **has already been appended**, while the full account window is not appended. Rejected requests do not themselves push that full account deadline later, but repeated requests can refill slots as they age. Exact expiry at 900 seconds was observed. `Retry-After: 900` is constant, not the actual time until the oldest entry expires; it can overstate the wait. Successes, registration failures and reauthentication share account budgets. One account/IP can therefore affect other flows; one IP affects unrelated accounts and anonymous bootstrap. Existing authenticated reads/logout remain usable, subject to normal session rules.

The application uses ASGI `request.client.host`; it does **not** independently parse arbitrary X-Forwarded-For. A direct TestClient request with a spoofed header still charged the actual test client's IP. This does not test a network proxy.

**Qualification of historical SP4-04:** the reviewed [launcher](../backend/app/serve.py#L29) sets one worker, loopback binding, `proxy_headers=security.production` and `forwarded_allow_ips='127.0.0.1'`. The [nginx template](../deploy/nginx-demo.conf.example#L27) overwrites X-Forwarded-For with `$remote_addr` and forwards via loopback. Installed locked Uvicorn middleware was inspected read-only: forwarded client identity is adopted only for trusted peers. Thus, with these exact production templates and no intervening proxy, external clients are **not necessarily all counted as loopback**. The older unconditional loopback concern is too broad for this launcher. Actual topology/firewall/proxy settings were not inspected or deployed. Additional upstream proxies may aggregate clients; trusting arbitrary forwarding chains or `*` would permit spoofing. A hostile local process can reach trusted loopback, so this is not protection against a compromised host.

The nginx template also proposes **64k** body size, **5 requests/second**, burst **20**, 429, timeouts and disabled access logs. It is not evidence these controls are enabled. Direct local API has no corresponding application body-size or Argon2 concurrency bound. Invalid/oversize validation can occur outside auth budgets; no flood or password-work saturation test was performed.

## Verified findings and safe reproductions

All reproductions below require a **new filtered source tree** and temporary synthetic fixtures, never an existing server/account/database. Use the `clients`, `register` and `login` helpers in [test_auth.py](../backend/tests/test_auth.py#L13). Never print cookies, CSRF, hashes, passwords or record contents. The temporary observation tests retained outside Git are the executable detailed evidence.

### A9-01 — Medium: unauthenticated budget poisoning

Register only `target@example.test` in the synthetic fixture and clear the test limiter. A second TestClient uses a different documentation-only IP and no cookies. Submit exactly **ten sequential**, valid-shaped login requests for that normalized identifier with an untrusted Origin. All return **403**. A valid-password login by the fixture owner from a different IP then returns **429**; its existing account read remains **200**. Repeat in an independent fixture using registration instead of login: same result. Missing Origin/CSRF variants each charge both budgets; six one-request parameter cases confirm the order. No password guess or external request is needed.

The attacker can send requests using a non-browser client. This does not prove cross-site JavaScript can bypass a preflight, steal tokens, revoke sessions or read health data. The effect is temporary access/reauthentication denial, not an account lock stored in the database. Shared IP poisoning can also block new bootstrap: a synthetic limiter prefilled with 29 timestamps plus one guard-rejected request reaches 30. This used direct test-state setup, not a 30-request load run.

### A9-02 — Medium: local state and targeted lockout tradeoff

Fill only the synthetic account's limiter with ten test timestamps; the first application's login returns 429. Construct a fresh Authentication instance with the **same synthetic database dependency**: session lookup and valid login work. No OS restart/multiworker load was run; the exact object-local state and this fresh-instance observation support the restart/worker limitation. A legitimate anonymous session/CSRF is obtainable by attackers too, so correcting A9-01 alone leaves account-only budget denial possible. Distributed IPs bypass per-IP aggregation, but increasing the global account limit is not a complete design.

### A9-03 — Low: membership distinction, not login-message enumeration

With valid synthetic anonymous guards, new registration is **201 with authenticated account/session state**; duplicate registration is **400**, `Unable to create an account with those details`. Generic duplicate wording does not hide that distinction. Wrong existing-user and unknown-user logins both return **401**, `Email or password is incorrect`; temporary instrumentation confirmed both execute password verification. No statistical timing study was run. Demo registration is blocked; no actual user address was queried.

### A9-04 — Medium: resource controls are incomplete

Static evidence: body parsing precedes limiter, no application byte cap, 64 MiB Argon2 operations, unbounded live-key map and whole-map cleanup scan. A small invalid body returns 422 without budget accounting; this task did not repeat the historical oversized-body experiment or test resource exhaustion. An attacker still needs reachable input capacity; exact availability impact depends on edge/runtime resources. Do not weaken Argon2 to address missing ingress/concurrency limits.

## Proposed remediation options — approval required

### P1: smallest compatible change

Change only the sequence in login and registration: keep mode refusal and body contract; resolve `previous`, run existing exact-Origin and CSRF checks, **then** call existing `attempts(request, data.email)` before user lookup/Argon2/insert. Reuse current errors, keys, limits, window and session issuance. Add permanent focused tests that fail under today's sequence. No UI, dependency, infrastructure, migration or production setting change is needed.

Acceptance:

- Missing/untrusted Origin, absent/invalid/mismatched CSRF and missing/expired anonymous sessions return existing guard errors **without charging either login/register budget**; do not invoke password work or mutate users/sessions.
- Valid guards still account known/unknown identifiers, successful/failed login, successful/duplicate registration consistently and before Argon2. Existing 30/IP, 10/account, expiry, generic errors, cookies, session rotation and demo refusal are unchanged.
- Ten invalid-guard requests cannot cause the formerly available owner's valid login to return 429. Cross-account and authenticated logout/global-revocation behavior remain unchanged.
- Document the tradeoff: invalid-guard traffic no longer receives this handler-level IP budget. Existing parser/guard work still needs ingress controls. If an early abuse budget is desired, design a **separate, bounded IP-only preauthentication namespace**, never account keys, with independent bootstrap/legitimate-user availability analysis. Do not quietly introduce that policy in P1.

P1 does **not** prevent valid-CSRF account targeting, global budget consumption by successes, shared-network overblocking, process reset, parser exhaustion or membership disclosure. Its release scope is the verified ordering defect, not closure of SP4-04.

### P2: decide account/IP policy and durability separately

| Option | Benefits | Risks / approval needs |
| --- | --- | --- |
| IP-only budget | Cheap aggregate bound; cannot name an unrelated account key | NAT/schools/VPNs unfairly share limits; botnets evade it; trusted proxy identity required |
| Account-only hard ceiling (current) | Aggregates guessing across IPs | Attacker can block a known account, including owner recovery/revocation; normalized identifiers are personal information |
| IP + account/IP pair primary budgets | Limits one source's guesses without immediately locking a target globally | Distributed attacks still need aggregate detection/controls; NAT and key-cardinality caps matter |
| Conservative account aggregate escalation | Detects distributed abuse; may trigger bounded backoff or operator-reviewed intervention instead of unconditional lockout | Requires a concrete safe policy, generic responses and recovery/accessibility review; in-process sleep is not a safe concurrency solution |
| Existing trusted edge controls | Reuses template infrastructure for body/time/IP bounds | Not durable account state; no automatic assurance without topology tests; proxy config changes need approval |
| Existing application database, dedicated abuse records | Potential transactional cross-worker/restart accounting without Redis | **No suitable existing abuse table exists**. A new approved additive schema/design, retention/index/locking/failure policy and migration tests would be necessary; do not overload LoginSession, health tables or demo markers. SQLite writer contention and PostgreSQL semantics need separate evidence. |

Recommend retaining verified ingress IP bounds plus bounded account/IP-pair accounting, with separately designed account-aggregate escalation. Thresholds, success accounting and whether security reauthentication needs independent namespaces are unresolved policy decisions; no new numeric policy is asserted. Do not silently drop distributed-guessing protection while removing a hard account ceiling. No Redis/new service is recommended for this local prototype. Current supported single-worker/loopback operation reduces exposure but does not make state persistent. Public multiworker/restart assurance remains blocked until an approved shared design is tested.

### P3: enrollment and disclosure policy

Choose explicitly between supervised/invited enrollment and an approved public enrollment/verification flow. Making duplicate text generic while retaining immediate auto-login for new registrations cannot make responses indistinguishable. A truly generic accepted response would require changed enrollment semantics and possibly verified delivery/identity workflows; these are **not** approved here. Do not invent password-reset shortcuts or send email. Preserve generic login errors and the dummy hash; assess timing with a separately authorized bounded methodology before claiming resistance.

## Privacy, errors and logging rules

Current account keys are unkeyed SHA-256 of normalized emails. This avoids plaintext map keys but is **not anonymization**: candidate addresses can be hashed offline. IPs and stable identifier digests can be personal data. Keep counters purpose-limited, time-bounded and inaccessible to browser/storage exports; no health values in keys. Durable designs need explicit retention/deletion, bounded cardinality and restricted operational access. A keyed identifier digest would require approved key lifecycle/rotation, not a hardcoded key or silent new secret.

Retain one generic 401 login message for missing-user/wrong-password outcomes; value-free 403 for guard failures; generic 429 and a conservatively computed retry interval without telling which account exists or which budget filled. Preserve value-free 422/503/500 responses. Do not falsely return login success for unknown accounts. A registration response policy must align with actual enrollment behavior rather than wording alone.

Never log bodies, passwords, password hashes, cookies, CSRF/reset tokens, raw candidate emails, raw authorization headers, health values, unfiltered exception text or query strings. Prefer aggregate outcome/action counters and coarse durations; any security-event identifiers/IP logging requires an explicit retention/access policy. [PrivateBoundary](../backend/app/security.py#L112), [private validation](../backend/app/main.py#L181), [launcher](../backend/app/serve.py#L29) and sample nginx suppress sensitive traces/access logs, but arbitrary development launch flags and OS/proxy log settings remain unverified. No sensitive logs or actual environment files were inspected.

## Synthetic regression specification

| Test group | Acceptance for a future implementation |
| --- | --- |
| Wrong and valid login | Known/unknown generic 401, dummy verification, no secret echo; valid password succeeds and rotates previous session; verify chosen success accounting |
| Invalid guards | Every missing/untrusted Origin, stale/mismatched CSRF, missing/expired session consumes no protected account budget; independent IP and account assertions; check login and register, existing protected reauth order retained |
| Exhaustion and boundaries | Limit−1/limit/limit+1, exactly 900s, partial window ageing, real Retry-After policy, no rejected-request indefinite extension, cleanup/cardinality caps |
| Targeted/shared-network abuse | Different attacker/victim IPs, same normalized account; unrelated accounts; multiple legitimate accounts behind one IP; account/IP and aggregate policy tested explicitly |
| Multiple instances/restart | Shared synthetic on-disk store only if approved: independent processes/engines, simultaneous final-slot contenders, restart before deadline, outage/failure policy, no timestamp rollback or double allowance; today's fresh-instance observation is not passing durable protection |
| Registration | New vs duplicate response policy, capitalization/whitespace normalization, concurrent unique insert, demo rejection and no partial account/session creation |
| Proxy trust | Direct spoofed forwarded headers ignored; exact trusted peer forwarding and untrusted peer rejection; rewritten single-hop chain and extra upstream proxy; do not infer this from TestClient alone |
| Session compatibility | CSRF, absolute/disabled idle behavior, stale cookies, current/global logout, wrong password, account isolation and persistent revocation unchanged |
| Resource/privacy | Bounded synthetic body/key tests, no load flood; no secrets/health in errors/logs, bounded retention/cleanup and concurrency; do not decrease Argon2 cost |

## Actual execution, reproduction and limitations

New evidence root: `%TEMP%/migramind-phase9-audit-dzbqyiog`. Copied only tracked backend `.py`, `.ini`, `.txt` source/dependency declarations, excluding data/backups/exports; no actual environment, SQLite/WAL/SHM, account, backup, health record, key or secret file was opened/copied. Reused the earlier isolated Python **3.13.12** environment read-only; no install/upgrade or fresh-install claim. Restricted child environment, private TEMP/TMP, `APP_ENV=development`, `DATA_MODE=local`, `DATABASE_URL=sqlite://`, `SESSION_HOURS=12`, `SESSION_IDLE_TIMEOUT_ENABLED=false`, `PYTHON_DOTENV_DISABLED=1`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=<new-source>/backend`. Existing fixtures create/dispose their own synthetic in-memory or pytest-temporary engines. No server socket, external request, provisioning or migration command ran.

| Check | Exact result |
| --- | --- |
| Initial existing + temporary observation batch | **117 passed / 1 failed / 1 deselected**, 26.29s pytest / 28.38s wall; 300s cap |
| Existing suite subset within that batch | **103 passed**, auth/security/global logout/idle modules; one migration case deliberately deselected; no existing test failure |
| Corrected temporary observations | **15 passed**, 3.16s pytest / 4.36s wall; 180s cap; overlap the first batch, not 15 additional existing workflows |
| Unique final coverage | **118 selected cases pass across the initial and affected runs**; not a claim of a clean single full-suite run or fixed vulnerabilities |
| Static source/proxy review | Authentication/session models, guards, validation, demo boundary, frontend errors, existing tests, launcher, nginx/systemd and CI reviewed; installed Uvicorn trusted-peer implementation inspected read-only |
| Documentation/integrity | **62 local links / 37 source-line references** checked; **65 tested backend source/declaration files** match the repository; prior release report body preserved; only the two expected documentation paths changed; `git diff --check` passed |

The single failed temporary observation tried to monkeypatch a read-only `PasswordHasher` instance method. Corrected only the temporary spy to patch its class method, then reran the 15 observations once under unchanged bounds. Initial result/log are retained. All 103 existing selected tests passed on the first run. No application change, threshold increase, hidden retry or load run. One existing Starlette/httpx deprecation warning remains. Passing observation tests confirm current vulnerabilities/limitations; they are **not remediation regressions** until their expectations are reversed for an approved fix.

From the new filtered backend copy and restricted environment above:

```text
<isolated-python> -B -m pytest -q -ra tests/test_auth.py tests/test_security.py tests/test_logout_all.py tests/test_session_idle.py tests/test_phase9_observations.py -k "not migration" --basetemp <new-root>/pytest-data -p no:cacheprovider
<isolated-python> -B -m pytest -q -ra tests/test_phase9_observations.py --basetemp <new-root>/observation-final-data -p no:cacheprovider
```

Use a **different, previously nonexistent** basetemp directory on repetition: pytest owns that target. `test_phase9_observations.py` exists only in the recorded temporary source, not the repository. Evidence includes the temporary scripts, `results.json`, `checks.log`, `observation-final.json`, `observation-final.log` and the corrected observation source. None prints credentials, tokens, health values or successful response bodies. Exact bounded reproduction logic is described per finding above; existing permanent tests are linked, and proposed permanent tests require implementation approval.

No complete backend/frontend/browser/build/dependency-security suite was rerun for this documentation-only task. No Linux, real proxy, OS process restart, simultaneous worker, physical device, external recovery/email, statistical timing, sustained attack, production topology or real-data check was performed. Historical Phase 8 results are preserved as historical evidence. No current advisory/third-party recommendation fetch was performed under the no-external-requests boundary.

## Rollout, rollback and unresolved decisions

1. Approve only P1 ordering plus permanent synthetic regressions first; review its diff and run focused/full safe suites and normal isolated CI before merge. Preserve generic errors, data, session architecture and disabled idle flag.
2. Independently decide public enrollment, threat model, attempt/success namespaces, account-target denial policy, NAT fairness, proxy topology, body/concurrency/cardinality limits and persistent/shared-state failure policy. A database-backed design needs explicit schema approval; do not implement a process-local workaround and claim cross-worker protection.
3. Before any exposure, validate actual trusted ingress, bounded work, privacy-safe operational evidence and restart/worker behavior; close existing storage, recovery, retention, accessibility, research and deployment gates. Local synthetic demo approval is not public/clinical approval.
4. P1 rollback, if separately authorized, reverts only order/tests, requires no data/schema restoration and reintroduces A9-01. Process-local counters may reset on deployment/restart; never restore sessions/password hashes/backups to reset limits. A future persistent design needs its own forward-compatible rollout, retention and rollback plan. Do not change defaults or enable idle timeout as part of abuse remediation.

**Approval is required before remediation.** Only this plan and the release-readiness link/status are changed in Phase 9. No authentication implementation, migration, dependency lock, production configuration, existing data, commit, push, PR, merge or deployment change.
