# Authentication & health data privacy — Sprint 6

Local prototype only. Do not deploy publicly or enter real health records yet.

Sprint 15 provides a separate read-only synthetic-demo path. Production now also requires explicit synthetic mode, acknowledgement and a dedicated initialized fixture database; it does not authorize real health-data hosting. See [deployment readiness](DEPLOYMENT_READINESS.md) and [operations](OPERATIONS_RUNBOOK.md). Existing local-development editing remains separate. Public liveness/readiness return status only; neither is clinical or research readiness.

Sprint 14 tightens this policy without authorizing production use: see [SECURITY_PRIVACY_AUDIT.md](SECURITY_PRIVACY_AUDIT.md). Invalid environment/origin/host/TTL settings fail startup. Production additionally requires explicit HTTPS origins and hosts, a PostgreSQL URL with `sslmode=verify-full`, and HTTPS as seen by ASGI. API docs are disabled in production. Generic errors and security headers cover normal and failed requests; field validation avoids echoing user-supplied names. Local loopback HTTP/SQLite remain supported. These changes do not implement encryption at rest, shared rate limiting, staff research access, consent enrollment or institutional approval.

## Architecture

- `app/auth.py` handles registration, login, logout, account settings/deletion and consent. Passwords use Argon2id (64 MiB, three passes, two lanes), with automatic rehash on successful login when parameters change. Passwords are 12–128 characters at registration. No default accounts or passwords exist.
- A fresh 256-bit opaque identifier is issued on registration/login, replacing the previous session. Only its SHA-256 digest is stored. The session cookie is HttpOnly, host-only, Path `/`, SameSite Lax. `APP_ENV=production` enables Secure and the `__Host-` cookie prefix; HTTPS infrastructure is required. Cookies contain no health information.
- Sessions expire absolutely after `SESSION_HOURS` (default 12). Anonymous CSRF bootstrap sessions expire after one hour. Logout revokes the current database session; account deletion revokes every session for that account. There is no prediction-based expiry or attack termination.
- `GET /api/auth/session` returns the signed-in account (or null) and a random session-bound CSRF token. The frontend keeps this token in memory. All mutations, including login/registration, require the token in `X-CSRF-Token` and an exact allowed `Origin`. CORS allows credentials only for configured origins. Cookies alone and SameSite alone are insufficient to make mutations.
- Session hardening: authenticated reads also require the session-bound `X-CSRF-Token`, so an old tab cannot read a newly signed-in account using the browser's shared cookie. API consumers must bootstrap and provide this header on reads as well as mutations. Session responses include `expires_at`; the UI clears at this deadline, discards in-flight responses after a session change, and clears other tabs on sign-in/sign-out/deletion. Cross-tab notifications contain no health data, identities or tokens. The compatibility fallback stores only a random notification value. Restoring a page from browser history revalidates the session.
- Login returns the same error for missing accounts and incorrect passwords, performing a dummy hash verification for unknown accounts. Duplicate registrations have a generic error. Registration still inherently reveals whether account creation succeeded: email verification and private invitation flows are not implemented.
- Authentication attempts use process-local 15-minute windows: 30 per direct client IP and 10 per normalized account identifier (hashed before use as a key). Untrusted forwarding headers are ignored. These limits are a prototype baseline, not a distributed abuse defense.
- SQL errors and validation responses are sanitized; SQL echo and documented request access logs are off. Do not enable body, cookie, export, or credential telemetry.

The design follows the [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), and [CSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) guidance. This is not a security certification.

## Ownership and migration

Migration `005` adds users, login sessions, sharing consents, and nullable indexed `owner_id` foreign keys to all eight existing health/support tables. Wellness date uniqueness and active attack-slot uniqueness are now per account; profiles and preferences are per-account singletons. Existing IDs, timestamps, content, and links are preserved. SQLite migrations check referential integrity after table copies; runtime SQLite connections enable foreign keys.

**Existing records remain `owner_id = NULL`.** No registration, login, export or account deletion claims, exposes or removes these records. This deliberately means old entries do not appear in new accounts. Any future transfer needs a separate, explicit, reviewed ownership process with a private backup. No claim endpoint is provided. `seed.py` remains a legacy synthetic fixture tool; it does not create accounts or make its unassigned rows visible to users. Do not seed a private database.

