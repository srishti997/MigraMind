# Phase 9I-D non-owner fixture and teardown design v1

## Phase 9I-L: exclusive batch controller trust review (2026-11-21)

**Design decision, not an implementation or authorization.** For this bounded
experiment, use one controller process under a dedicated host OS identity, with
a separate fixture identity and separately controlled bootstrap, maintenance and
teardown authorities. No PostgreSQL execution block is removed. The following
component is justified only if all 17 cases and repeatable crash/refusal checks
are worth implementing; a single manually supervised, never-restarted run is
simpler but depends more heavily on humans to prevent reuse and wrong-case access.

### Concrete claim store and state boundary

Use a **new, dedicated local SQLite metadata file**, separate from all MigraMind
data and the PostgreSQL volume, in a directory owned by the controller OS identity.
OS ACLs must deny fixture, maintenance and ordinary users read/write/replace access
to the directory and file, including SQLite journal files; separately controlled
bootstrap/teardown identities do not need claim-store write access. The store holds
no database passwords or health data. Its versioned record contains the full
immutable container ID, image digest/version, full private-volume ID and owner,
loopback port, run ID/nonce, and exactly 17 canonical test-name/ordinal entries,
each binding database, fixture/maintenance role, bootstrap owner, marker identity,
generation and writer. A reviewed canonical serialization/hash detects accidental
changes; the hash is not authentication against an actor who can rewrite the store.
The protected record is populated only from separately verified bootstrap/runtime
observations, not self-reported fixture assertions.

Before any fixture credential is issued, the controller takes an OS-level
exclusive process lock, verifies its own OS identity and exclusive resource
ownership, then opens the dedicated store and atomically inserts a **whole-batch
consumed** row with unique constraints on run ID, container ID, volume ID and
nonce in one serialized transaction. Use a reviewed local filesystem and SQLite
transaction configuration with durable commit (for example FULL synchronous
with an appropriate journal mode), and confirm the commit succeeded before
issuing any credential. Commit errors, unknown outcome, lock/store failure,
duplicate key, missing or malformed record, unverified mapping or failed flush
are refusal; never treat a timeout as permission to retry issuance. An independent
offline implementation review and crash tests must establish the actual platform's
locking, SQLite sync and storage guarantees; neither a function return nor a
human assertion proves that a device honored durability. All later invocations
check the durable consumed row and refuse that batch. This is a per-run claim
store, not a network allocator or general lifecycle service. It is a *proposed*
isolated metadata store: no SQLite file is created or opened in this review.

The claim is permanent even if zero credentials were issued. The controller
maintains the 17-case mapping in memory only during its single process lifetime,
starts each mapped test at most once, and abandons the whole batch on interruption,
ambiguous result, broken exclusivity or restart. Any restart refuses the consumed
record; it never reconstructs per-case progress or reissues credentials. A new
run requires a new independently verified container, private volume, nonce and
case identities. If claim state is unavailable or might have rolled back, stop
and preserve resources for separate review, not a new attempt against them.

### Principals and authentication

| Boundary | Control to implement and verify | Residual trust |
| --- | --- | --- |
| Bootstrap → controller | Independent operator verifies exact container/volume, marker, role ownership and grants; supplies an approved record through a protected channel. | Bootstrap and OS/runtime observations must be authentic; labels alone prove nothing. |
| Controller → fixture | Controller starts the fixed test under a distinct restricted OS identity. An inherited, non-inheritable-by-other-children private pipe or OS-authenticated IPC delivers only that case's fixture credential after durable claim and mapping check. Verify the child process/OS identity and bind the message to run, test and case; do not use command arguments, environment variables or shared files for credentials. | Fixture may perform multiple operations within its granted case. Host administrator/debugger or a compromised controller can still steal or copy credentials. Exact IPC/OS behavior requires platform review. |
| Fixture → maintenance | Controller relays only a request ID, exact run/case/test, bounded operation and synthetic injection, never a maintenance credential. Independent maintenance authority authenticates the controller/request, independently rechecks case/marker, generation/writer and actual time/freshness, then separately approves and uses its own credential. | Maintenance's direct UPDATE/DELETE can bypass the function; explicit synthetic-only risk acceptance is required. |
| Maintenance → controller | An authenticated channel binds a single confirmation to the run, case, unique request ID, operation and a committed result or sanitized SQLSTATE. Controller refuses duplicates, mismatch, unknown commit, missing/ambiguous confirmation or channel loss and abandons the batch. | Authentication and result provenance must be implemented independently. Synthetic false arguments for negative tests are allowed only after real evidence passes. |
| Teardown | Separately approved operator verifies exact resource identities and ownership; no deletion command or credential is available to fixture/controller test code. | Manual verification and runtime state can race; uncertainty stops deletion. |

