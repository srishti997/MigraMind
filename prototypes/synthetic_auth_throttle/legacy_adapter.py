"""Synthetic-only SQLite experiment. No app imports, environment URLs or path CLI."""
from contextlib import closing, contextmanager
from dataclasses import dataclass
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import secrets
import sqlite3
import tempfile
import time

WINDOW_MS = 900_000
LIMITS = {'ip': 30, 'account': 10}
MAX_CLOCK = 2**53 - WINDOW_MS


class StorageUnavailable(Exception):
    def __init__(self): super().__init__('Synthetic throttle storage unavailable; no admission confirmed')


class StorageBusy(StorageUnavailable):
    """Bounded SQLITE_BUSY/SQLITE_LOCKED failure, never an admission."""


class GuardRejected(Exception):
    def __init__(self): super().__init__('Synthetic guard rejected')


@dataclass(frozen=True)
class Decision:
    allowed: bool
    retry_after_seconds: int | None = None


@dataclass(frozen=True)
class SyntheticHandle:
    """Only share handles returned by SyntheticDatabase with owned test workers."""
    directory: str
    marker: str

    @property
    def path(self):
        directory = Path(self.directory)
        if (not directory.is_absolute() or directory.is_symlink()
                or not directory.name.startswith('migramind-synthetic-throttle-')
                or directory.resolve().parent != Path(tempfile.gettempdir()).resolve()
                or len(self.marker) != 64):
            raise ValueError('Only a newly created synthetic temporary store is supported')
        path = directory / 'synthetic-auth-throttle.sqlite'
        if path.is_symlink(): raise ValueError('Synthetic store must not be a symlink')
        return path


