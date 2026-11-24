"""Synthetic app-schema exercise. Run only under the isolated test launcher."""
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch

_allowed = {'PATH', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'TMPDIR',
            'DATABASE_URL', 'APP_ENV', 'DATA_MODE', 'MIGRAMIND_SYNTHETIC_SCHEMA_TEST'}
if (any(k.upper() not in _allowed for k in os.environ)
        or os.environ.get('DATABASE_URL') != 'sqlite://'
        or os.environ.get('APP_ENV') != 'development'
        or os.environ.get('DATA_MODE') != 'local'
        or os.environ.get('MIGRAMIND_SYNTHETIC_SCHEMA_TEST') != 'isolated-model-exercise'):
    raise RuntimeError('Synthetic isolated test environment required')

# app.main otherwise searches for and loads existing environment files.
with patch('dotenv.load_dotenv', return_value=False):
    from app.main import (Base, User, LoginSession, Episode, Wellness, EarlySymptom,
        DailyCheckin, CheckinRevision, Profile, Contact, AttackSession,
        SupportPreferences, SupportFeedback, app, auth, db, engine as import_engine)
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.auth import hasher
import recoverable_sqlite as backup

STAMP = '2025-01-02T12:00:00+00:00'
COOKIE = 'synthetic-session-token'
CSRF = 'synthetic-csrf-token'
PASSWORD = 'Synthetic-password-123'
PASSWORD_HASH = hasher.hash(PASSWORD)


def seed(engine):
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as s:
        s.add_all([User(id=i, email=f'synthetic-{i}@example.test', display_name=f'Synthetic {i}',
                       password_hash=PASSWORD_HASH, created_at=STAMP) for i in (1, 2)])
        s.flush()
        s.add_all([Episode(id=i, owner_id=i, date='2025-01-02', severity=i+3, duration=60,
                           trigger='synthetic light', notes=f'Synthetic episode {i}',
                           symptoms=['synthetic nausea']) for i in (1, 2)])
        s.add_all([Wellness(id=1, owner_id=1, date='2025-01-02', timezone_name='UTC', recorded_at=STAMP, stress=2),
                   EarlySymptom(id=1, owner_id=1, symptom='synthetic aura', onset_at=STAMP, timezone_name='UTC', recorded_at=STAMP),
                   DailyCheckin(id=1, owner_id=1, date='2025-01-02', timezone_name='UTC', created_at=STAMP, revision=1, values={'synthetic': True}),
                   Profile(id=1, owner_id=1, name='Synthetic profile'),
                   Contact(id=1, owner_id=1, name='Synthetic contact', relationship='friend', phone='000000'),
                   AttackSession(id=1, owner_id=1, started_at=STAMP, ended_at=STAMP, active_slot=None)])
        s.flush()
        s.add_all([CheckinRevision(id=1, owner_id=1, checkin_id=1, revision=1, action='create', recorded_at=STAMP, values={'synthetic': True}),
                   SupportPreferences(id=1, owner_id=1, preferred_contact_id=1),
                   SupportFeedback(id=1, owner_id=1, session_id=1, action_id='support_card', helpful=True, created_at=STAMP),
                   LoginSession(id=1, user_id=1, token_digest=__import__('hashlib').sha256(COOKIE.encode()).hexdigest(), csrf_token=CSRF, expires_at='2099-01-01T00:00:00+00:00')])
        s.commit()


def inspect_image(raw):
    if not 0 < len(raw) <= backup.MAX_IMAGE:
        raise ValueError('Invalid synthetic image size')
    reference = create_engine('sqlite://')
    try:
        seed(reference)
        with reference.begin() as c:
            c.exec_driver_sql('DELETE FROM login_sessions')
            expected = c.connection.driver_connection
            with closing(sqlite3.connect(':memory:')) as actual:
                actual.deserialize(raw)
                actual.execute('PRAGMA trusted_schema=OFF')
                if actual.execute('PRAGMA integrity_check').fetchall() != [('ok',)] or actual.execute('PRAGMA foreign_key_check').fetchall():
                    raise ValueError('Invalid synthetic image')
                query = "SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
                if actual.execute(query).fetchall() != expected.execute(query).fetchall():
                    raise ValueError('Synthetic schema mismatch')
                for table in Base.metadata.sorted_tables:
                    # Names are from application metadata, not caller-controlled input.
                    sql = 'SELECT * FROM "' + table.name + '" ORDER BY id'
                    if actual.execute(sql).fetchall() != expected.execute(sql).fetchall():
                        raise ValueError('Synthetic records mismatch')
    finally:
        reference.dispose()


class AppSchemaBackup(backup.SyntheticBackup):
    _schema = 'synthetic-app-models/1'
    _session_table = 'login_sessions'
    _inspect = staticmethod(inspect_image)

    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(prefix='migramind-synthetic-app-schema-')
        self._root = Path(self._temp.name)
        self._source = None
        engine = None
        try:
            path = self._root / 'synthetic-source.sqlite'
            with path.open('xb'): pass
            engine = create_engine('sqlite:///' + path.as_posix())
            @event.listens_for(engine, 'connect')
            def fk(conn, _): conn.execute('PRAGMA foreign_keys=ON')
            with engine.connect() as c:
                if c.exec_driver_sql('PRAGMA journal_mode=WAL').scalar().lower() != 'wal': raise RuntimeError('WAL unavailable')
            seed(engine)
            engine.dispose(); engine = None
            self._source = sqlite3.connect(path)
            return self
        except BaseException:
            if engine is not None: engine.dispose()
            self.__exit__(None, None, None)
            raise


class AppSchemaRecovery(backup.SyntheticRecovery):
    _schema = 'synthetic-app-models/1'
    _inspect = staticmethod(inspect_image)
