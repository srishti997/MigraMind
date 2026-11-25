"""Version-aware migration rehearsal, exclusively for generated synthetic fixtures."""
from contextlib import closing
import hashlib
import os
from pathlib import Path
import sqlite3
import stat
import tempfile
from unittest.mock import patch

import application_schema_exercise as fixture
import app.main as application
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
import recoverable_sqlite as backup

SUPPORTED = ('009', '010')
HEAD = '010'
PREFIX = 'synthetic-app-alembic/'
SCRIPT_LOCATION = Path(__file__).resolve().parents[2] / 'backend' / 'alembic'


class _OwnedDatabase:
    """A fixed-name new database with no caller-provided filesystem target."""
    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(prefix='migramind-synthetic-migration-')
        self.path = Path(self._temp.name) / 'synthetic.sqlite'
        with self.path.open('xb'): pass
        info = self.path.lstat()
        self._identity = (info.st_dev, info.st_ino)
        return self

    def __exit__(self, *_): self._temp.cleanup()

    def _check(self):
        info = self.path.lstat()
        if (self.path.is_symlink() or not stat.S_ISREG(info.st_mode)
                or (getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0))
                or (info.st_dev, info.st_ino) != self._identity):
            raise RuntimeError('Synthetic database identity changed')

    def connect(self):
        self._check()
        return sqlite3.connect(self.path.as_uri() + '?mode=rw', uri=True)

    def write_new_image(self, raw):
        self._check()
        with self.path.open('r+b') as stream:
            if stream.seek(0, os.SEEK_END) != 0: raise RuntimeError('Target is not empty')
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())

    def engine(self):
        return create_engine('sqlite://', creator=self.connect)

    def upgrade(self, revision):
        if revision not in SUPPORTED: raise ValueError('Unsupported synthetic revision')
        self._check()
        engine = self.engine()
        try:
            config = Config()  # Never load alembic.ini or its application database URL.
            config.set_main_option('script_location', str(SCRIPT_LOCATION))
            with patch.object(application, 'engine', engine):
                command.upgrade(config, revision)
        finally:
            engine.dispose()
        self._check()


def _seed(target):
    engine = target.engine()
    try:
        fixture.seed(engine, create_schema=False, include_session=False)
        with engine.begin() as connection:
            connection.exec_driver_sql(
                'INSERT INTO login_sessions (id,user_id,token_digest,csrf_token,expires_at) VALUES (1,1,?,?,?)',
                (hashlib.sha256(fixture.COOKIE.encode()).hexdigest(), fixture.CSRF, '2099-01-01T00:00:00+00:00'))
    finally:
        engine.dispose()


def _inspect(raw, revision):
    if revision not in SUPPORTED or not 0 < len(raw) <= backup.MAX_IMAGE: raise ValueError('Unsupported image')
    with _OwnedDatabase() as reference:
        reference.upgrade(revision)
        _seed(reference)
        with closing(reference.connect()) as expected, closing(sqlite3.connect(':memory:')) as actual:
            expected.execute('DELETE FROM login_sessions'); expected.commit()
            actual.deserialize(raw)
            actual.execute('PRAGMA trusted_schema=OFF')
            if actual.execute('PRAGMA integrity_check').fetchall() != [('ok',)] or actual.execute('PRAGMA foreign_key_check').fetchall():
                raise ValueError('Synthetic integrity failure')
            query = "SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
            def normalize(rows):
                result = []
                for kind, name, table, sql in rows:
                    if kind == 'table' and name == 'support_feedback':
                        # Alembic batch reflection emits these two constraints in
                        # nondeterministic order. Preserve every other SQL byte.
                        lines = sql.splitlines()
                        indices = [i for i, line in enumerate(lines) if line.strip().startswith((
                            'CONSTRAINT one_rating_per_session_action ', 'CONSTRAINT nonemergency_feedback_action '))]
                        if len(indices) != 2: raise ValueError('Unexpected constraints')
                        ordered = sorted(lines[i] for i in indices)
                        for i, line in zip(indices, ordered): lines[i] = line
                        sql = '\n'.join(lines)
                    result.append((kind, name, table, sql))
                return result
            if normalize(actual.execute(query).fetchall()) != normalize(expected.execute(query).fetchall()):
                raise ValueError('Synthetic schema mismatch')
            if actual.execute('SELECT version_num FROM alembic_version').fetchall() != [(revision,)]: raise ValueError('Revision mismatch')
            for table in fixture.Base.metadata.sorted_tables:
                sql = 'SELECT * FROM "' + table.name + '" ORDER BY id'
                if actual.execute(sql).fetchall() != expected.execute(sql).fetchall(): raise ValueError('Synthetic fixture mismatch')


class VersionedBackup(backup.SyntheticBackup):
    _session_table = 'login_sessions'

    def __init__(self, revision):
        if revision not in SUPPORTED: raise ValueError('Unsupported synthetic revision')
        self.revision = revision
        self._schema = PREFIX + revision
        self._inspect = lambda raw: _inspect(raw, revision)

    def __enter__(self):
        self._owned = _OwnedDatabase().__enter__()
        self._root = self._owned.path.parent
        self._source = None
        try:
            self._owned.upgrade(self.revision)
            _seed(self._owned)
            self._source = self._owned.connect()
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *_):
        try:
            if self._source is not None: self._source.close()
        finally:
            self._source = None
            self._owned.__exit__(None, None, None)


class VersionedRecovery(backup.SyntheticRecovery):
    def restore(self, blob, passphrase):
        # Untrusted header is only used to select an allowlisted parser; AEAD then
        # authenticates it, and _inspect compares it to alembic_version and schema.
        try:
            offset = len(backup.MAGIC)
            size = int.from_bytes(blob[offset+1:offset+3], 'big')
            if not 1 <= size <= backup.MAX_METADATA: raise ValueError()
            metadata = backup._json(blob[offset+3:offset+3+size])
            revision = metadata['schema'].removeprefix(PREFIX)
            if revision not in SUPPORTED or metadata['schema'] != PREFIX + revision: raise ValueError()
        except (TypeError, ValueError, KeyError, AttributeError, UnicodeError, RecursionError):
            raise backup.RejectedBackup('Synthetic backup rejected') from None
        self._schema = PREFIX + revision
        self._inspect = lambda raw: _inspect(raw, revision)
        raw = self._open(blob, passphrase)
        if self.target.exists(): raise backup.RecoveryFailed('Synthetic target exists')
        try:
            with _OwnedDatabase() as stage:
                stage.write_new_image(raw)
                if revision != HEAD:
                    stage.upgrade(HEAD)
                    with closing(stage.connect()) as connection:
                        if connection.execute('SELECT count(*) FROM login_sessions').fetchone() != (0,):
                            raise ValueError('Synthetic sessions present')
                stage._check()
                _inspect(stage.path.read_bytes(), HEAD)
                os.link(stage.path, self.target)
        except Exception:
            raise backup.RecoveryFailed('Synthetic recovery could not be published') from None
        return {'source_revision': revision, 'restored_revision': HEAD,
                'sessions_restored': 0, 'activation_allowed': False,
                'deletion_reconciliation': 'not established'}
