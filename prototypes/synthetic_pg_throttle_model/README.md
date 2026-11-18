# Synthetic PostgreSQL policy model and SQL-shape review

**Not a PostgreSQL limiter, adapter, migration or authentication component.**
Python 3.13 standard library only. There is no database driver/connection, SQL
execution, network, dependency install, environment database URL, persistent
counter file, service or live application import. The existing SQLite owner and
legacy prototypes are separate and unchanged.

From repository root:

```text
python -B -m unittest discover -s prototypes/synthetic_pg_throttle_model -p test_model.py -v
```

`model.py` uses in-memory synthetic state, injected integer time and copies to
represent atomic commit/rollback. `test_model.py` reads only the adjacent source
document `SQL_SHAPE.md` for text assertions. No SQL is parsed or applied.

## Modeled behavior

- Exact rolling `(time_ms - 900000, time_ms]`; equal cutoff expires. 30/IP and
  10/strip-lowercase account, shared login/register keys, duplicate same-ms
  attempts count separately. Fixed buckets are explicitly rejected by a test.
- Both budgets append together or neither does. Denial creates no missing key
  and changes no counters, though it may advance control high-water metadata.
  Success/wrong-password/duplicate-registration are all valid submitted attempts
  to be charged; actual password work is not implemented. No refund/reset API.
- Missing keys are conceptual empty windows protected by the **assumed** control
  gate; no stored placeholder. Capacity counts retained rows. Independent bounded
  cleanup deletes only valid expired rows and survives later denial/abort.
- Injected pre/post-wait guards, primary availability/writability, time trust,
  generation/writer and snapshot freshness determine fail-closed outcomes.
  Unknown commit can retain a charge without reporting success or auto-retrying.
- Backward observations quarantine without charges. Changed epoch or known
  untrusted time/snapshot quarantines without resetting quotas. No recovery,
  skew threshold or automatic transition back to READY is provided.

Input restrictions accept only documentation IP ranges and synthetic
`example.test` identifiers. State stores domain-separated SHA-256 digest bytes,
not raw addresses, passwords, cookies, tokens or health information. Hashes are
dictionary-guessable pseudonyms, not anonymity/encryption. No model state is
persisted or logged by the implementation.

## Explicit assumptions and limits

`Evidence` is supplied by tests, **not a detector or proof**. Setting
`time_trusted=True` makes a forward step age windows: the model intentionally
shows this. Structurally valid stale snapshots also pass if freshness is falsely
asserted. Real failover, unique writership, replication/RPO, restoration freshness
and trustworthy recovery elapsed time remain outside the model. A failed
quarantine commit does not establish global quarantine.
Default `Evidence()` denotes a pre-verified **synthetic fixture assumption**;
it does not establish trust in any actual server or discover an endpoint.

The lock trace describes intended order: session IDs → control → existing budget
keys → post-wait guard/time. It acquires **no locks**. The bounded permutation
helper explores all serial orders for up to four eligible requests; it does not
run threads, implement a scheduler/MVCC or reproduce READ COMMITTED. It assumes
the global control lock serializes real PostgreSQL transactions. Missing-row
creation, row locking, deadlocks, connection pools, replica routing, commit/WAL
durability and SQL validity require actual later PostgreSQL tests.

The model validates its complete bounded state for clarity. The PostgreSQL
proposal instead reads requested keys/control with separate reconciliation;
model corruption detection is not proof of identical production coverage.
Reconstructing a Model from a snapshot is a logical example, not a disk/process
restart guarantee. Guards are booleans, not real Origin/CSRF/session validation.
Only login/register are implemented here; anonymous bootstrap and protected
reauthentication remain specification requirements, not tested model features.

`SQL_SHAPE.md` contains intentional `<placeholders>`, unresolved constraints and
branch comments. It is non-executable documentation. Text tests do not certify
PostgreSQL syntax or planner lock order. READ COMMITTED/primary clock behavior,
array constraints, permissions and transaction application code are unvalidated.

## Global gate and later measurements

The proposed control row serializes every admission and cleanup, including
unrelated accounts. It protects gap creation/count/time but is a hot row. Model
runtime measures **nothing** about database throughput or latency.

Later, only with approval of a disposable PostgreSQL target: run at least 100
bounded four-contender races for IP/account/absent-key/capacity slots, retries
off, with controlled lock waits and faults. Record lock hold/queue/pool wait,
abort/error rates, p50/p95/p99 and CPU/RSS at 0/1000/10000 retained rows, comparing
one and multiple worker connections. Phase 9G's p95≤100ms/p99≤250ms and 128MiB
additional RSS remain **proposed owner-review targets**, not measured results.
Avoid inferring scaling or correctness from the Python permutations or changing
timeouts to hide failures.

Next approval: review unresolved time/primary/recovery/policy assumptions, then
authorize a disposable PostgreSQL SQL/locking test harness separately. No server,
application migration/flag/provider or live integration is included here.
