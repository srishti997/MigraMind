# PostgreSQL SQL shape — DESIGN ONLY, NOT APPLIED OR EXECUTABLE

This is a review artifact, **not a migration or deployable SQL script**. Angle
brackets are intentional unresolved placeholders. No driver/connection/parser
executes this document. Text-shape tests check ordering and required clauses,
not PostgreSQL syntax, isolation, lock acquisition, grants, durability or speed.

## Required proposed objects

```sql
-- DDL SHAPE ONLY. Do not execute or paste into an application database.
CREATE TABLE <dedicated_control> (
  singleton_id smallint PRIMARY KEY CHECK (singleton_id = 1),
  policy_version integer NOT NULL,
  key_codec_version integer NOT NULL,
  admission_generation text NOT NULL,
  approved_writer_hint text NOT NULL,
  state text NOT NULL CHECK (state IN ('READY', 'QUARANTINED')),
  last_db_ms bigint NOT NULL CHECK (last_db_ms >= 0),
  max_keys integer NOT NULL CHECK (max_keys BETWEEN 2 AND 10000),
  key_count integer NOT NULL CHECK (key_count BETWEEN 0 AND max_keys)
);
CREATE TABLE <dedicated_windows> (
  scope_rank smallint NOT NULL CHECK (scope_rank IN (0, 1)),
  key_digest bytea NOT NULL CHECK (octet_length(key_digest) = 32),
  times_ms bigint[] NOT NULL,
  expires_at_ms bigint NOT NULL,
  PRIMARY KEY (scope_rank, key_digest),
  CHECK (cardinality(times_ms) BETWEEN 1 AND CASE WHEN scope_rank = 0 THEN 30 ELSE 10 END),
  CHECK (array_ndims(times_ms) = 1 AND array_lower(times_ms, 1) = 1),
  CHECK (array_position(times_ms, NULL) IS NULL),
  CHECK (<reviewed_sorted_nonnegative_bounded_array_predicate>),
  CHECK (expires_at_ms = times_ms[cardinality(times_ms)] + 900000)
);
CREATE INDEX <expiry_index> ON <dedicated_windows> (expires_at_ms);
```

Required additional invariants: fixed reviewed policy/codec/generation and writer
binding; each element fits bigint with 900000 addition headroom, nondecreasing
order, and no existing event later than committed control high-water. Cross-row
count/high-water consistency requires transaction validation and bounded primary
reconciliation, not an unsupported cross-table CHECK. No committed empty key
or missing-control auto-initialization. The unresolved predicate needs actual
database/helper design before migration approval. Role/grant and schema-readiness
review are required; no public DML, health/session fields or credentials here.

## Admission transaction shape

Applicable real middleware/body/session/Origin/CSRF guards run **before** this
transaction. End only a preliminary read-only ORM transaction. Bootstrap and
protected reauthentication retain their documented distinct guards; this model
covers login/registration only. Primary-only routing and health evidence are
requirements, not proof established by these diagnostic queries.

```sql
-- BEGIN ADMISSION SHAPE
BEGIN ISOLATION LEVEL READ COMMITTED;
SET LOCAL lock_timeout = '250ms';
SET LOCAL statement_timeout = '1000ms';
SELECT pg_is_in_recovery(), current_setting('transaction_read_only');
-- Assert verified designated writer, not merely writable/currently promoted.
-- LOCK 1: applicable bindings, stable ascending ID; absent/bad binding fails guards.
SELECT <binding_columns> FROM <existing_session_binding>
 WHERE id = ANY(<server_binding_ids>) ORDER BY id FOR SHARE;
-- LOCK 2: every conforming admission/creation/deletion follows this gate.
SELECT <control_columns> FROM <dedicated_control>
 WHERE singleton_id = 1 FOR UPDATE;
-- LOCK 3: existing requested keys only, ordered scope 0 (IP), then 1 (account).
SELECT scope_rank, key_digest, times_ms, expires_at_ms FROM <dedicated_windows>
 WHERE (scope_rank, key_digest) IN (<server_derived_keys>)
 ORDER BY scope_rank, key_digest FOR UPDATE;
-- RECHECK_ACTUAL_GUARDS_AFTER_WAITS; preserve existing session expiry clock.
SELECT floor(extract(epoch FROM clock_timestamp()) * 1000)::bigint AS decision_ms;
-- VALIDATE_PRIMARY_GENERATION_STATE_AND_TIME; invalid/backward -> quarantine outcome.
-- RETAIN_EVENTS_STRICTLY_GREATER_THAN decision_ms - 900000; equal cutoff expires.
-- IF_EITHER_FULL: no window writes/inserts; metadata-only high-water may commit.
-- ELSE_CHECK_CAPACITY; missing keys remain in memory until BOTH budgets allow.
-- INSERT_MISSING_FIRST_REAL_ADMISSIONS_WITH_UNIQUE_PK;
-- UPDATE_EXISTING_BOTH_WINDOWS_AND_EXPIRES;
-- UPDATE_RETAINED_COUNT_AND_HIGH_WATER;
COMMIT;
-- END ADMISSION SHAPE
```

