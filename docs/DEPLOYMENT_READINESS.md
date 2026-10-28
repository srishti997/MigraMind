# Sprint 15: deployment and research operations readiness

Assessment date: 2026-10-28. Branch: `feat/deployment-readiness`. Scope: reproducible **synthetic-only demonstration**, not real health hosting, cloud deployment, recruitment or clinical prediction. No cloud/hosted infrastructure was provisioned, service published or external participant contacted. Only isolated loopback test servers and synthetic databases were created for verification. Publication is authorized only after the final source checks pass; deployment and merge remain separate, manual decisions.

## Readiness layers

| Layer | Current decision | Evidence and conditions |
| --- | --- | --- |
| Local development | Supported within existing synthetic/local boundary | Editable diary, authentication and history remain available in development `DATA_MODE=local`. This is not permission to enter private health records. |
| Local synthetic demonstration | Application path implemented; final validation recorded below | Dedicated fixture database, explicit acknowledgement, schema/marker preflight, fixed account, read-only API and frontend, labelled exports, local build preview. |
| Hosted synthetic demonstration / operational deployment | **CONDITIONAL / NOT OPERATIONALLY VERIFIED** | Templates and runbooks supplied; requires an owner, host, patched runtimes, DNS/TLS, PostgreSQL certificate/grant validation, nginx/systemd execution, firewall, monitoring and encrypted backup/restore drills. No public URL or working infrastructure is claimed. |
| Real health-data research | **NO-GO** | No institutional PI/controller, ethics/privacy approval, genuine enrollment/withdrawal infrastructure or independent onset/coverage evidence. [Sprint 13 pilot](PROSPECTIVE_PILOT_PROTOCOL.md) is a proposal; [research gates](RESEARCH_READINESS_GATE.md) still apply. |
| Clinical validation | **NOT ESTABLISHED** | No risk score, diagnosis/treatment recommendation or clinically validated predictive service. Synthetic software results cannot support clinical claims. |

## Changes and restrictions

- [Architecture](DEPLOYMENT_ARCHITECTURE.md): one-origin static frontend/TLS proxy, loopback API, separate verified-TLS PostgreSQL and reviewed operational roles; no provider/budget assumed.
- [Runbooks](OPERATIONS_RUNBOOK.md): build/start, configuration, migrations, encrypted backup design, restore verification, restart, alerts, incidents, fresh-target reset and safe rollback. All hosted procedures need operator execution/sign-off.
- Backend: `SecuritySettings` requires explicit synthetic mode/acknowledgement and dedicated demo namespace for production; new empty-marker migration `009`, fixed-fixture provisioning, startup/preflight, safe readiness probe and body-blocking read-only demo middleware. Normal local development remains editable. No prior migration file or existing database is changed by implementation.
- Frontend: server/build-controlled synthetic warning, fixed login email, no registration, no health writes before upload, mismatch rejection and synthetic export flags. A build template fixes demo mode even if the API is down. No runtime dependency was added.
- Operator templates in [deploy](../deploy/demo.env.example): fail-closed environment, frontend mode, loopback single-worker service, same-origin TLS/static reverse proxy, and restricted database grants. These are reviewable templates, not installed operations.

Readiness is not a percentage or a clinical count threshold. Liveness is only process availability; readiness is only a bounded database/schema/provenance check. It does not prove all records are fictional or clinically trustworthy. A privileged operator can still alter data; no semantic detector or tamper-evident host is claimed. Shared demo credentials, free-text bytes transmitted by deliberate clients and third-party infrastructure logs remain risks requiring restricted access and operator review.

## Validation evidence

Final results (all suites **zero failed, zero skipped**):

| Verification | Result |
| --- | --- |
| Backend full suite | **249 passed** in 366.42 seconds; one existing Starlette/httpx deprecation warning |
| Frontend unit suite | **69 passed** across 12 files in 43.49 seconds |
| Existing Playwright suite | **16 passed** with `--timeout=60000` against a new editable synthetic database |
| Built-demo Playwright suite | **2 passed** in 11.2 seconds at 320px width; mismatch rejection, no upload/writes, consent, synthetic export and logout |
| Production builds | Normal and explicitly synthetic TypeScript/Vite builds passed; final synthetic Vite build 16.48 seconds |
| Dependencies | OSV: 43 installed packages, zero known advisories/skips; npm audit: zero known advisories; pip compatibility passed; 31 base and 38 ML lock pins match installed versions |
| Deployment verification | Fresh SQLite migrations/provisioning, refusal to overwrite data, schema/marker and launcher preflight, bounded failure behavior, fixed-event/private errors, additive/idempotent 009, refusal of downgrade without data/schema loss, and plaintext SQLite backup/restore consistency passed |
| Preservation | Existing SQLite and all historical migration-file checksums unchanged; no existing database migration executed |

No hosted Linux, PostgreSQL/TLS, runtime role-grant, nginx/systemd or encrypted/off-host restore execution is claimed. No historical Sprint 14 counts are claimed as Sprint 15 evidence. Tests use synthetic temporary databases, including fixture refusal on existing rows, additive migration preservation, readiness and logging failures, export consent, frontend upload prevention and a dedicated built-demo browser workflow.