The claim store and OS ACL can enforce exclusivity and at-most-once *controller
issuance* only if their documented atomicity, durability, access control and
controller code hold. They do not enforce one SQL transaction per fixture, prove
server freshness, prevent a compromised authorized controller from violating the
protocol, or withstand an administrator who can rewrite all trust roots and
restore both claim state and the container. Protection against coordinated rollback
requires an independently controlled non-rollbackable ledger or equivalent; that
additional authority is not part of this bounded design. Operator attestations of
freshness or isolation are conditions, not cryptographic proof.

### Manual alternative and go/no-go

For a one-off demonstration, a separately supervised manual procedure with one
operator, a recorded one-use batch, 17 pre-created cases, separate maintenance
operator and total abandonment after interruption is simpler. A controller
materially improves repeatable mapping, duplicate refusal and crash handling only
after its store durability, OS isolation, IPC and failure paths are implemented
and independently tested; until then it adds complexity and is not a safety proof.
Do not weaken the one-use requirement merely to use a human checklist.

**No-go** unless independent reviewers approve the exact fresh container/volume,
case inventory and effective privileges; protected store/OS identities and
atomic durable claim semantics are demonstrated; credential/maintenance channels
are authenticated and separated; failure/rollback and synthetic-only maintenance
risk are reviewed; and separate execution and teardown approvals are obtained.
No component in this section is implemented. Minimal next work, if justified:
implement only the controller's protected batch claim and crash/refusal tests in
isolation, followed by fixed case dispatch and independent maintenance handoff;
review them before considering a separate PostgreSQL execution authorization.

## Phase 9I-K: bounded single-run acquisition decision (2026-11-21)

Recommend **B: one independently controlled exclusive single-run controller**
for this disposable 17-case experiment. A general durable allocator service (A)
can support resumable or distributed runs and atomic per-case claims, but adds
infrastructure not needed for one bounded run. Both A and B need trusted state
and authentication. A fresh container and 17 databases reduce the problem to
exclusive use of one pre-bound batch; they do not themselves prevent a second
controller, copied credentials, replay, restore or reuse after a crash.

For B, the independent run owner creates a protected run record binding a unique
run ID/nonce, full container and volume identities, fixed test-name-to-ordinal
mapping, case database and role identities, owner, marker, writer and generation.
Before giving any case credential to a fixture process, the controller must
atomically and durably mark the **entire batch consumed** in state inaccessible
to fixture and maintenance processes. Exclusive control of the record and
container, authenticated controller identity, atomic create-if-absent/consume,
and a reliable refusal of another controller are necessary. An exclusive host
lock alone is insufficient across restart or loss of its lock. The consumed
record must survive controller failure and be checked before any later run.

The controller starts only the fixed test mapped to each fresh case, once; the
fixture gets only that case's restricted credential and cannot access bootstrap,
maintenance or teardown credentials. Keep the record and credential distribution
under an independently controlled OS/runtime identity; prevent other principals
from starting a runner or reaching its credentials. Observe and verify the
container, database identities and effective privileges separately. If the
controller stops, a result is uncertain, exclusive control cannot be confirmed,
state is missing, or a duplicate/stale assignment is presented, stop the run
and never resume or reissue any case from that batch. Use a new independently
verified run and fresh resources only after separately authorized handling of the
old instance. An immutable record of consumption cannot be replaced by a local
boolean supplied by the fixture. Durable batch consumption is still necessary
for the stated cross-restart replay guarantee; B avoids a *general-purpose*
allocator, not durable trusted state.

Under those assumptions, an atomic durable batch claim and restricted credential
distribution can enforce at-most-once **controller issuance** and bind each
issued credential to its designated test. It does not prove a case was unused
before bootstrap, that a compromised runner cannot issue multiple transactions,
or that a host/runtime administrator cannot copy credentials, roll back state or
start another container. Those are independent verification and operator trust
conditions; advisory Python comparisons do not authenticate them. No guarantee
survives a restore of both protected consumption state and instance to an older
snapshot unless an external non-rollbackable authority detects it.

