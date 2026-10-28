# Sprint 15: synthetic demonstration operations runbook

Prepared 2026-10-28. **Execute only after an authorized operator reviews the target. No hosted service has been installed or deployed; equivalent local synthetic rehearsals are tested separately.** Every command must target an isolated synthetic database, never the existing personal/research database. Required operator, host/privacy/security owners and incident contact: **TBD**. See [architecture](DEPLOYMENT_ARCHITECTURE.md) and [readiness](DEPLOYMENT_READINESS.md).

## Local reproducible rehearsal (PowerShell)

Use new consoles so demo environment settings cannot contaminate normal test/development runs. From repository root, install reviewed locked dependencies with the existing Python 3.13 environment and `npm ci` in `frontend`. Do not run migrations using the default private database URL.

Backend console, starting in `backend`:

```powershell
$demoRoot = Join-Path (Get-Location) ('.research/demo-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $demoRoot | Out-Null
$env:APP_ENV='development'
$env:DATA_MODE='synthetic'
$env:DEMO_ACKNOWLEDGEMENT='synthetic-only-no-real-health-data'
$env:DATABASE_URL='sqlite:///' + (Join-Path $demoRoot 'migramind-synthetic-demo.sqlite').Replace('\','/')
$env:CORS_ORIGINS='http://127.0.0.1:5185'
$env:ALLOWED_HOSTS='127.0.0.1,localhost'
$env:PORT='8015'
./.venv/Scripts/python -m alembic upgrade head
# Enter a fresh demonstration-only password at the private prompt; no default password.
./.venv/Scripts/python -m app.demo provision
./.venv/Scripts/python -m app.serve --check
./.venv/Scripts/python -m app.serve
```

Stop if any step fails; PowerShell does not automatically stop after native-command errors. A second provisioning attempt must fail rather than clear or relabel records. Keep the demo root private. No recursive deletion is needed to reset: create a new versioned directory/target instead.

Frontend console, starting in `frontend`:

```powershell
npm.cmd ci
$env:VITE_API_URL=''
$env:VITE_DATA_MODE='synthetic'
$env:MIGRAMIND_API_PROXY='http://127.0.0.1:8015'
npm.cmd run build
node node_modules/vite/bin/vite.js preview --host 127.0.0.1 --port 5185 --strictPort
```

Open only `http://127.0.0.1:5185`, sign in as `demo@synthetic.example.test` with the privately set demo password, verify the warning and inspect Daily status/January 2026 diary data. Confirm writes are refused, research export still needs explicit consent, and `/api/ready` returns only `{"status":"ready"}`. Do not click live telephone/SMS links during demonstrations or smoke tests; existing device-native emergency access remains user-initiated. Stop both servers afterward. Vite preview here is a local build rehearsal, never the public hosting service. Use fresh consoles with `DATA_MODE=local` for existing editable-development tests.

## Initial hosted staging/deployment — not executed

1. Appoint an operator and obtain host/security/privacy approval for synthetic-only access. Choose host, database, DNS, certificate, persistent storage and backup destination; no account/budget is assumed. Configure firewalls so only HTTPS ingress is public; API is loopback-only and PostgreSQL is reachable only by authorized hosts.
2. Prepare an immutable reviewed release under `/opt/migramind/releases/RELEASE_ID`. Record source revision, dependency locks, runtime/OS versions and artifact hashes; independently review current runtime patches. Install OS dependencies from approved repositories. Build frontend with same-origin API and synthetic mode. Example Linux build sequence, from that release directory:

```sh
python3.13 -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip==26.2.2
backend/.venv/bin/python -m pip install -r backend/requirements.lock.txt
backend/.venv/bin/python -m pip check
cd frontend
npm ci
VITE_API_URL='' VITE_DATA_MODE=synthetic npm run build
```