Deployment validation boundaries:

- SQLite migration/provisioning/preflight and plaintext backup/restore consistency can be checked locally. This does **not** verify encrypted backups, PostgreSQL migrations/TLS/privileges or hosted recovery objectives.
- nginx/systemd and SQL templates have static tests only until run on an approved Linux/DB host. Docker's daemon is unavailable here; no container was built or started and none is required by the selected architecture.
- App dependency advisory checks do not cover host OS, Node/Python runtime patch status, DNS/certificates or infrastructure supply chains. Reproducible dependency pins are not proof of an immutable reviewed OS image.
- An auxiliary lock-comparison script initially failed to strip a pre-existing UTF-8 BOM; corrected decoding verified all pins without modifying either lockfile.
- Initial invocation of a targeted backend test from repository root failed collection (`app` not on the import path); commands must run from `backend`, as documented. The full suite is rerun from that directory. This command error is not hidden as a passing test.

## Remaining blockers and required sign-off

| Owner to appoint | Unresolved evidence before hosted exposure |
| --- | --- |
| Infrastructure/operator | Approved host/database budget or institutional allocation; named service owner; private network/firewall; patched supported runtimes; Linux service/proxy syntax/execution; TLS renewal; release/rollback rehearsal |
| Database/backup owner | TLS CA/hostname tests, least-privilege runtime/backup grants, encrypted persistent storage, encrypted off-host backup installation, key recovery, restore/retention/deletion drills and measured recovery times |
| Security/privacy reviewer | Independent review/penetration test, logging/telemetry boundaries, shared/rate/resource controls, incident contacts/process, secret rotation, isolation, local-device/download and shared-account risks |
| Research institution/ethics team | Genuine study consent/enrollment, withdrawal/retention governance, provenance and independently reviewable full-horizon outcomes, approved protocol and qualified investigators |
| Clinical governance | A separate validated intended-use study and appropriate regulatory assessment; no step here grants clinical deployment |

Recommended next action: review these changes and the read-only demo limits, then authorize a separate isolated staging rehearsal only after assigning operators and resolving host/security prerequisites. Keep hosted and real-data gates closed until the relevant evidence exists. The user separately authorized committing these changes, pushing the feature branch and opening a review PR after checks pass. No merge or deployment is authorized.

## Changed-file scope and handoff

Source changes are limited to demo/readiness/provisioning/startup code, the additive migration, synthetic regressions, UI/API guards, deployment templates, public environment examples, exact template ignore exceptions, package scripts and these guides. No dependency was added, no existing migration file changed, and no patient records, real credentials, databases, environments, browser outputs or generated datasets are included. Deployment/provisioning passwords in tests are explicitly fictional fixtures. Final checks passed: 34 intended source/config/test/documentation files, 37 local Markdown links, UTF-8/whitespace and credential-pattern checks, public template visibility, dependency-lock consistency and clean staged scope. All four loopback test servers were stopped. No database, dataset, virtual environment, browser output or generated artifact is in the source change set. Only the enumerated Sprint 15 source/config/test/documentation files are eligible for the authorized commit and review PR; no merge or deployment is performed.

## Final independent review

- Fixed indirect demo writes: absent profile/support defaults return a generic 503 instead of GET-triggered creation; login does not update demo password hashes. The integration regression inventories every installed mutation route and an unknown administrative path, forces the rehash condition, and compares all application tables (excluding intentionally mutable login sessions) across login, reads, export and logout. It also removes only synthetic defaults to verify reads do not recreate them.
- Fixed a logout/CSRF race: sign-in remains unavailable until the replacement anonymous session finishes loading; a deferred-session frontend regression verifies this.
- Fresh provisioning, nonempty-target refusal, strict consent, export labels, fixed fixture origin and guarded UI/backend behavior were reviewed. Provenance relies on the offline provisioner and trusted operator/DB access; the marker is not a cryptographic attestation of arbitrary database contents.
- Migration chain is 008 to 009 with one additive empty table. Fresh/existing SQLite upgrades, repeat upgrades and refused rollback preserve records. Existing private database and historical migration checksums remain unchanged. PostgreSQL-dialect DDL for 009 compiles without a connection; full PostgreSQL execution remains NOT VERIFIED. The historical Alembic environment has no offline branch, so an attempted CLI `--sql` check still required a connection and could not run against an example hostname. No existing migration environment was altered to bypass this limitation.
- Intermediate validation failures were investigated rather than counted as passes: an immutable Argon2 method required a class-level test stub; a sequential logout mock required route-based responses; a short OSV timeout passed on retry. The first browser run had a responsive timeout and the confirmed logout race; a subsequent run had one wellness-editor failure during a Vite source-edit navigation. A fixed-source run passed 15/16 with the account workflow timing out in cleanup at the default 30-second budget; final browser verification uses `npm run test:e2e -- --timeout=60000`, unchanged assertions and a fresh synthetic target. No application rate limit was relaxed.
- nginx/systemd/SQL environment templates received static review, including dedicated target naming, loopback/TLS assumptions, restricted runtime writes and secret separation. Live infrastructure, encrypted backups, off-host recovery and independent security/privacy review remain blockers, not passing tests.