The three cleanup tests pause for separately authenticated maintenance approval.
The independent maintenance operator verifies the exact run/case, marker,
generation, writer, actual time/freshness and requested bounded operation, then
performs the test-only operation under its own credential and confirms the case,
request, result or sanitized SQLSTATE back over an authenticated channel. The
negative cases may inject false *test inputs* only after actual evidence passes.
Ambiguous confirmation or commit causes the case/run to stop, not retry. The
fixture never receives the maintenance credential. Maintenance UPDATE/DELETE
can bypass cleanup policy, requiring explicit synthetic-only risk acceptance.

This choice relaxes **resumption and per-case reissue**, not the original
at-most-once safety objective: an interrupted batch is abandoned wholesale. It
also limits enforcement to the independently controlled host/state boundary;
protection against a malicious administrator or coordinated rollback requires
an additional independent authority. Neither this controller nor protected durable
state/authenticated handoffs are implemented. `EXECUTION_BLOCKED` remains true;
separate bootstrap, execution and teardown approvals and all existing isolation
checks remain required. Smallest next step: specify and independently review the
controller's atomic batch-consume storage, exclusive process/credential boundary,
crash behavior and maintenance confirmation protocol offline before implementation.

## Phase 9I-E subsequent update: dormant non-owner identity shape

`Target` now derives case database, fixture, maintenance and bootstrap-owner
identities from nonce and ordinal. Its dormant server identity comparison expects
the database owner to be the bootstrap owner rather than the fixture, and the
marker comparison includes ordinal and both non-owner roles. Marker/table owner
queries expect the bootstrap owner. These comparisons have only offline tests;
effective privileges, complete objects, independent evidence and PostgreSQL
semantics remain unverified. The manifest still does not select a case, and
`require_case` refuses every test pending independent one-use verification.
Consequently this is an incomplete refactor, not an executable non-owner runner.
The 17 tests and their assertions remain blocked, maintenance remains separately
controlled and unimplemented, and teardown comparator remains advisory only.

## Phase 9I-E follow-up: bootstrap template and fail-closed case selection

[BOOTSTRAP_TEMPLATE.md](BOOTSTRAP_TEMPLATE.md) provides a non-executable marker,
role and grant template for 17 nonce/ordinal cases. The SQL guard now compares
those derived identities and rejects missing/privileged roles and direct role
memberships. It remains unexecuted; this does not prove effective privileges or
safe bootstrap, including how the bootstrap authority acts as the NOLOGIN owner.

Test setup selects the existing mapped case but `Context.require_case` refuses:
there is no independently authenticated verifier or durable one-use registry.
`validate_precreated_case` checks supplied values only and explicitly returns
review-only, not verification. The legacy runner identity and connection logic
still expects fixture ownership and is incompatible with this template. The
17 tests cannot run; the three cleanup cases also lack their independent
maintenance process. Execution stays blocked. The teardown comparator remains
advisory and cannot inspect resources, authenticate a protected record, enforce
one-use authorization or delete anything.

## Phase 9I-I: partial SQL transition; integration remains blocked

`schema.sql` now checks a bootstrap-owned marker relation and expects its owner,
fixture, maintenance and case-ordinal metadata at bootstrap. Reservation and
cleanup compare control nonce with the marker's explicit nonce instead of parsing
the database name. This SQL is unexecuted and relies on a marker schema/template
that has not been implemented. Role existence, memberships, grants and complete
object ownership are not proven by this guard. The runner still uses the legacy
fixture-owner identity and single-nonce target; case mapping is not wired into
test setup, which continues to refuse. The proposed bootstrap grants below remain
placeholder documentation. No separate maintenance handoff execution exists.
`EXECUTION_BLOCKED` stays true. This partial change is **not a completed
integration or ready for pre-execution review**.

## Phase 9I-H: offline case contract, incomplete implementation

`case_contract.py` maps all 17 existing test method names to distinct ordinal
case identities and identifies the three maintenance cases. Its bounded, pure
maintenance request checker rejects mismatched cases/evidence, unknown fields,
invalid time/batch and inappropriate synthetic failure injection. It accepts no
credentials and performs no operation; independent identity/authority and real
clock/freshness still require verification. A false synthetic test argument is
not evidence that real observations are trustworthy. The current test setup and
cleanup still refuse, so this mapping is not connected to a functioning runner.