Before migrating an existing database, stop the backend and make a private SQLite backup (SQLite backup API) or a PostgreSQL backup. Run `python -m alembic upgrade head`. Migration 005 refuses automatic downgrade because removing ownership would discard security boundaries. The backup made in this workspace is under ignored `backend/.research/backups/`; it contains the pre-migration records and must remain private. Deleting an account does not purge pre-existing backups or previously downloaded exports.

Every health/support API uses the authenticated account on the server, including lists, edits, deletes, insights, recommendations, session lifecycle, feedback and JSON export. References to contacts and attack sessions are checked against the same account. Foreign record IDs are unavailable. Clients cannot assign ownership. `/api/health` and authentication bootstrap remain public; emergency `tel:112` access is available on the sign-in screen without authentication.

`GET /api/export` is the account export: account identity, health records, support preferences/feedback, and consent history. It excludes password hashes, login sessions, CSRF tokens, ownership metadata and unassigned legacy rows. The response is an attachment with `Cache-Control: no-store`; store downloads privately.

Account deletion requires the current password and exact `DELETE` confirmation. Child rows are deleted transactionally before the account; other accounts and unassigned records are untouched.

## Caregiver consent

Account settings can record explicit consent for a saved, owned trusted contact and the `support_card` scope. Consent has grant and revocation timestamps, is included in exports and can be revoked. Deleting a contact revokes its consents. **No caregiver access endpoint, public link, automatic transmission or background sharing exists.** Recording consent shares nothing. Existing manual copy/native sharing still requires user action.

## Local configuration

Copy `backend/.env.example` to ignored `backend/.env` if needed:

| Variable | Local default / purpose |
| --- | --- |
| `DATABASE_URL` | `sqlite:///./migramind.db`; PostgreSQL URL may contain private credentials |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173`; exact browser origins, no wildcards |
| `APP_ENV` | `development`; `production` requires HTTPS for Secure cookies |
| `SESSION_HOURS` | `12`; allowed 1–168 |
| frontend `VITE_API_URL` | Empty: same-origin Vite `/api` proxy. Never put secrets in `VITE_` values. |

No signing key or development password is committed: sessions use cryptographic randomness and server-side storage. Keep the database, environment files, backups, exports, local datasets and virtual environments out of Git. Bind both servers to loopback. A stale CORS setting must be updated if switching between `localhost` and `127.0.0.1`.

## Verify with two accounts

1. Start backend with `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log` from `backend` after installing requirements and migrating. Start `npm run dev -- --host 127.0.0.1` from `frontend`.
2. Open `http://127.0.0.1:5173` in a normal browser window and create synthetic account A. Use a separate browser profile or an incognito window to create B (ordinary tabs share cookies).
3. Add an episode, wellness check-in, contact, caregiver preferences and attack session in A. B should start empty and may independently log the same wellness date and start an active session. API requests for A's record IDs while signed in as B must fail.
4. In Account, edit the display name, explicitly record/revoke future consent, and sign out/in. In Settings, export JSON and verify it contains only that account's data.
5. Delete B using its password and `DELETE`; all B sessions must lose access. A's records remain. Keep emergency links unclicked during testing; no test places real calls or sends messages.

Run backend `python -m pytest -q`; frontend `npm test`, `npm run build`, `npm run test:e2e`. Browser tests require local servers and Chrome (`MIGRAMIND_BROWSER` can override its executable). The real API browser test creates temporary synthetic accounts and deletes them in cleanup; the six existing browser tests use synthetic mocked APIs. Automated browser tests check mobile overflow, keyboard interaction, reduced motion, device-link targets and two-account workflows.

## Remaining security work

No production-grade security claim: independent security review, HTTPS/proxy hardening, shared persistent rate limiting, email verification, password recovery/change, MFA, session/device management, encryption at rest, protected backups and retention/purge policy, operational monitoring and incident response remain outstanding. PostgreSQL migration behavior needs a running PostgreSQL instance; current verification uses SQLite. Local database administrators and offline research CLI tools remain privileged and can read database files across accounts; runtime authentication does not encrypt files or turn developer tooling into a user-facing authorization boundary. The research pipeline must not mix accounts or train without separate research consent. Screen-reader, real-device phone/SMS handling, long-session expiry UX, concurrency/load behavior, and a professional penetration test still require manual validation. Emergency access remains user-initiated and never depends on authentication or a model decision.