class SyntheticDatabase:
    """Owns one NEW temporary directory; never accepts a database/source path."""
    def __init__(self, *, max_keys=10_000, cleanup_batch=100):
        if type(max_keys) is not int or not 2 <= max_keys <= 10_000:
            raise ValueError('Synthetic max_keys must be between 2 and 10000')
        if type(cleanup_batch) is not int or not 1 <= cleanup_batch <= 100:
            raise ValueError('Synthetic cleanup_batch must be between 1 and 100')
        self._temp = tempfile.TemporaryDirectory(prefix='migramind-synthetic-throttle-')
        self.handle = SyntheticHandle(self._temp.name, secrets.token_hex(32))
        try:
            # Exclusive creation: schema initialization never opens an existing input file.
            fd = os.open(self.handle.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
            with closing(sqlite3.connect(self.handle.path)) as connection:
                connection.executescript('''
                    PRAGMA journal_mode=DELETE;
                    PRAGMA synchronous=FULL;
                    CREATE TABLE prototype_control (
                        id INTEGER PRIMARY KEY CHECK(id=1), marker TEXT NOT NULL,
                        version INTEGER NOT NULL CHECK(version=1),
                        last_ms INTEGER NOT NULL CHECK(last_ms>=0),
                        key_count INTEGER NOT NULL CHECK(key_count>=0 AND key_count<=max_keys),
                        max_keys INTEGER NOT NULL CHECK(max_keys BETWEEN 2 AND 10000),
                        cleanup_batch INTEGER NOT NULL CHECK(cleanup_batch BETWEEN 1 AND 100));
                    CREATE TABLE prototype_windows (
                        namespace TEXT NOT NULL CHECK(namespace IN ('ip','account')),
                        key_digest TEXT NOT NULL CHECK(length(key_digest)=64),
                        stamps TEXT NOT NULL CHECK(length(stamps)<=1024),
                        expires_ms INTEGER NOT NULL CHECK(expires_ms>=0),
                        PRIMARY KEY(namespace,key_digest));
                    CREATE INDEX prototype_expiry ON prototype_windows(expires_ms);
                    CREATE TRIGGER prototype_insert AFTER INSERT ON prototype_windows
                    BEGIN UPDATE prototype_control SET key_count=key_count+1 WHERE id=1; END;
                    CREATE TRIGGER prototype_delete AFTER DELETE ON prototype_windows
                    BEGIN UPDATE prototype_control SET key_count=key_count-1 WHERE id=1; END;
                ''')
                connection.execute('INSERT INTO prototype_control VALUES(1,?,1,0,0,?,?)',
                    (self.handle.marker, max_keys, cleanup_batch))
                connection.commit()
        except BaseException:
            self._temp.cleanup()
            raise

    def close(self): self._temp.cleanup()
    def __enter__(self): return self
    def __exit__(self, *args): self.close()


def synthetic_keys(ip, account):
    """Deliberately reject non-documentation IPs/non-example account identifiers."""
    if not isinstance(ip, str) or not isinstance(account, str) or not 3 <= len(account) <= 254:
        raise ValueError('Synthetic identifiers required')
    address = ipaddress.ip_address(ip)
    networks = ('192.0.2.0/24', '198.51.100.0/24', '203.0.113.0/24', '2001:db8::/32')
    if not any(address in ipaddress.ip_network(network) for network in networks):
        raise ValueError('Only documentation IP addresses are permitted')
    account = account.strip().lower()
    if (account.count('@') != 1 or not all(account.split('@')) or any(c.isspace() for c in account)
            or account.split('@')[1] != 'example.test'):
        raise ValueError('Only synthetic example.test accounts are permitted')
    return [('ip', hashlib.sha256(('synthetic-ip:' + str(address)).encode()).hexdigest()),
            ('account', hashlib.sha256(('synthetic-account:' + account).encode()).hexdigest())]


class ReservationAdapter:
    """Every operation uses an independent connection and SQLite writer reservation."""
    def __init__(self, handle, *, clock=None, busy_ms=250):
        if not isinstance(handle, SyntheticHandle): raise ValueError('Synthetic handle required')
        if type(busy_ms) is not int or not 0 <= busy_ms <= 1000: raise ValueError('Bounded busy timeout required')
        self.handle, self.busy_ms = handle, busy_ms
        self.clock = clock if clock is not None else lambda: time.time_ns() // 1_000_000

    @contextmanager
    def _transaction(self):
        connection = None
        try:
            # mode=rw refuses missing files instead of recreating empty/reset counters.
            connection = sqlite3.connect(self.handle.path.as_uri() + '?mode=rw', uri=True,
                timeout=self.busy_ms / 1000, isolation_level=None)
            connection.execute('PRAGMA synchronous=FULL')
            connection.execute('BEGIN IMMEDIATE')
            yield connection
        except GuardRejected:
            raise
        except sqlite3.Error as error:
            kind = getattr(error, 'sqlite_errorcode', 0) & 255
            if kind in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED): raise StorageBusy() from None
            raise StorageUnavailable() from None
        except Exception:
            raise StorageUnavailable() from None
        finally:
            if connection is not None:
                try:
                    if connection.in_transaction: connection.rollback()
                except sqlite3.Error:
                    pass
                finally:
                    connection.close()

    def _control(self, connection):
        row = connection.execute('SELECT marker,version,last_ms,key_count,max_keys,cleanup_batch FROM prototype_control WHERE id=1').fetchone()
        if (row is None or row[0] != self.handle.marker or row[1] != 1
                or any(type(n) is not int for n in row[2:])
                or not 0 <= row[2] <= MAX_CLOCK or not 0 <= row[3] <= row[4] <= 10_000
                or row[4] < 2 or not 1 <= row[5] <= 100):
            raise StorageUnavailable()
        return row

    def _now(self, control):
        stamp = self.clock()  # Sample AFTER acquiring the SQLite writer reservation.
        if type(stamp) is not int or not 0 <= stamp <= MAX_CLOCK: raise StorageUnavailable()
        return max(stamp, control[2])

    @staticmethod
    def _cleanup(connection, stamp, batch):
        return connection.execute('''DELETE FROM prototype_windows WHERE rowid IN
            (SELECT rowid FROM prototype_windows WHERE expires_ms<=? ORDER BY expires_ms LIMIT ?)''',
            (stamp, batch)).rowcount

    @staticmethod
    def _window(connection, key, stamp):
        row = connection.execute('SELECT stamps,expires_ms FROM prototype_windows WHERE namespace=? AND key_digest=?', key).fetchone()
        if row is None: return [], False
        if not isinstance(row[0], str) or len(row[0]) > 1024: raise StorageUnavailable()
        values = json.loads(row[0])
        if (not isinstance(values, list) or not 1 <= len(values) <= LIMITS[key[0]]
                or any(type(v) is not int or not 0 <= v <= stamp for v in values)
                or values != sorted(values) or row[1] != values[-1] + WINDOW_MS):
            raise StorageUnavailable()
        return [v for v in values if v > stamp - WINDOW_MS], True

    def _checkpoint(self, stage, connection):
        """Test subclasses inject failures here; no hooks into application state."""

    def reserve(self, *, action, ip, account, guard):
        if action not in ('login', 'register'): raise ValueError('Synthetic login/register only')
        keys = synthetic_keys(ip, account)
        if guard() is not True: raise GuardRejected()
        with self._transaction() as connection:
            # Synthetic contract: guards also recheck after waiting, before accounting.
            if guard() is not True: raise GuardRejected()
            control = self._control(connection)
            stamp = self._now(control)
            self._cleanup(connection, stamp, control[5])
            windows = [self._window(connection, key, stamp) for key in keys]
            if any(len(values) >= LIMITS[key[0]] for key, (values, _) in zip(keys, windows)):
                # Roll back maintenance too: denied reservation changes neither budget.
                return Decision(False, 900)
            count = connection.execute('SELECT key_count FROM prototype_control WHERE id=1').fetchone()[0]
            if count + sum(not exists for _, exists in windows) > control[4]: raise StorageUnavailable()
            for index, (key, (values, _)) in enumerate(zip(keys, windows)):
                values.append(stamp)
                connection.execute('''INSERT INTO prototype_windows VALUES(?,?,?,?)
                    ON CONFLICT(namespace,key_digest) DO UPDATE SET stamps=excluded.stamps,expires_ms=excluded.expires_ms''',
                    (*key, json.dumps(values, separators=(',', ':')), stamp + WINDOW_MS))
                if index == 0: self._checkpoint('after_first_write', connection)
            connection.execute('UPDATE prototype_control SET last_ms=? WHERE id=1', (stamp,))
            self._checkpoint('before_commit', connection)
            connection.commit()
            return Decision(True)

    def cleanup(self):
        with self._transaction() as connection:
            control = self._control(connection)
            stamp = self._now(control)
            removed = self._cleanup(connection, stamp, control[5])
            connection.execute('UPDATE prototype_control SET last_ms=? WHERE id=1', (stamp,))
            connection.commit()
            return removed