These IF branches are **not implemented SQL**. If quarantine is required, commit
only approved control metadata and return unavailable; an unconfirmed metadata
commit is not proof of global quarantine. Known exhaustion returns generic 429,
retry 900; storage/time/primary/capacity uncertainty returns proposed generic 503.
No password work or health/user/session write occurs under throttle locks. Real
auth work runs only after confirmed reservation commit and does not refund it.
Confirmed abort rolls back the entire staged pair. Unknown commit outcome never
automatically retries or refunds. No `ON CONFLICT` overwriting another admission.
No `SKIP LOCKED`, replica/cached absence, `now()` transaction-start sample or
fixed time-bucket arithmetic is an admission substitute.

## Independent maintenance transaction shape

```sql
-- BEGIN MAINTENANCE SHAPE (separate commit; not rollback-coupled to admission)
BEGIN ISOLATION LEVEL READ COMMITTED;
SET LOCAL lock_timeout = '250ms';
SET LOCAL statement_timeout = '1000ms';
SELECT <control_columns> FROM <dedicated_control>
 WHERE singleton_id = 1 FOR UPDATE;
SELECT floor(extract(epoch FROM clock_timestamp()) * 1000)::bigint AS candidate_ms;
SELECT <at_most_100_expired_keys> FROM <dedicated_windows>
 WHERE expires_at_ms <= <candidate_ms> ORDER BY expires_at_ms, scope_rank, key_digest
 LIMIT 100;
SELECT <candidate_rows> FROM <dedicated_windows>
 WHERE (scope_rank, key_digest) IN (<candidate_keys>)
 ORDER BY scope_rank, key_digest FOR UPDATE;
SELECT floor(extract(epoch FROM clock_timestamp()) * 1000)::bigint AS cleanup_ms;
-- REVALIDATE_TIME_AND_TRUST; do not purge while QUARANTINED.
-- DELETE_ONLY_VALID_CANDIDATES_STILL_EXPIRED_AT cleanup_ms;
-- UPDATE_COUNT_BY_ACTUAL_DELETIONS_AND_HIGH_WATER;
COMMIT;
-- END MAINTENANCE SHAPE
```

No session locks after control, unbounded purge, active eviction or automatic
repair/reset. The global gate serializes missing-key creation, reservations,
capacity accounting and cleanup even for unrelated identifiers. That cost is
intentional in this baseline, not PostgreSQL throughput evidence. Later actual
PG tests must measure lock queue/hold time, pool waits, aborts and tail latency
at 0/1000/10000 rows and final-slot/capacity races across processes.

## Time, recovery and portability caveats

This uses PostgreSQL-specific arrays, row locks, system functions and time
expression. It is not portable SQLite SQL. READ COMMITTED plus a Python
permutation model is not a proof of PostgreSQL MVCC, missing-row locks or commit
durability. Real PostgreSQL parser, session-schema, isolation, lock ordering,
deadlock, pool, primary-only and restoration/failover tests remain required.

Forward database wall-time is trusted only when explicitly attested; an
unobserved step can expire quotas early. Backward observations quarantine.
Writable/recovery/startup hints and copied generation do not prove newest state
or exclusive writership. Failover/restoration requires old-writer fencing,
verified state or full-window trusted quarantine. No recovery/clock threshold,
server, migration, production policy, bootstrap adapter or HTTP route is provided.
