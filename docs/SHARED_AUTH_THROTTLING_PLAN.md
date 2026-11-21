# Phase 9B: shared authentication throttling audit and design

## Phase 9I-E subsequent update: dormant non-owner identity (2026-11-21)

The dormant `Target` now derives case-ordinal database/fixture/maintenance names
and a distinct bootstrap owner. Identity, marker and relation-owner comparisons
expect that owner, not the fixture. Existing static tests reject fixture ownership
and missing/mismatched metadata. The manifest does not yet select a case and the
independently verified one-use case registry is absent: `require_case` refuses all
17 tests. Effective privilege/object checks and actual PostgreSQL behavior remain
unverified; bootstrap is still an unapplied template, separate maintenance is not
implemented and teardown is advisory. Execution remains blocked. No database,
SQL execution, container, provisioning, installation or teardown occurred.

Offline checks: **32** harness static, **6** case design, **2** case contract,
**3** teardown and **36** model tests passed. No PostgreSQL tests were run.

## Phase 9I-E follow-up: partial bootstrap and case wiring (2026-11-19)

Added an [unapplied bootstrap template](../prototypes/synthetic_pg_transaction_harness/BOOTSTRAP_TEMPLATE.md) for a bootstrap-owned marker and per-case fixture/maintenance roles. The unapplied schema guard now checks derived database/role names, role existence/flags and direct memberships. Test setup maps its method to a case, then refuses through `require_case`; the pure case observation comparator does not establish independent evidence. The existing runner still assumes fixture database ownership, the non-owner owner-impersonation/bootstrap workflow and one-use verifier are unimplemented, and separate maintenance execution remains absent. **Non-owner integration is incomplete and PostgreSQL execution remains blocked.** The teardown comparator remains advisory, without authenticated observations, protected record enforcement or deletion.

Offline tests: harness static **32**, case design **6**, case contract **2**, teardown comparator **3**, model **36** passed. No database case, connection, SQL execution, container, provisioning, installation or teardown was run. Review the proposed grants, PUBLIC/default privileges, ownership, runtime isolation and maintenance's direct UPDATE/DELETE bypass before any separately authorized execution.

## Phase 9I-I: partial SQL transition, integration blocked (2026-11-19)

The unapplied schema now expects a bootstrap-owned marker with case ordinal and
separate fixture/maintenance identities. Reservation and cleanup compare control
nonce to marker metadata instead of extracting a database-name suffix. Static text
checks pass, but SQL parsing, privileges and marker integrity are unverified. The
marker bootstrap/template, exact non-owner runner identity verification, per-test
case acquisition and independent maintenance execution remain unimplemented. The
17-case mapping is not wired into setup, which still refuses. Existing runner
identity assumptions remain incompatible. Execution stays blocked; this partial
change is not ready for independent pre-execution approval.

Offline checks: harness static **31 passed**, case design **5**, contract **2**,
teardown comparator **3**, model **36**. PostgreSQL tests were not run. No SQL,
connection, provisioning, container operation, installation or teardown occurred.
Maintenance direct UPDATE/DELETE still requires explicit synthetic-only risk review.

## Phase 9I-H: offline case contract, not execution-ready (2026-11-19)

Added a pure 17-test/ordinal mapping and bounded maintenance request-review contract. Three cases require maintenance; wrong case, incomplete evidence, invalid batch/time or inappropriate injected fault refuses. It neither authenticates evidence nor invokes cleanup. Static checks: harness **30**, case design **5**, case contract **2**, teardown **3**, model **36** passed; database tests not run. PostgreSQL connection, SQL execution, container, provisioning, installation and teardown did not occur.

**Implementation remains incomplete.** `schema.sql` still requires fixture database ownership and uses the old name suffix in both control paths; harness identity verification remains owner-based, the per-case mapping is not wired into test setup, and the non-owner bootstrap remains pseudocode. The execution block remains enabled; no safe role/ownership enforcement or PostgreSQL grant verification is claimed. Review and replace these coupled assumptions as one coherent bootstrap/runner change before any separately approved disposable execution. Maintenance direct UPDATE/DELETE remains a synthetic-only risk requiring explicit review.

## Phase 9I-G: minimum disposable PostgreSQL architecture (2026-11-19)