3. Create an **empty, new** dedicated PostgreSQL database ending `_synthetic_demo`, with verified TLS and separate owner/migration, runtime and backup roles. This is an operator/institution task, not an automated script in this sprint. Protect service/password/CA files and database storage. Never copy a personal database to “make a demo.”
4. Review [demo.env.example](../deploy/demo.env.example). Store real settings in `/etc/migramind/demo.env`, root-owned, mode 0600 or an approved secret manager. Set the actual HTTPS origin/allowed host, PostgreSQL URL and approved trust root. Do not place secrets in command arguments, Git, `VITE_` values, tickets, shell tracing or full environment dumps. Keep migration-owner credentials separate from the runtime environment.
5. With the service stopped and owner credentials privately loaded, run migrations and provisioning as described below. Set the one-off demo password at a private prompt or private provisioning environment; remove `DEMO_PASSWORD` afterward. Apply reviewed runtime-role grants, including removal of inherited/public health-table write privileges. Validate actual role isolation; the SQL template is not proof that privileges are correct.
6. Set `/opt/migramind/current` to the reviewed release, create the nonprivileged service account and required restricted directories, then review/install the [systemd template](../deploy/migramind-demo.service.example). Run `systemd-analyze verify` on the actual unit and `python -m app.serve --check` under runtime settings. Never run the API as the owner/superuser. The launcher enforces one worker and loopback ingress.
7. Review/install [nginx template](../deploy/nginx-demo.conf.example), replace example DNS/certificate paths, and run `nginx -t` with the actual TLS files. Certificates, renewal and trust are operator responsibilities. Do not use forwarding wildcard trust. The proxy overwrites scheme/IP headers; direct access to its trusted API listener must remain impossible externally.
8. Start staging manually, then verify HTTPS, Secure/HttpOnly/host-only cookies, Host/Origin/CSRF denials, both probes, synthetic UI/source flags, no editable data or registration, explicit export consent, session logout, CSP and no private payload logs. Exercise restart, backup/restore and rollback in isolated staging before authorizing any public demo. Staging and demonstration must not share databases, credentials or sessions.

No deployment command here is evidence that nginx, systemd, PostgreSQL TLS, network ACLs or hosted logs have actually been configured. Their execution is blocked pending an approved environment and owner.

## Database migrations and safe rollback

1. Stop/fence API traffic and use the dedicated migration role, never runtime credentials. Privately verify the exact database name, schema and environment; do not print a connection URL. Confirm the target is the approved synthetic database.
2. Obtain and verify an encrypted pre-change snapshot; record release/schema and checksum metadata. Do not proceed without a usable recovery path. For a new empty demo, document that it contains no records before initialization instead of copying existing records.
3. From the release's `backend` directory run `python -m alembic current`, review `python -m alembic heads`, then `python -m alembic upgrade head`. This release requires `009`. Run upgrade a second time in staging to confirm idempotence, then validate integrity, fixture marker and row counts. `009` creates only an empty provenance table; no existing row is labeled synthetic.
4. Run `python -m app.demo provision` **only** for a newly migrated empty target. It refuses existing application rows and does not overwrite fixtures or records. Select runtime settings, run `python -m app.serve --check`, and smoke-test readiness before reopening access.
5. Never edit/stamp historical migrations to force compatibility, use `Base.metadata.create_all` as production migration, or apply an automatic downgrade. Existing destructive downgrades and `009` provenance erasure are intentionally blocked. On failure keep ingress closed, preserve restricted diagnostics, restore to a separate target and verify before switching. Do not retry blindly with broader privileges.

Existing SQLite migration preservation and the new `008`→`009` additive/idempotent test use synthetic databases. They do not prove PostgreSQL execution or a production migration rollback.

## Encrypted backup, retention and restore — proposed procedure

**Encrypted/off-host backups are not configured or tested in this sprint.** Only a synthetic SQLite backup-API/restore consistency check is automated. Do not advertise operational backup or disaster-recovery coverage based on that test.

Proposed targets for operator approval: daily encrypted snapshots; seven daily and four weekly copies; 24-hour recovery-point and four-hour recovery-time objectives. These are operational planning choices, not measured SLAs or legal research-retention periods. Name the operator, key custodian and deletion/restore-verification owner before use. Keep the decryption private key outside the app host, verify public-key fingerprint out of band, restrict backup access and test key recovery. Do not put a passphrase in a shell command or repository.

On an approved Linux backup host, a reviewed PostgreSQL service file supplies connection/CA settings without command-line passwords. The following Bash example streams into public-key encryption instead of writing an unencrypted dump to disk:

```sh
set -euo pipefail
umask 077
: "${BACKUP_RECIPIENT:?Set the reviewed public-key fingerprint}"
: "${BACKUP_FILE:?Set a new path in approved restricted backup storage}"
pg_dump --dbname=service=migramind_demo_backup --format=custom --no-owner --no-acl |
  gpg --batch --encrypt --recipient "$BACKUP_RECIPIENT" --output "$BACKUP_FILE"
sha256sum "$BACKUP_FILE"
```

