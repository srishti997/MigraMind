"""Owned synthetic elapsed-clock authority. No application imports or user paths."""
from contextlib import closing, contextmanager
from dataclasses import dataclass, field, replace
from concurrent.futures import ThreadPoolExecutor
import hashlib
import hmac
import json
import multiprocessing
import os
from pathlib import Path
import secrets
import socket
import sqlite3
import tempfile
import threading
import time

WINDOW_MS = 900_000
LIMITS = {'ip': 30, 'account': 10}
MAX_CLOCK = 2**53 - WINDOW_MS


class StorageUnavailable(Exception):
    def __init__(self): super().__init__('Synthetic authority/storage unavailable; no admission confirmed')


class StorageBusy(StorageUnavailable): pass
class ContinuityLost(StorageUnavailable): pass


class GuardRejected(Exception):
    def __init__(self): super().__init__('Synthetic guard rejected')


@dataclass(frozen=True)
class Decision:
    allowed: bool
    retry_after_seconds: int | None = None


def _digest(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


@dataclass(frozen=True)
class SyntheticHandle:
    directory: str
    marker: str = field(repr=False)
    endpoint: tuple | None = None
    epoch: str = field(default='', repr=False)
    capability: str = field(default='', repr=False)

    @property
    def path(self):
        directory = Path(self.directory)
        if (not directory.is_absolute() or directory.is_symlink()
                or not directory.name.startswith('migramind-synthetic-throttle-')
                or directory.resolve().parent != Path(tempfile.gettempdir()).resolve() or not _digest(self.marker)):
            raise ValueError('Only owned synthetic temporary stores are supported')
        path = directory / 'synthetic-auth-throttle.sqlite'
        if path.is_symlink(): raise ValueError('Synthetic store must not be a symlink')
        return path


@contextmanager
def transaction(handle, busy_ms=250):
    connection = None
    try:
        connection = sqlite3.connect(handle.path.as_uri() + '?mode=rw', uri=True,
            timeout=busy_ms / 1000, isolation_level=None)
        connection.execute('PRAGMA synchronous=FULL')
        connection.execute('BEGIN IMMEDIATE')
        yield connection
    except (StorageUnavailable, GuardRejected): raise
    except sqlite3.Error as error:
        if (getattr(error, 'sqlite_errorcode', 0) & 255) in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
            raise StorageBusy() from None
        raise StorageUnavailable() from None
    except Exception: raise StorageUnavailable() from None
    finally:
        if connection is not None:
            try:
                if connection.in_transaction: connection.rollback()
            finally: connection.close()


def _state(connection):
    control = connection.execute('SELECT * FROM prototype_control WHERE id=1').fetchone()
    rows = connection.execute('SELECT * FROM prototype_windows ORDER BY namespace,key_digest LIMIT 10001').fetchall()
    return control, rows


def _schema_digest(connection):
    rows = connection.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name LIMIT 6").fetchall()
    if {r[1] for r in rows} != {'prototype_control','prototype_windows','prototype_expiry','prototype_insert','prototype_delete'}:
        raise StorageUnavailable()
    return hashlib.sha256(json.dumps(rows,separators=(',', ':')).encode()).hexdigest()


def _signature(control, rows, key, schema):
    data = json.dumps([list(control[:-1]), rows, schema], separators=(',', ':')).encode()
    return hmac.new(key, data, hashlib.sha256).hexdigest()


def _sign(connection, key):
    control, rows = _state(connection)
    connection.execute('UPDATE prototype_control SET state_mac=? WHERE id=1', (_signature(control, rows, key, _schema_digest(connection)),))


def _validate(connection, handle, key):
    control, rows = _state(connection)
    if (control is None or control[0] != 1 or control[1] != handle.marker or control[2] != 2
            or any(type(v) is not int for v in control[3:7]) or not 0 <= control[3] <= MAX_CLOCK
            or not 2 <= control[5] <= 10000 or control[4] != len(rows) or not 0 <= control[4] <= control[5]
            or not 1 <= control[6] <= 100 or control[7] != handle.epoch or control[8] != 'ACTIVE'
            or not _digest(control[9]) or not hmac.compare_digest(control[9], _signature(control, rows, key, _schema_digest(connection)))):
        raise StorageUnavailable()
    for namespace, digest, encoded, expiry in rows:
        if namespace not in LIMITS or not _digest(digest) or not isinstance(encoded, str) or len(encoded) > 1024:
            raise StorageUnavailable()
        values = json.loads(encoded)
        if (not isinstance(values, list) or not 1 <= len(values) <= LIMITS[namespace]
                or any(type(v) is not int or not 0 <= v <= control[3] for v in values)
                or values != sorted(values) or type(expiry) is not int or expiry != values[-1] + WINDOW_MS):
            raise StorageUnavailable()
    return control, rows


class Ownership:
    """Lifetime SQLite writer lock AND irreversible first-owner claim, not a lease."""
    def __init__(self, handle, key):
        self.lock = None
        try:
            path = handle.path.parent / 'synthetic-owner-lock.sqlite'
            if path.is_symlink(): raise ContinuityLost()
            self.lock = sqlite3.connect(path.as_uri() + '?mode=rw', uri=True, timeout=0, isolation_level=None)
            self.lock.execute('BEGIN IMMEDIATE')
            with transaction(handle, 0) as connection:
                control, rows = _state(connection)
                if (control is None or control[1] != handle.marker or control[8] != 'NEW'
                        or control[7] != '' or rows or not hmac.compare_digest(control[9], _signature(control, rows, key, _schema_digest(connection)))):
                    raise ContinuityLost()
                self.handle = replace(handle, epoch=secrets.token_hex(32))
                connection.execute("UPDATE prototype_control SET owner_epoch=?,state='ACTIVE' WHERE id=1", (self.handle.epoch,))
                _sign(connection, key); connection.commit()
        except sqlite3.Error:
            self.close(); raise StorageBusy() from None
        except Exception:
            self.close(); raise

    def close(self):
        if self.lock is not None: self.lock.close(); self.lock = None


class ElapsedClock:
    def __init__(self, manual=False):
        self.manual = manual
        self.origin = time.monotonic_ns()
        self.tick = self.last = 0
        self.broken = False
        self.lock = threading.Lock()

    def read(self):
        with self.lock:
            tick = self.tick if self.manual else (time.monotonic_ns() - self.origin) // 1_000_000
            if self.broken or type(tick) is not int or not self.last <= tick <= MAX_CLOCK:
                self.broken = True; raise ContinuityLost()
            self.last = tick
            return tick

    def advance(self, delta):
        with self.lock:
            if not self.manual or type(delta) is not int or delta < 0 or self.tick + delta > MAX_CLOCK:
                self.broken = True; raise ContinuityLost()
            self.tick += delta


def _send(stream, message):
    data = json.dumps(message, separators=(',', ':')).encode() + b'\n'
    if len(data) > 8192: raise StorageUnavailable()
    stream.sendall(data)


def _receive(stream):
    data = bytearray()
    deadline = time.monotonic() + 3
    while len(data) <= 8192:
        remaining = deadline - time.monotonic()
        if remaining <= 0: raise StorageUnavailable()
        stream.settimeout(remaining)
        part = stream.recv(1)
        if not part: raise StorageUnavailable()
        if part == b'\n': return json.loads(data)
        data.extend(part)
    raise StorageUnavailable()


def _frame_mac(frame, key):
    value = [frame.get(k) for k in ('epoch', 'nonce', 'sequence', 'role', 'body')]
    return hmac.new(key.encode(), json.dumps(value, separators=(',', ':'), sort_keys=True).encode(), hashlib.sha256).hexdigest()


class Wire:
    """Bounded authenticated frames with per-call nonces and ordered challenges."""
    def __init__(self, stream, handle, *, key=None, role='client', nonce=None, sequence=0):
        self.stream, self.epoch = stream, handle.epoch
        self.key, self.role = key or handle.capability, role
        self.nonce, self.sequence = nonce or secrets.token_hex(32), sequence

    def send(self, body):
        frame = dict(epoch=self.epoch, nonce=self.nonce, sequence=self.sequence, role=self.role, body=body)
        frame['mac'] = _frame_mac(frame, self.key)
        _send(self.stream, frame); self.sequence += 1

    def receive(self):
        frame = _receive(self.stream)
        if (not isinstance(frame, dict) or frame.get('epoch') != self.epoch or frame.get('nonce') != self.nonce
                or frame.get('sequence') != self.sequence or frame.get('role') != self.role
                or not isinstance(frame.get('body'), dict) or not _digest(frame.get('mac'))
                or not hmac.compare_digest(frame['mac'], _frame_mac(frame, self.key))):
            raise StorageUnavailable()
        self.sequence += 1
        return frame['body']


def request(handle, operation, *, capability=None, guard=lambda: True, **values):
    try:
        if handle.endpoint is None or handle.endpoint[0] != '127.0.0.1': raise StorageUnavailable()
        with socket.create_connection(handle.endpoint, timeout=3) as stream:
            stream.settimeout(3)
            stream.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            wire = Wire(stream, handle, key=capability, role='admin' if capability is not None else 'client')
            wire.send(dict(op=operation, **values))
            challenges = 0
            while True:
                response = wire.receive()
                if response.get('kind') == 'guard':
                    challenges += 1
                    if challenges > 2: raise StorageUnavailable()
                    wire.send({'guard': guard() is True}); continue
                status = response.get('status')
                if status == 'guard': raise GuardRejected()
                if status == 'busy': raise StorageBusy()
                if status != 'ok': raise StorageUnavailable()
                return response
    except (GuardRejected, StorageUnavailable): raise
    except Exception: raise StorageUnavailable() from None


def seal(handle):
    with transaction(handle, 1000) as connection:
        connection.execute("UPDATE prototype_control SET state='SEALED',owner_epoch=?,state_mac='' WHERE id=1", (secrets.token_hex(32),))
        connection.commit()


class _Runtime:
    def __init__(self, handle, key, admin, manual):
        self.handle, self.key, self.admin = handle, key, admin
        self.clock = ElapsedClock(manual)
        self.stop = threading.Event()
        self.fault = None
        self.fault_lock = threading.Lock()

    def guard(self, stream):
        stream.send({'kind': 'guard'})
        if stream.receive().get('guard') is not True: raise GuardRejected()

    def stamp(self, control):
        stamp = self.clock.read()
        if stamp < control[3]: self.clock.broken = True; raise ContinuityLost()
        return stamp

    def cleanup(self, stream=None, busy_ms=250):
        with transaction(self.handle, busy_ms) as connection:
            control, _ = _validate(connection, self.handle, self.key)
            if stream is not None: self.guard(stream)
            stamp = self.stamp(control)
            removed = connection.execute('''DELETE FROM prototype_windows WHERE rowid IN
                (SELECT rowid FROM prototype_windows WHERE expires_ms<=? ORDER BY expires_ms LIMIT ?)''', (stamp, control[6])).rowcount
            connection.execute('UPDATE prototype_control SET last_ms=? WHERE id=1', (stamp,))
            _sign(connection, self.key)
            _validate(connection, self.handle, self.key)
            if self.clock.broken: raise ContinuityLost()
            connection.commit()
            return removed

    def checkpoint(self, stage, connection, fault):
        if stage == fault: raise StorageUnavailable()
        if stage == 'after_first_write' and fault == 'locked':
            error = sqlite3.OperationalError('Synthetic locked injection')
            error.sqlite_errorcode = sqlite3.SQLITE_LOCKED
            raise error
        if stage == 'after_first_write' and fault == 'probe_lock':
            with closing(sqlite3.connect(self.handle.path, timeout=0, isolation_level=None)) as probe:
                try: probe.execute('BEGIN IMMEDIATE')
                except sqlite3.OperationalError as error:
                    if (error.sqlite_errorcode & 255) == sqlite3.SQLITE_BUSY: return
                raise StorageUnavailable()

    def reserve(self, stream, message):
        keys, busy = message.get('keys'), message.get('busy_ms')
        if (set(message) != {'op','action','keys','busy_ms'} or message.get('action') not in ('login', 'register') or not isinstance(keys, list) or len(keys) != 2
                or any(not isinstance(k, list) or len(k) != 2 or k[0] != n or not _digest(k[1]) for k, n in zip(keys, ('ip', 'account')))
                or type(busy) is not int or not 0 <= busy <= 1000): raise StorageUnavailable()
        self.cleanup(stream, busy)  # Independent commit survives subsequent denial/rollback.
        with transaction(self.handle, busy) as connection:
            control, rows = _validate(connection, self.handle, self.key)
            self.guard(stream)
            stamp = self.stamp(control)
            by_key = {(r[0], r[1]): json.loads(r[2]) for r in rows}
            windows = [[v for v in by_key.get(tuple(k), []) if v > stamp - WINDOW_MS] for k in keys]
            if any(len(values) >= LIMITS[k[0]] for k, values in zip(keys, windows)): return False
            if control[4] + sum(tuple(k) not in by_key for k in keys) > control[5]: raise StorageUnavailable()
            with self.fault_lock: fault, self.fault = self.fault, None
            for index, (k, values) in enumerate(zip(keys, windows)):
                values.append(stamp)
                connection.execute('''INSERT INTO prototype_windows VALUES(?,?,?,?) ON CONFLICT(namespace,key_digest)
                    DO UPDATE SET stamps=excluded.stamps,expires_ms=excluded.expires_ms''',
                    (*k, json.dumps(values, separators=(',', ':')), stamp + WINDOW_MS))
                if index == 0: self.checkpoint('after_first_write', connection, fault)
            connection.execute('UPDATE prototype_control SET last_ms=? WHERE id=1', (stamp,))
            _sign(connection, self.key)
            _validate(connection, self.handle, self.key)
            self.checkpoint('before_commit', connection, fault)
            if self.clock.broken: raise ContinuityLost()
            connection.commit()
            return True

    def handle_client(self, stream):
        with stream:
            stream.settimeout(3)
            stream.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            wire = None
            try:
                first = _receive(stream)
                if (not isinstance(first, dict) or first.get('role') not in ('client', 'admin')
                        or not _digest(first.get('nonce'))): raise StorageUnavailable()
                admin = first['role'] == 'admin'
                key = self.admin if admin else self.handle.capability
                if (first.get('epoch') != self.handle.epoch or first.get('sequence') != 0
                        or not isinstance(first.get('body'), dict) or not _digest(first.get('mac'))
                        or not hmac.compare_digest(first['mac'], _frame_mac(first, key))): raise StorageUnavailable()
                wire = Wire(stream, self.handle, key=key, role=first['role'], nonce=first['nonce'], sequence=1)
                message = first['body']
                op = message.get('op')
                if op == 'reserve': result = {'allowed': self.reserve(wire, message)}
                elif op == 'cleanup': result = {'removed': self.cleanup()}
                elif admin and op == 'advance': self.clock.advance(message.get('delta')); result = {}
                elif admin and op == 'fault':
                    if not self.clock.manual or message.get('stage') not in ('after_first_write', 'before_commit', 'locked', 'probe_lock'): raise StorageUnavailable()
                    with self.fault_lock: self.fault = message['stage']
                    result = {}
                elif admin and op == 'stop': self.stop.set(); result = {}
                else: raise StorageUnavailable()
                wire.send(dict(status='ok', **result))
            except GuardRejected: _safe_error(wire, 'guard')
            except StorageBusy: _safe_error(wire, 'busy')
            except Exception:
                if self.clock.broken:
                    try: seal(self.handle)
                    except StorageUnavailable: pass
                _safe_error(wire, 'unavailable')


def _safe_error(stream, status):
    try: stream.send({'status': status})
    except Exception: pass


def _owner_main(handle, key, admin, manual, ready):
    ownership = None
    try:
        ownership = Ownership(handle, key)
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0)); listener.listen(8); listener.settimeout(0.1)
            handle = replace(ownership.handle, endpoint=listener.getsockname())
            runtime = _Runtime(handle, key, admin, manual)
            ready.send(('ready', handle))
            slots = threading.BoundedSemaphore(8)
            with ThreadPoolExecutor(max_workers=8) as pool:
                while not runtime.stop.is_set():
                    try: stream, _ = listener.accept()
                    except socket.timeout: continue
                    if not slots.acquire(blocking=False): stream.close(); continue
                    def work(client=stream):
                        try: runtime.handle_client(client)
                        finally: slots.release()
                    pool.submit(work)
    except Exception:
        try: ready.send(('error', None))
        except Exception: pass
    finally:
        ready.close()
        if ownership is not None: ownership.close()


