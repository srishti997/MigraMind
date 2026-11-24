"""Synthetic version and migration checks, launched in the isolated app context."""
from contextlib import closing
import hashlib
import secrets
import sqlite3
import unittest
from unittest.mock import patch
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import recoverable_sqlite as crypto
import versioned_exercise as m


def metadata_parts(blob):
    offset = len(crypto.MAGIC)
    end = offset + 3 + int.from_bytes(blob[offset+1:offset+3], 'big')
    return crypto._json(blob[offset+3:end]), end


class VersionedTests(unittest.TestCase):
    def setUp(self):
        self.phrase = secrets.token_bytes(32)

    def archive(self, revision):
        with m.VersionedBackup(revision) as source:
            before = source._owned.path.read_bytes()
            blob = source.encrypt(self.phrase)
            self.assertEqual(hashlib.sha256(before).digest(), hashlib.sha256(source._owned.path.read_bytes()).digest())
            return blob

    def test_current_chain_recovery_and_relationships(self):
        blob = self.archive('010')
        with m.VersionedRecovery() as recovery:
            result = recovery.restore(blob, self.phrase)
            self.assertEqual(result['restored_revision'], '010')
            with closing(sqlite3.connect(recovery.target)) as c:
                self.assertEqual(c.execute('SELECT version_num FROM alembic_version').fetchall(), [('010',)])
                self.assertEqual(c.execute('PRAGMA integrity_check').fetchall(), [('ok',)])
                self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(), [])
                self.assertEqual(c.execute('SELECT count(*) FROM login_sessions').fetchone(), (0,))
                self.assertEqual(c.execute('SELECT count(*) FROM users').fetchone(), (2,))
                self.assertEqual(c.execute('SELECT count(*) FROM checkin_revisions JOIN daily_checkins ON checkin_revisions.checkin_id=daily_checkins.id').fetchone(), (1,))
                self.assertEqual(c.execute('SELECT count(*) FROM support_feedback JOIN attack_sessions ON support_feedback.session_id=attack_sessions.id').fetchone(), (1,))

    def test_older_migrates_only_copy_and_is_blocked_from_activation(self):
        blob = self.archive('009')
        with m.VersionedRecovery() as recovery:
            result = recovery.restore(blob, self.phrase)
            self.assertEqual(result, {'source_revision':'009', 'restored_revision':'010', 'sessions_restored':0,
                                      'activation_allowed':False, 'deletion_reconciliation':'not established'})
            with closing(sqlite3.connect(recovery.target)) as c:
                self.assertEqual(c.execute('SELECT version_num FROM alembic_version').fetchall(), [('010',)])
                self.assertIn('last_activity_at_ms', [row[1] for row in c.execute('PRAGMA table_info(login_sessions)')])
                self.assertEqual(c.execute('SELECT count(*) FROM login_sessions').fetchone(), (0,))
                self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(), [])
            engine = create_engine('sqlite:///' + recovery.target.as_posix(), connect_args={'check_same_thread':False})
            factory = sessionmaker(bind=engine)
            def override():
                with factory() as session: yield session
            m.fixture.app.dependency_overrides[m.fixture.db] = override
            try:
                with TestClient(m.fixture.app, headers={'Origin':'http://localhost:5173'}) as client:
                    client.cookies.set('migramind_session', m.fixture.COOKIE)
                    self.assertEqual(client.get('/api/episodes', headers={'X-CSRF-Token':m.fixture.CSRF}).status_code, 401)
            finally:
                m.fixture.app.dependency_overrides.clear(); m.fixture.auth.limiter.clear(); engine.dispose()

    def test_unknown_missing_tampered_and_inconsistent_version_rejected(self):
        blob = self.archive('009')
        metadata, end = metadata_parts(blob)
        for version in ('011', 'unknown', ''):
            changed = dict(metadata); changed['schema'] = m.PREFIX + version
            encoded = crypto._canonical(changed)
            candidate = crypto.MAGIC + bytes([crypto.VERSION]) + len(encoded).to_bytes(2, 'big') + encoded + blob[end:]
            with m.VersionedRecovery() as recovery:
                with self.assertRaises(crypto.RejectedBackup): recovery.restore(candidate, self.phrase)
        tampered = dict(metadata); tampered['schema'] = m.PREFIX + '010'
        encoded = crypto._canonical(tampered)
        with m.VersionedRecovery() as recovery:
            with self.assertRaises(crypto.RejectedBackup):
                recovery.restore(crypto.MAGIC + bytes([crypto.VERSION]) + len(encoded).to_bytes(2, 'big') + encoded + blob[end:], self.phrase)
        changed = dict(metadata); del changed['schema']; encoded = crypto._canonical(changed)
        with m.VersionedRecovery() as recovery:
            with self.assertRaises(crypto.RejectedBackup):
                recovery.restore(crypto.MAGIC + bytes([crypto.VERSION]) + len(encoded).to_bytes(2, 'big') + encoded + blob[end:], self.phrase)
        # Authenticate a deliberately inconsistent revision; image validation must reject it.
        raw = AESGCM(crypto._key(self.phrase, bytes.fromhex(metadata['salt']))).decrypt(bytes.fromhex(metadata['nonce']), blob[end:], blob[:end])
        metadata['schema'] = m.PREFIX + '010'; encoded = crypto._canonical(metadata)
        aad = crypto.MAGIC + bytes([crypto.VERSION]) + len(encoded).to_bytes(2, 'big') + encoded
        # Fresh nonce for test resealing.
        metadata['nonce'] = secrets.token_bytes(12).hex(); encoded = crypto._canonical(metadata)
        aad = crypto.MAGIC + bytes([crypto.VERSION]) + len(encoded).to_bytes(2, 'big') + encoded
        candidate = aad + AESGCM(crypto._key(self.phrase, bytes.fromhex(metadata['salt']))).encrypt(bytes.fromhex(metadata['nonce']), raw, aad)
        with m.VersionedRecovery() as recovery:
            with self.assertRaises(crypto.RejectedBackup): recovery.restore(candidate, self.phrase)

    def test_wrong_phrase_corruption_destination_and_failed_migration(self):
        blob = self.archive('009'); corrupted = bytearray(blob); corrupted[-1] ^= 1
        with m.VersionedRecovery() as recovery:
            for candidate, phrase in ((blob, secrets.token_bytes(32)), (bytes(corrupted), self.phrase)):
                with self.assertRaises(crypto.RejectedBackup): recovery.restore(candidate, phrase)
            recovery.target.write_bytes(b'synthetic existing')
            with self.assertRaises(crypto.RecoveryFailed): recovery.restore(blob, self.phrase)
            self.assertEqual(recovery.target.read_bytes(), b'synthetic existing')
        original = m._OwnedDatabase.upgrade
        def fail_head(target, rev):
            if rev == '010':
                with closing(target.connect()) as connection:
                    connection.execute('CREATE TABLE synthetic_partial_migration(id INTEGER)')
                    connection.commit()
                raise RuntimeError('synthetic migration failure')
            return original(target, rev)
        with m.VersionedRecovery() as recovery, patch.object(m._OwnedDatabase, 'upgrade', fail_head):
            with self.assertRaises(crypto.RecoveryFailed): recovery.restore(blob, self.phrase)
            self.assertFalse(recovery.target.exists())

    def test_compare_current_migrations_to_models(self):
        with m._OwnedDatabase() as target:
            target.upgrade('010')
            engine = target.engine()
            try:
                with engine.connect() as connection:
                    changes = compare_metadata(MigrationContext.configure(connection), m.fixture.Base.metadata)
                    summary = sorted(set(str(item[0] if isinstance(item, tuple) else item[0][0]) for item in changes))
                    print('Synthetic migration/model comparison:', len(changes), 'differences;', summary)
                    for group in changes:
                        for item in (group if isinstance(group, list) else [group]):
                            print('Difference:', item[0], item[2], item[3], str(item[-2]), '->', str(item[-1]))
                    self.assertIsInstance(changes, list)
            finally: engine.dispose()

    def test_older_copy_can_reintroduce_a_later_deleted_fictional_account(self):
        with m.VersionedBackup('009') as source:
            blob = source.encrypt(self.phrase)
            # A later deletion in the independently owned source is not present
            # in the already-created backup and is not an authoritative ledger.
            with closing(source._owned.connect()) as connection:
                connection.execute('PRAGMA foreign_keys=ON')
                connection.execute('DELETE FROM episodes WHERE owner_id=2')
                connection.execute('DELETE FROM users WHERE id=2')
                connection.commit()
                self.assertEqual(connection.execute('SELECT count(*) FROM users WHERE id=2').fetchone(), (0,))
        with m.VersionedRecovery() as recovery:
            result = recovery.restore(blob, self.phrase)
            with closing(sqlite3.connect(recovery.target)) as c:
                self.assertEqual(c.execute('SELECT count(*) FROM users WHERE id=2').fetchone(), (1,))
                self.assertEqual(c.execute('SELECT count(*) FROM episodes WHERE owner_id=2').fetchone(), (1,))
            self.assertFalse(result['activation_allowed'])


if __name__ == '__main__': unittest.main(verbosity=2)
