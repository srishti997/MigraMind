# Phase 9I-D non-owner fixture and teardown design v1

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