The existing SQL still assumes a single nonce at the end of the database name,
including the control checks inside reserve and cleanup, and its bootstrap guard
requires the fixture to own the database. Existing harness identity checks make
the same owner assumption. The placeholder grants below and no verified case
allocator do not enforce the requested ownership boundary. No executable
bootstrap template or non-owner runner was produced in this partial phase; do
not apply the legacy SQL or treat the mapping as authorization. The execution
block remains true. Review and implement these guard, bootstrap and runner
changes together before any separately approved execution; the maintenance role
still has the documented direct UPDATE/DELETE bypass risk.

## Phase 9I-G: minimum practical architecture decision

**Decision: no-go for execution today; another offline implementation and
review phase is required.** This section supersedes the earlier proposed custom
controller/lease mechanism below. Retain the prior material as design history;
no generic lifecycle service, privileged helper or RLS is required for this
bounded experiment. No infrastructure or SQL operation is authorized here.

Use one newly created disposable PostgreSQL container with an exclusively owned
private data volume and an explicitly chosen high port bound only to loopback.
A separate bootstrap operator creates 17 fresh, nonce/ordinal-derived case
databases, one per test, with distinct restricted fixture credentials and separate
maintenance credentials. Bootstrap owns each database, schema, table, index and
function. Fixture and maintenance roles own nothing, have no administrative role
membership, and cannot create/drop databases, roles or objects. Fixture cannot
DELETE windows, TRUNCATE or CREATE; maintenance has the narrowly documented
fixture-table SELECT/UPDATE/DELETE needed for cleanup and row locking. The
fixture process never receives maintenance credentials. No actual role/grant
behavior has been verified against a server.

The 14 non-maintenance tests use one case each. For each of the three cleanup
tests, the fixture prepares its case and pauses; an independent maintenance
operator/process verifies the case, performs the specifically requested test-only
operation, and returns only the result and sanitized error/SQLSTATE. The test
then checks its existing assertions. The rollback and deliberately untrusted
freshness tests need explicit, reviewed negative-test protocols: the operator
must first independently establish that the disposable target and actual
generation/writer/time/freshness are trustworthy, then inject a synthetic fault
or false **test argument**. Never mistake a deliberately false argument for
permission to proceed against an actually unverified target. No maintenance
credential, connection or authority goes into the fixture runner. Unknown commit
or connection result stops the case without retry.

**Maintenance risk decision:** recommend accepting direct maintenance UPDATE and
DELETE only for this independently verified, single-use synthetic instance, if
the responsible reviewer explicitly accepts it for that run. These privileges
can bypass every cleanup trust/expiry check, and fixture UPDATE/INSERT also allow
synthetic-state manipulation; trust is in the separated operator and isolation,
not enforced function-only access. No acceptance is implied by this document or
the user's architecture-review request. This gives no evidence for production
cleanup security, safe failover or real-data use. No SECURITY DEFINER or RLS is
proposed for these tests.

### Independent checks and manual lifecycle

Before later approved setup, record an independently generated run nonce, the
reviewed image digest and PostgreSQL version, full container ID, full volume ID,
loopback address/high port, case-to-database/role mapping, database owner, marker,
writer/generation and lifecycle state. Bootstrap and teardown authorities are
separate from fixture and maintenance credentials. A second reviewer compares
the record with runtime inspection of the exact container ID/image, published
address/port, mount source and all volume attachments. Inspect the dedicated
instance's database/role catalogs and ACLs with separately controlled read-only
authority: exact expected database/role names, owner and object definitions,
role flags/memberships and effective privileges (including PUBLIC/default ACLs),
no cross-case access, no unexpected schemas/extensions/objects, and distinct
fixture and maintenance identities. Verify marker, generation and writer against
the run record before testing and before teardown. Refuse on incomplete catalog
visibility, identity mismatch, an unexpected attachment, stale or partial setup,
untrusted time/freshness or uncertain result.

Catalog/runtime comparisons can check observed IDs, ACLs, mounts and endpoint
configuration; they cannot by themselves prove exclusive host control, image
trust, observation integrity, clock continuity, freshness after restore, or that
the instance contains no real data. A responsible operator must independently
attest a newly created synthetic-only instance, isolation, trusted time and
freshness, and review the provenance of observations. Assertion alone is not
evidence of identity. The existing comparators are advisory and cannot perform
or authenticate these checks.

