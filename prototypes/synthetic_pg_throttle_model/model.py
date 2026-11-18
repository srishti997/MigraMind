"""In-memory specification model, NOT a database or authentication adapter."""
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import ipaddress
from itertools import permutations

WINDOW_MS = 900_000
LIMITS = {0: 30, 1: 10}
MAX_MS = 2**63 - 1 - WINDOW_MS


class Status(str, Enum):
    ALLOWED = 'allowed'
    LIMITED = 'limited'
    UNAVAILABLE = 'unavailable'
    GUARD_REJECTED = 'guard_rejected'


@dataclass(frozen=True)
class Result:
    status: Status
    reason: str
    retry_after_seconds: int | None = None


@dataclass(frozen=True)
class Evidence:
    """Injected assertions, not measurements or proof of a real primary."""
    available: bool = True
    primary: bool = True
    writable: bool = True
    time_trusted: bool = True
    freshness_verified: bool = True
    generation: str = 'synthetic-generation-1'
    writer: str = 'synthetic-primary-1'


@dataclass(frozen=True)
class Window:
    stamps: tuple[int, ...]
    expires_ms: int


@dataclass
class State:
    generation: str = 'synthetic-generation-1'
    writer: str = 'synthetic-primary-1'
    mode: str = 'READY'
    high_water_ms: int = 0
    key_count: int = 0
    max_keys: int = 10_000
    windows: dict = field(default_factory=dict)


class Time:
    """Deterministic stand-in for a sample taken after locks, never OS time."""
    def __init__(self, value=0): self.value = value
    def read(self): return self.value


def keys(ip, account):
    if not isinstance(ip, str) or not isinstance(account, str) or not 3 <= len(account) <= 254:
        raise ValueError('Synthetic identifiers required')
    address = ipaddress.ip_address(ip)
    if not any(address in ipaddress.ip_network(n) for n in
               ('192.0.2.0/24', '198.51.100.0/24', '203.0.113.0/24', '2001:db8::/32')):
        raise ValueError('Documentation IP ranges only')
    account = account.strip().lower()
    if (account.count('@') != 1 or not all(account.split('@')) or any(c.isspace() for c in account)
            or account.split('@')[1] != 'example.test'):
        raise ValueError('Synthetic example.test accounts only')
    return ((0, hashlib.sha256(('synthetic-ip:' + str(address)).encode()).digest()),
            (1, hashlib.sha256(('synthetic-account:' + account).encode()).digest()))


