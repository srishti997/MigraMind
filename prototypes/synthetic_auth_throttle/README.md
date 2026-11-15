# Synthetic SQLite authentication reservation experiment

## Current: monotonic owner authority and hardening

**Synthetic-only; not application authentication.** The approved owner design
supersedes the historical UTC experiment below. Python 3.13 standard library;
no new package, app migration, deployment or existing database path.

```text
python -B -m unittest discover -s prototypes/synthetic_auth_throttle -p test_adapter.py -v
```

`adapter.py` is the current API facade; `authority.py` implements it. Original
UTC implementation/tests are preserved as `legacy_adapter.py` and
`legacy_test_adapter.py` (excluded from current discovery). They are historical
evidence, **never a fallback**. The original three red regression tests remain
byte-for-byte preserved in their task temporary evidence directories; current
tests cover the same defects under the new owner API.

### Ownership, elapsed time and fencing

`SyntheticDatabase()` exclusively creates a new temporary directory and two
owned SQLite files, then spawns one authority process. It never takes a user
database path. One file stores counters; the second supplies a lifetime SQLite
writer lock. No WAL mode is enabled and no existing SQLite file is opened.

Only the authority samples elapsed time, using `time.monotonic_ns()` relative
to its in-memory origin. Workers supply neither wall-clock nor elapsed ticks.
Wall-clock changes cannot age/reset counters. There is no skew tolerance or
UTC high-water heuristic. A negative/decreasing authority tick causes failure
and seals the store; it is not clamped. Under tests, an owner-only manual elapsed
clock advances deterministic time. Workers cannot invoke that administrative
operation, and no real OS clock is changed.

A distinct random epoch binds the owner to the counter file. Epoch alone is
**not** continuity proof:

1. `BEGIN IMMEDIATE` on the separate owner-lock file is held for the owner's
   lifetime. Competing owners cannot acquire it concurrently.
2. The first claim irreversibly changes control state from NEW to ACTIVE in the
   counter DB. If a crash releases the owner lock, another process still refuses
   the already-claimed store. There is no takeover/rebase/reset API.
3. Every cleanup/reservation validates ACTIVE state, matching epoch, schema and
   authenticated data **inside the counter DB's writer transaction**.
4. Controller fencing commits SEALED state and a new fence epoch using the same
   writer lock as reservations. A running stale owner/client then cannot admit.
   An in-flight reservation commits before the fence, or sees the committed
   fence and fails. A failed/busy fence attempt is **not** proof of fencing.

Worker restarts preserve state while the same owner survives. Owner crash,
authority process restart, machine reboot, unavailable authority or lost epoch
continuity fails closed; no elapsed time is inferred from UTC or a fresh
monotonic origin. The old store cannot be resumed, even if the test controller
still has its keys. A new temporary synthetic store is a new experiment, not
recovery of old protection. Host reboot was not physically tested. The design
assumes a trusted OS monotonic source/local filesystem and cooperating synthetic
processes, not a compromised kernel, hostile local administrator or copied-file
rollback attack. Suspend may slow ageing if the platform's monotonic clock
pauses; no wall-clock catch-up is attempted. Cross-platform suspend behavior
and elapsed-clock accuracy remain unverified.

### Internal IPC and privacy

Owned workers contact a temporary **127.0.0.1-only** endpoint in that authority
process. It is bounded local IPC, not an external service or deployed API.
Frames are JSON (no pickle request deserialization), at most 8192 bytes, with
three-second frame/connection deadlines and at most eight active handlers.
Admission handlers still use independent SQLite connections and writer locks.

Fresh per-call nonces, ordered frame numbers, epochs and HMAC-SHA256 authenticate
requests, guard challenges and replies. This prevents a stale/reused endpoint or
replayed old response from falsely confirming authority continuity. Ephemeral
client/admin capabilities are passed only in owned-process memory; they are not
transmitted as plaintext credentials, stored in SQLite, printed or committed.
Transport is authenticated, not encrypted. Workers are trusted capability
holders; this is not isolation from malicious authorized worker code.

Persist only domain-separated hashed documentation IPs/example.test accounts,
bounded timing metadata, epoch/provenance identifiers and authentication tags.
No passwords, session cookies/tokens or health fields exist in this API. A
separate memory-only key authenticates the complete bounded counter/control
snapshot **and schema definitions**. It detects missing/deleted active windows,
in-range count corruption, altered limits/expiry and missing/modified triggers.
It is not encryption, anonymity, general tamper-proof storage or protection
against a privileged process reading memory. Hashes remain dictionary-guessable.

### Accounting, maintenance and safe failure

Exact window `(elapsed_ms - 900000, elapsed_ms]`; equality at cutoff expires.
30/IP and 10/strip-lowercase account, shared login/registration budgets. Both
append in one `BEGIN IMMEDIATE` transaction or neither is charged. This remains
different from live account-limit denial, which still charges IP.