The [architecture decision and go/no-go checklist](../prototypes/synthetic_pg_transaction_harness/NON_OWNER_DESIGN.md#phase-9i-g-minimum-practical-architecture-decision) select one fresh disposable container and private volume, 17 pre-created isolated case databases, separate bootstrap/fixture/maintenance/teardown authorities, independent identity/privilege checks and a bounded manually controlled teardown. This supersedes the proposed custom lifecycle-controller/lease requirement for this limited experiment, without claiming a manual process is race-proof. Three cleanup cases need an independent maintenance handoff, including a protocol distinguishing verified real conditions from injected synthetic failures.

Direct maintenance UPDATE/DELETE can bypass cleanup policy. The recommendation is conditional acceptance **only for a verified disposable synthetic run**, subject to explicit responsible-reviewer approval; no such acceptance follows from this offline architecture review. This does not establish production cleanup security, time continuity or snapshot freshness. No SECURITY DEFINER, RLS or lifecycle service is introduced. The legacy owner guard, verification and runner remain incompatible; execution stays blocked, and a further offline implementation and review phase is required. Separate approval is required before any container, SQL, execution or teardown.

Existing offline tests: harness static **30 passed**, case design **5 passed**, teardown comparator **3 passed**, and model/SQL shape **36 passed**; `git diff --check` passed with line-ending warnings. No database tests were run.

## Phase 9I-F: offline architecture reconciliation (2026-11-19)

The [compatibility matrix](../prototypes/synthetic_pg_transaction_harness/NON_OWNER_DESIGN.md#phase-9i-f-compatibility-matrix-supersedes-historical-execution-directions) maps legacy fixture-owner SQL, owner-based target verification, single-target naming, bootstrap/reset and fixture cleanup to the required non-owner changes. The pure `case_design.py` derives per-case identities and refuses supplied collisions, incomplete inventories, stale states and maintenance evidence mismatches. It does not allocate or authenticate resources, ensure freshness or isolate credentials; its maintenance result is review only. The teardown comparator remains advisory. All 17 database tests remain blocked; three require separate maintenance orchestration.

Existing maintenance UPDATE/DELETE permits bypass of cleanup trust policy. Alternatives are separately reviewed SECURITY DEFINER, RLS, or explicit acceptance of the disposable-case residual risk; none is introduced. No executable bootstrap was added because privileges, ownership, direct mutation and PostgreSQL behavior cannot be established from static text. Legacy SQL and identity checks remain incompatible and execution remains blocked. Static harness **30 passed**, case-design **5 passed**, teardown comparator **3 passed**, model **36 passed**. No PostgreSQL connection, SQL execution, container operation, provisioning, installation or teardown occurred. A verified non-owner bootstrap, independently authenticated one-use allocator/maintenance interfaces and safe separate lifecycle authority remain future work, requiring separate review and approval.

## Phase 9I-E: separate maintenance role, offline preparation (2026-11-19)

The revised unapplied [role design](../prototypes/synthetic_pg_transaction_harness/NON_OWNER_DESIGN.md) separates bootstrap, per-case fixture, per-case maintenance and infrastructure teardown authorities. Fixture has SELECT/INSERT/UPDATE on windows but no DELETE; maintenance has SELECT/UPDATE/DELETE on windows and SELECT/UPDATE on control, plus narrowly listed schema, database, marker and function grants. UPDATE supports row locking. Maintenance's direct table privileges can bypass cleanup policy; grants are not enforcement of time, freshness or expiry. No RLS or SECURITY DEFINER is introduced. No maintenance credential or executable maintenance process is provided to the runner.

The dormant `initialize` and per-test reset now refuse without SQL, and test setup refuses pending a real verified per-case allocator; the 17 test cases remain but cannot execute. Cleanup calls refuse pending a separately controlled process. The existing execution block stays true. Legacy server identity checks and SQL remain owner-based and incompatible, and bootstrap remains pseudocode, not a finished executable template. This is partial offline hardening, not a completed non-owner runner.

The pure offline teardown comparator checks supplied identities, stopped state, revisions, bounded observation age and affirmative conditions, and emits only a review result. It does not authenticate inputs, verify real resources, enforce or consume a lease, prevent replay, or delete anything. A protected record, independent observers and separate teardown authority are still required. Static checks **30 passed**, comparator tests **3 passed**, model/SQL-shape **36 passed**; no PostgreSQL tests ran. No connection, SQL execution, Docker, provisioning, installation or teardown occurred. Independent review of DELETE/UPDATE risks, complete non-owner bootstrap, identity verification, credential isolation and separate maintenance implementation remain blockers before any future execution approval.

## Phase 9I-D: non-owner design review (2026-11-18)

The [unapplied design](../prototypes/synthetic_pg_transaction_harness/NON_OWNER_DESIGN.md) separates an independent bootstrap owner, a non-owner fixture login with scoped invoker-function/table privileges, and an independent container/volume teardown authority. Bootstrap owns the database, schemas, tables, functions and indexes; the fixture owns none. Each test gets a pre-created fresh case database and role, avoiding fixture TRUNCATE, CREATE or owner privileges. The manifest is placeholder SQL for review, not executable bootstrap. No SECURITY DEFINER helper is proposed; direct DELETE remains limited to the synthetic windows table for the cleanup case. Actual minimum grants and catalog behavior remain unvalidated.

The teardown contract specifies separate one-use authorization, independent fresh runtime and database observations compared to a protected run record, lifecycle fencing, exact identity and ownership rechecks before each deletion, generation/writer checks, and affirmative time/freshness conditions. Ambiguous, partial, interrupted or repeated operations require manual review, not deletion. These are requirements for an unimplemented controller, not an enforceable mechanism today. Current runner ownership checks, self-initializing DDL, test TRUNCATE/reset and format-only evidence validator conflict with the design; `EXECUTION_BLOCKED` remains true. The design does not independently prove clock continuity, snapshot freshness or safe teardown.

Offline checks: **29 harness static/unit tests passed** in 0.020s and **36 model/SQL-shape tests passed** in 0.124s. `git diff --check` passed with a line-ending warning. These tests establish document/source properties only. No SQL, database connection, Docker, setup, installation or teardown occurred. This is an offline design and does not authorize Stage B. Before execution approval, implement and independently review the non-owner bootstrap and case isolation, complete privilege/object verification and a separately controlled fail-closed teardown controller, then validate all on a specifically approved fresh disposable target.

## Phase 9I-C: harness hardening and execution hold (2026-11-18)

Reviewed the existing harness and Phase 9I-B findings on `security/shared-auth-throttling` at `01eae2a`. **Execution remains blocked in code and the harness is not ready for a disposable-container execution review.** Its current test role owns the database, conflicting with the required separation from database-destruction authority. A separately owned database, non-owner fixture role and reviewed least-privilege bootstrap remain unimplemented. No setup, database connection, SQL, container, dependency installation or teardown was performed.

The runner now refuses PostgreSQL execution before manifest loading, password prompting or driver import. Its dormant preflight additionally checks direct role memberships, unexpected schemas/extensions and fixture relation ownership; these unexecuted checks do not fully verify effective privileges, object definitions or instance isolation. The offline lifecycle evidence validator rejects missing/malformed fields and non-affirmative ownership, isolation, privilege, object, time, freshness and complete-setup assertions. It validates input shape only, not resource identity or comparison against independently collected evidence, and cannot authorize setup or teardown. The README's versioned runbook requires a new dedicated container and private volume, independent ownership/identity review, and refusal on ambiguous or partial state; a concrete reviewed non-owner bootstrap and fail-closed teardown mechanism are still absent.

The prepared contention test now requests rollback when blocking was not observed and commits only after observation; its bounded waits and driver behavior remain unverified. An interrupted transaction, statement timeout, connection loss or lost commit acknowledgement must stop the run without blind retries, and no fixture reset is safe unless the target has actually been verified. Existing test fixture reset bypasses lifecycle assertions; the execution block is the present safety boundary, not proof that reset is safe. Neither SQL syntax nor prepared database tests were run.

Non-database validation: **26 harness static/unit checks passed**, including blocked execution, missing/ambiguous evidence and rollback-path fakes; **36 pure model/SQL-shape checks passed**. `git diff --check` passed with an existing line-ending warning. No database-dependent guard regression was run. Prior prototypes and Phase 9I-A/B records are preserved.

Before requesting authorization for execution, implement and independently review the non-owner database/role separation, complete object/effective privilege checks and verified fixture writes, evidence comparison against actual independently inspected container and volume, partial-setup recovery, and an enforceable fail-closed teardown procedure. Then separately obtain explicit approval for the exact container provisioning, connections/SQL, tests and teardown. Time/freshness assertions are operator conditions, not proof of recovery safety.

## Phase 9I-B: read-only disposable harness preflight (2026-11-18)

**Verdict: do not execute the current harness, even on a separately verified disposable target, until the target-isolation and teardown concerns below are resolved and separately reviewed.** No database, SQL, provisioning, Docker, installation, setup, test execution against PostgreSQL or teardown was used in this review. This section supersedes any earlier implication that Stage B is ready merely on approval.

Reviewed all six harness files and the complete runner, schema, 17 prepared tests and documented operator lifecycle. Existing uncommitted work was preserved. `python -B -m unittest discover -s prototypes/synthetic_pg_transaction_harness -p test_static.py -v` passed **23 tests** in 0.020s; these are pure/text/AST checks, not PostgreSQL validation. A source-search command using a shell-incompatible brace expression failed before accessing the files; a corrected search completed. No dependency or application configuration was changed.

### Isolation and lifecycle findings

- The normal runner requires the exact acknowledgement and flag, validates a nonce/port-only manifest, derives database and role names, fixes host and hostaddr to loopback, strips inherited PG/application variables in its child and requests an interactive password. It checks database, owner, current/session roles, writable/recovery state, direct role flags and a role-owned marker before writes. A connection and read-only identity queries necessarily happen before those checks. The `_worker` entry point also accepts the flags directly; these are accidental-use barriers, not a security boundary against a caller able to alter code/process state. The manifest command creates a local directory/file without the execution acknowledgement; it does not connect.
- No arbitrary DSN, host, role or credential argument is accepted and no application configuration is intentionally read. This cannot guarantee that an operator does not type an existing secret at the password prompt, or that inherited executable/system paths and platform driver behavior are trustworthy. Marker/identity values and loopback/high port do not prove the entire server disposable, exclusive, fresh or free of real data. The object inventory checks selected relation types, not all functions, operators, extensions, memberships, grants, schema contents or external objects. Direct role flags do not exclude inherited privileges or role memberships; re-verification permits certain harness relation names without establishing their owner/definition. File path validation also has a check/read race. Require independently isolated instance/process identity and restricted role/membership/privilege review; address these checks before execution.
- Setup by the future operator creates a role and database plus marker schema/table/row. Runner setup executes guarded `CREATE SCHEMA`, tables, functions and index, `REVOKE`, then inserts control/binding rows in a transaction. Admission inserts/updates windows and control, or quarantines control. Maintenance updates control and deletes expired windows. Every test fixture **TRUNCATEs** windows and resets control/bindings; tests also update capacity and bindings. These are real destructive writes if isolation fails. Runner has no DROP or automatic instance teardown.
- **Teardown requirement is not met.** The README asks an operator to check instance, port, derived database/role and marker before destroying the disposable instance; it does not require or enforce exact ownership plus generation/writer and affirmative time/freshness assertions. The SQL maintenance gate is not instance teardown, and fixture TRUNCATE bypasses it. There is no implemented fail-closed teardown gate to verify. Specify and review a concrete fail-closed lifecycle that refuses deletion on missing, ambiguous or mismatched evidence, including partial-setup/interruption cases, before authorizing setup. Synthetic trust flags do not themselves establish real clock/freshness evidence.
- Static SQL names are fixed, values use driver parameters, and subprocess invocation uses an argument list without a shell. No dynamic SQL identifier interpolation, shell command construction, DSN input or `SECURITY DEFINER` was found. The setup example requires an operator to substitute a nonce, and separately create role/database; safe identifier handling and privileges for that external procedure are not implemented or verified. SQL's guard does not independently check bootstrap relation ownership; Python checks it. Actual effective role privileges and database permissions remain unverified.

### Test and failure limitations

The 17 unexecuted cases cover final account/IP slots, concurrent missing keys, shared budgets, cutoff, injected rollback, maintenance, capacity, guard rejection, lock timeout and synthetic time/generation/freshness evidence. The race polls `pg_blocking_pids` before releasing the first transaction; scheduling, SQL syntax and psycopg behavior remain unverified. Its `finally` commits the first transaction even if observing contention or an assertion fails, leaving fixture state; the suite continues and the next test resets it. There is no final fixture teardown. It does not establish cross-process behavior, actual failover/restore, lost commit acknowledgements, statement timeout, deadlock, pool failure or full partial-setup recovery.

Setup is intended as a single driver transaction and the context managers intend rollback on errors, but server/driver behavior and an interrupted or uncertain commit have not been tested. A committed schema remains after completion or interruption, and repeated invocation refuses an existing schema; it does not clean it. The 180-second worker timeout and bounded connection/statement/lock waits do not prove cancellation, server rollback or a known commit outcome; the executor may wait for a worker thread on exit. Treat interrupted/unknown outcomes as ambiguous and stop, never retry against or remove an unverified target.

README describes a separately approved local PostgreSQL instance and mentions Docker without providing an actual versioned local PostgreSQL/Docker setup or isolation-verification procedure. Python 3.13 and `psycopg==3.3.6` are specified; the project locks list `psycopg` and `psycopg-binary` 3.3.6, while the runner checks only the former distribution. Driver/native-lib availability, provenance and server/platform compatibility are untested; nothing was installed.

Minimum next gates: resolve and review independent instance isolation, effective privileges, marker/object ownership and race concerns; produce a precise fail-closed setup, interruption and teardown procedure satisfying every requested identity/generation/writer/time/freshness condition; review and correct test failure/cleanup behavior and dependencies; then obtain separate explicit approval for the exact disposable environment, provisioning, connection/SQL, tests and eventual teardown. Preserve all broader recovery, performance, security and integration gates.

## Phase 9I-A follow-up: maintenance trust gate (2026-11-18)

The existing uncommitted harness was reviewed on `security/shared-auth-throttling` at `01eae2a`. Maintenance now requires explicit matching generation and writer assertions and affirmative time-trust and freshness assertions before deleting anything; missing or mismatched evidence quarantines. These are synthetic caller assertions, not detection of stale state, clock steps or a new primary. One additional dormant database test covers untrusted cleanup and persistent quarantine, bringing the prepared count to **17**, none executed in this follow-up. The earlier 16-case evidence below is historical.

Current non-database checks: harness static suite **23 passed** and preserved in-memory model/SQL-shape suite **36 passed**. No PostgreSQL connection or SQL execution, setup, container, installation or teardown occurred. SQL syntax, actual locking and safe operation remain unverified pending separate Stage B approval and independently verified disposable-instance isolation.

## Phase 9I-A: disposable PostgreSQL harness prepared, not executed (2026-11-15)

Verified `security/shared-auth-throttling` at `01eae2a`. Preserved the uncommitted Phase 9H model and report changes, and all earlier SQLite experiments. This stage adds only the independent [harness README](../prototypes/synthetic_pg_transaction_harness/README.md), [guarded runner](../prototypes/synthetic_pg_transaction_harness/harness.py), [executable SQL source](../prototypes/synthetic_pg_transaction_harness/schema.sql), [dormant database tests](../prototypes/synthetic_pg_transaction_harness/test_database.py) and [non-database tests](../prototypes/synthetic_pg_transaction_harness/test_static.py). No application integration, migration or feature activation.

### Isolation and transaction design

Execution requires both explicit Stage B acknowledgement and approval flags. No arbitrary DSN is accepted: only loopback, an explicit high port, nonce-derived disposable database/role names and a bounded nonce-matching temporary manifest. The child environment excludes PostgreSQL/application database settings. Password input is interactive, never a command argument, environment variable or report value. Before any schema write, the runner verifies exact database/session/current-user/owner identity, an unprivileged role, writable primary, an owned plain-table synthetic marker and an allowed object inventory. SQL also has a pre-DDL identity/marker guard. Existing harness schemas are refused. The driver is imported lazily only after the execution permit. These guards prevent accidental targeting; they do not establish cluster disposability against a dishonest operator or malicious host. Separate human verification of a newly disposable instance remains mandatory.

Prepared tables are synthetic control, binding and rolling-window records, with constraints, primary keys and an expiry index. READ COMMITTED transactions lock binding, then global control, then existing budget keys in stable scope/digest order. The global control row serializes admission and safe missing-key creation: **a correctness mechanism and throughput bottleneck, not a scalability claim**. Windows retain timestamps strictly greater than `sample_ms - 900000`; exact lower-bound equality expires. Login/register share 30/IP and 10/normalized-account budgets. Both append or neither does; a denial can advance time metadata without charging either budget. Admission is confirmed only after commit. Cleanup uses a separately committed bounded transaction and preserves active windows. Constraints/count reconciliation fail closed on inconsistent state; no recovery/reset is implemented. Binding/guard inputs are fake fixtures, not actual authentication or Origin/CSRF protection.

Default time is sampled from the writable primary after locks; deterministic tests inject milliseconds. Backward observations and known-untrusted forward time, changed generation/writer or stale snapshots quarantine. Injected trust/freshness flags are assertions, not detectors. Trusted forward jumps can still age budgets; a writable primary does not prove clock continuity or snapshot freshness. No threshold, automatic reset, safe failover or operational recovery is approved or established.

### Actual Stage A evidence

Only standard-library static/pure tests ran from filtered temporary source copies using existing isolated Python 3.13.12; no installation or environment modification. Commands:

```text
python -B -m unittest discover -s prototypes/synthetic_pg_transaction_harness -p test_static.py -v
python -B -m unittest discover -s prototypes/synthetic_pg_throttle_model -p test_model.py -v
```

| Check | Actual result |
| --- | --- |
| Initial harness safety/static run | 22 passed; 0.022s suite / 0.49s wall |
| Final harness safety/static run | **23 passed**, zero failures/skips; 0.021s / 0.32s |
| Preserved Phase 9H model/SQL-text suite | **36 passed**, zero failures/skips; 0.090s / 0.28s |
| Prepared PostgreSQL cases | **16 not selected or executed**, not passing results |

The final run follows an added no-driver/application-import assertion and sanitized connection-close failure handling; runs overlap and are not additive coverage totals. No failures, timeouts or hidden retries. Evidence: task-owned temporary `migramind-phase9ia-7clcs_bp` directory, `static-final.json`, `results.json` and logs. No target manifest, bootstrap schema, database connection, SQL execution, driver load, container, setup or teardown occurred. Existing backend/guard and SQLite prototype suites were deliberately not run because they open databases, prohibited in Stage A. No frontend/build claim is made.

The dormant cases prepare two independent connections with explicit observed `pg_blocking_pids` contention, final IP/account slots, missing keys, shared action budgets, exact boundaries, rollback, independent cleanup, capacity, guard rejection, lock timeout and injected clock/generation/snapshot failures. Bounded test coordination timeouts and SQLSTATE assertions are prepared, not verified. Static SQL text/AST checks **do not compile PL/pgSQL, validate driver API compatibility or prove PostgreSQL isolation, locking, integrity or performance**.

### Stage B approval gates and verdict

Final non-database integrity checks: 99 local documentation links resolve, ten prior prototype files match their Stage A baseline byte-for-byte, new Python sources parse, and diff whitespace checks pass. The task-owned runtime temporary directory is empty. A directory-local `.gitignore` exception includes only `schema.sql`, which the repository-wide SQL-dump exclusion would otherwise hide; no global exclusion or application configuration changed.

**Prepared for separately approved Stage B; not PostgreSQL-validated or ready for application integration.** Obtain approval before any connection, SQL, installation, provisioning or teardown. Stage B needs a newly disposable local instance with recorded PostgreSQL version, reviewed preinstalled driver (runner requires the existing lock's `psycopg==3.3.6`), isolated nonce-derived unprivileged role/database, owned marker and independently verified instance identity. Follow the README's explicit opt-in setup/run/teardown procedure; none was performed here. Do not reuse application configuration, credentials or databases. Validate syntax, constraints, actual locks, failure/rollback, storage cleanup and measured contention first. Clock/freshness/recovery, production guard integration, supported-platform evidence and all existing release blockers remain open. No deployment, live limiter changes or schema activation is authorized.

## Phase 9H: synthetic reference model and SQL-shape validation (2026-11-15)

Verified clean `security/shared-auth-throttling` at **`01eae2a`**, which already contains the prior Phase 9B–9G work. Preserved all existing reports and SQLite/legacy prototypes. Approved scope implemented only under [synthetic_pg_throttle_model](../prototypes/synthetic_pg_throttle_model/README.md): [in-memory model](../prototypes/synthetic_pg_throttle_model/model.py), [tests](../prototypes/synthetic_pg_throttle_model/test_model.py) and [non-executable SQL-shape document](../prototypes/synthetic_pg_throttle_model/SQL_SHAPE.md). **No PostgreSQL instance, driver connection, SQL execution, migration, application schema/provider/flag or authentication integration.**

### Reference behavior and assumptions

The model uses only standard-library in-memory dataclasses, deterministic injected integer time and copied candidate states for commit/rollback. It accepts only documentation IPv4/IPv6 and synthetic `example.test` identifiers, normalized by strip/lowercase and separately hashed for IP/account. It imports neither the SQLite authority nor application code; it has no clock/network/database/environment URL, file persistence or credential/session/health input. Tests read only the adjacent SQL source document. Pseudonymous hashes remain guessable, not anonymous/encrypted.

- Exact **rolling `(sample_ms−900000, sample_ms]`**, 30/IP and 10/account; equality at the lower boundary expires. Same-ms submissions remain separate events. Login/register share keys; fixed buckets are explicitly rejected by a boundary counterexample.
- All-or-nothing: both counters append or neither does. Missing keys stay conceptual until both budgets and capacity permit; denial creates nothing and never charges an otherwise free IP. Denial may commit **high-water metadata only**, without pruning/storing any different window or changing key count. This is distinct from live partial-IP accounting.
- Committed reservation is independent of later credential outcomes; no refund/reset/recovery API. The model never handles actual passwords or verifies login/registration success. Confirmed injected aborts roll back the staged pair and allocation count. Injected lost commit acknowledgement leaves committed charges but returns unavailable; no automatic retry/refund.
- Independent cleanup commits bounded expiry/count/time changes. A subsequent denied/failed admission cannot undo it. Active windows are never evicted. Malformed/missing/inconsistent state, invalid time/evidence and capacity exhaustion fail closed without repairing state. Healthy expired windows can be reclaimed in bounded batches; untrusted expired data cannot be cleaned into validity.
- Guard inputs are synthetic booleans before accounting and after assumed waits, not an Origin/CSRF/session implementation. Actual Phase 9A remains unchanged and was checked separately. Only login/register are model features; bootstrap IP-only and protected reauthentication remain unimplemented requirements for any future real provider.

**Locking/isolation assumption, not implementation:** trace describes sorted session IDs → global control → existing budget keys (scope 0 IP, scope 1 account) → post-wait guard → primary time → commit. Missing keys are marked absent under the assumed control gate, not “locked nonexistent rows.” There is no Python mutex, thread scheduler, database transaction or MVCC. `serial_orderings()` enumerates at most four requests' serial permutations. The final-slot tests explore **24 orders each** for four logical same-time account/IP contenders; each order admits one under the assumed serialized gate. Same-key/capacity permutations test allocation invariants, not actual PostgreSQL unique-index races. Concurrent PostgreSQL correctness is still an acceptance requirement.

Full-state validation in this small model is intentionally clearer/stronger than the proposed real provider's per-request key reads plus separate reconciliation; it is not evidence of identical production corruption coverage. Reconstructing a model from a copied State is logical restart reasoning, not disk/process/replication durability. Model execution time says nothing about SQL latency/throughput.

### Time, primary and freshness tests deliberately retain missing guarantees

`Evidence` flags/generation/writer are **injected assertions from the test**, not measurements of a server. They allow modeling conservative outcomes without inventing an approved clock threshold or recovery service:

| Scenario | Modeled result and limitation |
| --- | --- |
| Backward observed time or cleanup sample reverses after assumed waits | Quarantine, no charges/deletion, no automatic return to READY. Exact zero-tolerance observation is the Phase 9G proposal, not an activated product policy. |
| Forward step with `time_trusted=False` | Quarantine without resetting counters. The model knows the uncertainty because the fixture supplies it. |
| Forward step with `time_trusted=True` | Windows age and an exhausted quota can reopen. A passing test explicitly confirms **the model does not detect an unobserved forward jump**. |
| Changed primary generation/writer or known stale snapshot | Quarantine, preserve counters, no new epoch/reset/recovery. These outcomes depend on external trust evidence. |
| Valid-looking old same-generation state falsely marked fresh | Can be accepted; structural checks/generation do not prove snapshot freshness. This limitation is tested, not hidden behind a fake detector. |
| Unavailable DB, replica/read-only or sample failure | Unavailable, no unmetered fallback or automatic retry. No persistent global quarantine is claimed when storage cannot commit it. |
| Injected quarantine-commit failure | Unavailable while prior READY state remains; failed metadata commit is **not global quarantine proof**. A real admission gate/recovery contract is still required. |

No clock skew/recovery threshold, trusted primary authority, OS clock manipulation, automatic reset or real recovery was added. Actual time discipline, split-brain fencing, writer identity, RPO, snapshot provenance and full-window trusted quarantine remain Phase 9G approval gates.

### SQL shape and static checks

`SQL_SHAPE.md` is explicitly **DESIGN ONLY, NOT APPLIED OR EXECUTABLE**, with intentional `<placeholders>` and branch comments. It identifies proposed control/window tables, primary/expiry indexes, scope/digest/array constraints, unresolved sorted/range predicate and cross-control invariants, primary diagnostics, transaction-local timeout proposals, READ COMMITTED boundaries, session/control/key row-lock order, post-wait `clock_timestamp()` sampling, first-real-admission inserts and separate bounded maintenance commit.

Three text-shape tests assert required structural tokens/order and absence of admission `SKIP LOCKED` or transaction-start `now()` shortcuts. They do not parse/compile SQL, enforce permissions, resolve placeholders, validate PostgreSQL array functions/constraints, prove planner/lock order or apply any DDL. No migration file or database driver call exists in this prototype. Connection/pool/session-schema handling and real quarantining branch code are unresolved implementation work.

The control row is deliberately a **global serialization point**, including unrelated keys and maintenance. It simplifies creation/capacity/high-water reasoning but is a possible hot-row bottleneck. Later approved disposable PostgreSQL tests must record queue/lock-hold/pool wait, abort/error rates and p50/p95/p99/RSS at 0/1000/10000 rows across worker counts, with at least 100 bounded final-slot races per IP/account/absent-key/capacity case and retries off. Existing proposed p95≤100ms/p99≤250ms and additional RSS≤128MiB remain owner-review targets, not results inferred from this fast model. No load/latency benchmark or server provisioning occurred.

### Exact Phase 9H execution and preservation

New evidence root `%TEMP%/migramind-phase9h-fbu1qndk`: filtered source, starting report baselines, test logs/JSON and private TEMP/TMP. Reused isolated Python **3.13.12** dependencies read-only; new model itself is standard-library only. Backend checks use explicit development/local, `DATABASE_URL=sqlite://`, idle false, dotenv/bytecode disabled and copied-source PYTHONPATH. New model uses no database at all; existing guard fixtures create/dispose synthetic in-memory SQLite only. No existing database/account/health/backup/export/secret/environment/profile access, install/provisioning or external infrastructure.

| Check | Actual result |
| --- | --- |
| Initial model/SQL-text suite | **32 passed**, 0.103s unittest / 0.34s wall; 90s cap |
| Final expanded model/SQL-text suite | **36 passed: 33 model + 3 text-shape tests**, 0.130s suite / 0.34s wall; 90s cap |
| Existing Phase 9A guard regressions | **31 passed**, 5.43s pytest / 6.83s wall; 120s cap |
| Failures/skips/retries | **0 failures / 0 selected skips**, no timeout/retry-until-green; existing backend Starlette/httpx deprecation warning |
| Documentation/source integrity | **92 local links / 34 source references**, **69 tested source/declaration/SQL-shape files matched**; six existing SQLite-prototype files equal HEAD; prior report bodies preserved; exactly six intended changes; no DB/network/app/SQLite-prototype imports in new model; app/migrations/locks/configuration unchanged; whitespace passed |

Final run adds four explicit cases for denial-only high-water, cleanup-time reversal, invalid evidence/time failure and malformed window invariants. It overlaps the first 32; do not sum them as distinct tests. No model implementation changed after the first successful run, only those four tests; backend source did not change, so its passing run was not repeated. Historical SQLite prototype results remain historical; that unchanged suite was not rerun unnecessarily here.

```text
# Filtered new repository root, no installation or SQL application.
<isolated-python> -B -m unittest discover -s prototypes/synthetic_pg_throttle_model -p test_model.py -v
# Copied backend, restricted environment above, previously nonexistent owned basetemp.
<isolated-python> -B -m pytest -q -ra tests/test_auth_guard_order.py --basetemp <new-root>/guard-data -p no:cacheprovider
```

Evidence: `model-first.log`, `model-final.log`, `model-final.json`, `guard-regressions.log`, `results.json`, copied tested code/artifact, starting baselines and TEMP wrappers. No real PostgreSQL syntax/isolation/lock/primary/failover/restore/pool or durability test, new live provider, full backend/frontend/browser/build, Linux, migration, infrastructure or performance test was run. No application/prototype-SQLite/auth/dependency/lock/configuration change, commit, push, PR, merge or deployment. Only the four new isolated model/artifact/README files and two reports change in this phase.

**Verdict: model/specification evidence only; NOT READY for application integration or a PostgreSQL correctness claim.** Unresolved: primary forward-time trust and recovery/freshness, unique-writer fencing, real row/creation/deadlock/constraint semantics, global-gate performance, integrity/retention, guard/session handoff, live accounting/NAT/targeting/enrollment policies and actual schema/pool/flag approval. Prior privacy/storage/recovery/accessibility/research/clinical gates remain unchanged.

**Smallest next safe step requires approval:** authorize a disposable PostgreSQL SQL/transaction test target and an isolated harness that replaces artifact placeholders, validates parser/constraints and runs a first two-connection final-slot/rollback/guard-order experiment against synthetic data only. Do not reuse an existing MigraMind database or treat model passes as permission to install a service, write application migrations or activate a limiter. Resolve the database-time/recovery trust decisions before application implementation.

## Phase 9G: PostgreSQL-ready transactional design — proposed, not implemented (2026-11-15)

Verified `security/shared-auth-throttling`, HEAD `c32cb28` (PR #24), preserving Phase 9B–9F reports, isolated SQLite code, archives and tests. **Architecture/design only.** Decision **PG-ADR-01: PROPOSED** continues Phase 9F's deferral of application integration. Keep the monotonic SQLite authority as an isolated experiment; do not import it into routes or silently replace its approved clock model with database wall time.

The proposed provider is PostgreSQL-ready in its **specification**, not validated on PostgreSQL. No SQL implementation, new limiter/reference model, migration, package, pool/flag setting, server installation or infrastructure was created. Existing Python/SQLAlchemy/psycopg support is a reuse opportunity, not proof that this transaction, deployment or recovery contract works.

### Decision record and policy

| Decision | Proposed baseline | Consequence / approval gate |
| --- | --- | --- |
| Window | **Exact rolling 900000ms**, events in `(db_ms−900000, db_ms]`; lower-cutoff equality expires | Keep 30/IP and 10/account. Millisecond flooring is explicit precision versus live float monotonic seconds; same-ms attempts remain separate list elements. |
| Accounting | Atomic **all-or-nothing** pair; valid successes, incorrect known/unknown passwords and duplicate/new registration charge before password work | Live account-full still charges IP; disabled mode retains that old rule. Adoption of the new live policy needs explicit approval, not merely a storage flag. |
| Namespaces | Same IP/account keys across login/register and current password reauthentication; bootstrap IP-only; no action in key | No multiplication of quotas by endpoint. Ordinary reads/current logout remain outside this limiter; collection/research throttles are separate. |
| Store | Primary-only PostgreSQL, durable bounded windows and control row | No stale replica/cache reads, Redis or process-memory fallback. Database reachability/primary/freshness proof is a deployment prerequisite. |
| Concurrency | READ COMMITTED plus explicit row locks and one global control-row gate | Correctness-first baseline serializes admissions. This is a known hot row, **not a scalable-throughput claim**. Optimize/partition only after a separate design/test review. |
| Time | Sample primary `clock_timestamp()` after locks, floor once to integer UTC ms, persist observed high-water | Observed backward movement quarantines. Forward movement is trusted only under an approved primary-clock contract; DB time is not independent elapsed-time proof. |
| Failure | Known limit→generic 429; store/time/generation/capacity uncertainty→generic 503 | Fail closed; no password work or success response after unconfirmed reservation. Availability is deliberately reduced. |
| Retries | **Zero automatic reservation retries** initially | Known aborts return unavailable; ambiguous commits never replay automatically. Optional bounded retry policy is a separate decision. |

**Rolling versus fixed:** a fixed/tumbling 15-minute bucket is simpler but can allow almost 60/IP or 20/account around a bucket transition. Token buckets also change burst semantics. Neither preserves the existing rolling-window policy and neither is recommended here. Existing live [Limiter](../backend/app/auth.py#L66) uses monotonic float time; the SQLite owner uses elapsed integer ms; this design changes the clock authority, not the 30/10 counts or rolling policy.

### Proposed durable schema and invariants

Dedicated additive objects, names provisional, one application/deployment per control realm:

- `auth_throttle_control`: fixed singleton ID, policy/key-codec version, expected admission generation, approved writer/startup identity hint, state READY/QUARANTINED, integer `last_db_ms`, retained `key_count`, fixed `max_keys`, and bounded maintenance/recovery metadata. This is not a session/user/health row. A generation or startup timestamp is a cohort/restart hint, **not proof of primary freshness**. Missing/unknown control state fails unavailable rather than recreating empty counters.
- `auth_throttle_windows`: primary key `(scope_rank, key_digest)`, scope 0=IP/1=account, 32-byte domain-separated SHA-256 digest, bounded nonempty `BIGINT[]` admission ms and `expires_at_ms`. Fixed versioned bounds: at most 30 IP or 10 account elements; elements non-null, nonnegative, nondecreasing and no later than committed control high-water; duplicates are allowed. Expiry equals last admission + 900000, with checked integer range before addition. Shape/range/order invariants must be enforced by reviewed database checks/helper or trusted-writer validation under lock, not assumed from a Python list. No committed placeholder/empty window.
- Primary-key index and expiry index. Proposed initial cap **10000 retained windows**, cleanup batch≤100, inherited as candidate bounds from Phase 9E; not enabled configuration or measured PostgreSQL limits. Unique/check constraints, transactional count maintenance and primary-only bounded reconciliation must agree. Unexpected drift/schema/array data quarantines or fails closed, not repairs to zero.

This baseline does **not** copy A's ephemeral-key HMAC over every row/schema on each request: that would retain its key-loss and global-scan costs. PostgreSQL checks, restricted writer roles, transactions, bounded invariant reconciliation and database corruption/error reporting are the proposed integrity boundary. They do not detect every valid-looking unauthorized delete/old snapshot or protect against a malicious DBA/full host. If equivalent missing-row cryptographic assurance is required, durable key/freshness design and cost need explicit approval; it is not silently claimed. No new HMAC secret/key-management setting is introduced here.

### Atomic reservation transaction and final-slot argument

Use a dedicated short reservation transaction, separate from password work, user creation and health/session mutations. Preliminary actual auth guards remain first; release only a **read-only** preliminary ORM transaction before starting this one. Never roll back pending writes or hold two pool checkouts waiting for each other.

**Mandatory lock order across every writer:** applicable session-binding row(s) in ascending ID → singleton control row → existing window rows sorted `(scope_rank, key_digest)`. Maintenance/recovery never acquire session rows after locking control. Login/register can use an anonymous or authenticated binding as permitted today. Bootstrap with no valid binding retains its existing IP-only/no-extra-CSRF policy, rather than inventing a new guard. Unauthenticated or guard-invalid protected requests never reserve.

1. Begin READ COMMITTED on the verified primary with bounded transaction-local timeouts. Lock the applicable current session binding `FOR SHARE` (not KEY SHARE if non-key session updates must be excluded); reuse current Origin/CSRF/account/session rules. No user-existence lookup to decide whether to count a credential identifier. Session/absolute/idle validation keeps its **existing injectable auth clock**; limiter DB time does not silently change authentication expiry policy.
2. Lock control `FOR UPDATE`. Require the expected policy/codec/generation and appropriate state. Recheck actual applicable guards after waits before budget outcomes; an expired/revoked/mismatched binding returns the existing guard error with no charges. QUARANTINED/missing store is unavailability, not an unknown-account result. Origin/CSRF requests already invalid at entry still receive Phase 9A guard responses before throttle work.
3. Read existing requested windows `FOR UPDATE` in fixed key order. Missing keys are empty **only in transaction memory**. The global control lock serializes every compliant creator/deleter, so it locks the creation gap without needing a fake empty row. Never use `SKIP LOCKED`/replica absence to treat a contended key as empty.
4. Sample primary wall time **after all waits/locks**. Proposed expression: `floor(extract(epoch FROM clock_timestamp()) * 1000)::bigint`. Do not use transaction-start `now()` as the decision time. Validate integer/range and existing timestamps/expiry. If sample < persisted high-water, stage a QUARANTINED/backward-clock outcome and commit that control transition **without charges**; return unavailable only after handling commit outcome. Do not raise an exception that accidentally rolls back the quarantine and then claim it persisted.
5. Filter each locked list to values strictly greater than `sample−900000`. If either already has its limit, append **neither**, create no missing key and return Limited(900). Updating only observed clock metadata on this denial is permissible; it is not a budget charge. Do not prune/create rows merely to make a denied operation look successful. Independent maintenance owns physical deletion.
6. If both have room, check retained-key capacity for the missing-key count. Capacity uncertainty/exhaustion is Unavailable, not an invented credential error. Only now insert missing rows with their **first real admission**, and append to existing rows. One transaction updates both windows, retained-row count and high-water. Unique PK protects against duplicate creation; an unexpected conflict while the control gate is held indicates a noncompliant writer/race and aborts safely. Do not blindly upsert over another transaction's admitted list.
7. Commit, release all locks/connection, then report Allowed and perform existing password verification/hash/registration/session issuance. Wrong password, duplicate registration or later auth-write rollback **does not refund** this committed reservation. Any precommit exception rolls back both budget changes and new-key count. Unknown commit outcome reports unavailable, never automatic refund, replay or false success.

With one final account/IP slot, worker A holds the control and key locks, writes its lists and commits. B cannot read that decision state until it acquires the gate; under READ COMMITTED its later locked reads see A's commit and deny. If A aborts, B sees the old state and may admit. Absent-row insertion and capacity allocation are serialized by the same gate. Every participant, including maintenance, must obey this protocol; table uniqueness alone does not make count-then-write atomic. This is a design argument requiring real PostgreSQL contention tests, not a passing PostgreSQL result.

**Guard/transaction handoff:** the current SQLite boolean/IPC challenge is not reused. A future app adapter must run real guard logic on the locked primary transaction/connection, preserve cookie binding and account authorization, and reload needed ORM state safely after reservation commit. It must not add password work inside the lock or make ordinary logout/read paths depend on this control row. Session revocation may race a request already authorized before its commit as today; this limiter is not a revocation redesign.

### Isolation, errors, deadlocks, pools and retries

READ COMMITTED is sufficient **only with the explicit global/key locking and trusted writers above**; repeatable read/serializable alone is not a substitute for correct missing-key handling. Lock order includes session interactions, global logout, deletion and maintenance. No control-holder may later wait for a session row. Unrelated health transactions must not call the limiter mid-write. Review all application mutators for cycles before integrating.

Baseline: no automatic retry for deadlock `40P01`, serialization abort `40001`, unavailable/timeout or connection failure. Confirm rollback, release pool resources and return generic 503. These known-aborted outcomes can be safely evaluated for at most one bounded retry later, but only with repeated guards and a total deadline; that is not this recommendation. A connection lost during commit is ambiguous and must never be retried without a separately approved idempotency/freshness contract. Request IDs unbound to changed credentials can become guessing shortcuts; do not persist password hashes/CSRF/cookies as deduplication payloads.

Proposed resource settings for later testing, **not configuration edits**: auth transaction pool≤2 connections/worker, no overflow, checkout wait≤1s; `SET LOCAL lock_timeout='250ms'` and `statement_timeout='1000ms'` within each transaction. Total DB connection budgets include worker count plus ordinary app pools. Connection establishment, filesystem/WAL flush and scheduling are not bounded by checkout/lock timeouts alone. Use explicit rollback/reset on return, discard broken connections, keep pre-ping/reconnect separate from replaying DML and avoid leaked isolation/timeout/read-only settings on pooled connections. Reuse existing infrastructure only if these bounds and ordinary-session availability can be demonstrated; no pool/driver version change is authorized.

### Primary time, failover and recovery contract

**Guarantee being proposed:** atomic durable counting against one writable primary's observed integer wall-clock timeline and the approved restoration/primary-generation procedures. It is **not** unconditional 900 seconds of independent physical elapsed time. PostgreSQL primary time can jump just as host time can; changing SQL clock functions does not solve that.

| Event | Required contract / limitation |
| --- | --- |
| Normal time and backward movement | Sample after locks; exact cutoff, no unapproved tolerance/clamp. Observed `db_ms < last_db_ms` quarantines without charges. Even a small real backward correction may deny service; this conservative availability choice needs approval. |
| Forward clock step | A larger sample alone cannot distinguish real idle time from a jump. The baseline explicitly trusts primary forward-time discipline; a jump can expire windows early. Known uncertainty/clock alerts block admission and cleanup until reviewed recovery. No automatic detector or arbitrary skew threshold is claimed. If immunity to arbitrary forward jumps remains mandatory, **this DB-time contract is insufficient**; do not implement/enable it without a revised authority requirement. |
| Routine DB/app restart | App-worker restart retains committed rows and does not reset budgets. DB restart requires verified recovery of the same authoritative committed state and clock/endpoint health; uncertainty selects quarantine. An ordinary connection reconnect must not initialize an empty store. |
| Primary failover/promotion | Drain/fence application admissions **before** changing writer endpoint. Fence old writer/network/credentials so split-brain primaries cannot both authorize. New writer starts blocked until state freshness, replication/RPO, time and a new expected admission generation are approved. Automatic promotion that copies READY and admits immediately does not meet this contract. |
| Restored/stale snapshot | Rows, checksums, MACs and generation text do not prove newest state. A restored snapshot can omit charged attempts. Do not serve from it merely because it parses. Treat it as uncertain; preserve verified budgets or conservatively quarantine all new admissions. No real restore performed here. |
| Transaction rollback | Confirmed aborted reservation makes no budget charge. Independent committed maintenance remains. A connection-loss/commit acknowledgement gap can retain a charge; no replay or promised refund. |
| Replica/DB unavailability | No security decision from replicas/caches/old primary or process memory. Fail closed 503; existing read/logout operations keep their normal dependencies, not a new limiter fallback. |

`pg_is_in_recovery() = false`, writable transaction state, correct schema and expected generation are necessary checks, not proof of freshness or unique writership. Two split-brain servers can both report writable. Routing, primary election/fencing, replication acknowledgements, WAL durability and RPO require explicit deployment evidence outside this provider. Local commit durability is not proof that failover retains every acknowledged reservation; replication policy must be approved/tested. This task installs/provisions none of it.

Require approved writer/startup binding on connection acquisition and inside the control transaction; a changed/unconfirmed identity quarantines rather than trusting a copied READY row. A value such as `pg_postmaster_start_time()` can signal a restart but is not cryptographic identity or restore/split-brain proof. Planned restart/promotion drains admission first; unplanned changes must not become an automatic READY transition. The trusted source/operational attestation for writer identity and its tests are unresolved deployment gates. Ordinary reconnect to the same verified writer never resets counters or replays an ambiguous attempt.

If storage cannot commit a clock-health quarantine, the affected call still fails closed but **this provider alone cannot claim a durable global quarantine across other workers**. That requires the approved admission-control/operational gate and confirmation of persisted state before reopening. An ambiguous commit or an unavailable database is not proof that READY changed to QUARANTINED. This distributed-failure assumption is a release gate, not an implemented emergency fallback.

Recovery decision record carries Phase 9F forward: prefer verified remaining-budget preservation if a latest authoritative state/time anchor is available; otherwise close **all affected new admissions** for a full trusted 900-second elapsed interval after the last possible old admission before explicit reinitialization/new generation. Do not time that quarantine using the same suspect jumping wall clock. Loss of the independent recovery observer's continuity restarts quarantine or keeps it blocked. Old writer/worker traffic must be proven unable to admit; a stop acknowledgement/busy fence is insufficient. Without that proof, neither an empty table nor copied generation is safe recovery. No recovery service/tool/state reset is implemented here; an operational owner must approve the contract.

### Primary-only security routing

Use one explicitly designated writable-primary auth pool for **all** control/window/session reads involved in admission and every write/cleanup/reconciliation. No read-replica routing, ORM read/write split, stale cache or replica-based “missing user/key” shortcut. Verify transaction read-only/recovery/schema/policy/generation before decisions; failure is unavailable, not fallback. Pool stale connections must be drained across promotion. Maintenance uses the same primary. Neither a TLS-valid endpoint nor `pool_pre_ping` establishes that it is the newest/sole primary. PostgreSQL credentials/grants/TLS/hosting remain separate approval work; no actual DSN or secret was inspected.

### Bounded maintenance, cardinality and privacy

Cleanup is a **separate committed transaction**, never a refund side effect of denial. Lock control, select at most 100 expired candidates using the expiry index, lock them in the same key order, resample/validate DB time after waits, delete only still-expired valid rows, decrement count by actual rows removed and commit high-water. Recheck clock against both persisted high-water and the earlier candidate-sampling time. On clock/store quarantine, do not purge using suspect time. `SKIP LOCKED` could be used only for a separately reviewed maintenance optimization, never to authorize against absent keys. The global gate makes it unnecessary initially.

Recommend bounded primary maintenance on a coordinated application lifecycle/job with a proposed≤5s cadence and ≤100 rows/batch, no extra Redis/service. Admit the cleanup-lag/lock contention SLO only after measurement; denied/no traffic must not starve it. Capacity includes retained expired rows until deletion. No active eviction, unlimited synchronous purge loop or allocation beyond cap. Full count/invariant reconciliation is bounded to cap+1 at controlled startup/maintenance intervals; requests examine only involved keys plus control, rather than A's six full-snapshot reads. Drift/quarantine is not automatically repaired. The count protocol is trusted-writer state, not a guarantee against an administrator silently editing valid-looking rows.

Use server-side existing strip/lowercase email semantics and length/body validation, not provider-specific alias rules or user-supplied digests. Key allocation must not depend on user existence. Canonical peer IP comes only from verified ASGI/proxy trust; a documented shared unknown-peer sentinel remains bounded, never a bypass. One key codec/version per cohort; IPv6/raw-host canonicalization and tagged digest encoding change key identity and need cutover tests. Scope/digest are server-derived, never request-selected namespace or deployment realm.

Unkeyed digests are pseudonyms, not anonymity: IP/email candidates remain guessable. A keyed digest would require explicit durable-secret rotation/continuity approval, not an ephemeral per-worker secret. No raw passwords, tokens, session cookies, emails/IPs or health values in limiter tables/logs. Restrict database roles and exports; retain eligible event metadata only through the window plus bounded cleanup lag. Account deletion need not instantly clear an operational abuse budget (which could enable re-registration bypass), but this privacy/retention policy requires separate approval; it does not authorize inspecting real accounts.

Shared NAT/IP ceilings can block unrelated legitimate users. The global account ceiling can be targeted by an attacker with valid anonymous CSRF; distributed sources and high-cardinality candidates can consume the global capacity. Durable storage makes these effects survive workers/restarts; it does not solve them. Keep ingress/body/concurrency controls and separately evaluate account/IP-pair/escalation policy without silently dropping global guessing protection. Registration 201 versus duplicate 400 still reveals membership; generic 429/401 alone is not an enumeration redesign. No password recovery/idle/clinical feature change is proposed.

### Fail-closed errors, observability and availability

- Known exhausted budget: existing generic **429**, `Too many attempts. Try again later.`, `Retry-After: 900`; no information about which budget/account exists. Constant retry may overstate the remaining wait but is compatible initially.
- Unavailable store/pool/primary/time/generation/capacity/integrity/commit: proposed generic **503**, `Authentication is temporarily unavailable. Try again later.` No Argon2, account/session creation, false success or process-memory admission fallback. Preserve current applicable guard 401/403 and malformed-body 422 before accounting.
- Fail-open would improve availability but defeats the shared-guessing guarantee exactly when storage can be induced to fail; not recommended. Incident reauthentication/global sign-out can be blocked under fail-closed behavior; no hidden bypass/exemption is added. Existing valid-session bootstrap, reads and current logout do not acquire a throttle-control dependency.
- Observe aggregate action/outcome, coarse latency, queue/lock/abort counts, retained-key/capacity/cleanup lag and quarantine/generation health. Alert immediately on primary/time/generation uncertainty, quarantine, counter drift or repeated store errors. Thresholds for latency/busy-rate alerts require measured approval, not invented security policy. Never log bodies/credentials, key digests as account identifiers, raw exception/SQL parameter/DSN values or health data. No telemetry service is created.

### Additive migration, feature-off and rollback gates

No migration is written. A future approved next revision after actual head [010](../backend/alembic/versions/010_session_activity.py) would add only dedicated control/windows/index/constraint/helper metadata; no user/session/health backfill or counter reset. Number is not reserved. Follow [Alembic conventions](../backend/alembic/env.py); test fresh install, synthetic upgrade with preservation, idempotent head and failure behavior before adopting. Existing exact [SCHEMA_REVISION](../backend/app/deployment.py#L7) readiness may advance even with behavior disabled; do not bypass it or auto-migrate at application startup.

Proposed strict **`AUTH_SHARED_THROTTLING_ENABLED=false`** preserves existing process-local behavior byte-for-byte when off, including live partial-IP charging, successes/failures, demo refusals, sessions/CSRF/cookies, and no shared-table reads/writes or shadow/double charging. Flag does not exist now. Enabled provider must reject unsupported dialect/policy/schema, bad values and unapproved deployment modes at startup. A PostgreSQL URL alone is not activation approval. Initial future testing is synthetic/temporary only; production true remains blocked until separate hosting/time/recovery/security approval.

No mixed memory/shared workers or mismatched key codecs/generations. Quiesce new auth, validate schema/provider and approved clock/recovery contract, deploy off, verify compatibility, then opt in only as one reviewed cohort. Old in-memory history has no reliable import; require explicit supervised reset acceptance or conservative full-window quarantine after verified drain. Drain pools/workers during failover/cutover. Rollback coordinates disable/provider changes, retains additive schema, never restores old health/session/password snapshots or destructively downgrades counters. Returning to memory loses durability/shared protection and restores partial-IP policy; acknowledge this loss, and revalidate time/freshness before re-enable. Idle enforcement remains disabled by default and is unrelated.

### Comparison with the monotonic SQLite authority

| Concern | Isolated SQLite owner A | Proposed PostgreSQL contract |
| --- | --- | --- |
| Clock guarantee | Wall-independent elapsed time while one owner survives; terminal continuity loss | Durable primary wall timeline across app restarts, but explicit forward-time trust/recovery gate; **not** the same stronger clock promise |
| Admission | Same-file writer serialization plus owned IPC/epoch fencing | Primary row locks/control gate; no owner RPC or toy guard transcript. Existing HTTP authorization/freshness still applies. |
| Integrity/recovery | Full bounded HMAC/schema scans, ephemeral private key; owner loss cannot resume | Durable DB state/checks/roles and controlled reconciliation; lacks A's per-request cryptographic missing-row guarantee unless separately designed |
| Latency/concurrency | Two transactions, six full-state reads and guard IPC; Phase 9F smoke only | One admission transaction over two keys/control plus separate maintenance; network/pool/serial control costs unknown; no speed claim or benchmark |
| Operations | Two files, one owner process, local capabilities/no takeover | Database migration/grants/TLS/primary fencing, replication/RPO, backup/recovery/alerts; **more infrastructure responsibility**, less per-app authority lifecycle |
| Portability | Windows evidence; local-file only; no hosting proof | PostgreSQL-specific behavior; SQLite cannot validate it; Windows/Linux client and hosted primary/failover evidence required |

### Exact acceptance gates and smallest next step

All criteria below are **requirements, not executed PostgreSQL results**:

1. Policy: exactly 30/IP and 10/account; combined login/register/reauth keys and IP-only bootstrap; known/unknown failures, success/duplicate registration; same-ms multiplicity; tests at 899999/900000/900001ms and a fixed-bucket-boundary counterexample to prevent accidental semantic replacement.
2. Transactions: actual PostgreSQL independent connections/processes, at least 100 bounded four-contender final-slot races for IP/account/absent keys/capacity: exactly one last admission, no partial charge, duplicate row or count drift. Test zero-slot denials create nothing, rollback after each staged write, primary locks after waits and cleanup races. Retries disabled in the baseline.
3. Guards/sessions: all 31 Phase 9A cases in disabled/enabled modes plus session expiry/revocation/CSRF change during waits; no budget changes on guard/body/dependency rejection, cookie/session/ordinary/global logout parity, cross-account ownership, no Argon2 or health writes under throttle locks.
4. Time/recovery: controlled primary-time forward/backward movement, high-water/quarantine commit/rollback, same-primary restart, stale connection/replica rejection, old-primary fencing and restored-state uncertainty. Assert no recovery admission until authoritative budgets or full trusted quarantine are proven. Accept/document residual forward-wall-time assumption; do not declare clock safety from a mocked clock or generation alone.
5. Resource/failure: cap/array/cleanup bounds, no active eviction, corrupt/missing/unknown control/schema, known aborts/deadlocks/lock/query/pool failures and ambiguous commit. Zero automatic unmetered fallback, retry or false success; no leaked transactions/connections or persisted secrets. Future injected faults, not real disk destruction.
6. Performance/operations: retain Phase 9F's **proposed** p95≤100ms/p99≤250ms added latency and additional RSS≤128MiB as owner-review targets, measured with ≥100 controlled samples at 0/1000/10000 windows and separately approved contention. Quantify the global-control bottleneck rather than presume PG scale. Proposed cleanup within ten minutes after expiry under healthy operation, even without admitted traffic; measure backlog and pool impact.
7. Migration/flags/UI: temporary PostgreSQL fresh/upgrade datasets only when separately approved; exact flag-off parity and startup/readiness failures; rollback/re-enable without reset. Real frontend→temporary backend with synthetic accounts must distinguish 429/503, avoid false login success, protect other-account content and handle lost responses without hidden duplicate reservations. Linux/Windows supported-version checks and actual primary/failover evidence remain separate.

**Smallest next synthetic implementation proposal:** first approve PG-ADR-01's database-time trust, global-gate, accounting and recovery assumptions. Then authorize an isolated SQL-construction/specification test harness plus injected-time reference-model tests, outside app routes/migrations and with no server installation. Such a harness can validate policy/state transitions and SQL shape, **not PostgreSQL locking/isolation/durability**. Actual transaction acceptance needs later explicit approval for a disposable PostgreSQL target. No model, SQL adapter, migration or provisioning has been implemented in Phase 9G. If A's arbitrary-wall-jump immunity is still required for the hosted limiter, resolve that requirement before implementing this wall-time design.

### Actual Phase 9G validation and limitations

New evidence root `%TEMP%/migramind-phase9g-6q3aa0l6`: filtered backend/prototype source and starting report/README baselines; newly created synthetic SQLite fixtures only; read-only reuse of isolated Python 3.13.12 dependencies. Restricted development/local, `DATABASE_URL=sqlite://`, idle false, dotenv/bytecode disabled, copied-source PYTHONPATH and private TEMP/TMP. No existing database/account/health/backup/export/secret/private configuration access, actual DSN inspection, installation or external service.

| Existing check run in Phase 9G | Exact outcome |
| --- | --- |
| Unchanged isolated SQLite authority suite | **32 passed**, 67.459s unittest / 69.21s wall; 240s cap |
| Existing Phase 9A guard-ordering regressions | **31 passed**, 21.80s pytest / 27.28s wall; 120s cap |
| Failures/retries | **None**; existing Starlette/httpx deprecation warning |
| Documentation/source integrity | **84 local links / 34 source references**, **71 unchanged tested source/declaration files**; all previous report bodies and prototype files preserved; only two Phase 9G document edits; zero owned store directories left; app/migrations/locks/configuration unchanged; whitespace passed |

```text
# New filtered temporary root, no install/provisioning.
<isolated-python> -B -m unittest discover -s prototypes/synthetic_auth_throttle -p test_adapter.py -v
# Copied backend, explicit environment above, new owned basetemp.
<isolated-python> -B -m pytest -q -ra tests/test_auth_guard_order.py --basetemp <new-root>/guard-data -p no:cacheprovider
```

These checks preserve existing behavior; they do **not validate the proposed PostgreSQL design**. No PostgreSQL connection/installation/provisioning/SQL execution/compilation harness, failover/restore, new reference model, full backend/frontend/browser/build, Linux, performance or new architecture test was run. Phase 9F replay/stop/timing observations remain historical and unfixed; no recovery or IPC repair is smuggled into this design task. Evidence includes `prototype.log`, `guard-regressions.log`, `results.json`, starting baselines, tested source and TEMP wrapper.

**Decision status: PROPOSED / NOT READY for application implementation or activation.** Unresolved approval gates: database-wall-time contract and forward jumps, primary fencing/freshness/RPO/quarantine, global-gate throughput, durable integrity/retention/key policy, safe guard transaction handoff, live all-or-nothing/NAT/targeting policy, schema/flag/pool settings and operator ownership. Prior storage/recovery/enrollment/accessibility/clinical/research blockers remain unchanged; public/real-health release is NO-GO. Only this report and release readiness change. No app/prototype/migration/dependency/configuration edit, commit, push, PR, merge or deployment.

## Phase 9F: architecture and operational feasibility review (2026-11-15)

Verified `security/shared-auth-throttling`, HEAD `c32cb28` (merged PR #24). Preserved all uncommitted Phase 9B–9E source, tests, archives and report bodies. **Audit/design only.** This review was resumed after interruption; completed synthetic results from the earlier part of the same Phase 9F task were retained, not rerun merely to obtain new passes. No architecture, recovery mechanism, route, migration, dependency, flag or configuration is implemented here.

**Recommendation (c): defer application integration until a PostgreSQL-ready transactional/recovery design is approved.** Retain A as an isolated safety experiment, not as the next live authentication component. This does not mean installing PostgreSQL for the local demo: keep current documented loopback/synthetic limitations and do not make public-security claims. The earlier Phase 9E verdict allowed a separate design review; it did not approve deployment. This review identifies operational gates that still prevent integration.

### Independent ownership and fencing assessment

[Ownership](../prototypes/synthetic_auth_throttle/authority.py#L129) combines a lifetime SQLite writer reservation on the lock file with a committed, irreversible NEW→ACTIVE claim in the counter file. Main-file `BEGIN IMMEDIATE` serializes the first claim even independently of the extra lock file. [Runtime validation](../prototypes/synthetic_auth_throttle/authority.py#L110) checks epoch/state and authenticated data inside each main-file writer transaction. [Seal](../prototypes/synthetic_auth_throttle/authority.py#L250) uses that same writer lock. Under one actual local file identity, working SQLite filesystem locks, trusted OS and cooperating code, **competing owners and admissions after a committed seal are prevented**. Existing process-race/stale-client tests passed again. This is not a distributed consensus, lease-based failover or malicious-host proof.

- **Process death:** OS lock release does not authorize takeover: persisted ACTIVE prevents a new owner, and memory-only integrity keys/origin are not a recoverable time authority. This preserves safety by refusing service. Worker restart with the same surviving authority works; owner or host restart is terminal for that store.
- **Connection reuse:** current workers open a fresh loopback connection per operation; epoch/nonce/sequence/MAC checks reject stale or unsigned replies. Already authorized work can commit **before** a fence linearizes. Closed-client/response-loss ambiguity may retain a charge; a timeout is not proof of rollback.
- **Filesystem assumptions:** separate lock and counter files must stay on a nonsynced local filesystem with reliable locking and durability. Moving/replacing/unlinking files, restoring old signed snapshots, VM rollback, sync conflict copies and network filesystems are outside the proof. Epoch text and an acquired lock on a replacement inode cannot establish continuity. No real filesystem/OneDrive/host security settings were inspected or changed.
- **Suspension:** a paused owner can retain locks and deny service. Platform monotonic suspend behaviour is unverified; paused elapsed time may conservatively overblock, but UTC catch-up is forbidden in A. Suspending all processes, reboot and power loss were not physically tested.
- **Abnormal shutdown:** there is no creator-parent liveness watchdog in [owner loop](../prototypes/synthetic_auth_throttle/authority.py#L370). Normal context cleanup is tested; abrupt controller death could orphan a still-live authority. That is a source-derived lifecycle risk, not an observed orphan or a reason to reset counters. FULL synchronous mode and a rollback journal do not independently certify power-loss durability on actual hardware.

### Evidence-backed operational findings

| Finding | Evidence and prerequisites | Assessment |
| --- | --- | --- |
| F9F-01: terminal authority loss lacks an operational recovery path | Existing crash/refusal tests and irreversible claim/key lifecycle. One ordinary owner restart can deny all new reservations indefinitely. | **Medium operational integration blocker**, intentional current fail-closed design, not an authentication bypass. Availability/owner responsibilities must be approved before adoption. |
| F9F-02: authenticated request transcript can be replayed within the active epoch | A new synthetic store accepted a recorded initial request and its two recorded guard replies twice; each key held two admissions. Server accepts a client nonce but stores no used-nonce set and supplies no fresh server challenge nonce. | **Low under trusted-worker/local-host prototype assumptions**; adoption gate if IPC is a security boundary. Requires access to a valid local transcript, not demonstrated remote/key compromise. Fresh-client-nonce reply protection is not full request replay protection. No real auth/CSRF flow was attacked. |
| F9F-03: normal stop acknowledgement is not fencing | Paused a synthetic admission at its second guard, obtained authenticated `stop` success, then completed the admission. Final control remained ACTIVE as the process exited. | **Low lifecycle/API ambiguity**, not a bypass of committed SEALED state. Recovery must explicitly fence/drain; a stop acknowledgement is insufficient. |
| F9F-04: global verification and IPC consume a significant local latency budget | Every successful reservation performs two writer transactions and six bounded full snapshot reads/sign/validation operations, plus schema/JSON/HMAC and guard round trips. Small timing sample below. | **Medium feasibility gate** at growing cardinality; no throughput/saturation outage claimed. Adding workers does not remove SQLite serialization. |

A separate observation held the counter writer lock: `fence()` returned StorageBusy and the old owner could still reserve after release. A later successful fence blocked it. This is correct failure signalling, but confirms that an attempted/busy fence is not a completed ownership change. No patch to protocol, stop or recovery was made. Same-epoch transcript replay should be addressed by a separately approved freshness/idempotency design (or removal of this IPC path), not an unbounded remembered-nonce map. It can consume budgets; it does not prove a live password or session bypass.

### Architecture decision matrix

| Dimension | A: monotonic SQLite owner (actual prototype) | B: direct SQLite transactional limiter (alternative) | C: PostgreSQL-backed shared limiter (future hosted design) |
| --- | --- | --- | --- |
| Correctness | Exact sliding window, local monotonic authority, atomic pair, epoch fencing under the assumptions above. | `BEGIN IMMEDIATE` gives same-file atomicity without owner IPC. Requires an explicit host/database wall-time, anomaly, restart and recovery policy; not equivalent to A by changing one clock call. | Transactional row locks/conditional reservations, absent-key creation, consistent lock order and capacity coordination can provide shared accounting. A plain SELECT-then-INSERT at READ COMMITTED is insufficient. |
| Clock | No UTC dependence while owner survives; no safe rebase after loss. | SQLite wall time still comes from host OS. Integer precision/cutoffs, backward/forward jumps, high-water and quarantine must be specified. No arbitrary tolerance is approved. | Primary DB time sampled after relevant locks, not stale transaction-start time or app-worker clocks. DB clocks also need anomaly/failover policy; not inherently monotonic. |
| Recovery/availability | Same-owner worker restarts work; owner loss fails closed permanently. Two SQLite files, ephemeral keys and no takeover. | Process restart can retain counters with durable clock/state rules; still one host/file and writer contention. Fail-closed on corruption/clock uncertainty; manual quarantine may be necessary. | App-worker restarts need not lose state; availability depends on DB/replication/failover/RPO. Lost commits or stale restore must not silently reopen budgets. |
| Concurrency/latency | SQLite writer serialization plus two IPC guard challenges, global scans and local process lifecycle. Eight handlers do not mean eight concurrent writers. | Avoids owner transport/global MAC design if replaced with reviewed bounded database invariants; still serial writes and interaction with session/diary transactions. Such simplification changes integrity/trust policy and needs approval. | Row-level concurrency can reduce unrelated-key contention; shared IP/account hot spots and capacity locks remain. Network/DB round trips and pools introduce measurable cost. |
| Operations | Owner supervision, terminal loss, epoch/fencing, two-file lifecycle, IPC capabilities and ephemeral key management. | Fewer processes/endpoints; explicit time/restore, migrations, maintenance and file protections still required. | Existing SQLAlchemy/psycopg support is useful, but grants/TLS/migrations/backup/monitoring are separate unapproved operational work. |
| Portability | Windows functional evidence only; no multi-host/network filesystem support. Suspend/locking needs Linux evidence. | Local Windows/Linux testing needed, not a general multi-host solution. | PostgreSQL-specific tests/primary-clock/locking/failover required; SQLite tests cannot certify it. No instance provisioned. |

**Concrete candidate B policy, for review rather than activation:** sample one integer UTC-ms host-clock value after `BEGIN IMMEDIATE`; reject any sample below committed high-water, without a guessed skew tolerance; otherwise use that sample with the exact rolling cutoff and commit its high-water with state. Normal process restart reads durable windows and that high-water. Forward wall-time advancement is explicitly trusted as elapsed time under B, so an undetected forward step can expire budgets: this is a weaker guarantee than A, not a hidden solution. Known clock correction, uncertain downtime or stale restore requires drain/quarantine and operator approval, never an automatic reset. Moving the sample into SQLite SQL does not improve the clock's authority. B also needs durable integrity/key or database-invariant policy; memory-only owner MAC keys cannot simply be discarded while claiming equivalent checks. None of these changes is approved here.

**Why (c):** terminal loss and operational control requirements are too costly for a general authentication dependency, while globally authenticated scans already add substantial latency in a small smoke check. B is attractive for a supervised single-host prototype but requires an expressly weaker/different wall-clock continuity contract than the approved A safety model. Do not silently make that substitution. A remains valuable research evidence, not an available hosted auth service.

Evidence that could change the decision: choose **(a)** if a named operator explicitly accepts terminal fail-closed loss and demonstrates recovery/lifecycle, cross-platform correctness and acceptable costs for a narrow synthetic deployment; choose **(b)** if a reviewed host-time/quarantine contract and low-volume local-only requirement are approved and tested. C becomes implementable only after primary-time, transactional recovery, schema and deployment gates pass; PostgreSQL is not a blanket security guarantee.

### Recovery alternatives — design only, no reset performed

Current A has **no recovery API**. A new temporary store is a new experiment; it is not restoration of the old allowance. Never flip ACTIVE→NEW, replace a clock origin/key/epoch and call it continuity, restore health/session snapshots, or infer elapsed time from old UTC. Authentication reads/logout that do not reserve should retain their ordinary availability, but normal DB failure still affects them.

| Proposal | Conservative treatment of budgets | Required proof/limitation |
| --- | --- | --- |
| R1: controlled manual reinitialization after quarantine | Stop/drain new reservations, fence every reachable old authority and prove unreachable ones cannot authorize application requests. Keep **all affected new admissions closed for a full 900 seconds measured by a new trusted elapsed authority after the last possible old admission**. Then explicitly initialize a new generation/store. Restart the quarantine if its clock continuity is lost. | Requires a durable application-wide admission/generation gate, verified quiescence and approved owner procedure; none exists today. An unconfirmed busy fence or stopped IPC listener is insufficient. Blanket denial conservatively preserves unknown/active quotas; no premature reset. Downtime/incident-response cost must be accepted. |
| R2: live handoff preserving verified remaining budgets | While old authority/key still trustworthy, freeze reservations and authenticate a latest snapshot at a known old elapsed instant. Carry each still-live event's remaining lifetime into the new generation **without credit for unmeasured handoff downtime**, re-sign under approved new authority, fence old clients and atomically publish the new admission generation. | No direct copy of monotonic timestamps into another origin. Needs an explicit representation for remaining lifetime, cross-generation fencing and interrupted-handoff state machine. If old authority is lost/unverifiable mid-handoff, fall back to R1, not guessed ages. No handoff is implemented. |
| R3: conservative full-window budgets from a verified latest snapshot | At minimum, preserve exhausted/full quotas for each relevant known IP/account for a complete new window; block unknown keys too if snapshot completeness/freshness cannot be proved. | Potentially severe overblocking; a stale/incomplete snapshot or lost integrity key is not proof of the set of active keys. Without completeness, this reduces to blanket quarantine R1. |
| Durable B/C recovery | Retain committed state, primary clock and approved integrity/grant/key lifecycle; replay/restore only under a defined RPO and quarantine if newer attempts could be missing. | Existing MACs authenticate contents, **not freshness**. New stable keys, recovery control or infrastructure require separate approval; no existing key/backup was accessed. |

R1 is the smallest conservative **recovery contract to specify**, not an instruction to reset anything now. Recovery must have separate authorization/audit, a named owner, clear 503/retry wording, old-worker/client rejection and a tested rollback/abort state. Adding a recovery command to A without this application-wide gate would weaken its fencing claim. No recovery mechanism, snapshot restoration or owner reinitialization was executed in this audit.

### Operational risks and accidental-corruption assurance

The [state/schema checks](../prototypes/synthetic_auth_throttle/authority.py#L87) reconcile bounded row counts, validate types/ranges/order/expiry, and HMAC the logical rows/control plus schema definitions. Existing tests cover in-range drift, negative/malformed/missing values, deleted active windows and missing objects. This is useful **accidental logical-corruption detection while the owner retains its key**. SQLite parse/IO failures fail closed too. It does not establish whole-file/page integrity, recoverability after key loss, newest-state provenance or resistance to malicious full-host/key access. Replaying an older complete correctly signed snapshot within an epoch is not prevented by HMAC alone; no destructive restore test was run. Do not call hashes anonymous, HMAC encryption, or the prototype tamper-proof storage.

No autonomous cleanup scheduler exists: each guarded reservation performs independent committed maintenance; explicit `cleanup()` also exists. An idle surviving store can retain expired metadata indefinitely. A future retention SLA therefore needs a bounded cadence/lifecycle owner, not just the 100-row deletion cap. All active keys remain protected; capacity exhaustion blocks new allocations with unavailability, including distributed high-cardinality candidate identifiers. Existing-key traffic still pays global verification cost. Pseudonymous IP/account state and SQLite free pages/snapshots need retention/copy policy. No real filesystem, existing backup or OS encryption setting was inspected.

The live three-second guard IPC wait occurs while a SQLite writer reservation is held. Slow/paused synthetic workers can delay other clients even though each frame is bounded; busy timeout bounds lock waiting, not total filesystem/JSON/HMAC/commit latency. Treat eight handlers, busy wait 0–1000ms, 8192-byte frames and bounded snapshots as resource limits, not a throughput or total-deadline guarantee. Creator-parent death/orphan cleanup, process shutdown during IO, file replacement/sync and actual power loss require explicit acceptance evidence. No host suspend/reboot, disk filling or filesystem disruption was attempted.

### Exact live/prototype policy differences

The requested "fixed-window boundaries" need correction: **actual live and prototype policies are rolling/sliding windows, not fixed/tumbling buckets**. Live retains `(monotonic_now−900, now]` in float seconds; A retains `(owner_elapsed_ms−900000, now]` in integer milliseconds. Events exactly at the lower cutoff expire. A fixed bucket replacement could double admissions near bucket rollover and is not compatible.

| Policy | Live auth today | Prototype/recommended integration issue |
| --- | --- | --- |
| Accounting | IP check first; account-full still charges IP. Valid successes, bad passwords and duplicate registration all charge. | Atomic all-or-nothing; less shared-IP collateral denial but already-blocked accounts can retry without spending these auth budgets. Ingress work still needs limits; adopting it live needs approval. |
| Actions | [attempts](../backend/app/auth.py#L144) shared across login/register/logout-all/account deletion, bootstrap IP-only. | A only implements login/register; no actual password/bootstrap/reauth flow. All current consumers must move together in any future enabled mode. |
| Guards/session | [Phase 9A order](../backend/app/auth.py#L183): actual session/Origin/CSRF before accounting; body errors precede handler. | Toy callback/IPC challenge is not real authorization. Future integration must recheck authoritative session state after lock waits without weakened guards or read-to-write deadlock. |
| Errors | Generic 429, `Retry-After: 900`; known/unknown wrong login identical 401. | Prototype has exceptions/Decision, **no implemented HTTP 503**. Generic fail-closed 503 for store/clock/capacity failure is a proposal, not current app behavior. Lost responses can retain charges. |
| Keys/privacy | ASGI peer host memory key; SHA-256 strip/lowercase email. Trusted proxy policy matters. | Canonical documentation IP and tagged digests, synthetic domain restriction. Different encoding/canonicalization requires reviewed cutover; hashes are pseudonymous/guessable. |
| NAT/targeting/enrollment | Shared IP and global account ceilings can overblock NAT or allow valid-CSRF account targeting; new vs duplicate registration differs. | Durable state and atomic charging do not solve these. No registration-enumeration/recovery redesign or claim of complete abuse prevention. |

Legacy SQLite/UTC code is a prior **synthetic adapter**, not the application's process-local Limiter. It has the same prototype atomic charging but a different clock. No fallback path to it or architecture change was added in Phase 9F.

### Disabled-by-default design sequence and rollback gates

1. Approve the common exact-window/accounting/failure/recovery contract and choice of B/C before coding. Keep A isolated. No migration/flag change follows from this review. Existing idle enforcement remains false by default.
2. Define a small transaction-provider interface using normalized server identity and real guard revalidation; no client clock/namespace/limits. PostgreSQL provider uses primary-time after locks, deterministic key/absent-row locking and separate durable recovery rules. No owner-IPC callback transplanted into actual authentication.
3. Review an additive next Alembic revision after actual head (currently [010](../backend/alembic/versions/010_session_activity.py)); no number reserved here. Dedicated throttle/control objects only, no health/session backfill. Follow [migration conventions](../backend/alembic/env.py) with fresh/upgrade/idempotency/preservation tests on temporary synthetic copies. No automatic migration at startup. Readiness currently expects exact [SCHEMA_REVISION](../backend/app/deployment.py#L7); a new release may need upgraded schema even when behavior is off. Do not bypass readiness for an unmigrated database.
4. Proposed strict **`AUTH_SHARED_THROTTLING_ENABLED=false`** defaults to the exact existing process-local behavior: no shared-table reads/writes, no atomic-policy switch, no shadow/double charge. Flag does not exist now. True requires matching schema/policy/provider, explicit opt-in and appropriate deployment validation. Unknown values/unsupported true must fail startup, not silently fallback. A must not become hosted mode by setting a flag.
5. Validate enabled paths only against temporary synthetic databases/accounts and real temporary frontend/backend interaction. No provisioning or existing-data migration is authorized by these instructions. Preserve session cookies/expiry/CSRF/ordinary logout/global revoke and account isolation.
6. Opt-in only after platform/correctness/recovery/latency criteria pass, with a named operational owner. Drain old workers; no mixed memory/shared or different-policy cohort. Memory history has no reliable import: explicitly accept a supervised reset or conservatively quarantine after the last old admission. A false flag cannot be represented as persistent shared protection.
7. Rollback drains admissions before coordinated disable/provider rollback; retain additive tables, do not destructively downgrade or restore health/session/password snapshots. Returning to memory loses durability and restores partial-IP policy; document that loss. Re-enable only after schema/time/state/restore checks. If recovery/cutover state is uncertain, keep new auth closed rather than manufacture empty quotas. Existing authenticated reads/current logout should not gain an extra limiter dependency.

### Measurable acceptance criteria — proposed, not claimed passed

| Area | Required evidence before a future integration |
| --- | --- |
| Windows/Linux correctness | Same supported Python/locked dependency versions on Windows and a supported Linux runner; exact 30/10 and 899999/900000/900001ms boundaries, both providers/modes, malformed inputs/guards and zero unrelated account data changes. At least 100 bounded four-contender races for IP/account/absent-key/capacity cases, retries off: exactly one final-slot admission each. |
| Restarts/fencing/shutdown | Worker restarts preserve limits; owner/DB restarts and interrupted recovery follow the selected contract. Zero old-generation admissions after a **committed** fence; busy seal and stop acknowledgement never treated as fenced. Test parent/controller death, stale open connections, fresh/replayed request transcripts, ambiguous commit and safe owned-process cleanup. |
| Storage/integrity | Inject BUSY/LOCKED/permission/IO/commit errors without filling real disks; no unmetered fallback, false success, partial charge or active eviction. Test corruption/key loss and freshness/restore separately. No real backup restoration or power-loss claim from an exception test. |
| Recovery | On temporary stores, exercise drain/fence/abort and full-window quarantine with controlled trusted elapsed time. Zero new admissions during quarantine; no restart shortcut; no original counter/health/session changes unless explicitly specified. Verify interrupted handoff never double-admits; key/provenance loss selects blanket denial rather than trusting unknown state. |
| Performance/cadence | Proposed local added-latency gates: p95≤100ms and p99≤250ms at 0/1000/10000 retained windows, from at least 100 controlled sequential samples per condition plus separately authorized bounded contention tests; peak additional RSS target≤128MiB. Targets require owner approval/measurement, not clock-skew tolerances. No busy timeout tuning to hide correctness failures. |
| Capacity/retention | Never exceed 10000 live/retained rows or 30/10 events/key; no active-key eviction. Under a healthy approved scheduler, proposed expired-metadata cleanup within ten minutes after eligibility, measured even with all admissions denied or no traffic. Verify backlog, IO cost, contention and lease/cadence across workers. Not implemented today. |
| Frontend/backend | Real browser→temporary backend, fresh synthetic accounts only: valid/wrong login, registration, 429 and proposed 503, retries/response loss without duplicate reservation, CSRF rejection, stale session, other-account isolation, ordinary/global logout and flag-off parity. No UI false extension/login success or persisted sensitive drafts. |
| Operational/manual | Approved suspend/resume/reboot/recovery and local filesystem locking checks on target platforms, no host changes in this audit. PostgreSQL staging evidence for primary-time/row locks/replication/RPO/failover/grants/TLS needed before hosted claims. |

The six 1000-row timing observations below all exceed the proposed 100ms local threshold; they cannot establish a p95/p99 distribution. This is an early feasibility warning, not a benchmark failure of an approved SLA. A dedicated reproducible performance plan and consent for bounded testing are required before optimizing or changing architecture.

### Actual Phase 9F checks and limitations

Finalized 2026-11-15; retained the completed pre-interruption checks from this same task. New evidence root **`%TEMP%/migramind-phase9f-fo5rf1e3`**, also recorded by `%TEMP%/migramind-phase9f-root.txt`. Filtered backend/prototype source, private TEMP/TMP, reused isolated Python 3.13.12 dependencies read-only; explicit development/local, `DATABASE_URL=sqlite://`, idle false, dotenv/bytecode disabled and copied-source PYTHONPATH. Only newly created synthetic stores/counter fixtures and owned loopback IPC were used. No existing database/account/health/backup/export/secret/configuration/profile access or package installation.

| Check | Actual outcome |
| --- | --- |
| Unchanged 32 prototype cases + four temporary operational observations | **36 passed**, 54.200s unittest / 55.81s wall; 240s cap |
| Existing Phase 9A guard regressions | **31 passed**, 21.77s pytest / 26.24s wall; 120s cap |
| Test failures/retries | **None**; existing Starlette/httpx deprecation warning. Observations pass by establishing current limitations, not fixes. |
| Documentation/integrity | **79 local links / 32 source references**, **71 unchanged tested source/declaration files**; all previous report bodies/prototype files preserved; only two Phase 9F documentation edits; zero owned store directories remain; app/migrations/locks/configuration unchanged; whitespace passed |

Timing smoke: two fresh stores, starting with **0** or **1000 prefilled synthetic counter windows**, six sequential allowed reservations each. The 1000-window setup uses fixture-only synthetic counter rows authenticated with that fixture's owner key; it is not application provisioning or patient/demo account seeding. No keys, bodies or capabilities are logged. No sustained/production load or extrapolated throughput claim.

| Prefilled windows | Median of six | Maximum of six |
| --- | --- | --- |
| 0 | **50.346ms** | **67.365ms** |
| 1000 | **148.830ms** | **160.313ms** |

Temporary observations: replay exactly one synthetic authenticated request/guard transcript into the same active epoch; stop with one in-flight synthetic admission; fail a fence against one deliberately held synthetic writer lock then verify a later completed fence; twelve total sequential timing samples. No external attack, destructive filesystem operation, actual recovery/restore, schema change or architecture implementation.

Reproduction from the new filtered copy and restricted environment:

```text
<isolated-python> -B -m unittest discover -s prototypes/synthetic_auth_throttle -p "test*.py" -v
# test_operational_observations.py exists only in that task's temporary source.
<isolated-python> -B -m pytest -q -ra tests/test_auth_guard_order.py --basetemp <new-root>/guard-data -p no:cacheprovider
```

Use a previously nonexistent owned basetemp. Evidence: starting report/README baselines, unchanged tested source, temporary observation module, `prototype-review.log`, `guard-regressions.log`, `results.json`, `latency-smoke.json` and wrapper in TEMP. No full backend/frontend/browser/build/dependency audit, Linux, live PostgreSQL, 10000-row/performance-load campaign, physical suspension/reboot/power loss, real proxy or recovery was performed. Source-level filesystem/parent-death/restore risks remain distinguished from executed observations.

**Next step:** approve a recovery/admission-generation and primary-time/transaction acceptance contract for the future PostgreSQL-ready design, using synthetic fixtures only. That is smaller and safer than immediately integrating or adding takeover/reset logic to A. Further architecture changes, recovery implementation, migrations or services require separate approval. Existing NAT/valid-CSRF targeting/enrollment, storage/copy protection, recovery/retention, manual accessibility/device and research/clinical gates remain open. **NOT READY for application integration or public/real-health release.** No commits, pushes, PRs, merges or deployment.

## Phase 9E: approved monotonic owner authority and hardening (2026-11-12)

Verified `security/shared-auth-throttling` at PR #24 merge `c32cb28`. Preserved all earlier report bodies and original prototype source/tests. The prior Phase 9E stop below is **historical and superseded by explicit approval of the owner/epoch design**, not silently ignored. This implementation is entirely synthetic, with no auth-route, migration, flag, dependency or production change.

### Implemented files and preservation

[adapter.py](../prototypes/synthetic_auth_throttle/adapter.py) now exposes the owner-backed API implemented in [authority.py](../prototypes/synthetic_auth_throttle/authority.py); [test_adapter.py](../prototypes/synthetic_auth_throttle/test_adapter.py) contains 32 current acceptance cases. [README](../prototypes/synthetic_auth_throttle/README.md) documents safe execution, boundaries and recovery. The original UTC [legacy_adapter.py](../prototypes/synthetic_auth_throttle/legacy_adapter.py) is byte-identical to the starting adapter. [legacy_test_adapter.py](../prototypes/synthetic_auth_throttle/legacy_test_adapter.py) preserves the starting 24 tests with only its import redirected to that archive. Legacy code is never an admission fallback; the current client reuses only its pure synthetic identifier normalization helper. Legacy filenames are outside the current `test_adapter.py` discovery pattern.

The three original deterministic red regression tests are retained **unchanged** at `%TEMP%/migramind-phase9e-s_4ge23d/source/prototypes/synthetic_auth_throttle/test_hardening_regressions.py` and copied byte-for-byte to the new evidence root as `phase9e-original-red-regressions.py`. Their legacy worker-clock API is not the new API: new acceptance cases exercise the same defects with owner time. Do not claim those unchanged historical tests now pass against a different constructor/API. Starting source/report baselines remain available for exact preservation checks.

### Clock, ownership and proof of fencing

One spawned owner process holds the only elapsed-clock origin (`time.monotonic_ns()`), explicit ownership epoch and private integrity key. Workers never sample time to authorize reservations and cannot supply a timestamp. Toy guard callbacks stay worker-local and are challenged after each relevant writer lock. Configured IPC deadlines use local monotonic time only for failure/availability, never budget ageing.

The elapsed counter is integer milliseconds since that owner's origin. Wall-clock movement in either direction does not enter the calculation. No UTC inference, skew tolerance or arbitrary jump threshold. Decreasing/invalid authority time fails and seals the store, rather than clamping. Tests use an owner-only manual elapsed clock; positive manual advance represents actual elapsed test time, not a wall-clock update. Client capabilities cannot invoke this administrative operation. A deterministic unit test holds monotonic readings fixed while replacing wall-clock readings; an additional worker test changes wall readings while the owner's budget stays exhausted. No real OS clock was changed.

**Continuity is not inferred from epoch text:**

1. Exclusive first ownership obtains and holds a lifetime `BEGIN IMMEDIATE` writer reservation on a separate owned SQLite lock file. There is no expiring lease or takeover timer.
2. Claiming also commits a permanent NEW→ACTIVE transition and new epoch in the counter database. A second concurrent claimant loses the lock. After owner death releases it, any replacement still rejects the already-claimed state. Old counters are never resumed using a fresh origin/key/epoch, even by the surviving test controller.
3. Each cleanup/admission validates ACTIVE state, expected epoch, schema and authenticated snapshot **inside the counter file's `BEGIN IMMEDIATE` transaction**, then commits before releasing that writer lock. The lifetime ownership lock is retained until request handlers finish and the owner exits.
4. Explicit controller fencing commits SEALED state with a new fencing epoch under the same counter writer lock. A stale owner can remain alive but its next operation fails. The fence either waits for an earlier reservation to commit first, or commits first and prevents the reservation. **No admission after a completed fence is authorized by the old epoch.** A busy/failed fence attempt is not a completed fence; callers must not display success.

Six initial ownership/fencing feasibility tests passed before proceeding. Final tests include two synchronized competing owner processes (exactly one owner), active-owner claim refusal, stale epoch/capability rejection, still-running stale owner and pre-opened client after seal, in-flight commit versus fence ordering, owner crash with an open transaction, refusal to resume after process death, and late fresh worker exhaustion. These are protocol/SQLite functional evidence under the assumptions below, not a formal proof against hostile OS or disk rollback.

### Authority IPC, key lifecycle and failure behavior

The owner exposes a temporary **127.0.0.1-only** internal endpoint to owned synthetic workers, not an external/deployed service. Requests/replies/challenges use bounded JSON, no pickle request deserialization, 8192-byte frames, fresh call nonces, ordered frame numbers, epoch binding and **HMAC-SHA256** with standard-library `hmac`/`hashlib`. Authentication prevents an unsigned/reused endpoint or replayed old response from falsely reporting continuity. Capabilities are not sent as plaintext values; authenticated frames contain digests/metadata only. Eight active handlers maximum; no unbounded work queue; three-second connection/frame waits, no automatic request retry. Transport is authenticated, not encrypted; trusted capability-holding test workers and a trusted local host are explicit assumptions.

Separate random client/admin capabilities and a snapshot-integrity key exist only in the controller/owner/owned worker memory as appropriate. They are not written to SQLite or logs; handle repr redacts them. The private snapshot key does not go to reservation workers. No credentials, session cookies/tokens, health information or actual secrets are inputs. Stored documentation IP/example.test account identifiers are domain-separated SHA-256 pseudonyms, not anonymity/encryption. HMAC tags and provenance/epoch values are metadata, not clinical data or authentication sessions.

Owner crash/normal owner process restart/machine reboot/lost authority/unavailable endpoint/stale epoch **fail closed**. Worker restarts alone preserve state as long as the exact owner survives. No authority rebase, clock fallback or owner takeover exists. Endpoint reuse also fails authentication of a fresh nonce. Reboot was not physically performed; loss-of-owner tests and irreversible claim protocol cover the stated model. Suspend can conservatively slow ageing on platforms where monotonic time pauses; it never triggers wall-clock catch-up. Accurate trusted host monotonic timing, reliable local SQLite locking and a non-hostile controller/kernel are assumptions. VM snapshot rollback, malicious memory/key access, copied-file rollback and cross-host operation are not secured by this prototype.

### Independent cleanup and authenticated state/capacity

Dedicated counter schema is **prototype version 2**, created only in a brand-new temporary directory. Control now contains owner state/epoch and snapshot tag in addition to bounds/elapsed time/count. The second SQLite file is only a lifetime lock; no application schema exists in either file. No Alembic revision or upgrade of even an old synthetic store is attempted.

Each guarded reservation first verifies the entire bounded authenticated state, removes at most the configured expired batch and **commits maintenance independently**. Its subsequent admission transaction revalidates state/guards/time and atomically appends **both IP/account timestamps or neither**. A denial or injected later write/commit failure cannot roll back earlier cleanup. Active windows are never evicted. Exact window `(elapsed−900000,elapsed]`, 30/IP and 10/normalized account, shared login/register keys, constant denial retry 900 seconds remain. Live partial-IP semantics are untouched.

Limits: 10000 retained windows, 30/10 timestamps, serialized lists at most 1024 characters, at most 100 expired rows deleted per maintenance transaction; busy wait defaults to 250ms within 0–1000ms. Verification reconciles up to **cap+1 (10001) rows** and authenticates row contents, control metadata and schema SQL, before maintenance/admission; invariants are checked again before commit. This deliberately bounded full-state scan is a performance cost, not a 100-row total-work claim. No throughput/large-cap benchmark is asserted. No autonomous background scheduler; guarded operations and explicit bounded maintenance drive cleanup.

Missing/deleted active windows are detected even when triggers make the count superficially consistent. Negative/impossible/noninteger/missing control metadata, in-range count drift, altered list/expiry/limits, missing/modified schema objects and MAC mismatch fail without automatic repair or eviction. Well-formed expired state is recoverable by cleanup; untrusted expired state is not silently deleted. Original corrupt-count and denial-cleanup regressions now have current-API passing acceptance cases. Memory-only state authentication is not general forensic/tamper-proof storage or evidence of malicious-disk recovery.

Actual SQLITE_BUSY, injected SQLITE_LOCKED, capacity and transactional faults return safe unavailability, never a memory fallback/false admission. Faults after first write or before commit roll back both admission counters, while prior maintenance can remain committed. Authenticated response loss may leave a committed charge; no automatic refund or replay. There is no HTTP status mapping, real Origin/CSRF/session implementation, bootstrap/reauth integration or live health transaction in this experiment. Existing Phase 9A behavior is unchanged.

### Validation and exact results

Evidence root: `%TEMP%/migramind-phase9e-authority-48hemiqj`. Filtered source, owned temporary stores/processes/loopback endpoints, prior baselines and frozen three red tests only. Reused isolated Python **3.13.12** dependencies read-only. Backend child uses development/local, `DATABASE_URL=sqlite://`, idle false, dotenv/bytecode disabled, copied-source PYTHONPATH and private TEMP/TMP. No existing database/WAL/SHM/account/health/backup/export/secret/environment/browser-profile access, install, migration/provisioning or external request.

| Executed check | Exact result |
| --- | --- |
| Initial exclusive-owner/fencing feasibility | **6 passed**, 4.914s unittest / 5.30s wall; 180s cap |
| Initial hardened prototype suite | **31 passed**, 24.518s suite / 25.08s wall; 240s cap |
| Final hardened prototype, after schema-authentication test/check | **32 passed**, 24.256s suite / 24.65s wall; 240s cap; includes the earlier ownership tests |
| Relevant existing backend | **134 passed / 1 migration case deselected**, 33.20s pytest / 35.28s wall; 300s cap; all 31 Phase 9A cases included |
| Final documentation/integrity | **69 local links / 24 source references**, **71 tested source/declaration files matched**; prior report/README bodies, original adapter/test evidence and all three red tests preserved; eight intended files; zero owned synthetic-store directories left; app/migrations/locks/configuration unchanged; whitespace passed |

No executed test failure, timeout, skipped prototype case or retry-until-green. Added fresh-nonce authenticated IPC before the first full suite; subsequent review added authenticated schema checks and one permanent case, justifying one final prototype rerun. Backend source did not change afterward, so its passing suite was not repeated. An initial patch-format attempt was rejected before file mutation (duplicate target operations); corrected the editing method without affecting tests/data. Existing backend Starlette/httpx deprecation remains.

```text
# New filtered temporary repository root; no dependency installation.
<isolated-python> -B -m unittest discover -s prototypes/synthetic_auth_throttle -p test_adapter.py -v
# Copied backend, restricted environment above, new owned basetemp.
<isolated-python> -B -m pytest -q -ra tests/test_auth.py tests/test_auth_guard_order.py tests/test_security.py tests/test_logout_all.py tests/test_session_idle.py -k "not migration" --basetemp <new-root>/backend-data -p no:cacheprovider
```

Logs/results are outside Git: `fencing-first.*`, `prototype-first.log`, `prototype-final.*`, `backend.log`, `final-results.json`, starting source/report baselines and frozen red tests. Archived legacy tests are preservation evidence, not an additional current acceptance run. Full backend/frontend/browser/build/Linux/PostgreSQL/load/power-loss/physical-reboot checks were not run. No authentication or app migration/dependency/configuration change; idle remains disabled by default. No commit, push, PR, merge or deployment.

**Verdict: READY FOR SEPARATE INTEGRATION-DESIGN REVIEW under these synthetic assumptions, NOT for live integration.** Review fail-closed owner loss/no takeover, persistence/recovery/availability policy, global-scan/IPC/SQLite contention costs, platform suspend behavior and real guard/transaction handoff first. Same-host authority and ephemeral keys are not a hosted durability/recovery design. Live shared limiting, PostgreSQL/multi-host validation, resource/NAT/valid-CSRF targeting, enrollment/recovery/storage/retention/accessibility/research gates remain open; public/real-health release is still NO-GO. Further implementation requires separate approval.

## Phase 9E: reproductions complete; clock-policy approval required (2026-11-12)

Verified `security/shared-auth-throttling` at `c32cb28`, preserving all uncommitted Phase 9B/9C/9D reports and prototype work. **Stopped before hardening implementation under Phase 9E's explicit clock-policy gate.** No arbitrary threshold, new persistent time authority or silent change of restart semantics was chosen. Adapter and existing tests remain unchanged; only this report, release readiness and the prototype README record the blocker. No hardening fix or integration-readiness claim.

### Deterministic red regressions and current results

Created three **temporary regression tests** in a filtered copy, with only new synthetic stores. They assert the requested hardened behavior and all fail against the existing adapter:

1. Exhaust ten account slots, then inject a forward UTC step of exactly 900000ms without a real elapsed wait. Expected safe failure; current adapter admits instead. A stored UTC high-water cannot detect a forward step.
2. Create two expired windows plus two active exhausted windows. Deny a reservation; expected independently committed bounded expiry cleanup leaves two active rows. Current rollback leaves **four** rows, proving cleanup depends on acceptance.
3. In a fresh two-row-cap store, deliberately change control count from two to zero (in-range but inconsistent). Expected safe failure on allocating a new pair; adapter admits it. Only this owned temporary store is corrupted; no real/local application database is inspected.

| Phase 9E execution | Exact outcome |
| --- | --- |
| Three new hardening regressions against unchanged code | **3 expected failures**, 0.260s unittest / 0.56s wall; 120s cap; no errors/timeouts |
| Existing prototype suite | **24 passed**, 3.021s suite / 3.25s wall; 180s cap; includes independent connection/process final-slot races and BUSY/LOCKED/rollback checks |
| Relevant existing auth/guard/security/revocation/idle | **134 passed / 1 migration case deselected**, 27.15s pytest / 28.88s wall; 300s cap; includes all 31 Phase 9A guards |
| Documentation/integrity | **62 local links / 24 source references**, **68 unchanged tested source/declaration files**; all three prior documentation bodies preserved; only three Phase 9E documentation changes; adapter/tests/auth/migrations/locks/configuration unchanged; whitespace check passed |

The red failures are **unfixed**, not converted into passes or retried until green. Existing passes do not satisfy the requested hardening acceptance. No threshold, assertion, timeout or counter policy was changed. Existing Starlette/httpx deprecation remains.

### Why the clock gate is unresolved

The adapter persists UTC milliseconds and uses `max(current_utc, stored_high_water)`. It clamps rather than rejects backward time. Forward discontinuities can prematurely expire both counters **and cleanup records**. Sampling SQLite's wall clock instead of Python's still depends on the host wall clock and does not resolve this ambiguity. Exact 900-second timestamp arithmetic is not proof that 900 seconds actually elapsed.

Paired wall/monotonic observations can reveal discontinuities while a trusted observer remains alive, but sampling differences, clock adjustment and suspend behavior need an approved policy. Phase 9D's **2000ms threshold was a proposal only**; Phase 9E explicitly withholds arbitrary tolerance choices. A zero-difference comparison is not automatically safe: separate samples have scheduling/resolution differences and can cause false lockouts.

Persisting a monotonic number alone is not a valid reboot/epoch-continuity design. Worker restart on the same clock epoch differs from host/authority restart; an increased monotonic value after an unknown reboot does not prove continuity. With only persisted UTC state and a new UTC reading, genuine downtime and a forward jump can produce the same observations. A safe unrestricted restart policy therefore needs a new authority/epoch design, approved residual clock-trust assumptions or restrictive fail-closed reopening semantics. Those decisions have not been made.

### Alternatives requiring explicit approval

| Option | Clock behavior and restart contract | Tradeoff / recommendation |
| --- | --- | --- |
| **A: synthetic store-owner monotonic authority** | One owned, lifetime-scoped monotonic authority provides elapsed ticks to synthetic workers after their write reservation. Persist an explicit authority/epoch binding; reject backward ticks and missing/mismatched/unreachable authority. Worker restarts can retain counters while the same authority lives; authority loss/host restart cannot silently rebase or reopen the old store. | **Recommended next synthetic design.** No wall-clock skew threshold. Requires approval of new owner/epoch/IPC design and the intentionally narrower restart guarantee; no external service/install or live integration. Continuity/recovery and suspend semantics still need tests. This is a proposal, not implemented or proven. |
| B: UTC plus monotonic observation, approved tolerance and persistent quarantine | Detect agreed anomalies, latch shared failure state, fail closed; specify trusted recovery and explicit behavior when all observers restart. | Requires analysis/approval of tolerance and residual restart/host-clock trust. It cannot guarantee arbitrary offline-forward-jump detection from UTC alone. No particular threshold is approved here. |

Simply trusting larger UTC values, changing to SQLite `now`, resetting timestamps on worker restart, accepting the prior 2-second suggestion or silently losing persisted budgets does **not** meet the stated fail-closed clock requirement. No outside time service, OS setting, boot identity source or infrastructure was accessed/provisioned.

**Approval requested:** choose the synthetic owner/epoch design (A), or authorize a specific alternative clock/restart policy and its acceptance analysis. Until then, adapter hardening is stopped. Cleanup's eligibility depends on trusted time; do not implement independent destructive expiry around the known forward-jump gap. Capacity consistency can be hardened later, but no partial hardening is claimed after the explicit stop condition.

### Evidence, reproduction and remaining status

Evidence root `%TEMP%/migramind-phase9e-s_4ge23d`: filtered copied backend/prototype, three original report/README baselines, temporary `test_hardening_regressions.py`, `red-regressions.log`, `existing-prototype.log`, `backend.log`, `results.json` and TEMP wrapper. Reused isolated Python 3.13.12 dependencies read-only; no installation. Restricted development/local child environment with `DATABASE_URL=sqlite://`, idle false, dotenv/bytecode disabled, copied-source PYTHONPATH and private TEMP/TMP. Every prototype store is newly generated; controlled test corruption changes only its own temporary counter metadata. No credential/token/cookie/health value is written to prototype tables or printed.

```text
# Filtered temporary root; the first command intentionally demonstrates 3 failures.
<isolated-python> -B -m unittest discover -s prototypes/synthetic_auth_throttle -p test_hardening_regressions.py -v
<isolated-python> -B -m unittest discover -s prototypes/synthetic_auth_throttle -p test_adapter.py -v
# Copied backend, new owned basetemp only.
<isolated-python> -B -m pytest -q -ra tests/test_auth.py tests/test_auth_guard_order.py tests/test_security.py tests/test_logout_all.py tests/test_session_idle.py -k "not migration" --basetemp <new-root>/backend-data -p no:cacheprovider
```

Only the three documentation files change during Phase 9E; the temporary red tests are retained outside Git, so the repository's passing legacy suite is not silently altered. No new permanent regression/fix has been integrated. Full backend/frontend/browser/build/Linux/PostgreSQL, new clock authority, cleanup/count fixes and live integration are **not run or completed**. Existing databases/accounts/health/backups/exports/secrets/configuration were not accessed; no migration, dependency, production/OS setting, external request, commit, push, PR, merge or deployment. **NOT READY for a successful hardening/integration-design sign-off:** three findings remain open and clock design approval is the next gate. A separate discussion may review these alternatives, but must not be described as completed remediation.

## Phase 9D: integration design and policy review (2026-11-12)

Verified `security/shared-auth-throttling` at PR #24 merge `c32cb28`. Starting work was the two uncommitted Phase 9B/9C reports and three synthetic prototype files; all preserved. **This section is a recommendation, not policy activation or implementation approval.** Only this report and release readiness change in Phase 9D. Prototype, actual auth, migrations, settings and dependencies remain unchanged. Earlier sections are preserved historical evidence where recommendations differ.

### Decision matrix and exact compatibility comparison

| Topic | Live process-local implementation | Synthetic SQLite experiment | Recommended integration policy (requires approval) |
| --- | --- | --- | --- |
| Window | Floating-point process-monotonic seconds; `(now−900,now]` | Integer UTC ms; `(now−900000,now]`, clamped to committed high-water | Exact rolling 900000ms window; cutoff expires. Explicit ms precision and clock safeguards below; no fixed-window substitution. |
| Limits/actions | 30/IP, 10/account; shared login/register/logout-all/account deletion; bootstrap IP-only | 30/IP, 10/account, shared login/register only | Keep numbers and shared namespaces, including current reauthentication and IP-only bootstrap. No extra budget on ordinary reads/logout or collection/research policy change. |
| Identity | Raw ASGI client host in memory; SHA-256 of strip/lowercase email | Canonical documentation IP and example.test account, separately tagged SHA-256 | Reuse current email normalization; validate/canonicalize trusted ASGI peer IP under a reviewed policy. Domain-tag hashes, never raw identifiers in storage. Digest/canonicalization change is an explicit cutover choice. |
| Successful/failed credentials | Both charge before password work; duplicate registration charges too | Only reservations modeled; a committed reservation is not refunded later | Charge validly guarded submitted attempts regardless of later password/unique-insert outcome. No success reset or password-result-based refund. |
| IP-full rejection | No IP/account append | Neither append | Preserve. |
| Account-full rejection | **IP charged**, account unchanged | **Neither charged** | Recommend **atomic all-or-nothing** for enabled mode only, subject to explicit approval. Disabled mode keeps exact live behavior. |
| Guards | Actual session/Origin/CSRF before accounting; malformed body rejected first | Toy callback before storage and after lock | Preserve actual Phase 9A guards; authoritative same-transaction recheck after lock waits. Toy callback is not usable production security. |
| Concurrency/durability | One-key Python lock; instances/restarts independent | `BEGIN IMMEDIATE`, independent connections/processes share file | Short database-owned reservation; no Python-only coordination, Argon2 under lock or mixed-mode workers. |
| 429 | Generic detail and constant `Retry-After: 900` | Decision false with 900, no HTTP integration | Initially preserve exact generic 429/detail/900 header; overstatement of remaining wait remains documented. No account/budget disclosure. |
| Store failure | No separate shared store; ordinary DB errors already private | Safe exception, never an admission | Enabled mode fails closed with value-free 503; never 401/429 for unavailable storage or fallback to memory. |

Evidence: [live limiter/attempts](../backend/app/auth.py#L66), [guards and route order](../backend/app/auth.py#L183), [synthetic adapter](../prototypes/synthetic_auth_throttle/adapter.py) and [README](../prototypes/synthetic_auth_throttle/README.md). The prototype cannot handle arbitrary real account/IP inputs, auth-bootstrap/reauth operations, application session revalidation, schema readiness or rollout; it must not be imported into live routes as-is.

**Accounting recommendation:** all-or-nothing avoids spending a shared NAT/IP allowance on attempts already refused by an account ceiling and makes the atomic decision easier to reason about. It prevents a blocked-account retry from indirectly starving unrelated users of that IP budget. The cost is that repeated attempts against a full account become uncharged by these auth budgets; they still spend parsing/guard/database work. Neither policy prevents valid-CSRF targeted account lockout or distributed guessing. Keep independently reviewed ingress/body/concurrency limits as an activation gate; do not invent a new pre-guard account budget or claim this storage change closes abuse risk. Preserving the current partial charge is a viable lower-change alternative if the owner declines the new policy; that would require a different adapter/test branch, not silently treating Phase 9C as compatible. No live decision has changed here.

### Precise proposed clock policy

1. For a **single-host SQLite** adapter, use an injectable nonnegative integer UTC-ms sample (`time.time_ns() // 1000000`) **after obtaining the writer reservation**, not request-arrival/transaction-start time. SQLite `now` also uses host time; moving the expression into SQLite does not create an independent trusted clock. SQL date conversions can add precision/version differences. Prefer the explicit Python ms clock locally; existing prototype results do not validate all SQLite date functions/platforms.
2. Compare events with `stamp > effective_now−900000`; equality expires. Persist nondecreasing `effective_now=max(sampled_utc, committed_high_water)` on successful reservations and committed maintenance. Rollback must not change it. Denied requests append no events; the proposed clock-health metadata decision is separate from charging attempts.
3. Prototype clamp alone is insufficient: **observed** a 900000ms forward step reopened an exhausted window. Recommend startup validation plus a per-process UTC/monotonic paired baseline. A proposed anomaly threshold is **2000ms** divergence between elapsed UTC and elapsed monotonic, or UTC more than 2000ms behind persistent high-water. Small skew is clamped; large anomalies block new shared admissions with 503. Threshold is a proposal, needs platform/suspend tests and explicit approval. Do not reject a normal long idle interval merely because UTC exceeds old high-water by 900 seconds.
4. A detected anomaly should latch shared clock-health state under the same control lock, so a newly started worker cannot silently bypass another worker's detection. This would require approved control metadata and a reviewed owner recovery action; no latch/detector/recovery command exists today. Clock-health failure commits only that metadata, never budget charges, before returning unavailable. If metadata cannot commit, that operation still fails closed; durable cross-worker quarantine cannot then be guaranteed.
5. Independent same-host processes use the same OS clock plus durable high-water, not persisted monotonic readings. A fresh process cannot distinguish a legitimate downtime interval from a forward jump while every process was stopped. That residual requires trusted OS time and operational restart/clock evidence; no purely local timestamp trick proves it away. Suspend/resume behavior, false-positive availability and multiworker clock-health races are activation gates. Do not claim this matches live monotonic resistance without tests.
6. PostgreSQL hosting needs primary-database time sampled after locks and separately tested monotonic/clock-health policy; cross-host application clocks and read replicas must not decide admission. Backup restore/clock correction must never automatically clear windows or create a fresh allowance. Recovery requires trustworthy time, bounded quarantine and owner review.

Clock tests: 899999/900000/900001ms, partial ageing, repeated timestamps, mild/backward/large-forward skew, time advanced while waiting for a lock, independent processes, process restart after downtime, suspend/resume, clock-health commit/rollback and recovery. These are **future** tests; Phase 9D observed the unchanged prototype, not a completed clock solution.

### Capacity, cleanup and corruption policy

Recommend retaining prototype **10000 retained rows**, **30/10 timestamps**, **1024-character serialized lists**, **100-row cleanup batches**, default **250ms busy timeout** with at most **1000ms configured wait** as provisional local bounds. These are not production load measurements or a total request deadline: JSON processing, scheduling, filesystem IO and commit may exceed busy wait. No infinite retry or unbounded request/cleanup loop. A future end-to-end deadline must not interrupt a transaction and then falsely refund a potentially committed reservation.

Never evict active keys. Count namespaces consistently, allocate both required rows in the same transaction and refuse new required allocation with generic 503 at capacity. Existing valid keys may proceed if no allocation is needed. Expired retained rows are capacity overhead until physically deleted; expired timestamps are never eligible even if maintenance lags. Unknown namespace/key/array/version/expiry formats must fail closed, not reset to empty.

**Observed maintenance gap:** the prototype's denied reservation rolls back its otherwise successful deletion of unrelated expired rows. Cleanup therefore cannot depend on accepted requests. Recommend independent, bounded, committed maintenance in the future application lifecycle: proposed one batch of at most 100 rows per five seconds, a transactionally coordinated lease so workers do not multiply maintenance work, no extra external service. An uncontented 10000-row expired backlog would need up to 100 batches; that is not a measured cleanup SLA. Health/lag/capacity alarms and real SQLite contention tests must establish a target (proposed cleanup within ten minutes of expiry while healthy). Busy cycles skip work and report aggregate lag; never block user requests doing a whole-table purge. This lifecycle/lease is not implemented or approved by this review.

**Observed count-integrity gap:** in a new synthetic store capped at two rows, intentionally changing control `key_count` from two to zero (still within SQL range checks) allowed a second pair; actual table had four rows while metadata said two. This required direct store modification; no remote exploit or ordinary-transaction drift was shown. Current JSON/marker checks do not verify row-count consistency. Treat as a **Medium pre-integration corruption/resource assurance gap**, not a reason to alter the prototype during design review.

Recommend bounded reconciliation under the writer reservation at startup, before **new-key allocation**, and in maintenance: enumerate/count at most cap+1 keys, compare with control, reject mismatch/overflow with safe 503 and an owner-visible value-free event. No automatic repair, eviction or resetting budgets. This adds bounded worst-case scanning on allocation (up to 10001 rows), unlike the prior no-scan ambition; low-volume suitability and latency must be measured. Existing-key requests need no full scan; triggers maintain counts in normal operation. Direct malicious file changes remain a host-compromise threat, not solvable by metadata validation alone. Corrupt counters, expiry/list invariants and trigger/schema integrity need separate startup validation.

Account identifiers are attacker-controlled even with valid CSRF. Never allocate counters only for existing users, accept a client hash as authority or change email canonicalization to special-provider rules. IP parsing must use trusted ASGI identity; preserve a documented bounded `unknown` sentinel if no peer exists rather than silently introducing a bypass. Canonical IPv6 consolidation changes raw-host key equivalence and needs tests. Hashes remain dictionary-guessable pseudonyms; no HMAC secret is introduced. Restrict SQL/log/export access, retain only window metadata plus bounded cleanup lag and document remaining SQLite pages/backups. HMAC/retention/key rotation are separate approval topics, not claims of anonymity or cryptographic integrity.

### Failure decisions, errors and recovery

| Situation | Recommended enabled-mode behavior |
| --- | --- |
| Known budget full | Generic existing 429 + `Retry-After: 900`; neither key charged. No user-existence detail or password work. |
| Guard/schema-body rejection | Keep existing 403/401/422 ordering/details; no shared or memory charge. If initial guards pass but session expires/revokes during lock wait, recheck fails without a charge. |
| BUSY/LOCKED or unavailable DB | Bound wait; safe generic 503 such as `Authentication is temporarily unavailable. Try again later.`; no fallback/admission or automatic non-idempotent retry. Actual BUSY and injected LOCKED have been tested only at prototype level. |
| Malformed state/count drift/capacity/clock health | Same generic 503, distinguish only through approved aggregate operational categories. Do not convert to wrong-password/unknown-user errors or clear keys. |
| Exception before reservation commit | Roll back both keys and maintenance atomically; no admission. |
| Reservation committed, later wrong password/duplicate or auth transaction rollback | Retain both charges. Reservation success does not imply authentication success. |
| Ambiguous commit/response loss | No false success, no assumed refund or automatic retry. A lost response may retain a charge. Future request deduplication needs separate replay/privacy design. |

Fail-open improves availability but explicitly forfeits shared abuse protection and can be induced by an attacker who causes store failure. Recommend fail-closed **only for actions already reserving**: login/register/new anonymous bootstrap/password reauthentication. Existing valid-session bootstrap, protected reads and ordinary current-session logout must not acquire a new throttle-store dependency. They still depend on their normal session DB; same-file lock contention may affect them anyway. Global logout's throttled reauthentication can be unavailable during an incident; retain that known limitation until a separately approved incident-response policy is designed. No invisible exception or weakened password confirmation.

Logging: safe action/result category, bounded coarse timing, busy/capacity/clock-health metrics; never raw email/IP, key digests in public logs, bodies, password/hash, token/cookie/CSRF, health fields, SQL parameters or exception strings. Monitoring distinguishes policy exhaustion from unavailability without exposing which account exists. Recover by draining admissions, checking owned schema/storage/time through an approved operator procedure, then controlled resumption; do not copy/read a real database under this task, restore old user/session/password snapshots, reset a corrupt counter to zero or fail over workers to memory. A stale restored throttle snapshot loses recent admissions; use a reviewed full-window quarantine from trustworthy recovery time or explicitly accepted supervised reset. Corruption/clock signals are operational gates, not implemented commands.

### Narrow future integration contract

Propose an internal `reserve_auth_attempt(context, guard_in_transaction, clock) -> Allowed | Limited(retry_after=900) | Unavailable` boundary. Inputs are server-derived normalized account (optional for bootstrap), trusted peer identity and an allowlisted action (`bootstrap`, `login`, `register`, `logout_all`, `delete_account`). The action does not split current shared IP/account namespaces. No request-supplied namespace, database path, timestamps, limits or counter contents. Store no credentials/health/CSRF; necessary guard request values stay ephemeral in memory. Return no health/user row or token.

Integration sequence, **not route code**:

1. Keep existing middleware, body/dependency checks, demo restrictions and actual Phase 9A guards before any accounting. Plain invalid requests must not touch either limiter. Valid existing bootstrap remains uncharged.
2. Select exactly one authoritative auth backend for the process cohort. In disabled mode call the existing `attempts()` unchanged; do not use all-or-nothing policy or write shadow counters. In enabled mode never call the memory auth limiter as a fallback or double charge. Keep collection/research consumers on their existing behavior through an explicit auth-specific interface.
3. End only a preliminary read-only ORM auth transaction before `BEGIN IMMEDIATE`; never roll back pending health/session writes. Carry immutable binding identifiers, not live ORM entities into another connection. Reserve in a separate short transaction using the same database and fresh authoritative session view.
4. `guard_in_transaction` reuses real session expiry, CSRF/Origin and account authorization logic on that transaction/connection **after locks/waits**. It must not open an independent stale read transaction or substitute the prototype boolean callback. Recheck cookie/session binding and current account; fail with existing guards before counter writes. Lock order/session revocation races require synthetic same-file tests before code integration.
5. After confirmed reservation commit, run existing password/user/session issuance flow. Reload needed rows safely, preserve cookie rotation, fixed absolute/idle expiry behavior, demo write boundary and global/current logout semantics. A later revocation can still race an already-authorized request, as today; shared throttling is not a revocation redesign. No health data/model API change.

### Additive migration and disabled-by-default rollout

An approved application implementation **would need** dedicated additive throttle tables/control metadata/indexes/triggers (including reviewed clock-health/maintenance fields); no suitable application counter table exists. Prototype initialization is not an Alembic migration and must not run in application startup. Never reuse `login_sessions`, demo markers or health tables as a throttle ledger. No migration is created here.

Follow [Alembic conventions](../backend/alembic/env.py) and current [010 revision](../backend/alembic/versions/010_session_activity.py) only after review. Use the next available revision after current head (number not reserved here). Fresh install creates empty windows and fixed control metadata; upgrade adds only those objects, with no health/session rewrite/backfill, secrets or data relocation. Test preservation, indexes/checks, trigger counts, idempotent `upgrade head` and startup mismatch on synthetic old databases. Do not invoke real upgrade/provisioning.

Proposed flag name **`AUTH_SHARED_THROTTLING_ENABLED=false`**, strict `true`/`false`, local-only true initially; invalid value or true on production/synthetic-demo/unsupported dialect fails startup, not silent fallback. This flag **does not exist today**. Disabled-mode behavior uses current memory accounting exactly; it does not read/write throttle tables or initialize them. Enabled mode requires matching schema/policy version and fail-closed state validation. New release readiness likely advances [SCHEMA_REVISION](../backend/app/deployment.py#L7) to the new migration even when behavior is disabled, following current exact-head checks. Thus **off does not necessarily avoid the schema-adoption prerequisite**: test/document it, do not weaken readiness to hide a missing migration. Stage reviewed synthetic migration before deploying such a version. No automatic migration, existing-database validation or new flag in this task.

All auth-budget consumers must change backend together. No live per-request toggle, mixed memory/shared workers, silent feature activation, or different policy versions writing the same keys. Quiesce new auth, upgrade through an approved owner procedure, validate synthetic-style acceptance, deploy off, then make a separately approved coherent local activation. Old memory history cannot be imported reliably; explicitly accept a supervised reset or wait a full 900s from draining the final old request under trustworthy time before new admissions. Do not claim continuous protection across an uncoordinated cutover. Enabling idle timeout is unrelated and remains forbidden.

Rollback: drain new auth and coordinate workers before disabling shared mode; off restores old **partial-IP** memory semantics and loses shared durability. Retain additive tables as forward-compatible metadata; do not destructively downgrade/drop them or restore sessions/health/password data. Before re-enabling, validate schema/clock/expiry and counter age; no empty-table reset to bypass protection. Old-code deployment, exact schema-readiness checks and retention need a separately tested rollback compatibility plan. Production/network filesystem/multi-host SQLite are not approved; PostgreSQL needs a distinct adapter, primary time, absent-key/row-lock ordering, deadlock/capacity/failover/restart tests and hosted privacy/operations review.

### Acceptance gates and smallest next step

| Gate | Synthetic acceptance before adopting any integration |
| --- | --- |
| Accounting modes | Disabled preserves all old expectations including partial IP charge; enabled has all-or-nothing outcomes; 30/10/900, shared actions, success/wrong/unknown/duplicate and 429 detail/header unchanged otherwise. |
| Guards/session safety | Existing 31 Phase 9A cases plus both modes, expired/revoked/mismatched session during lock wait, missing auth, actual CSRF/Origin, malformed bodies/dependency failure, cookie/session rotation, ordinary/global logout and protected content behavior. No rejected request charges either backend. |
| Concurrency/persistence | Independent file-backed engines and processes, final IP/account slots, two absent keys/capacity slot, partial-write/commit rollback, subsequent fresh process, no Argon2 while locked and no automatic ambiguous-commit replay. |
| Clock | Exact cutoffs, sub-ms quantization, UTC/monotonic skew, high-water, forward/backward jumps, restarts/downtime, shared quarantine state, lock-wait sampling and suspended devices; no silently cleared windows. |
| Resource/integrity | Maximum rows/list sizes, active-key preservation, expired-key reclaim, independently committed maintenance on all-denied traffic, corrupt in-range count detection/oversize state, bounded reconciliation/lease races and cleanup contention with synthetic diary/session writes. |
| Failure/availability | Actual BUSY, injected LOCKED/disk/commit faults, generic 503/no raw values, no memory fallback, guards/known-limit distinctions, current logout/read paths without extra throttle dependency, security-reauth outage explicitly documented. |
| Migration/flag/rollback | Synthetic fresh/010→next upgrade and no health/session changes, flag off parity, missing schema strict readiness, unsupported true refusal, coherent cutover, no mixed modes, reviewed disable/re-enable/old-code schema compatibility. |
| Isolation/privacy | Two synthetic accounts and shared/different IPs, no key/health/token export/logging, normalization/IPv6/unknown-peer/proxy contracts, no user-existence-dependent allocation; durable targeting/NAT remains a disclosed policy risk. |

**Smallest safe implementation proposal:** separately approve a synthetic-only hardening increment for count reconciliation, independent bounded maintenance and clock anomaly tests/policy in the prototype. Keep routes/flags/migrations untouched. Approve the all-or-nothing integration policy and resource/time thresholds explicitly before requesting an application adapter or additive migration. Current prototype alone is **NOT READY for live integration**. No Critical/High authentication bypass was demonstrated; clock/count/maintenance gaps are Medium pre-integration assurance/resource issues with the prerequisites stated above. Public/real-health release and prior storage/recovery/privacy/accessibility/hosted/research gates remain NO-GO.

### Actual Phase 9D checks

New temporary root `%TEMP%/migramind-phase9d-8rg_ncs4`, filtered backend/prototype source, private TEMP/TMP, synthetic fixture databases and read-only reuse of isolated Python 3.13.12 dependencies. Saved both starting report bodies and copied the three prototype files unchanged. Explicit development/local, `DATABASE_URL=sqlite://`, idle false, dotenv/bytecode disabled, copied-source PYTHONPATH and restricted OS environment; no actual configuration, SQLite/WAL/health/account/backup/export/secret/profile access, migration, provisioning, server or external request.

| Check | Exact outcome |
| --- | --- |
| Unchanged 24 prototype cases + five temporary review observations | **29 passed**, 3.851s unittest / 4.32s wall; 180s process cap |
| Existing Phase 9A guard regressions | **31 passed**, 6.70s pytest / 8.49s wall; 120s cap |
| Documentation/integrity | **60 local links / 24 source references**, **69 unchanged tested source/declaration files**; both prior report bodies and all three prototype files preserved; only two Phase 9D documentation edits; auth/migrations/locks/configuration and guard order unchanged; whitespace check passed |
| Failures/retries | **None**; existing Starlette/httpx deprecation warning |

The five temporary observations confirm large-forward-jump allowance reset, rollback of unrelated cleanup on denial, stable canonical IPv6/normalized-account digests, no refund after a simulated later auth failure, and the explicitly injected count-drift capacity gap. These passing observations establish current limitations, **not passing fixes**. The later-auth-failure observation is a toy control-flow check, not an integrated application transaction. Corruption edits only a newly generated temporary store, never an existing database.

```text
# New filtered repository root; temporary test_review_observations.py is not committed.
<isolated-python> -B -m unittest discover -s prototypes/synthetic_auth_throttle -p "test*.py" -v
# Copied backend, explicit environment above, new owned basetemp only.
<isolated-python> -B -m pytest -q -ra tests/test_auth_guard_order.py --basetemp <new-root>/guard-data -p no:cacheprovider
```

Evidence outside Git: starting report baselines, unchanged copied prototype/backend source, temporary observation module, `prototype-review.log`, `guard-regressions.log`, `results.json` and the TEMP wrapper. Full backend/frontend/browser/build, Linux, live PostgreSQL, load/latency, real proxy, schema migration, clock-health solution and application integration were not run. Historical Phase 9C results remain historical. No policy, adapter/test/README, auth/session code, migration, flag, dependency/configuration, commit, push, PR, merge or deployment change in Phase 9D.

## Phase 9C: approved synthetic SQLite prototype (2026-11-12)

Verified `security/shared-auth-throttling` at merged PR #24, with only the two expected uncommitted Phase 9B reports before prototype work. Preserved both report bodies. Added only [synthetic adapter](../prototypes/synthetic_auth_throttle/adapter.py), [24 focused tests](../prototypes/synthetic_auth_throttle/test_adapter.py) and [safe-run README](../prototypes/synthetic_auth_throttle/README.md), separate from application code/migrations. **No live auth integration or current policy change.** The earlier design below remains historical where this approved prototype deviates.

### Actual schema, semantics and deviations

- `SyntheticDatabase()` exclusively creates its own temporary directory/file; no database path, environment URL, existing-file initialization or app import. Handles are shared only with owned test processes. Documentation-only IPv4/IPv6 and synthetic `example.test` accounts are accepted; passwords/tokens/health fields are not inputs.
- Dedicated `prototype_control` stores schema version 1, a synthetic marker, last committed clock high-water mark, row count/cap and cleanup batch. `prototype_windows` stores fixed IP/account namespaces, domain-separated SHA-256 digests, bounded timestamp JSON and expiry. Composite primary key, expiry index, insert/delete count triggers and SQL size/count checks enforce normal-operation bounds. No Alembic migration or application table.
- Retain **30/IP and 10/strip-lowercase account per 900000ms**, with login/register sharing keys and exact `(now − 900000, now]` eligibility. **Approved deviation from Phase 9B/live semantics:** either-limit denial rolls back the whole reservation, so neither key is charged. The live account-denial path still charges IP. This experiment is not a compatible drop-in replacement; live adoption needs a separate accounting decision.
- Every operation uses its own SQLite connection, FULL synchronous rollback-journal behavior and `BEGIN IMMEDIATE` **before counter reads/clock sampling**. Both accepted appends and high-water update commit together. No Python mutex. Password work and unrelated application transactions do not exist in this prototype.
- A required toy guard callback must return exactly true before storage and after acquiring the writer reservation. Rejection does not charge. This is isolated ordering-contract evidence, **not a new implementation of CSRF/Origin/session security**. The real guards and routes remain byte-for-byte unchanged and their 31 tests pass.
- UTC integer clock is injectable; persistent high-water clamp prevents backward movement. Large forward jumps and future high-water lockout remain limitations; no cross-host clock/clock-jump detector. Millisecond precision and domain-separated digest encoding are explicit prototype choices rather than live-key compatibility claims.

### Concurrency, failures, bounds and privacy

Two independent four-process races prefill all but one **account** or **IP** slot: exactly **one admitted, three denied** in each. Independent connections/adapters and four synchronized threads also serialize correctly. A later fresh process after the contenders exit observes durable exhaustion. This demonstrates normal process restart/reopening persistence on the same new synthetic file, not power-loss/crash recovery or real service restart. An in-transaction probe confirms a second connection's `BEGIN IMMEDIATE` receives actual SQLITE_BUSY while the first holds the writer reservation. No sleep-based race assertions or load test.

Either limit denial rolls back all staged maintenance and counters. Injected failure after the first write or before commit also leaves both keys/control unchanged. Default busy timeout **250ms**, bounded configuration **0–1000ms**; contention test uses zero wait deterministically. Actual BUSY and injected SQLITE_LOCKED map to `StorageBusy`, a safe `StorageUnavailable` subtype. Corrupt requested JSON, wrong marker, invalid clock, missing storage and capacity/fault errors fail closed; no memory fallback, automatic retry or false admission. Missing store is opened `mode=rw` and is not recreated. Ambiguous failure after an actual commit could still retain a charge; no transport idempotency guarantee.

Defaults: **10000 retained key rows**, up to **30/10 timestamps**, JSON at most **1024 characters/row**, at most **100 expired rows deleted per operation** using expiry index. Trigger-maintained row count and capacity check share the write transaction. No active-key eviction or whole-table cleanup loop. Tests with smaller bounds prove capacity rejection changes neither key, existing pairs continue, expired rows reclaim capacity and active counters remain exact. Retained expired rows can require multiple explicit bounded cleanup calls; capacity rejection rolls back its partial cleanup rather than doing unbounded work. No autonomous maintenance scheduler, file shrink/secure erase or disk-growth/latency benchmark.

Raw IP/email are absent from persisted rows; canonical IP and strip/lowercase account are separately tagged SHA-256 digests. These are guessable pseudonyms, not anonymity/HMAC/encryption. No new key/secret lifecycle; synthetic marker only checks store provenance. SQLite checks and marker do not defend against hostile local file/process manipulation. Physical pages/backups and successful reservations remain metadata requiring future retention/storage protection. No real backups are created/read by this prototype.

Compared with Phase 9B, standard-library sqlite3 replaces the proposed application SQLAlchemy integration; there is no singleton migration, HTTP 503 mapping, bootstrap/reauth adapter, read-transaction handoff, scheduler or live-session revalidation. SQLite still serializes all writers. The separate synthetic store cannot measure interference with diary/session writes. PostgreSQL needs a separate implementation for row locks, absent-key insertion, primary clock, capacity and deadlocks/failover; neither PostgreSQL nor Redis is validated by these results.

### Exact validation and reproduction

New evidence root: `%TEMP%/migramind-phase9c-_ca1s_p0`. Filtered source copy, new fixture databases and private TEMP/TMP only; reused earlier isolated Python **3.13.12** dependencies read-only. Prototype itself uses only the standard library. Restricted backend environment explicitly sets development/local, `DATABASE_URL=sqlite://`, `SESSION_HOURS=12`, **`SESSION_IDLE_TIMEOUT_ENABLED=false`**, `PYTHON_DOTENV_DISABLED=1`, disabled bytecode and copied-source PYTHONPATH. No existing user data, SQLite/WAL/SHM, health/account/backup/export, secret, actual environment or browser profile was opened/copied.

| Phase 9C check | Exact result |
| --- | --- |
| Prototype unittest suite | **24 passed**, 5.426s suite / 6.11s wall; 180s process cap |
| Existing auth/guard/security/revocation/idle | **134 passed / 1 migration case deselected**, 42.00s pytest / 44.49s wall; 300s cap; all 31 Phase 9A regressions included |
| Documentation/integrity | **52 local links / 21 source references**, **68 tested source/declaration files matched**; both original Phase 9B report bodies preserved; exactly five intended files; app/migrations/locks/configuration unchanged; whitespace check passed |
| Failures/retries | No executed test failure, timeout or flaky rerun. Earlier validation launch was rejected before process creation because automatic approval review timed out; one authorized retry started the completed checks. No security-policy rejection or unsafe-action conclusion is inferred from that timeout. |

From a filtered temporary copy under the explicit environment above:

```text
# Copied repository root; standard library only, no installation.
<python-3.13> -B -m unittest discover -s prototypes/synthetic_auth_throttle -p test_adapter.py -v
# Copied backend; use a new owned basetemp directory every time.
<isolated-python> -B -m pytest -q -ra tests/test_auth.py tests/test_auth_guard_order.py tests/test_security.py tests/test_logout_all.py tests/test_session_idle.py -k "not migration" --basetemp <new-root>/backend-data -p no:cacheprovider
```

Process contenders use spawn, bounded queue/barrier/join waits and finally cleanup of owned children only. Runtime verified **Python 3.13.12 / SQLite 3.51.2**. Read the prototype README before use; never supply an existing database. Evidence outside Git: initial Phase 9B document baselines, filtered tested source, `prototype.log`, `backend.log`, `results.json`, `integrity.json` and the TEMP test wrapper. Existing Starlette/httpx deprecation remains. No migration/provisioning/server/external request, Redis/dependency/configuration change or real-data operation. No frontend/browser/build/Linux/PostgreSQL/performance/power-loss validation in this phase; no product/UI change warrants a new claim for those checks.

**Next step requires approval:** review the all-or-nothing accounting deviation, failure/clock/capacity/maintenance policies and synthetic results before any migration or route integration design. Continue isolated transaction/guard handoff tests first; no implicit permission to connect this adapter to live authentication. Account targeting/NAT, enrollment privacy, persistent rollout/recovery, storage, manual accessibility, hosted/research gates remain open. Public/real-health release is NO-GO; live shared throttling is still unimplemented. No commit, push, PR, merge or deployment.

## Historical Phase 9B audit/design — before the approved synthetic experiment

Assessment: **2026-11-12, Asia/Calcutta**. Verified clean `security/shared-auth-throttling`, identical to local `main` at **`c32cb28b019aae293bcb9d530ff17506db16115e`**, merged PR #24 (`1375f8a` guard-ordering implementation). Login/register guards precede accounting. No remote fetch/CI status claim. **Design only: no shared limiter, schema, configuration, service or dependency is implemented.**

## Decision

Recommend a separately approved, **SQLite-backed exact sliding-window reservation** using the existing local database/SQLAlchemy infrastructure, dedicated additive throttle tables and a short transaction. This is for a low-volume local installation on one host with a local filesystem, not a general hosted architecture. There is **no existing counter table** to reuse; "existing SQLite-backed" means reuse of the database infrastructure, not a claim that counters are already durable. Any new migration requires explicit approval and synthetic validation first.

Preserve 30/IP and 10/normalized account per 900 seconds and Phase 9A's guards. Do not quietly combine storage work with different thresholds, enrollment policy or account/IP-pair semantics. A durable account ceiling makes valid-CSRF targeting survive restarts and span workers; **durability alone does not close the abuse finding**. Account-target denial and NAT fairness require a separate policy decision before exposure.

For future PostgreSQL hosting, use a PostgreSQL-specific transactional implementation and database-authoritative time with tested row locks, absent-row creation, capacity handling and failure behavior. Do not share SQLite over a network filesystem or assume SQLite locking proves PostgreSQL correctness. Redis is an alternative at a future operational scale, not the smallest local solution.

## Current implementation and evidence

Reviewed [Phase 9/9A evidence](AUTH_ABUSE_PROTECTION_PLAN.md), [security/privacy audit](SECURITY_PRIVACY_AUDIT.md) and [release gates](RELEASE_READINESS.md). Historical findings are qualified by the merged guard fix, not overwritten.

| Property | Confirmed implementation |
| --- | --- |
| Storage/ownership | [Limiter](../backend/app/auth.py#L66): `defaultdict(deque)` and `threading.Lock`; each [Authentication instance](../backend/app/auth.py#L83) creates its own limiter. No persistent/shared counter state. |
| Keys/thresholds | [attempts](../backend/app/auth.py#L144): IP key `('ip', request.client.host or 'unknown')`, **30**, then account key `('account', sha256(normalized_email))`, **10**; common **900-second** sliding windows. Email stripped/lowercased by [Credentials](../backend/app/auth.py#L33). |
| Shared actions | Login, registration, password-confirmed global logout and account deletion use the same IP/account namespaces. Success, wrong password and duplicate registration all charge. Anonymous bootstrap uses IP only; valid bootstrap does not charge. Collection/research keys are distinct but use the same Limiter object. |
| Guard order | [register/login](../backend/app/auth.py#L183): mode restrictions, then existing session/Origin/CSRF, **then** `attempts()`, before password work. FastAPI malformed JSON/schema rejection happens before the handler. Protected reauthentication dependencies validate authentication/CSRF first. |
| Locking | A lock spans cleanup, count and append for **one** key. IP and account checks acquire/release it separately; not an atomic multi-key reservation. One instance cannot oversubscribe one key at a fixed clock, but independent instances can each admit to their own limit. |
| Partial accounting | If IP is full, account is untouched. If IP passes and account is full, IP remains charged and account is not appended. Password/database failure does not refund memory counters. |
| Window/cleanup | Process-monotonic time; remove events **<= now − 900**, keep events in `(now − 900, now]`. Every check scans every key, deletes expired entries/empty keys. No timer or maximum live-key count. Inactive expired keys remain in memory until another check. |
| Errors | Generic 429 `Too many attempts. Try again later.`, constant `Retry-After: 900`. It can overstate actual remaining time. Guards return their existing 403 even when counters are full. Wrong known/unknown login remains generic 401. |
| Other storage | [session model](../backend/app/main.py#L41) persists cookie digests, CSRF, absolute expiry/activity; it is **not** a throttle ledger. Session revocation can survive restart while attempt counters do not. |

The reviewed [launcher](../backend/app/serve.py#L29) is one-worker loopback, trusts forwarding only from `127.0.0.1` in production. The [nginx template](../deploy/nginx-demo.conf.example#L27) overwrites X-Forwarded-For with its peer address. These reduce some topology risks, but do not prove actual host/proxy settings. No real configuration/secret file was read. Do not trust arbitrary X-Forwarded-For or `*` to repair IP aggregation. Multiple legitimate users behind NAT still share a real IP; another upstream proxy can aggregate them too.

## Findings and priorities

| Finding | Severity, prerequisites and evidence | Gate |
| --- | --- | --- |
| ST-01: independent workers/restarts reset or multiply allowances | **Medium**, reachable auth service using multiple processes/restarts. Independent limiter instances each admitted their own remaining slot; fresh Authentication instance accepted the same synthetic session/account after the first was throttled. Two fresh child processes each began empty. | Refines A9-02 / S7-04 / SP4-04; shared/persistent protection unimplemented, public-hosting blocker. |
| ST-02: distributed targeted-account and shared-IP denial remain | **Medium**, candidate identifier and valid anonymous guards, or shared-IP traffic. Same global account/IP keys across actions; strict durable storage would preserve/amplify this limitation rather than cure it. | Explicit policy/NAT/incident-response decision before public or real-user exposure. No real attack performed. |
| ST-03: unbounded cardinality/cleanup and storage-failure policy absent | **Medium**, reachable many identifiers/IPs or future shared-store failure. Current map has no capacity bound and scans all keys; there is no shared-store outage policy to test today. | Resource/availability gate. No memory/CPU exhaustion or new store outage was attempted. |

Phase 9A remains addressed: invalid Origin/CSRF/session requests are uncharged. Registration new/duplicate distinction and missing recovery remain existing open findings, not newly discovered reset-token defects. No new Critical/High finding, password bypass or health-record disclosure was demonstrated.

## Alternatives

These are engineering designs based on reviewed code and normal transaction primitives, **not benchmarked/provisioned candidates**. No external service/documentation fetch was performed under the no-external-requests boundary.

| Option | Atomicity/concurrency | Durability/recovery | Cost, bounds, latency and migration |
| --- | --- | --- | --- |
| Existing local SQLite infrastructure + dedicated tables | `BEGIN IMMEDIATE` before reads reserves the single writer; transaction performs guard recheck, both-key decision and committed reservation. Separate processes/engines must point to the same local file. Serial writes contend with diary/session writes; no claim of unlimited workers. | Committed counters survive normal process restart. Journal recovery handles transactions; restoring an old backup/resetting keys/file loses newer counters. Disk errors/locks need explicit fail-closed handling. | No new service/dependency; **new approved schema required**. Low operational complexity for one host. Strict key/row/transaction caps; no Argon2 while locked. No latency measurement. Network/shared/cloud-sync SQLite paths unsuitable for this design. |
| PostgreSQL-backed counters using existing supported SQLAlchemy/psycopg stack | Row locks or transactional conditional updates; lock ordering, `INSERT ... ON CONFLICT` for absent rows, capacity coordination and bounded deadlock handling must be designed/tested. Count-then-insert without locks is unsafe at READ COMMITTED. | Committed primary state survives app restart; DB failover/restore can lose reservations according to actual replication/RPO. Read replicas/caches cannot authorize. | Approved equivalent schema, grants/indexes/cleanup/connection budgets and DB-clock tests required. Adds DB round-trip/lock latency; suitable topology can scale beyond SQLite, not proven here. Existing driver availability is not deployment approval. |
| Redis-backed throttling | One atomic script/function should prune/check/charge all keys and preserve partial IP semantics; separate GET/INCR/EXPIRE calls race. Cluster keys need a compatible common slot or different approved design. | TTL is cleanup, not guaranteed durable security state. Restart/eviction/failover and persistence/replication choices can reset/lose budgets. No fail-open fallback. | New service/client dependency/secrets/TLS/ACL/monitoring/backup policy require approval. Additional network hop and memory/key caps, noeviction/capacity failure policy and script/runtime bounds. Excess operational complexity for this local prototype; not installed. |

Exact rolling windows need bounded event timestamps or an equivalent exact representation. A fixed 15-minute bucket can admit near twice the limit across bucket boundaries; token bucket/GCRA changes semantics. Neither is a silent compatible substitution for the existing 900-second sliding window.

## Recommended local design — proposal only

### Schema and privacy

Propose two **new additive** tables, names provisional:

- `auth_throttle_windows`: composite primary key `(namespace, key_digest)`, a bounded JSON array of admission timestamps in integer UTC milliseconds, and indexed `expires_at_ms` equal to last retained event + 900,000. Namespace is a fixed allowlist (IP/account); max array length 30 for IP and 10 for account. Exact representation, types, corruption checks and index names need implementation review. Empty rejected account keys are not created.
- `auth_throttle_control`: one fixed row holding schema/policy version, a global clock high-water mark and active-window-row count. This coordinates time/capacity without scanning all keys. The migration initializes only this synthetic-independent metadata, never user/session/health rows. It must not store passwords, tokens, health values or raw identifiers.

For a first compatible design, keep current SHA-256 normalized-account identity and store a domain-separated digest of the ASGI client identifier instead of raw IP. Hashing is **pseudonymization, not anonymity**; candidate email/IP dictionaries remain feasible. Bound access/retention and avoid exporting these rows through health/account APIs. No new HMAC secret is assumed. A keyed HMAC would better resist offline key guessing but requires separately approved key storage, rotation and cross-worker continuity; rotating a key without carrying active state resets budgets. No hardcoded or per-worker random key.

Namespaces must remain shared across login/register and existing auth reauthentication; do not accidentally put each endpoint in a new independent bucket. Bootstrap IP accounting needs the same durable IP namespace for compatibility. Do not replace collection/research throttling as an incidental change: inventory and explicitly separate the auth adapter from unrelated existing Limiter consumers. Unknown namespaces/types must fail safely, not create arbitrary tables/keys.

### Clock and boundary policy

Current `time.monotonic()` cannot be persisted across restarts or compared across hosts. Propose an injected aware-UTC millisecond clock for local SQLite, sampled **after acquiring the writer reservation**; within the same transaction use `effective_now = max(sampled_now, stored_control_high_water)`, persist the high-water mark and compare integer boundaries. One host supplies the local clock; a backward step must not prune newer events or move time backward. A large forward jump can prematurely expire events, and a future high-water mark can prolong lockout after correction. Define clock-jump detection/fail-closed operational handling and synthetic tests before adoption; never silently clear counters to repair time. This is a proposal, not an existing clock guarantee.

For hosted PostgreSQL, prefer database-primary time sampled **after locks are acquired**, with equivalent durable nondecreasing policy where required. A transaction-start timestamp sampled before a long wait can be stale. App-worker clocks are not a safe cross-host authority. Exact 900,000ms cutoff removes timestamps `<= effective_now − 900000`; cutoff timestamps expire, newer ones count. Millisecond quantization is an explicit implementation precision choice compared with current floating-point monotonic seconds and needs boundary tests/approval.

### Atomic reservation algorithm

The linearization point is **successful throttle-transaction commit**. Do not hold a writer/row lock during Argon2, user insertion, response generation or unrelated health writes.

1. Retain Phase 9A validation and guards before attempting reservations. End any preliminary **read-only** ORM transaction before obtaining a SQLite write reservation; otherwise readers can cause lock upgrade/deadlock failures. Carry only necessary in-memory session identifiers, not logs. Do not roll back unrelated writes.
2. In a fresh short transaction, SQLite uses `BEGIN IMMEDIATE` **before** reading throttle state. Revalidate applicable session/Origin/CSRF against authoritative state after waiting; if expired/revoked/invalid, roll back with the existing guard error and **no counter changes**. Account deletion/global logout dependency guards need the same careful treatment. This recheck and session locking must be tested with revocation; no accounting on a guard failure caused by a lock wait.
3. Lock/read control, sample/clamp time, perform bounded expiry cleanup, validate stored shapes/namespace/policy. Read/prune only involved IP/account windows. Strict caps apply before allocating rows. Do not treat corrupt state as an empty window.
4. If IP already has 30 live events, reject with generic 429 **without appending either key**. Valid metadata/pruning may commit but must not refund live events. If IP has capacity, stage its timestamp.
5. If the account already has 10 live events, **commit the staged IP charge only**, then return the same 429. This deliberately preserves today's partial-accounting rule. Otherwise stage the account timestamp; commit both atomically. An IP-only bootstrap reservation skips account handling.
6. Only after confirmed commit perform password hashing/verification and existing auth transaction. Wrong password, duplicate registration or later auth-write rollback **does not refund** a confirmed reservation. If a reservation commit is ambiguous or unavailable, do not run password work or claim success, and do not automatically retry a non-idempotent reservation. A lost response may charge a slot without a completed login; that is a bounded safety/availability tradeoff. True request-id deduplication would need its own privacy/replay design, not cookie/password-derived IDs.

Two SQLite workers cannot both observe the last slot before charging because only one owns the write reservation; the second reads the first's committed window after obtaining the lock. No reliance on Python locks for cross-process safety. An exception before commit rolls back **all staged changes**; account-limit denial is an intentional partial commit, not an exception accidentally rolling back the IP charge. Use an explicit decision result, then raise/return 429 after the required commit. Do not put reservations in a transaction that rolls back on ordinary login 401 or duplicate-register 400.

For PostgreSQL, the simplest reference path can lock the singleton control row plus involved rows for the whole short reservation, giving the same serial semantics but a known global bottleneck. A hosted scalable variant should lock involved key rows in deterministic order (including absent-row insertion/conflict handling), coordinate capacity allocation separately and use primary time; evaluate lock ordering with session revocation to avoid deadlocks. It requires PostgreSQL-specific contention tests and measured bounds before claiming hosted readiness. Redis's equivalent script must preserve the same decisions, key bounds and partial-IP charge.

### Failure behavior and resource bounds

Recommend **fail closed for new auth reservations**, with a generic value-free **503** on storage unavailability, lock timeout, malformed counter state or capacity saturation; 429 only for known exhausted budgets. Do not silently fall back to memory or admit unmetered attempts. A DB/store outage should not be presented as a wrong password or missing account. No password work/user/session issuance after failed reservation. Guard errors remain their original status, independent of account existence.

Do not introduce a throttle-store dependency on existing authenticated reads, current logout or guard rejection; these do not reserve today. Existing DB-dependent operations still require their normal database. New bootstrap, login/register and existing password reauthentication can become unavailable; a same-database outage already affects sessions but additional lock/capacity failures can newly block them. Fail-open improves availability but discards the security guarantee; a supervised local owner could choose it only as an explicit approved policy, never the release default or per-worker fallback. Global-revocation incident-response availability needs a separate policy review; no exemption/new budget silently added here.

Illustrative **proposed**, not configured, local bounds for initial synthetic evaluation: 10,000 window rows maximum, 30 timestamp elements/row maximum, cleanup at most 100 expired rows/reservation and 100/maintenance batch, and a 1-second total reservation lock/transaction deadline. Require measurements before accepting these numbers. Capacity allocation and cleanup/count maintenance must be serialized by control state so two workers cannot both allocate the last row. Do not evict active keys to make room; refuse new required allocation safely. Preserve existing-key handling under the documented capacity policy; registration of new synthetic identifiers must not crowd out established keys without an explicit availability decision.

Index expiry, delete bounded expired rows with matching count updates, prune a requested key lazily, and schedule bounded maintenance on a local approved lifecycle. No full-map/table scan under every lock, unbounded cleanup queue or per-key timers. Expired state becomes ineligible exactly at deadline even if physical cleanup waits. Physical deletion/SQLite free pages and backups are not secure erasure; idle maintenance, file-growth monitoring and copy-retention policy are still required. OS backups/snapshots of these tables carry pseudonymous metadata; restoring older state loses newer reservations and is not a security reset strategy.

Use short retention (900-second eligibility plus explicitly bounded maintenance lag), no raw body/email/IP/password/token/health logging, no counter values in user exports, no SQL parameter logging, and aggregate outcome/latency/capacity monitoring only. Stored array/key byte lengths and namespace validation must reject attacker-created oversized payloads. Per-IP limits reduce but cannot eliminate distributed high-cardinality growth; ingress body/concurrency/time limits remain necessary. Global capacity fail-closed behavior itself can be targeted for denial of service: disclose and test it, do not call it complete abuse prevention.

## Identity, NAT, registration and attack-policy decisions

- Preserve current normalized-email identity across all guarded submissions, including nonexistent addresses; do not allocate/look up counters only when a user exists, which introduces enumeration and bypass. Changing normalization can split or merge budgets; requires separate compatibility tests. CSRF-valid attackers can target the known global account ceiling; durable storage prolongs that consequence.
- IP-only blocking penalizes shared households, schools, VPNs and mobile NAT; account-only blocking permits targeted lockout. Account/IP-pair plus separately approved aggregate escalation is a possible future policy, **not** permission to remove distributed-guessing protection or change the 30/10 contract in the storage step.
- Use only validated server/ASGI peer identity after approved trusted-proxy processing. Do not accept client-supplied IP/email hashes as limiter keys or allow a new forwarded header to reset the namespace. Document unknown-peer behavior and IPv4/IPv6/canonicalization before rollout.
- Registration and login share keys today; separate namespaces would multiply attempts and require approval. Synthetic-demo registration remains forbidden. Hashing a new registration password still requires prior reservation. Duplicate/new response distinction cannot be fixed merely by generic wording while new registration immediately signs in.
- Existing valid sessions, ordinary logout and Phase 9A rejected requests must not be newly charged. Counters are not recovery identity proof, session invalidation, an account lock flag, clinical monitoring or an emergency service.

## Acceptance and synthetic test plan

All future implementation tests must use new temporary file-backed SQLite databases for real cross-engine/process visibility, synthetic identities and controlled clocks. In-memory isolated engines alone cannot establish a shared implementation. No load attack or existing database test is authorized by this plan.

| Group | Required assertions before adopting a shared implementation |
| --- | --- |
| Compatibility/guards | All 31 Phase 9A cases; missing/bad Origin/CSRF/session and malformed body never reserve; guard-invalid + full budget remains 403. Include expiry/revocation while waiting for reservation lock. |
| Keys/actions | 30/IP and 10/account, shared login/register/reauth, normalized identifiers, success/wrong password/duplicate registration, unknown-user generic errors and dummy verification; anonymous bootstrap IP-only; unrelated collection/research behavior unchanged. |
| Concurrency | Two independent engines/processes at limit−1, synchronized contenders: exactly one admission and others 429; absent keys, differing IPs/same account, same IP/different accounts, final capacity row, cleanup racing admission; exact counter state after each outcome. No sleep-based race assertion. |
| Multi-key semantics | IP-full never charges account; account-full charges IP once; two-key success commits together; transaction exception rolls back staged writes; 401/400 after confirmed reservation does not refund it. |
| Restart/durability | Commit admissions, dispose engines/terminate only owned child, reopen same synthetic file in fresh app/process: limits persist. In-flight uncommitted transaction disappears safely. Test normal DB crash recovery separately before making guarantees. |
| Clock/windows | Controlled 899999/900000/900001ms, partial ageing, same timestamp, restarts, lock wait, backward/forward jumps/high-water behavior; no stale transaction-start time or reset on clock correction. |
| Outage/failure | Lock timeout, read-only/full-disk simulation through injected storage faults, bad rows/policy version, commit failure/ambiguous outcome, deadlock retry bounds; generic 503, no Argon2/unmetered fallback, existing read/current-logout paths do not depend on extra throttle storage. |
| Capacity/privacy | Bounded arrays/rows/cleanup work, no active-key eviction, key allocation races, expired-row reuse, idle maintenance, unknown namespaces, pseudonymous dumps only; no secret/health logs or API exports. |
| Migration/recovery | Approved fresh/upgrade/idempotency and startup mismatch behavior on synthetic old schema; preservation of synthetic users/health/session rows; no live auto-migration. Backup/restore/reset-window policy tested without restoring real data. |
| Hosted alternatives | PostgreSQL primary/time/row-lock/isolation/creation races, failover/restore assumptions and deadlocks; Redis script atomicity/cluster slots/TTL/eviction/restart. Neither passes on the strength of SQLite tests. |

## Rollout, rollback and approval boundary

1. **Smallest safe next implementation:** approve a narrowly scoped, synthetic-only SQLite reservation adapter and additive schema/test design with the above 30/10/900 contract, guard ordering and explicit failure/clock/capacity policy. Start with isolated adapter/process tests, then separately review route/transaction integration. No real-data migration or default switch follows automatically from a prototype approval.
2. Settle numerical resource bounds, clock anomaly threshold, retention/maintenance owner, security-reauth availability and valid-CSRF/NAT policy. Review the migration and startup behavior before creating it. Existing SQLAlchemy/Alembic infrastructure is sufficient; no Redis/dependency change needed locally.
3. Approved integration must move **all existing auth-budget consumers**, not just login, to the same chosen authoritative store. No mixed memory/shared workers, shadow data deciding authorization or dual charge. Coordinate worker cutover; there is no durable old in-memory history to import. A fresh shared store creates a one-time allowance reset: block new auth during cutover or explicitly accept that supervised-local risk. Do not claim uninterrupted old-window continuity.
4. Require synthetic migration, focused/full safe tests, actual independent-process contention and measured SQLite lock latency before local activation. Public/multi-host PostgreSQL deployment requires its own implementation, ingress/clock/identity/security/privacy review and staging evidence. Do not enable idle enforcement as part of this change.
5. Code rollback may retain additive tables, but reverting to memory resets/discards shared protection and breaks the claimed guarantee. Stop/drain new auth before coordinated rollback; prefer a reviewed forward fix. Never restore user/session/password snapshots or delete health data to reset counters. Restoring a stale throttle snapshot may erase recent admissions; fail closed/quarantine new auth for a reviewed full 900-second interval from a trustworthy recovery clock before resuming, or explicitly accept a supervised reset. Clock anomalies need a separate recovery procedure. No automatic destructive downgrade.

Existing storage/copy protection, account recovery, retention/restore, registration privacy, human/device accessibility, historical Edge uncertainty, hosted operations and research/clinical gates remain. **Public/real-health release is NO-GO.** Approval is required before any implementation, migration, setting/service change or real-data operation. No Redis install, application edit, commit, push, PR, merge or deployment occurs in this audit.

## Actual safe validation and reproduction

All execution was on this Windows machine, under a new `%TEMP%/migramind-phase9b-so26n1a3`. Copied tracked backend `.py`, `.ini`, `.txt` source/dependency declarations only, excluding data/backup/export paths; no existing SQLite/WAL/SHM, user account/health record, backup, export, environment file, credential or secret was read/copied. Saved only the release document as a baseline for preservation checking. Reused earlier isolated Python **3.13.12** dependencies read-only; no install/upgrade, Redis or fresh-install claim.

Child environment was restricted to OS essentials plus `APP_ENV=development`, `DATA_MODE=local`, `DATABASE_URL=sqlite://`, `SESSION_HOURS=12`, `SESSION_IDLE_TIMEOUT_ENABLED=false`, `PYTHON_DOTENV_DISABLED=1`, `PYTHONDONTWRITEBYTECODE=1`, copied backend `PYTHONPATH`, private TEMP/TMP and UTF-8 output. Existing fixtures create/dispose synthetic memory/pytest-temporary databases. Temporary observations import the existing implementation; they do not implement any proposed shared-counter adapter or schema.

| Check | Exact result |
| --- | --- |
| Selected existing auth/guard/security/revocation/idle tests plus observations | **140 passed / 1 migration case deselected**, 44.81s pytest / 47.19s wall; 300s process cap |
| Existing coverage within that batch | **134 passed**, including all **31 Phase 9A** regressions; no guard-order regression |
| Temporary observations within that batch | **6 passed**; overlap the 140 total, not additional cases |
| Failures/retries | **None**; one existing Starlette/httpx deprecation warning |
| Documentation/integrity | **47 local links / 21 source-line references** verified; **66 tested backend source/declaration files unchanged**; prior release evidence and guard ordering preserved; only two expected documentation paths changed; `git diff --check` passed |

The six temporary tests are:

1. One Limiter prefilled to nine, four synchronized threads contest one remaining account slot: exactly **one admission / three 429**, final count ten. Barrier waits capped at five seconds. This checks existing in-instance safety, not future database concurrency.
2. Two independent Limiters each prefilled to nine, two synchronized contenders: **both admit**, combined state twenty. This demonstrates independent allowances with only two contested checks, not a load run.
3. First actual Authentication instance rejects a synthetic account after direct test-state exhaustion; a fresh instance with the same synthetic database dependency and cookie accepts login. Persisted session identity and ephemeral throttling are distinct.
4. Two sequential new owned Python processes each import the existing Limiter, assert empty state and admit one synthetic check. Child caps fifteen seconds each. No OS/service restart or durable-store recovery test was performed.
5. Controlled-clock exact 900-second cutoff, partial ageing, static Retry-After and retention until the next check. No sleep/wall-clock waiting.
6. Interleaved IP/account operations show separate-key locking and preserved IP charge on account rejection. No claim that a single instance's per-key lock over-admits.

From a **new filtered** backend copy under the restricted environment above:

```text
<isolated-python> -B -m pytest -q -ra tests/test_auth.py tests/test_auth_guard_order.py tests/test_security.py tests/test_logout_all.py tests/test_session_idle.py tests/test_shared_throttle_observations.py -k "not migration" --basetemp <new-root>/pytest-data -p no:cacheprovider
```

Use a previously nonexistent, owned basetemp path on every repetition. `test_shared_throttle_observations.py` is retained only in the recorded temporary source tree, not the repository. Evidence: `migramind-phase9b-checks.py` in TEMP, filtered source/temporary test, `results.json`, `checks.log` and release baseline. Outputs contain outcome assertions, not credential/session/health values. Existing synthetic owner-isolation/global-logout tests operate only on their fixture records.

No migration/provisioning command, application server, external request, real account operation, load/attack scan, candidate database counter table, Redis or infrastructure was run/created. No full backend/frontend/browser/build/advisory suite rerun: selected tests are appropriate to this documentation-only audit. No Linux, live PostgreSQL, SQLite shared-file counter concurrency/crash recovery, network proxy, Redis persistence/failover, sustained latency/capacity, real host restart or physical-device verification. Proposed transactional guarantees remain **acceptance requirements, not passing implementation results**. Existing historical release/security blockers are preserved.