class Model:
    """Atomic copies + SERIAL ORDER ASSUMPTION, not PostgreSQL READ COMMITTED."""
    def __init__(self, clock, state=None):
        self.clock = clock
        self.state = deepcopy(state) if state is not None else State()
        self.trace = []

    def snapshot(self): return deepcopy(self.state)

    def _valid(self):
        s = self.state
        if (not isinstance(s, State) or s.mode not in ('READY', 'QUARANTINED')
                or not isinstance(s.generation, str) or not s.generation.startswith('synthetic-')
                or not isinstance(s.writer, str) or not s.writer.startswith('synthetic-')
                or type(s.high_water_ms) is not int or not 0 <= s.high_water_ms <= MAX_MS
                or type(s.max_keys) is not int or not 2 <= s.max_keys <= 10000
                or type(s.key_count) is not int or not isinstance(s.windows, dict)
                or s.key_count != len(s.windows) or not 0 <= s.key_count <= s.max_keys):
            return False
        for key, row in s.windows.items():
            if (not isinstance(key, tuple) or len(key) != 2 or type(key[0]) is not int or key[0] not in LIMITS
                    or not isinstance(key[1], bytes) or len(key[1]) != 32 or not isinstance(row, Window)
                    or not isinstance(row.stamps, tuple) or not 1 <= len(row.stamps) <= LIMITS[key[0]]
                    or any(type(v) is not int or not 0 <= v <= s.high_water_ms for v in row.stamps)
                    or row.stamps != tuple(sorted(row.stamps)) or type(row.expires_ms) is not int
                    or row.expires_ms != row.stamps[-1] + WINDOW_MS):
                return False
        return True

    @staticmethod
    def _unavailable(reason): return Result(Status.UNAVAILABLE, reason)

    def _quarantine(self, reason, fault):
        if fault == 'quarantine_commit': return self._unavailable('quarantine_unconfirmed')
        candidate = self.snapshot()
        candidate.mode = 'QUARANTINED'
        self.state = candidate
        return self._unavailable(reason)

    def _gate(self, evidence, fault):
        if (not isinstance(evidence, Evidence) or any(type(getattr(evidence, name)) is not bool for name in
                ('available','primary','writable','time_trusted','freshness_verified'))):
            return self._unavailable('invalid_evidence')
        if not evidence.available: return self._unavailable('storage_unavailable')
        if not evidence.primary or not evidence.writable: return self._unavailable('not_writable_primary')
        if not self._valid(): return self._unavailable('untrusted_state')
        if self.state.mode != 'READY': return self._unavailable('quarantined')
        if (evidence.generation != self.state.generation or evidence.writer != self.state.writer
                or not evidence.time_trusted or not evidence.freshness_verified):
            return self._quarantine('untrusted_time_primary_or_snapshot', fault)
        return None

    def _sample(self, fault, minimum=None):
        try: stamp = self.clock.read()
        except Exception: return None, self._unavailable('time_unavailable')
        if type(stamp) is not int or not 0 <= stamp <= MAX_MS:
            return None, self._quarantine('invalid_time', fault)
        if stamp < self.state.high_water_ms or (minimum is not None and stamp < minimum):
            return None, self._quarantine('backward_time', fault)
        return stamp, None

    def reserve(self, *, action, ip, account, evidence=Evidence(), guards_ok=True,
                guards_after_wait=True, session_ids=(1,), fault=None):
        if action not in ('login', 'register'): raise ValueError('Synthetic login/register only')
        selected = keys(ip, account)  # Validated synthetic inputs, not HTTP body handling.
        if (not isinstance(session_ids, tuple) or any(type(v) is not int or v <= 0 for v in session_ids)
                or len(set(session_ids)) != len(session_ids)):
            raise ValueError('Synthetic binding IDs required')
        self.trace = ['preliminary_guards']
        if not guards_ok: return Result(Status.GUARD_REJECTED, 'preliminary_guard')
        # ASSUMPTION: the caller has selected primary-only routing and holds these
        # locks in this order for the whole modeled transaction. No mutex/DB exists.
        self.trace += [f'session:{i}' for i in sorted(session_ids)] + ['control:for_update']
        self.trace += [f'budget:{k[0]}:for_update' if k in self.state.windows else f'budget:{k[0]}:missing_under_control'
                       for k in sorted(selected)] if isinstance(self.state, State) and isinstance(self.state.windows, dict) else []
        self.trace.append('recheck_guards')
        if not guards_after_wait: return Result(Status.GUARD_REJECTED, 'guard_after_wait')
        failure = self._gate(evidence, fault)
        if failure is not None: return failure
        self.trace.append('primary_time_after_locks')
        stamp, failure = self._sample(fault)
        if failure is not None: return failure
        if fault in ('deadlock', 'pool', 'lock_timeout', 'statement_timeout'):
            return self._unavailable('confirmed_abort_or_unavailable')
        candidate = self.snapshot()
        windows = [tuple(v for v in candidate.windows[k].stamps if v > stamp - WINDOW_MS)
                   if k in candidate.windows else () for k in selected]
        if any(len(values) >= LIMITS[k[0]] for k, values in zip(selected, windows)):
            if fault == 'before_commit': return self._unavailable('confirmed_rollback')
            candidate.high_water_ms = stamp  # Metadata only; no window pruning/creation.
            self.state = candidate
            return Result(Status.LIMITED, 'budget_exhausted', 900)
        missing = sum(k not in candidate.windows for k in selected)
        if candidate.key_count + missing > candidate.max_keys:
            return self._unavailable('capacity')
        for index, (key, values) in enumerate(zip(selected, windows)):
            candidate.windows[key] = Window(values + (stamp,), stamp + WINDOW_MS)
            if index == 0 and fault == 'after_ip_write': return self._unavailable('confirmed_rollback')
        candidate.key_count += missing
        candidate.high_water_ms = stamp
        if fault == 'before_commit': return self._unavailable('confirmed_rollback')
        self.state = candidate
        self.trace.append('commit_pair')
        if fault == 'lost_commit_ack': return self._unavailable('commit_unknown_no_retry')
        return Result(Status.ALLOWED, 'committed')

    def cleanup(self, *, evidence=Evidence(), batch=100, fault=None):
        if type(batch) is not int or not 1 <= batch <= 100: raise ValueError('Bounded batch required')
        self.trace = ['control:for_update']
        failure = self._gate(evidence, fault)
        if failure is not None: return failure, 0
        first, failure = self._sample(fault)
        if failure is not None: return failure, 0
        selected = sorted((k for k, v in self.state.windows.items() if v.expires_ms <= first),
                          key=lambda k: (self.state.windows[k].expires_ms, k))[:batch]
        self.trace += [f'budget:{k[0]}:for_update' for k in sorted(selected)]
        self.trace.append('primary_time_after_locks')
        stamp, failure = self._sample(fault, minimum=first)
        if failure is not None: return failure, 0
        candidate = self.snapshot()
        for key in selected:
            if candidate.windows[key].expires_ms <= stamp: del candidate.windows[key]
        removed = len(self.state.windows) - len(candidate.windows)
        candidate.key_count -= removed
        candidate.high_water_ms = stamp
        if fault == 'before_commit': return self._unavailable('confirmed_rollback'), 0
        self.state = candidate
        self.trace.append('commit_maintenance')
        return Result(Status.ALLOWED, 'maintenance_committed'), removed


def serial_orderings(seed, requests, clock_value=0):
    """Explore <=4 request permutations, NOT threads, lock scheduling or PG MVCC."""
    if not 1 <= len(requests) <= 4: raise ValueError('Bounded scenario only')
    outcomes = []
    for order in permutations(range(len(requests))):
        model = Model(Time(clock_value), seed)
        results = tuple(model.reserve(**requests[i]) for i in order)
        outcomes.append((order, results, model.snapshot()))
    return outcomes