After a separately approved run, the fixture and maintenance operators stop work
and close connections. Before stopping the server, the independent reviewer
records the matching marker, generation/writer and affirmative time/freshness
assessment; a stopped server cannot supply fresh database observations. The
teardown operator then independently checks the recorded full container ID,
image, port, volume ID/mount and ownership against current runtime observations,
confirms no test activity and obtains separate teardown approval. Recheck the
exact container and volume mapping immediately before each manually authorized
removal; remove only that recorded disposable container and then its private
volume after confirming it has no remaining attachments. Stop without deletion
if identity, ownership, state, generation/writer or evidence is missing,
conflicting, changed, or ambiguous. For partial bootstrap or interrupted work,
preserve resources for separately authorized manual review; do not infer that
missing markers or time/freshness attestations permit destruction. This is an
operator procedure, not an implemented or race-proof deletion tool; host/runtime
control and the risk of changes between inspection and removal remain explicit.

### Go/no-go and implementation order

- **Go only after:** separately approved fresh container and private volume;
  recorded and independently verified IDs, roles, ownership and grants;
  trustworthy time/freshness assertions; explicit acceptance of the bounded
  maintenance risk; reviewed bootstrap, runner and maintenance changes; and a
  separate operator/approval for teardown. Failure or ambiguity is **no-go**.
- **1.** Prepare reviewed, unapplied bootstrap SQL for owner-created case
  objects and explicit role grants, changing the legacy owner/nonce guard.
- **2.** Replace single-target and fixture-owner validation with exact case and
  bootstrap-owner verification. Map all 17 tests to unique pre-created cases;
  reject reused or partial cases without DDL or reset.
- **3.** Add a separately controlled maintenance handoff for the three cleanup
  tests, including the negative-test protocol above and no credential sharing.
  Preserve all existing assertions and do not retry uncertain transactions.
- **4.** Add offline tests for identity/privilege/refusal paths and review the
  SQL/driver and operator procedures. Keep `EXECUTION_BLOCKED` until a separate
  review and explicit execution approval. Later PostgreSQL execution would
  validate actual syntax, grants, isolation, contention and timeouts.

There is no implementation or provisioning approval in this architecture
decision, and no manual deletion is performed or authorized now.

## Phase 9I-F compatibility matrix (supersedes historical execution directions)

| Legacy source assumption | Non-owner target | Required change before execution |
| --- | --- | --- |
| `schema.sql` guard requires database owner=current fixture; nonce is database suffix | Bootstrap owns database; names contain nonce and case ordinal | Replace guard and marker contract under separately reviewed bootstrap authority; do not apply legacy SQL. |
| `schema.sql` creates schema, tables, index and functions as its invoker | Bootstrap creates and owns every object | Separate bootstrap-only schema installation from fixture privileges and verify object definitions/owners. |
| `harness.Target` supplies one database and one role per nonce | Fresh database plus distinct fixture and maintenance role for each case | Replace target, manifest and connection identity handling with independently verified per-case mapping. |
| `validate_server_identity` expects database owner to equal session/current fixture | Database owner differs from fixture | Verify exact bootstrap owner and non-owner session role plus effective privileges and memberships. |
| `verify_target` expects marker/schema and fixture relations owned by fixture | Bootstrap owns marker, schema and all objects | Check independently pinned owner/definitions/ACLs, functions, indexes, extensions and complete inventory. |
| `initialize` once created DDL and rows; worker still calls it | Bootstrap pre-creates each isolated case | Existing initialize now refuses; remove worker dependency when reviewed allocator exists. |
| Tests previously TRUNCATEd and reset shared fixture | Fresh pre-created case per test | Setup now refuses; replace with verified unique one-use case acquisition; no reset/DDL. |
| Test `cleanup` previously used fixture credentials | Independently controlled maintenance process with separate credentials | Current helper refuses; design a separate authenticated invocation and result channel without transferring credentials. |
| `lifecycle_evidence` and teardown comparator accept supplied assertions | Independent observations bound to protected record and distinct authorities | Implement provenance, freshness, fencing and replay controls outside the fixture; comparator remains advisory. |
| Existing `Context.connect` and worker are legacy blocked paths | No fixture-owned DB, no application configuration | Keep block; independently review any future replacement and never reuse legacy identity validation. |