After toy guard recheck under a writer reservation, validate state and commit a
separate bounded cleanup transaction **before** the admission transaction.
Denied/failed admissions cannot undo that cleanup. Recheck the toy guard again
under the admission writer lock. Guards are callbacks, not implementation of
real Origin/CSRF/session protection; live Phase 9A code is unchanged.

Caps: 10000 retained windows, 30/10 timestamps, 1024 JSON characters per row;
delete at most 100 expired rows per maintenance operation. Never evict active
windows. Reconcile and authenticate **all retained rows up to cap+1** before
cleanup or admission, plus schema validation. This bounded scan is deliberate
integrity hardening and a performance cost; deletion of 100 rows does not mean
the entire operation reads only 100. Legitimate expired state is reclaimable;
untrusted expired/active state fails before deletion, without automatic repair.
No background scheduler or secure-erasure/file-shrink guarantee is provided.

SQLite busy wait defaults to 250ms, configurable 0–1000ms. Actual BUSY and
injected LOCKED fail safely; no retry, process-local fallback or unmetered
admission. Failed partial writes roll back both keys; prior cleanup remains
committed. Storage/authority/clock/integrity failure never becomes allowed.
An ambiguous response loss can leave a committed charge; never assume refund.
Commit is the admission linearization point; a completed reservation cannot
authorize a new request after a later fence.

There are no application routes, HTTP status mapping or production flag. No
PostgreSQL/Redis implementation, crash-proof disk durability claim, performance
benchmark, network-filesystem support or live recovery procedure. PostgreSQL
requires different row/ownership locks, primary time, fencing and failover
testing. This prototype deliberately sacrifices owner-restart availability.
Separate integration-design review is required; implementation/deployment is
not approved. Existing public/real-health release blockers remain unchanged.

Current validation on the same Windows host: **32 hardened tests passed**;
**134 selected backend tests passed, one migration test deselected**, including
all 31 Phase 9A guard cases. No executed test failure or timeout. Six preliminary
ownership cases and the initial 31-case run overlap the final suite. Linux,
PostgreSQL, physical reboot/suspend, performance and full application/browser
build checks were not run. Historical results below are separate evidence.

## Historical UTC prototype and earlier blocked-hardening status

Everything below is preserved historical documentation and does not describe
the current owner-backed API. In particular the prior stop is superseded by
explicit approval of this owner design; no old UTC implementation is used as
a fallback.