Do not use `--yes` to overwrite a snapshot or disable TLS/key trust checks. Confirm the process exit status and encrypted output, transfer only ciphertext to approved off-host storage, and retain checksum, release/schema, key fingerprint and completion time as restricted metadata. Use signed manifests or approved integrity controls where required; a checksum alone does not prove authenticity. Scheduler, transfer, encryption and expiry must be installed and tested by the operator. Keep GPG/backup-client diagnostics private; they can disclose metadata. See [PostgreSQL dump/restore documentation](https://www.postgresql.org/docs/current/backup-dump.html) and [GnuPG operational commands](https://gnupg.org/documentation/manuals/gnupg/Operational-GPG-Commands.html).

Restore drill, before first exposure and at least monthly thereafter:

1. Select a known verified ciphertext/manifest and restore into a **new empty**, network-isolated database ending `_synthetic_demo`, never over the serving database. Verify checksum/key/release and use the approved decryption key on the recovery host.
2. With reviewed service-file targets, stream `gpg --decrypt "$BACKUP_FILE"` into `pg_restore --dbname=service=migramind_demo_restore --exit-on-error --single-transaction --no-owner --no-acl`. Use Bash `pipefail`, not a shell that ignores an upstream failure. Ensure the restore service points to the new isolated target, and review grants afterward because `--no-acl` does not restore them.
3. Check schema/marker, exact fixture identity, counts, foreign keys and representative histories, then run the application preflight and read-only browser checks. Delete restored login sessions only after independently verifying the dedicated target, to prevent resurrecting sessions. Rotate the demonstration credential or use fresh provisioning for a reset. Record elapsed recovery time, all failures and authorized sign-off; do not log row contents or connection strings.
4. Only switch serving configuration after successful verification and approved incident/recovery decision. Retire old copies under the approved schedule with auditable deletion; do not blindly delete directories or databases by a computed name. Rotation/withdrawal obligations must include restored copies, manifests and exports. Synthetic operations do not establish future health-data consent or retention compliance.

## Restart, monitoring and recovery

`/api/health` is a DB-independent liveness probe returning `{"status":"ok"}`. `/api/ready` returns only ready/unavailable with HTTP 200/503 after checking connectivity, migration revision and, for demo mode, fixture provenance/identity. Both are unauthenticated, no-store and disclose no host, DB name, version, stack, secret or record. Do not mistake liveness for dataset, TLS or clinical readiness. Poll fixed HTTPS URLs internally; never attach credentials, user identifiers or health query strings.

The startup event describes application initialization, not a substitute for the readiness probe. Operational logger `migramind.operations` emits fixed JSON event names only (`startup_ready`, `startup_blocked`, `readiness_unavailable`, `demo_write_blocked`). No health/body/path/token field is accepted. Uvicorn request logs are disabled; nginx access logs are disabled in the template. Restrict and review infrastructure error logs, generic tracebacks and journal retention separately; third-party infrastructure is not sanitized merely by this application code. Do not enable raw request tracing, session replay, SQL echo, full exception values or unapproved external error services.

Proposed alerts: three consecutive readiness failures, abnormal restart/5xx/429 rates, TLS expiry under 14 days, storage over 80%, backup age over 26 hours and restore drill overdue over 30 days. These thresholds are proposed operations settings, not deployed monitors or clinical rules. Route to a named internal operator through approved channels; no notification is configured here. Review aggregate counts/latencies without recording health data or raw identities.

For recovery: fence ingress if readiness fails; compare intended release/config without dumping secrets; verify database reachability/TLS/schema and disk; inspect only restricted value-free events; correct the identified cause; run preflight; restart the service manually and recheck probes, demo restrictions and logout. Never “fix” an outage by setting production to development, disabling certificate verification, exposing the API port, removing the marker check or enabling health writes. Repeated start failures stop after the unit's bounded restart budget and require operator action.

## Incident response

On suspected real-data entry, cross-account exposure, secret compromise or unexpected writable behavior: close ingress and stop affected services/exports; preserve minimum restricted evidence without payload copies; notify the appointed security/privacy/operator leads; assess actual scope and applicable reporting duties. Do not claim a breach is ruled out by a green test. Revoke/rotate affected secrets and sessions, isolate snapshots and arrange authorized deletion/recovery. Keep any accidentally received real data out of Git, test fixtures, issue trackers and external AI tools. Resume only after authorized review and verification. No real-data processing, clinical escalation monitoring or research recruitment is authorized by this runbook.

## Demo reset and release rollback

Reset is a **fresh-target replacement**, not destructive SQL against a live database: close access; record old target/release; create a new empty dedicated namespace; migrate/provision with a new private demo password; apply runtime grants; verify preflight and read-only behavior; switch configuration and restart; retire the old target only after an independently reviewed retention decision. Code intentionally has no reset/delete command and refuses provisioning existing data. Never point reset instructions at the default private database or reuse a research export as a fixture.

Rollback requires a previously tested **demo-aware** release and schema-compatible snapshot. Close access, restore to a new target if needed, atomically select the paired backend/frontend release and correct environment, preflight and smoke-test, then reopen. **Do not roll back to Sprint 14 or earlier for a hosted demo**: those releases lack the synthetic-only write boundary. Prefer a forward fix or keep offline when no compatible safe rollback exists. No automatic migration downgrade, loss of audit history or silent “stamp head” is allowed.
