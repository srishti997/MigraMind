# Pull Request #1 security review

Current disposition: **MERGE READY for the reviewed local prototype hardening change, once the approved commit is pushed and the updated PR head is verified. Production security readiness: NOT READY.** Re-verification found no remaining confirmed critical/high-severity issue within the loopback-only prototype scope. The original published revision below was NOT MERGE READY; its high-severity session/UI findings are addressed by this hardening change. Pushing requires separate user approval; no merge or public deployment is authorized.

## Scope and reviewed revision

GitHub PR head `refs/pull/1/head` and `feat/authentication-privacy` both resolved to `9813fc35da17eedc6fbf11f1923652f3d8047f46`; main resolved to `3945a3fae997cdb141e80962665d624b99e6e7bf`. Reviewed all 23 files changed by the branch, with particular attention to authentication, every health-data route, frontend account transitions and migration 005. GitHub CLI was unavailable; read-only Git refs verified the PR revision. This review does not assert CI status or branch-protection approval.

## High: stale screens and shared-cookie session changes expose health data

Published code: `backend/app/auth.py` checked the session-bound token only for mutations; `frontend/src/Authentication.tsx` listened only for the current tab's API 401 responses. The frontend retained private state after sign-out in another tab and after server session expiry until another request occurred. An old tab could also fetch records for the newly signed-in account using its shared browser cookie while its UI still represented the previous account. These are shared-browser session-context failures, not an IDOR allowing A's independent session to fetch B's records by ID.

Reproduction: authenticate two clients as synthetic A and B, give the A client B's shared cookie while retaining A's in-memory token, then read `/api/episodes`. The added regression failed against published code with **HTTP 200 instead of 401**. Browser review also established that there was no cross-tab state-clearing mechanism.

Local fixes:

- Require the session-bound token on all protected reads, as well as the existing origin/token checks on mutations.
- Broadcast sign-in/sign-out/deletion events without private payloads; clear mounted account data and revalidate in other tabs. Use a non-sensitive storage-event fallback where BroadcastChannel is unavailable.
- Reject late API results and old bootstrap responses after session changes. Prevent a late anonymous/bootstrap token from overwriting a new login token.
- Return the server's absolute session deadline and clear mounted private screens at that deadline, while retaining unauthenticated emergency access. Revalidate browser-history restorations. Do not end attack records automatically.
- Compare request-token bytes to reject malformed non-ASCII tokens without a string-comparison TypeError.

Regression coverage includes stale-token reads across every relevant collection/export/account endpoint, two tabs in the same browser context, discarded delayed responses, and a simulated session-expiry deadline.

## Authorization and account controls

| Area | Evidence |
| --- | --- |
| Registration/passwords | Argon2id with per-password salts, 64 MiB/three passes/two lanes; 12–128 character registration passwords; hashes absent from responses/exports |
| Login/logout | Generic invalid-credential responses with dummy verification for missing accounts; session/token rotation; revoked-cookie replay rejected; logout revokes the database session |
| Cookies/expiry | Opaque 256-bit identifiers stored only as digests; HttpOnly, host-only, SameSite Lax; Secure and `__Host-` prefix in production; server rejects invalid/expired sessions |
| CSRF/CORS | Missing/wrong tokens and missing/foreign origins rejected across protected mutations; untrusted-origin preflight rejected; default allowlist contains only local frontend origins |
| Diary/wellness/early symptoms | Both-direction list isolation and forbidden foreign updates/deletes; ownership injection rejected; independent same-date wellness records |
| Attack sessions | Own list/current/start/end; foreign session end and diary references rejected; independent active sessions |
| Contacts/profile/preferences | Own lists/singletons; foreign contact references rejected; profile updates and preference reset do not change the other account |
| Feedback/recommendations/consent | Own history/ranking/contact selection; foreign session/contact/feedback/consent IDs rejected; no public caregiver-access route |
| Export | Both directions and attempted `owner_id`/`user_id` query overrides return only the authenticated account's records, metadata and consent history; credentials/session secrets excluded |
| Account deletion | Password plus exact confirmation; owned children and all account sessions removed transactionally; other accounts and unassigned legacy rows preserved |

The bidirectional matrix compares the victim's complete export before and after attempted writes/deletes, rather than checking status codes alone. Existing independent-session ownership checks showed no cross-user IDOR in the reviewed routes. No automatic calls or messages were activated by tests.

## Migration and sensitive-file review