`case_design.py` is a pure proposal interface: `Case(nonce,ordinal)` derives
distinct bounded database/fixture/maintenance identifiers and a bootstrap owner;
`propose_case` refuses case collisions, incomplete inventories and non-NEW state.
It does not reserve identifiers or establish inventory completeness, freshness,
atomicity, object ownership or protection from races. An actual independent
allocator must atomically reserve and persist one-use case identities and refuse
partial, collision, stale, uncertain and repeated requests. The owner is a
run-scoped authority, and its actual identity/ownership must be independently
verified rather than treated as a case collision.

`review_maintenance` compares exact supplied case and generation/writer evidence
and explicit trust assertions; it returns review only. It authenticates neither
the maintenance principal nor the observations and cannot prove credentials are
separated. A future separately controlled process needs authenticated identity,
independent live evidence, a bounded one-use request tied to the case and no
maintenance secret in the fixture process; uncertain outcomes forbid retry.

Maintenance UPDATE and DELETE may bypass the function's policy; table privileges
do not enforce expiry or trust. Alternatives requiring separate review include a
carefully constrained SECURITY DEFINER helper, RLS with independently verified
policy and time inputs, or accepting the current separate-role risk in a truly
disposable case. None is introduced here. The least-privilege proof, direct role
ACLs and default ACLs are still unvalidated: no executable bootstrap template is
supplied. The comparator cannot authorize destruction.

All 17 existing database cases are blocked by case allocation, non-owner
bootstrap/identity verification and the global execution block. The three cleanup
cases additionally require independent maintenance orchestration and confirmation;
their assertions remain in the source. Actual SQL parsing, permissions and
concurrent transactions remain untested.

**UNAPPLIED DESIGN ONLY.** The SQL fragments below contain intentional placeholders
and are not a script, migration, provisioning instructions, or authorization to
execute. No target exists as a result of this document. The current harness remains
blocked and is incompatible with this design. No teardown implementation exists.

## Authorities and ownership

| Authority | Scope | Ownership and powers |
| --- | --- | --- |
| Bootstrap | Separately controlled disposable-container setup principal, including the minimum cluster-admin authority needed only during setup | Creates fresh container-local roles and databases; owns every test database, `harness_bootstrap` and `synthetic_throttle` schema, marker, control, bindings and windows tables, all associated indexes/constraints, and the three fixture functions. Not available to runner. |
| Fixture | Unique restricted LOGIN per test database, no memberships and NOINHERIT | Owns no database, schema, table, index, function, role, container or volume. Only explicitly listed grants in its own test database. No container-runtime socket/API or bootstrap/teardown credentials. |
| Maintenance | Separate non-owner LOGIN, unique per case, controlled by an independent maintenance process | Has narrowly enumerated fixture-table grants including table-level windows DELETE. No credentials are sent to fixture runner. |
| Teardown | Independent infrastructure principal and approval, no runner access | Controls removal of the exact recorded disposable container and its dedicated volume only after the gate below. It does not use the fixture database role; it need not own PostgreSQL objects or drop roles/databases individually. |

Bootstrap credentials are scoped to the isolated instance, not the host's other
instances; fixture and teardown principals have no membership in bootstrap or
one another. Any runtime or OS principal able to bypass these boundaries remains
trusted. Provisioning and teardown must be implemented and independently reviewed
outside the test runner; a boolean in the runner cannot enforce this separation.

## Bootstrap and grant manifest — unresolved SQL shape

One newly created database and one new fixture role per test case, each derived
from the run nonce plus a bounded test ordinal. A fresh, single-run container and
volume contain only those databases and required PostgreSQL template/system
databases. No resource or identifier is reused. The preprovisioner creates the
fixture schema/functions and initial empty control/binding rows before handing out
the individual test credential. Login/register share the same synthetic budgets.
The exact PostgreSQL version, fixed identifier codec, quoting, object hashes and
full database/role grant manifest must be reviewed before implementation.

The following is intentionally **non-executable pseudocode**, not a request to
substitute names and run it:

