"""Run only through run_app_schema_tests.py with a restricted environment."""
from contextlib import closing
import hashlib
import secrets
import sqlite3
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import application_schema_exercise as m
import recoverable_sqlite as backup


class ApplicationSchemaTests(unittest.TestCase):
    def setUp(self):
        self.phrase = secrets.token_bytes(32)
        with m.AppSchemaBackup() as source:
            self.blob = source.encrypt(self.phrase)

    def test_schema_records_and_foreign_keys(self):
        with m.AppSchemaRecovery() as recovery:
            recovery.restore(self.blob, self.phrase)
            image = recovery.target.read_bytes()
            self.assertNotIn(m.CSRF.encode(), image)
            self.assertNotIn(hashlib.sha256(m.COOKIE.encode()).hexdigest().encode(), image)
            with closing(sqlite3.connect(recovery.target)) as c:
                self.assertEqual(c.execute('PRAGMA integrity_check').fetchall(), [('ok',)])
                self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(), [])
                self.assertEqual(c.execute('SELECT count(*) FROM users').fetchone(), (2,))
                self.assertEqual(c.execute('SELECT count(*) FROM login_sessions').fetchone(), (0,))
                self.assertEqual(c.execute('SELECT count(*) FROM checkin_revisions JOIN daily_checkins ON checkin_revisions.checkin_id=daily_checkins.id').fetchone(), (1,))
                self.assertEqual(c.execute('SELECT count(*) FROM support_feedback JOIN attack_sessions ON support_feedback.session_id=attack_sessions.id').fetchone(), (1,))
                self.assertEqual(c.execute('SELECT count(*) FROM support_preferences JOIN contacts ON support_preferences.preferred_contact_id=contacts.id').fetchone(), (1,))

    def test_models_reopen_session_revocation_and_account_isolation(self):
        with m.AppSchemaRecovery() as recovery:
            recovery.restore(self.blob, self.phrase)
            engine = create_engine('sqlite:///' + recovery.target.as_posix(), connect_args={'check_same_thread': False})
            factory = sessionmaker(bind=engine)
            def override():
                with factory() as session: yield session
            m.app.dependency_overrides[m.db] = override
            try:
                with factory() as session:
                    self.assertEqual(session.query(m.User).count(), 2)
                    self.assertEqual(session.query(m.Episode).filter_by(owner_id=1).one().symptoms, ['synthetic nausea'])
                    self.assertEqual(session.query(m.LoginSession).count(), 0)
                with TestClient(m.app, headers={'Origin':'http://localhost:5173'}) as client:
                    client.cookies.set('migramind_session', m.COOKIE)
                    self.assertEqual(client.get('/api/episodes', headers={'X-CSRF-Token':m.CSRF}).status_code, 401)
                    # Create fresh synthetic sessions directly, then exercise actual API authorization.
                    with factory() as session:
                        for i in (1, 2):
                            session.add(m.LoginSession(user_id=i, token_digest=hashlib.sha256(f'synthetic-new-{i}'.encode()).hexdigest(),
                                csrf_token=f'synthetic-csrf-{i}', expires_at='2099-01-01T00:00:00+00:00'))
                        session.commit()
                    for i in (1, 2):
                        client.cookies.clear(); client.cookies.set('migramind_session', f'synthetic-new-{i}')
                        response = client.get('/api/episodes', headers={'X-CSRF-Token':f'synthetic-csrf-{i}'})
                        self.assertEqual(response.status_code, 200)
                        self.assertEqual([row['owner_id'] for row in response.json()], [i])
            finally:
                m.app.dependency_overrides.clear(); m.auth.limiter.clear(); engine.dispose()

    def test_application_issued_session_is_invalid_after_restore(self):
        with m.AppSchemaBackup() as source:
            source_engine = create_engine('sqlite:///' + (source._root / 'synthetic-source.sqlite').as_posix(), connect_args={'check_same_thread': False})
            factory = sessionmaker(bind=source_engine)
            def override_source():
                with factory() as session: yield session
            m.app.dependency_overrides[m.db] = override_source
            try:
                with TestClient(m.app, headers={'Origin':'http://localhost:5173'}) as client:
                    csrf = client.get('/api/auth/session').json()['csrf_token']
                    result = client.post('/api/auth/login', headers={'X-CSRF-Token':csrf},
                                         json={'email':'synthetic-1@example.test', 'password':m.PASSWORD})
                    self.assertEqual(result.status_code, 200)
                    cookie = client.cookies.get('migramind_session')
                    issued_csrf = result.json()['csrf_token']
                    self.assertEqual(client.get('/api/episodes', headers={'X-CSRF-Token':issued_csrf}).status_code, 200)
                blob = source.encrypt(self.phrase)
            finally:
                m.app.dependency_overrides.clear(); m.auth.limiter.clear(); source_engine.dispose()
        with m.AppSchemaRecovery() as recovery:
            recovery.restore(blob, self.phrase)
            engine = create_engine('sqlite:///' + recovery.target.as_posix(), connect_args={'check_same_thread':False})
            factory = sessionmaker(bind=engine)
            def override_recovery():
                with factory() as session: yield session
            m.app.dependency_overrides[m.db] = override_recovery
            try:
                with TestClient(m.app, headers={'Origin':'http://localhost:5173'}) as client:
                    client.cookies.set('migramind_session', cookie)
                    self.assertEqual(client.get('/api/episodes', headers={'X-CSRF-Token':issued_csrf}).status_code, 401)
            finally:
                m.app.dependency_overrides.clear(); m.auth.limiter.clear(); engine.dispose()

    def test_wrong_passphrase_and_corruption(self):
        bad = bytearray(self.blob); bad[-1] ^= 1
        with m.AppSchemaRecovery() as recovery:
            for blob, phrase in ((self.blob, secrets.token_bytes(32)), (bytes(bad), self.phrase)):
                with self.assertRaises(backup.RejectedBackup): recovery.restore(blob, phrase)
            self.assertFalse(recovery.target.exists())

    def test_schema_drift_is_rejected(self):
        with m.AppSchemaRecovery() as recovery:
            raw = recovery._open(self.blob, self.phrase)
        with closing(sqlite3.connect(':memory:')) as connection:
            connection.deserialize(raw)
            connection.execute('CREATE TABLE unexpected_synthetic_object(id INTEGER)')
            changed = connection.serialize()
        with self.assertRaises(ValueError): m.inspect_image(changed)

    def test_existing_destination_and_interruption(self):
        with m.AppSchemaRecovery() as recovery:
            recovery.target.write_bytes(b'synthetic existing')
            with self.assertRaises(backup.RecoveryFailed): recovery.restore(self.blob, self.phrase)
            self.assertEqual(recovery.target.read_bytes(), b'synthetic existing')
        with m.AppSchemaRecovery() as recovery:
            with patch.object(backup.os, 'link', side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt): recovery.restore(self.blob, self.phrase)
            self.assertFalse(recovery.target.exists())
            self.assertEqual(list(recovery._root.glob('.synthetic-recovery-*')), [])


if __name__ == '__main__': unittest.main(verbosity=2)