class SyntheticDatabase:
    def __init__(self, *, max_keys=10000, cleanup_batch=100, manual_clock=False, autostart=True):
        if type(max_keys) is not int or not 2 <= max_keys <= 10000: raise ValueError('Bounded key cap required')
        if type(cleanup_batch) is not int or not 1 <= cleanup_batch <= 100: raise ValueError('Bounded cleanup required')
        self._temp = tempfile.TemporaryDirectory(prefix='migramind-synthetic-throttle-')
        self.handle = SyntheticHandle(self._temp.name, secrets.token_hex(32), capability=secrets.token_hex(32))
        self._key, self._admin = secrets.token_bytes(32), secrets.token_hex(32)
        self._process = None
        self.manual_clock = manual_clock
        try:
            fd = os.open(self.handle.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600); os.close(fd)
            with closing(sqlite3.connect(self.handle.path)) as connection:
                connection.executescript('''PRAGMA journal_mode=DELETE; PRAGMA synchronous=FULL;
                    CREATE TABLE prototype_control (
                        id INTEGER PRIMARY KEY CHECK(id=1),marker TEXT NOT NULL,version INTEGER NOT NULL CHECK(version=2),
                        last_ms INTEGER NOT NULL CHECK(last_ms>=0),key_count INTEGER NOT NULL CHECK(key_count>=0 AND key_count<=max_keys),
                        max_keys INTEGER NOT NULL CHECK(max_keys BETWEEN 2 AND 10000),cleanup_batch INTEGER NOT NULL CHECK(cleanup_batch BETWEEN 1 AND 100),
                        owner_epoch TEXT NOT NULL,state TEXT NOT NULL CHECK(state IN ('NEW','ACTIVE','SEALED')),state_mac TEXT NOT NULL);
                    CREATE TABLE prototype_windows (
                        namespace TEXT NOT NULL CHECK(namespace IN ('ip','account')),key_digest TEXT NOT NULL CHECK(length(key_digest)=64),
                        stamps TEXT NOT NULL CHECK(length(stamps)<=1024),expires_ms INTEGER NOT NULL CHECK(expires_ms>=0),PRIMARY KEY(namespace,key_digest));
                    CREATE INDEX prototype_expiry ON prototype_windows(expires_ms);
                    CREATE TRIGGER prototype_insert AFTER INSERT ON prototype_windows
                        BEGIN UPDATE prototype_control SET key_count=key_count+1 WHERE id=1; END;
                    CREATE TRIGGER prototype_delete AFTER DELETE ON prototype_windows
                        BEGIN UPDATE prototype_control SET key_count=key_count-1 WHERE id=1; END;''')
                connection.execute("INSERT INTO prototype_control VALUES(1,?,2,0,0,?,?,?,'NEW','')", (self.handle.marker, max_keys, cleanup_batch, ''))
                _sign(connection, self._key); connection.commit()
            with closing(sqlite3.connect(self.handle.path.parent / 'synthetic-owner-lock.sqlite')) as connection:
                connection.execute('CREATE TABLE synthetic_lock_marker(marker TEXT)')
                connection.execute('INSERT INTO synthetic_lock_marker VALUES(?)', (self.handle.marker,)); connection.commit()
            if autostart: self.start_owner()
        except BaseException: self.close(); raise

    def start_owner(self):
        if self._process is not None and self._process.is_alive(): raise ContinuityLost()
        if self._process is not None: self._process.close()
        context = multiprocessing.get_context('spawn')
        receiver, sender = context.Pipe(duplex=False)
        process = context.Process(target=_owner_main, args=(self.handle, self._key, self._admin, self.manual_clock, sender))
        self._process = process
        process.start(); sender.close()
        try:
            if not receiver.poll(10): raise ContinuityLost()
            status, handle = receiver.recv()
            if status != 'ready': raise ContinuityLost()
            self.handle = handle
        except Exception:
            if process.is_alive(): process.terminate()
            process.join(5); raise ContinuityLost() from None
        finally: receiver.close()

    def advance(self, delta_ms): request(self.handle, 'advance', capability=self._admin, delta=delta_ms)
    def inject_fault(self, stage): request(self.handle, 'fault', capability=self._admin, stage=stage)
    def fence(self): seal(self.handle)

    def crash_owner(self):
        if self._process is not None and self._process.is_alive(): self._process.terminate(); self._process.join(5)

    def close(self):
        if self._process is not None:
            if self._process.is_alive():
                try: request(self.handle, 'stop', capability=self._admin)
                except StorageUnavailable: pass
                self._process.join(5)
                if self._process.is_alive(): self._process.terminate(); self._process.join(5)
            self._process.close(); self._process = None
        self._temp.cleanup()

    def __enter__(self): return self
    def __exit__(self, *args): self.close()


class ReservationAdapter:
    """Worker RPC client: no clock sampling or direct SQLite admission."""
    def __init__(self, handle, *, busy_ms=250):
        if not isinstance(handle, SyntheticHandle): raise ValueError('Synthetic handle required')
        if type(busy_ms) is not int or not 0 <= busy_ms <= 1000: raise ValueError('Bounded busy timeout required')
        self.handle, self.busy_ms = handle, busy_ms

    def reserve(self, *, action, ip, account, guard):
        from legacy_adapter import synthetic_keys  # Pure bounded synthetic normalization only.
        if action not in ('login', 'register'): raise ValueError('Synthetic auth actions only')
        keys = synthetic_keys(ip, account)
        if guard() is not True: raise GuardRejected()
        result = request(self.handle, 'reserve', action=action, keys=keys, busy_ms=self.busy_ms, guard=guard)
        return Decision(result['allowed'], None if result['allowed'] else 900)

    def cleanup(self): return request(self.handle, 'cleanup')['removed']