```sql
-- DESIGN ONLY: bootstrap principal on a verified fresh disposable instance.
CREATE ROLE <fixture_role> LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
  NOREPLICATION NOBYPASSRLS NOINHERIT;
CREATE ROLE <maintenance_role> LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
  NOREPLICATION NOBYPASSRLS NOINHERIT;
CREATE DATABASE <case_database> OWNER <bootstrap_owner>;
REVOKE ALL ON DATABASE <case_database> FROM PUBLIC;
GRANT CONNECT ON DATABASE <case_database> TO <fixture_role>;
GRANT CONNECT ON DATABASE <case_database> TO <maintenance_role>;
-- Bootstrap pre-creates the fixed, owned marker and schema.sql objects.
REVOKE ALL ON SCHEMA harness_bootstrap, synthetic_throttle FROM PUBLIC;
GRANT USAGE ON SCHEMA harness_bootstrap, synthetic_throttle TO <fixture_role>;
GRANT USAGE ON SCHEMA harness_bootstrap, synthetic_throttle TO <maintenance_role>;
REVOKE ALL ON ALL TABLES IN SCHEMA harness_bootstrap, synthetic_throttle FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA harness_bootstrap, synthetic_throttle FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA synthetic_throttle FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE <bootstrap_owner> IN SCHEMA synthetic_throttle REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE <bootstrap_owner> REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE <bootstrap_owner> IN SCHEMA synthetic_throttle REVOKE ALL ON TABLES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE <bootstrap_owner> IN SCHEMA synthetic_throttle REVOKE ALL ON SEQUENCES FROM PUBLIC;
GRANT SELECT ON harness_bootstrap.identity TO <fixture_role>;
GRANT SELECT, UPDATE ON synthetic_throttle.control TO <fixture_role>;
GRANT SELECT, UPDATE ON synthetic_throttle.bindings TO <fixture_role>;
GRANT SELECT, INSERT, UPDATE ON synthetic_throttle.windows TO <fixture_role>;
GRANT EXECUTE ON FUNCTION synthetic_throttle.valid_window(smallint, bigint[]) TO <fixture_role>;
GRANT EXECUTE ON FUNCTION synthetic_throttle.reserve_attempt(text, integer, bytea, bytea, text, text, bigint, boolean, boolean, boolean, text) TO <fixture_role>;
GRANT SELECT ON harness_bootstrap.identity TO <maintenance_role>;
GRANT SELECT, UPDATE ON synthetic_throttle.control TO <maintenance_role>;
GRANT SELECT, UPDATE, DELETE ON synthetic_throttle.windows TO <maintenance_role>;
GRANT EXECUTE ON FUNCTION synthetic_throttle.cleanup(bigint, bigint, integer, text, text, text, boolean, boolean) TO <maintenance_role>;
```

These are proposed table-level grants for the current SECURITY INVOKER functions,
not proven minimum column grants. Row locks and test mutations require UPDATE;
cleanup needs DELETE and admission needs INSERT. The separately controlled
maintenance role has table-level DELETE, capable of bypassing cleanup's trust and
expiry checks. Grants do not enforce that policy. No narrower native DELETE grant
is proposed without RLS or SECURITY DEFINER; independently audit this residual risk.
UPDATE on windows is proposed because cleanup locks rows FOR UPDATE. It also permits
direct mutation and is a further residual risk. Neither role has sequence grants;
no sequences are expected. Both have zero role memberships, including no SET ROLE
path, and no administrative flags. PUBLIC and default privileges must be revoked
globally and per fixture schema as applicable; verify effective rights after bootstrap.
The independent maintenance process must check exact case identity, role/owner,
generation, writer, time and freshness evidence before any mutation, and refuse
ambiguous results. It is not implemented; its credential must never enter the
fixture process, environment, command line, files available to it, or logs.
The fixture lacks CREATE on database/schema, TRUNCATE, REFERENCES and TRIGGER,
and owns nothing. Revoke PUBLIC CONNECT/TEMPORARY on every case database and
unneeded PUBLIC schema privileges, default grants, role membership and indirect
grants; inspect effective rights including PUBLIC and predefined roles. Disallow
database/schema CREATE and TEMP, large-object rights, extension creation and
cross-case access; independently verify no effective ability to SET ROLE to an
owner or privileged role. PostgreSQL catalogs, pg_blocking_pids and built-in
function rights need separate version-specific minimal-grant validation.

