# Disposable PostgreSQL transaction harness — Stage A preparation

## Phase 9I-L: batch claim trust boundary

The [bounded controller review](NON_OWNER_DESIGN.md#phase-9i-l-exclusive-batch-controller-trust-review-2026-11-21) specifies a controller-only, ACL-protected local SQLite metadata store with a durable atomic whole-batch claim before credentials, distinct OS identities and independently authenticated maintenance confirmation. This is a design only: the store, controller and channels do not exist, and no SQLite or PostgreSQL operation was performed. Crash or uncertainty abandons the batch. Host integrity and non-rollbackable state remain trust limits; `EXECUTION_BLOCKED` remains true.

## Phase 9I-K: bounded case acquisition decision

The [single-run decision](NON_OWNER_DESIGN.md#phase-9i-k-bounded-single-run-acquisition-decision-2026-11-21) recommends one independent exclusive controller and a durable atomic **whole-batch** consumption record, rather than a general allocator service. Every case is tied to one test; interruption abandons the whole batch, with no resumption or reissue. This requires independently protected state, authenticated control and credential isolation; local advisory comparisons cannot provide them. The controller and separate maintenance handoff are not implemented and PostgreSQL execution remains blocked.

## Phase 9I-E subsequent update: non-owner identity shape

The dormant target and identity comparison now derive a case ordinal, fixture,
maintenance and distinct bootstrap-owner identity. No independently verified
case selection exists: test setup still refuses, and the execution block remains.
The bootstrap template is unapplied, actual privileges are unverified, and the
maintenance handoff and safe teardown remain separately controlled and unimplemented.

## Phase 9I-E follow-up: incomplete non-owner integration

The [unapplied bootstrap template](BOOTSTRAP_TEMPLATE.md) defines a marker and
proposed per-case roles/grants. Test setup now selects its mapped case but refuses
until independently authenticated one-use verification exists. SQL/driver/grant
semantics are unverified, the legacy runner remains owner-based, and maintenance
handoff is not implemented. Execution stays blocked; no setup or teardown is
authorized. [Details](NON_OWNER_DESIGN.md#phase-9i-e-follow-up-bootstrap-template-and-fail-closed-case-selection).

## Phase 9I-I: partial SQL transition only

The SQL guard now expects bootstrap-owned marker metadata and both transaction
functions compare control nonce with that marker. The marker bootstrap, non-owner
runner and case wiring are not implemented, so this is not a complete integration.
The SQL has not been parsed or executed by PostgreSQL. Execution remains blocked.

## Phase 9I-H: case contract only; execution blocked

`case_contract.py` supplies an offline 17-case mapping and bounded maintenance
request review with no credentials, database access or execution. The runner and
SQL are **not** yet adapted to non-owner case identities; test setup and cleanup
still refuse, and the bootstrap remains unapplied pseudocode. The execution block
remains enabled. See [implementation limits](NON_OWNER_DESIGN.md#phase-9i-h-offline-case-contract-incomplete-implementation).

## Phase 9I-G: minimum disposable architecture

[Decision and go/no-go checklist](NON_OWNER_DESIGN.md#phase-9i-g-minimum-practical-architecture-decision): one new isolated container and private volume, 17 pre-created per-test databases, separate bootstrap, fixture, maintenance and teardown authorities, and a bounded independently checked manual teardown. A separate operator may accept maintenance's direct table-mutation risk only for a verified synthetic run; this is not production security evidence. Earlier lifecycle-controller/lease directions are historical and superseded for this bounded experiment. The current code is incompatible, `EXECUTION_BLOCKED` remains true, and another offline implementation/review phase is required. No setup, execution or teardown is authorized here.

## Phase 9I-F reconciliation

See the [compatibility matrix and authority interfaces](NON_OWNER_DESIGN.md#phase-9i-f-compatibility-matrix-supersedes-historical-execution-directions).
`case_design.py` only compares supplied synthetic identities and evidence; it
does not allocate, authenticate, connect, invoke maintenance or authorize cleanup.
All 17 database cases remain blocked, and the three cleanup cases additionally
need independent maintenance orchestration. No PostgreSQL execution is permitted.

## Phase 9I-E: separate maintenance, offline only

The [revised role manifest](NON_OWNER_DESIGN.md) separates fixture and maintenance
roles. The fixture gets no windows DELETE, TRUNCATE, CREATE or ownership; maintenance
uses a separately controlled process and credential, neither implemented nor
available to the fixture runner. Its table-level DELETE and UPDATE can bypass the
cleanup function and its trust policy. Exact privilege sufficiency is unverified.
The dormant runner initialization and fixture resets now refuse; each test setup
also refuses until independent per-case allocation and verification are implemented.
The 17 cases remain present but cannot run. `EXECUTION_BLOCKED` remains true.

`teardown_plan.py` is a pure offline comparison exercise, with no command, database,
container or filesystem deletion capability. It returns only a review result; it
cannot authenticate observations or record provenance, enforce a lease, consume
one-use authorization, prevent replay or authorize deletion. Fresh independent
resource verification and a separately approved teardown controller remain absent.
No bootstrap or maintenance process is implemented; the manifest is unapplied
pseudocode. Historical directions below do not authorize any operation.

## Phase 9I-D design review

The [non-owner bootstrap, grants and teardown contract](NON_OWNER_DESIGN.md)
proposes independently controlled bootstrap and teardown authorities and a
restricted non-owner fixture role, with a fresh pre-created case database per
test instead of fixture resets. The SQL is placeholder design only, not an
executable bootstrap. The proposed independent teardown controller, comparison
of observed resources and fencing do not exist yet. The current runner and SQL
still assume fixture ownership and remain incompatible. **Execution stays blocked.**
No lifecycle procedure, SQL, container or database is authorized by this design.

## Phase 9I-C safety hold and lifecycle runbook v1

**Execution is disabled in source. Do not run the Stage B commands below.**
The existing test role owns the database, so it can have database-destruction
authority. A non-owner design with narrowly scoped fixture privileges is still
required. No setup or teardown implementation is authorized or provided.
This section supersedes the older setup and teardown directions below.

For a future independently approved and independently reviewed run, require a
new disposable PostgreSQL **container**, new private data volume, fresh identity,
and an explicitly assigned high loopback-only port. Never use an existing server,
container, role, database, volume or data directory. A separate provisioner,
not the harness role, owns container and volume lifecycle. Record an immutable
full container ID, reviewed image digest and exact PostgreSQL version, unique
nonce, volume ID/labels and ownership, network mapping, database and role IDs,
effective privileges, memberships, fixture object owners, generation and writer.
The operator must independently inspect actual resources and compare each value
with the approved run record; caller-supplied values are not independent evidence.

1. **Before setup:** separately approve exact image/digest, platform, lifecycle
   procedure and isolated driver. Establish that nonce, container, volume, port,
   role and database are new and unoccupied; verify loopback-only publishing and
   exclusive volume ownership. Stop on missing, conflicting or ambiguous evidence.
   A versioned, reviewed non-owner role and bootstrap procedure is still missing;
   do not create anything until it and its allowed privileges have been reviewed.
2. **After setup, before tests:** independently compare actual container/image,
   volume/port, role/database, effective privileges/memberships, object inventory
   and ownership with the record. Check marker, generation and writer, and obtain
   affirmative operator-approved time and freshness assertions. These assertions
   are conditions for this synthetic exercise, not evidence of clock continuity,
   snapshot freshness, safe recovery or fencing. No assertion permits targeting
   an existing instance or application data.
3. **Interruption, uncertain commit or partial setup:** stop, preserve the record,
   do not retry a reservation and do not assume setup or rollback completed. Do
   not reuse the nonce or automatically remove any resource. Missing setup or
   evidence is a refusal, not permission to delete.
4. **Teardown:** a separately approved provisioner must reverify the exact recorded
   container ID, digest/version, unique nonce, volume ownership, network/port,
   database/role identity and ownership, effective privileges/objects, generation
   and writer, plus affirmative time and freshness assertions. Compare observations
   to independently recorded expected values, not merely to their format. If any
   evidence is absent, inconsistent or ambiguous, refuse all deletion and request
   review. A concrete independently reviewed teardown mechanism that enforces this
   is not yet provided; consequently **no teardown is authorized** by this runbook.

`lifecycle_evidence()` is a non-database input-shape check, not a provisioner,
teardown tool or resource verifier. It does not compare generation/writer,
container ID or image digest against independently observed resources. The
database inventory checks are incomplete and unvalidated. The harness must
not be enabled until those gaps and fixture-reset isolation are resolved and
independently reviewed. The historical Stage B command below is retained for
context only and currently refuses execution before opening a manifest or driver.

**Not executed against PostgreSQL. Not a production limiter, application schema,
migration, recovery tool or deployment.** Current approval permits ONLY source
preparation and the non-database/static command below. No container, cluster,
database, manifest setup, package install or teardown was performed in Stage A.

```text
# The ONLY execution approved for Stage A:
python -B -m unittest discover -s prototypes/synthetic_pg_transaction_harness -p test_static.py -v
```

`harness.py` is opt-in orchestration, `schema.sql` is synthetic-only executable
SQL prepared for later compilation, `test_database.py` contains dormant Stage B
cases, and `test_static.py` uses only standard-library pure/AST/text checks.
Import/discovery does not import psycopg or connect. Database test class setup
skips unless the explicit runner has granted a permit AND installed a fresh
owned schema. Static checks cannot certify SQL syntax, psycopg APIs, PostgreSQL
locks, time, isolation or cleanup; no SQL has been applied or parsed by a server.

## Target isolation and permission boundaries

There is **no DSN, host, dbname, role or password CLI parameter**, and no reuse
of application database/PG environment configuration. A bounded manifest must
have exactly format/classification/nonce/port fields, live at:

```text
<system-temp>/migramind-pg-harness-<32-lowercase-hex-nonce>/target.json
```

Other locations, symlinks, oversized/duplicate/extra fields, mismatched directory
nonce, default 5432 and ports outside 49152–65535 are refused. Database and role
are derived as `migramind_throttle_synthetic_<nonce>` and `mm_synthetic_<nonce>`.
Only 127.0.0.1 is permitted. A nonce is a run identity, not a password or proof
that a cluster is disposable. Stage B human approval must attest that the entire
instance is fresh/owned and contains no real databases/data. Marker spoofing by
a malicious host/admin is outside these accidental-target protections.

SQL execution requires both the exact acknowledgement and `--stage-b-approved`.
The outer runner launches an isolated Python child with a restricted environment
(no PG*, DATABASE_URL, APP_ENV, HOME or inherited app credentials). The child
prompts interactively for the fresh disposable role password; no password file,
argument or environment secret is accepted. Explicit target/timeout/null passfile
parameters prevent libpq defaults from choosing another host/database/user.
Do not print/store that password. Python strings are not guaranteed zeroized.
No TLS claim: loopback transport uses sslmode=disable for disposable tests only.

Before every independent connection permits harness writes, it verifies:

- Exact database/session/current role and database owner; writable primary.
- No superuser, CREATEDB, CREATEROLE, replication or BYPASSRLS privileges.
- A plain role-owned `harness_bootstrap.identity` table/schema with exactly one
  strict synthetic marker matching nonce, classification, database, role and tag.
- No unexpected user relations in other schemas or the bootstrap/harness schemas.
- Fresh `synthetic_throttle` schema absence before installation. Existing harness
  schemas are refused at run startup, never silently reused or dropped.

`schema.sql` repeats marker/identity/privilege checks BEFORE any CREATE operation.
Driver errors exposed by the connection wrapper contain only a sanitized SQLSTATE,
never connection strings, password, driver exception or bound data. This is not
independent proof of primary freshness/unique writership; failover/RPO remain
unvalidated. No existing application database is an acceptable Stage B target.

## Stage B prerequisites and setup — NOT authorized or performed now

Require a separate explicit Stage B approval, reviewed exact source/diff, Python
3.13, already available reviewed `psycopg==3.3.6` (current project lock), and a
separately approved disposable local PostgreSQL instance. No version is certified
by Stage A; record Python/driver/server versions and instance identity in Stage B.
Do not install dependencies, start Docker or create a cluster on this approval.

Future Stage B operator sequence:

1. Select an unused explicit high loopback port on a fresh disposable instance;
   record its exact owned process/container/cluster identity. Do not target an
   existing local server, application database or remote/shared cluster.
2. ONLY after approval, create a new manifest (no DB setup is automated):

   ```text
   python -B prototypes/synthetic_pg_transaction_harness/harness.py create-manifest --port <explicit-high-port>
   ```

3. Using the disposable instance's separate setup authority, create the derived
   restricted login role and derived database owned by that role, with a fresh
   interactive password. Do not put credentials into commands/history/repository.
   Connect as the derived role to its derived database, not an administrator.
   Prepare the following marker there, substituting only the manifest nonce:

   ```sql
   -- FUTURE DISPOSABLE TARGET ONLY. No Stage A execution.
   CREATE SCHEMA harness_bootstrap;
   CREATE TABLE harness_bootstrap.identity (
     id integer PRIMARY KEY CHECK(id=1), nonce text NOT NULL,
     classification text NOT NULL, synthetic_only boolean NOT NULL,
     db_name text NOT NULL, role_name text NOT NULL, schema_tag text NOT NULL);
   -- In psql, :nonce is an operator-supplied manifest value, not a secret:
   INSERT INTO harness_bootstrap.identity VALUES
     (1, :'nonce', 'SYNTHETIC_ONLY_DISPOSABLE', true, current_database(), current_user,
      'migramind-throttle-harness-v1');
   ```

   Ensure bootstrap schema/table are owned by that derived role, that its role
   flags meet the checks, and that no other user relations exist. The runner does
   not create a role/database, elevate privileges, use administrator credentials
   or automatically “repair” a rejected target.
4. Only with separate approval, execute the explicit runner:

   ```text
   python -B prototypes/synthetic_pg_transaction_harness/harness.py run-postgres --manifest <absolute-owned-target.json> --ack I_ACCEPT_STAGE_B_DISPOSABLE_SYNTHETIC_SQL --stage-b-approved
   ```

   It prompts for the disposable role password, verifies target isolation,
   creates the fresh synthetic schema once and selects ONLY the Stage B test
   module. There is no generic SQL-file or connection-string execution option.
   Noninteractive CI password delivery is not implemented; no env-secret shortcut.

## Prepared schema/transaction tests — unexecuted

Only `synthetic_throttle` objects: control metadata, synthetic boolean bindings,
digest-keyed windows, expiry index and validation/reserve/cleanup functions.
Array checks enforce 30/IP or 10/account, one dimension/nonempty/nonnegative/
nondecreasing bounded bigint entries, 32-byte digests and exact expiry. Same-ms
duplicates count. Missing keys have no committed placeholder.

Caller-owned READ COMMITTED transaction locks binding FOR SHARE → control FOR
UPDATE → existing windows in scope/digest order. The global gate serializes
missing-key creation/capacity/final slots. Primary `clock_timestamp()` is sampled
after locks unless an explicit synthetic test clock is injected. Both budgets
append or neither does; account-full does NOT charge IP. Live auth is unchanged.
Control metadata can advance on denial. Python reports allowed only after commit.

Functions have fixed pg_catalog search_path and SECURITY INVOKER, never DEFINER.
No credentials, tokens, session cookies, raw IP/email or health fields. The small
bindings table and booleans are test guards, not actual Origin/CSRF/session code.
All test input identifiers are documentation IPs/example.test accounts.

Prepared two-connection tests hold the first uncommitted reservation, observe
actual blocking with `pg_blocking_pids` from that same connection, then commit
and inspect the second outcome. No sleep is used to assume a race. Coordination
uses explicit 2s observation/3s lock/5s statement bounds, not proposed production
latency settings. There are no automatic admission retries. A separate 50ms
lock-timeout test requires SQLSTATE 55P03; rollback faults require P0001 rather
than accepting any SQL error. None has run in Stage A.

Separate maintenance requires explicit generation, writer, time-trust and freshness
assertions; missing or mismatched evidence quarantines before any deletion. These
assertions are injected, not proof of a trustworthy server or clock.
Maintenance commits bounded valid expired deletions; it does not run
automatically as a side effect of denied admission. Fixture resets TRUNCATE ONLY
the freshly installed harness windows and reset synthetic control between tests.
This is not operational recovery or permission to reset any existing limiter.
Known backward/untrusted forward time, writer-generation mismatch and stale-state
flags quarantine without resetting counters. Those flags are injected assertions,
not a detector or actual primary failover/restore. Trusted forward time still
ages quotas. No clock threshold or automatic return from quarantine is invented.

## Teardown and remaining gates

The runner deliberately contains **no DROP DATABASE/role/container/cluster** and
no automatic instance teardown. Stage B operator must verify recorded instance
ID, high port, derived database/role and marker before removing ONLY that whole
owned disposable instance through its approved lifecycle. Never delete/drop
anything on an existing server. If ownership is uncertain, stop and ask. Remove
only the matching newly created manifest directory after safe artifact review;
no recursive delete command is provided here or executed now.

Global control serializes unrelated users and maintenance. Harness count
reconciliation also scans up to 10001 rows: no scalability/latency guarantee.
Actual parser/constraints/PLpgSQL, permissions, blocking, deadlocks, pools, WAL,
primary freshness, restore/suspend/reboot and performance still need Stage B or
later approval/evidence. Static passes are not PostgreSQL correctness. This
harness does not implement live sessions, registration/password handling,
bootstrap quotas, hosted operation, recovery, application migrations or flags.