Migration 005 adds nullable owner IDs without assigning existing rows. Tests cover upgrades from 001 and 004, preservation of all eight legacy tables and their linked IDs, and foreign-key integrity. A separate test registers the first user as ID 1 against legacy records also numbered 1: these remain unassigned, unavailable to that account, and unchanged after account deletion. No ownership-claim endpoint exists. PostgreSQL migration execution remains unverified without an available instance.

Tracked/source-candidate scanning found no credential tokens, private keys, credential-bearing database URLs, database files or private dataset paths. Literal passwords in tests are synthetic fixtures. `.gitignore` excludes local secrets, health records, exports, research data, backup databases, dependencies and test/build output. Runtime SQL echo is off; validation responses omit raw inputs and SQL errors are sanitized. No new health-body/credential logging was found. This is source review and pattern scanning, not proof against every possible secret or infrastructure logging path.

## Remaining risks and scope limits

- **Medium, deployment:** rate limits are process-local and trust the ASGI client address. Uvicorn's proxy middleware can derive this address from forwarded headers from trusted peers. A deployed proxy must sanitize these headers and use shared rate limits. For local verification the server was launched with `--no-proxy-headers`; use this flag for the documented loopback-only workflow.
- **Medium, configuration:** `APP_ENV` enables secure cookies only for exact `production`; unknown values silently use development behavior. CORS accepts the configured origin strings without rejecting wildcard/malformed configuration at startup. Current defaults are loopback-only, but production should fail closed on invalid configuration and require explicit HTTPS origins.
- **Low, rate-limit accuracy:** the limiter clears whole idle keys instead of expiring individual timestamps, so its advertised sliding window can over-throttle legitimate activity. Rejections do not extend the window; this is not unlimited brute-force access.
- Email verification, account recovery, password-change/MFA, session/device management, encryption at rest, retention/backup purge, strict deployment headers/body limits, independent penetration testing and operational security remain outstanding. Duplicate registration can still reveal successful account creation; generic text alone cannot eliminate this.
- Browser expiry clearing depends on JavaScript scheduling; suspended devices/tabs may delay timers. Server-side expiry and read binding remain authoritative. Screen readers, native dialers/SMS handlers, long-lived real-device behavior, PostgreSQL and concurrency/load testing remain manual requirements.
- No Python advisory-database audit was performed; `pip check` verifies installed dependency compatibility, not absence of vulnerabilities. npm audit covers the JavaScript dependency graph only.

Relevant references: [OWASP session-management guidance](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) discusses sensitive browser state after logout; [Uvicorn proxy settings](https://www.uvicorn.org/settings/) describes forwarded-header trust. No production-grade security or clinical claim is made.

## Final local verification

- Backend: **72 passed**, including the new bidirectional account matrix, every protected mutation's origin/token checks, session replay, stale-tab reads, migration preservation and legacy ID collisions. One existing upstream TestClient deprecation warning remains.
- Frontend: **35 passed**, including discarded stale responses/tokens and clearing health screens at session expiry.
- Browser: **7 passed**, including two independent synthetic accounts, two tabs sharing one account, cross-tab sign-out clearing, mobile overflow, keyboard/reduced-motion behavior and safe phone/SMS link inspection. All temporary synthetic accounts were cleaned up.
- Production build: passed. `pip check`: no broken requirements. npm audit: zero reported vulnerabilities. Whitespace checks passed.
- Local frontend and proxied API health both returned HTTP 200; servers remain available at `http://127.0.0.1:5173` and `http://127.0.0.1:8000`.
- The original PR head above identifies the vulnerable revision, not the hardening commit containing this document. The hardening commit must update `feat/authentication-privacy` and its PR ref before the published PR receives this recommendation. No force-push or merge into main is authorized.

## Hardening commit re-verification

Before creating `fix: harden authentication and user data isolation`, the full backend suite passed again (**72 tests**), the targeted authentication/authorization module passed independently (**16 tests**, already included in the full count), the frontend suite passed (**35 tests**), and the production build passed. The source-candidate scan found no private records, database files, real credentials, or generated output; literal password matches were synthetic test fixtures. Existing ignore rules cover local databases/backups, secrets and generated files. The medium/low risks above remain explicitly outside production readiness; they are not a production security approval. Push and remote-hash verification are separate approval-dependent steps.

All **7 browser tests** passed again against the final backend. An initial rerun reached the long-running local server's expected HTTP 429 authentication limit from accumulated test traffic; the backend was restarted without changing limits, the failed run's verified synthetic accounts were removed, and the complete browser suite then passed. `pip check` also passed. Repeat browser suites against fresh limiter state or an isolated test server; do not disable rate limiting to make tests pass.