The placeholders cannot safely be interpolated as SQL text. A later reviewed
provisioner must validate nonce/ordinal bounds and use identifier-aware quoting,
parameters for data, and explicit exact inventories. A database owner role and
bootstrap principal must be concretely selected and shown non-impersonable before
the design is runnable. Restrict bootstrap exposure and inspect ownership/ACLs for
all schemas, tables, indexes, functions, operators, types, extensions, triggers,
default ACLs, role memberships and grants, including unexpected objects. Fail
closed if inventory visibility or baseline/system catalog assumptions are unclear.

## Fixture isolation and reset

No runner reset command is granted. Each test receives a new case database, role
and initially empty pre-created fixture; test processes may connect only to their
assigned case. A failed or interrupted case is abandoned, never retried in place.
The old `setUp` TRUNCATE and control/binding reset and `initialize` DDL have been
removed. The current test setup refuses every case until an independently verified
case allocator exists; existing tests that mutate control
or bindings must use their own fresh case. Two-connection tests use the same
case role/database, with a separate provisioned case per test. This is a design,
not an implemented test runner. No SECURITY DEFINER helper is introduced. Such a
helper would execute with owner authority and could permit arbitrary reset or
search-path/ownership abuse; it would require a narrow API, fixed search path,
strict validation, revoked PUBLIC EXECUTE, independent audit and separate
approval. It is unnecessary for this per-case design.

## Independent inspection and teardown contract

The future lifecycle controller must accept only a signed/immutable run record
created before provisioning, never an arbitrary connection string, name or target.
The record binds nonce, unique run ID, full immutable container ID, image digest
and PostgreSQL version, exact dedicated volume ID plus lifecycle ownership,
loopback-only host address and port, case database/role IDs and owners, expected
object/ACL inventory, writer/generation, and monotonic lifecycle state. Independent
read-only inspection from the runtime/host and a separate database verifier must
compare actual resource IDs, image, mounts, exclusive volume attachment, network,
role flags/memberships, privileges, objects and marker to the record. Labels or
operator assertions alone are insufficient. Verify independent provenance and
protect the record and inspection channels from the fixture principal.

The intended enforcement mechanism is a separate teardown controller, inaccessible
to the runner, that atomically consumes a one-use teardown authorization for the
exact run record; obtains fresh independent runtime and database observations;
checks exact IDs, ownership, generation, writer and permitted lifecycle state;
requires separate affirmative operator time/freshness conditions; and acquires an
exclusive lifecycle lease/fences new test access. Immediately before **each**
destructive operation it rechecks the exact full ID and ownership/mount mapping.
It removes only the matching whole container and then only its verified dedicated
volume. Any missing, stale, contradictory, unverifiable or changed evidence,
unknown operation outcome, unexpected attachment, inability to obtain a lease or
incomplete state causes refusal and manual review, with no fallback by name.
Independent observations and operator conditions are both required; neither
establishes real clock continuity, latest-state recovery, or exclusive primary
fencing by itself. State changes between inspection and deletion, runtime API
identity semantics and controller compromise remain unresolved; implement and
independently test fencing and rechecks before relying on this contract.

Permitted normal state transition is `NEW -> BOOTSTRAPPED -> TESTING -> STOPPED
-> TEARDOWN_AUTHORIZED -> REMOVED`, with independent durable observations at each
step. Partial bootstrap, interrupted tests, timeout, lost connection, ambiguous
commit, stale resources, repeated invocation, failed verification or unexpected
state enter `REVIEW_REQUIRED`; no retries, reset or deletion. A partial bootstrap
may lack a database marker, generation or writer: the normal teardown gate then
cannot pass, and resources remain for independently authorized manual review.
No automatic cleanup or force-delete exception is defined. Teardown itself needs
separate explicit approval, and runner code contains no lifecycle delete command.

## Existing implementation gap

Current `validate_server_identity` and SQL guard require the fixture to own the
database; `verify_target` expects fixture-owned objects. Both contradict this proposal.
The case allocator and independent maintenance process are not implemented. Existing lifecycle
validation accepts caller assertions and checks formats rather than independently
verified equality, lifecycle transitions, image version or full object inventory.
These must be redesigned, not merely toggled. `EXECUTION_BLOCKED` stays true.
No PostgreSQL parsing, grants, race handling, authentication, database/container
isolation or teardown has been validated by offline text tests.
