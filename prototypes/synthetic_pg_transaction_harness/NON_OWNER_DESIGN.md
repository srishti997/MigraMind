# Phase 9I-D non-owner fixture and teardown design v1

**UNAPPLIED DESIGN ONLY.** The SQL fragments below contain intentional placeholders
and are not a script, migration, provisioning instructions, or authorization to
execute. No target exists as a result of this document. The current harness remains
blocked and is incompatible with this design. No teardown implementation exists.

## Authorities and ownership

| Authority | Scope | Ownership and powers |
| --- | --- | --- |
| Bootstrap | Separately controlled disposable-container setup principal, including the minimum cluster-admin authority needed only during setup | Creates fresh container-local roles and databases; owns every test database, `harness_bootstrap` and `synthetic_throttle` schema, marker, control, bindings and windows tables, all associated indexes/constraints, and the three fixture functions. Not available to runner. |
| Fixture | Unique restricted LOGIN per test database, no memberships and NOINHERIT | Owns no database, schema, table, index, function, role, container or volume. Only explicitly listed grants in its own test database. No container-runtime socket/API or bootstrap/teardown credentials. |
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
CREATE DATABASE <case_database> OWNER <bootstrap_owner>;
REVOKE ALL ON DATABASE <case_database> FROM PUBLIC;
GRANT CONNECT ON DATABASE <case_database> TO <fixture_role>;
-- Bootstrap pre-creates the fixed, owned marker and schema.sql objects.
REVOKE ALL ON SCHEMA harness_bootstrap, synthetic_throttle FROM PUBLIC;
GRANT USAGE ON SCHEMA harness_bootstrap, synthetic_throttle TO <fixture_role>;
REVOKE ALL ON ALL TABLES IN SCHEMA harness_bootstrap, synthetic_throttle FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA synthetic_throttle FROM PUBLIC;
GRANT SELECT ON harness_bootstrap.identity TO <fixture_role>;
GRANT SELECT, UPDATE ON synthetic_throttle.control TO <fixture_role>;
GRANT SELECT, UPDATE ON synthetic_throttle.bindings TO <fixture_role>;
GRANT SELECT, INSERT, UPDATE, DELETE ON synthetic_throttle.windows TO <fixture_role>;
GRANT EXECUTE ON FUNCTION synthetic_throttle.valid_window(smallint, bigint[]) TO <fixture_role>;
GRANT EXECUTE ON FUNCTION synthetic_throttle.reserve_attempt(text, integer, bytea, bytea, text, text, bigint, boolean, boolean, boolean, text) TO <fixture_role>;
GRANT EXECUTE ON FUNCTION synthetic_throttle.cleanup(bigint, bigint, integer, text, text, text, boolean, boolean) TO <fixture_role>;
```

These are proposed table-level grants for the current SECURITY INVOKER functions,
not proven minimum column grants. Row locks and test mutations require UPDATE;
cleanup needs DELETE and admission needs INSERT. DELETE is deliberately broad
within the one disposable windows table; it is not authorization for other data.
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
The current `setUp` TRUNCATE and control/binding reset, and `initialize` DDL,
must be removed in a later implementation; existing tests that mutate control
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
database; `verify_target` expects fixture-owned objects; `initialize` issues DDL;
tests TRUNCATE and reset state. All contradict this proposal. Existing lifecycle
validation accepts caller assertions and checks formats rather than independently
verified equality, lifecycle transitions, image version or full object inventory.
These must be redesigned, not merely toggled. `EXECUTION_BLOCKED` stays true.
No PostgreSQL parsing, grants, race handling, authentication, database/container
isolation or teardown has been validated by offline text tests.