**Phase 9E status: hardening stopped pending clock-policy approval.** Three new
temporary red regressions reproduce the forward-clock, denial-cleanup and
corrupt-count gaps; none is fixed. The existing 24-test suite still passes and
does not establish the requested hardening. See the
[clock alternatives and exact evidence](../../docs/SHARED_AUTH_THROTTLING_PLAN.md#phase-9e-reproductions-complete-clock-policy-approval-required-2026-11-12).
No skew threshold or new authority/epoch design has been approved. Adapter and
existing tests are unchanged. Do not interpret the historical behavior below as
a fail-closed forward-jump policy or readiness to integrate.

**Not connected to MigraMind authentication.** Python 3.13 standard library only;
no new dependencies, application imports, migrations, environment database URL,
server, CLI input path or real account/password processing. Existing login and
registration still use their original process-local limiter and Phase 9A guards.

Run from the repository root with an available Python 3.13 interpreter:

```text
python -B -m unittest discover -s prototypes/synthetic_auth_throttle -p test_adapter.py -v
```

Each fixture constructs `SyntheticDatabase()`, which exclusively creates a new
`migramind-synthetic-throttle-*` directory under Python's temporary directory.
It owns only `synthetic-auth-throttle.sqlite` and its temporary SQLite journal.
The context/fixture closes connections and child processes before removing that
owned directory. There is no database-path argument. Do not adapt this test to an
existing database, browser profile, backup, export or application deployment.
The tests accept only documentation IP ranges and synthetic `example.test`
identifiers. No credentials, cookies, tokens or health fields are accepted.

## Tables and transactions

- `prototype_control`: singleton marker, schema version 1, last committed clock
  high-water mark, row count, maximum keys and cleanup batch size.
- `prototype_windows`: `(namespace, key_digest)` primary key, bounded JSON list
  of UTC-millisecond admissions and expiry. Namespaces are `ip` and `account`.
- An expiry index supports bounded deletion. Insert/delete triggers maintain the
  row count under a SQL capacity constraint. No application table is present.

Each reservation opens a **new connection**, sets FULL synchronous behavior,
then obtains `BEGIN IMMEDIATE` before reading counters or sampling the clock.
No Python mutex coordinates reservations. Default SQLite rollback-journal mode
is used; no WAL mode, OS setting or existing file is changed. Successful commit
is the admission point. Lock ownership ends before any hypothetical password
work; this prototype does not perform such work.

Both counters must have space: **30/IP and 10/normalized account** in the rolling
window `(now - 900000, now]`. An event exactly 900000ms old expires. Login and
registration share the same keys. On success both counters append once; on
either limit denial neither counter changes, including rollback of maintenance.
`Decision(False, 900)` is an exhausted-budget result, not storage failure.

**Approved Phase 9C deviation:** live code and Phase 9B's proposed compatibility
algorithm charge IP when account rejects. This prototype deliberately makes
the pair all-or-nothing per the Phase 9C requirement. It is not a drop-in
compatible replacement; changing live accounting needs separate approval.

## Bounds, errors and clocks

Default cap: **10000 retained key rows**, each with at most 30 IP or 10 account
timestamps and 1024 JSON characters. Cleanup deletes at most **100 expired
rows** per operation; tests use smaller caps/batches. No active-key eviction,
full-map scan, automatic retry, unmetered fallback or unbounded cleanup loop.
Existing keys can continue without allocation at capacity. Expired rows can
temporarily occupy capacity; explicit bounded `cleanup()` reclaims them.
Physical file pages do not shrink or securely erase on deletion. Caps bound
logical state, not every OS/page-cache/disk allocation or contention cost.

Default SQLite busy timeout is **250ms**, configurable only within **0–1000ms**
for these tests. `StorageBusy` (a `StorageUnavailable` subtype) maps real
SQLITE_BUSY and SQLITE_LOCKED codes to a safe failure; LOCKED mapping is tested
by injection, actual writer contention produces BUSY. Missing/unreadable or
malformed storage, bad marker, clock validation, capacity and transaction errors
raise `StorageUnavailable`; they never report an admission. No raw SQLite error
is exposed by the adapter. Failure after a partial write rolls back both keys.
No HTTP response mapping is integrated; generic 503 is a possible future policy,
not a change to the application. An ambiguous failure after a real commit could
retain a charge; do not assume a transport failure refunds it or auto-retry it.

Clock is sampled after obtaining the writer reservation. The default uses UTC
milliseconds; tests inject deterministic integer clocks. A persistent high-water
mark clamps backward movement. Large forward jumps still expire windows and a
future high-water mark may prolong lockout after clock correction. No drift
detector, cross-host time authority or production recovery policy is implemented.
No claim that this is as clock-jump-resistant as the live monotonic clock.

## Privacy and guard contract

Email normalization is strip/lowercase with basic syntax validation. Canonical
documentation IPv4/IPv6 and normalized accounts are domain-separated SHA-256
digests; raw identifiers are not persisted. Hashes are **pseudonymous**, not
anonymous: candidate emails/IPs can be guessed offline. They are not HMACs and
no new encryption/key-management claim is made. The random temporary store
marker is a synthetic provenance check, not an authentication credential,
encryption key or protection against a hostile local process. Handles should be
passed only to owned test workers; this is not a sandbox for hostile callers.

`reserve(..., guard=...)` requires a toy callback returning exactly `True` before
opening storage and again after the writer reservation. A rejected check raises
`GuardRejected` without accounting. This models intended order only; it does
**not** implement Origin/CSRF/session validation. Future integration must reuse
actual guards, revalidate authoritative sessions after lock waits and avoid
holding preliminary read transactions during SQLite lock upgrades. Existing
backend guard-order tests remain the evidence for real application protection.

## Coverage and limits

Tests use independent connections, adapter objects, four synchronized threads
and spawned processes. Separate account/IP final-slot races admit exactly one
of four contenders; a later fresh process sees durable exhaustion. An explicit
probe verifies that a second connection cannot acquire `BEGIN IMMEDIATE` during
the first transaction. No sleeps are used to assert races. Startup/barrier/join
waits are bounded; failures terminate only the test's own children.

Other checks cover fresh schema, no reinitialization, limits/action sharing,
normalization, exact/partial ageing, rollback injection, actual BUSY, injected
LOCKED, corrupt data, wrong marker, missing-file refusal, capacity/cleanup,
privacy and guard order. These are bounded functional checks, not a throughput,
latency, saturation, power-loss or malicious-user benchmark.

SQLite serializes writers across the whole file and may delay diary/session
writes in a future integration. This synthetic store contains no such tables,
so it does not measure that interference. PostgreSQL cannot reuse
`BEGIN IMMEDIATE`; row locks, absent-row races, capacity allocation, primary
clock, deadlocks/failover and transaction integration need their own adapter and
tests. Redis, hosting and multi-host/network-filesystem SQLite are not validated.

No startup guard, schema migration, application flag, enrollment change,
collection/research limiter change, proxy trust change or auth activation is
provided. Future route integration and accounting-policy decisions require
separate approval. Public/real-health release blockers remain unchanged.
