"""Synthetic-only passphrase recovery tests; no user paths or app imports."""
from contextlib import closing
import base64
import json
import os
from pathlib import Path
import secrets
import sqlite3
import subprocess
import sys
import unittest
from unittest.mock import patch

import recoverable_sqlite as m


def parts(blob):
    offset=len(m.MAGIC);size=int.from_bytes(blob[offset+1:offset+3],'big')
    end=offset+3+size
    return m._json(blob[offset+3:end]),end


class RecoverableTests(unittest.TestCase):
    def setUp(self):
        self.passphrase=secrets.token_bytes(32)
        with m.SyntheticBackup() as source:self.blob=source.encrypt(self.passphrase)
        # Source is closed and no key is stored in this test or backup object.

    def test_new_context_recovers_rows_relationships_and_no_sessions(self):
        with m.SyntheticRecovery() as recovery:
            self.assertEqual(recovery.restore(self.blob,self.passphrase),{'synthetic_only':True,'sessions_restored':0})
            with closing(sqlite3.connect(recovery.target)) as db:
                self.assertEqual(db.execute('PRAGMA integrity_check').fetchall(),[('ok',)])
                self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
                self.assertEqual(db.execute('SELECT email,day,severity FROM users JOIN episodes ON users.id=episodes.user_id').fetchall(),[('synthetic@example.test','2025-01-02',6)])
                self.assertEqual(db.execute('SELECT symptoms.label,triggers.label FROM episodes JOIN symptoms ON symptoms.episode_id=episodes.id JOIN triggers ON triggers.episode_id=episodes.id').fetchall(),[('SYNTHETIC nausea','SYNTHETIC light')])
                self.assertEqual(db.execute('SELECT count(*) FROM sessions').fetchone(),(0,))

    def test_recovery_in_fresh_process_without_original_key(self):
        # Send synthetic material over a pipe, never through arguments or files.
        worker = r"""
import base64, json, sqlite3, sys
from contextlib import closing
sys.path.insert(0, sys.argv[1])
import recoverable_sqlite as m
data = json.load(sys.stdin)
with m.SyntheticRecovery() as recovery:
    recovery.restore(base64.b64decode(data['blob']), base64.b64decode(data['phrase']))
    with closing(sqlite3.connect(recovery.target)) as db:
        assert db.execute('PRAGMA integrity_check').fetchone() == ('ok',)
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []
        assert db.execute('SELECT count(*) FROM episodes').fetchone() == (1,)
        assert db.execute('SELECT count(*) FROM sessions').fetchone() == (0,)
print('synthetic recovery passed')
"""
        payload = json.dumps({'blob': base64.b64encode(self.blob).decode(),
                              'phrase': base64.b64encode(self.passphrase).decode()})
        allowed = {'PATH', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'TMPDIR'}
        env = {k: v for k, v in os.environ.items() if k.upper() in allowed}
        result = subprocess.run([sys.executable, '-I', '-B', '-c', worker,
                                 str(Path(m.__file__).resolve().parent)],
                                input=payload, text=True, capture_output=True,
                                env=env, timeout=30)
        self.assertEqual(result.returncode, 0, 'Synthetic recovery subprocess failed')
        self.assertEqual(result.stdout.strip(), 'synthetic recovery passed')

    def test_wrong_passphrase_and_corruption_are_rejected_before_staging(self):
        bad=bytearray(self.blob);bad[-1]^=1
        with m.SyntheticRecovery() as recovery,patch.object(m.tempfile,'mkstemp',side_effect=AssertionError('No staging')):
            for blob,phrase in ((self.blob,secrets.token_bytes(32)),(bytes(bad),self.passphrase),(self.blob[:-1],self.passphrase)):
                with self.assertRaises(m.RejectedBackup):recovery.restore(blob,phrase)
            self.assertFalse(recovery.target.exists())

    def test_salts_and_nonces_are_independent(self):
        with m.SyntheticBackup() as source:
            a=source.encrypt(self.passphrase);b=source.encrypt(self.passphrase)
        ma,_=parts(a);mb,_=parts(b)
        self.assertNotEqual(ma['salt'],mb['salt']);self.assertNotEqual(ma['nonce'],mb['nonce'])

    def test_metadata_tamper_and_unsupported_version_rejected(self):
        tampered=self.blob.replace(b'AES-256-GCM',b'AES-128-GCM',1)
        version=bytearray(self.blob);version[len(m.MAGIC)]=2
        with m.SyntheticRecovery() as recovery:
            for candidate in (tampered,bytes(version)):
                with self.assertRaises(m.RejectedBackup):recovery.restore(candidate,self.passphrase)

    def test_excessive_kdf_parameters_rejected_without_derivation(self):
        metadata,end=parts(self.blob);metadata['n']=2**30
        encoded=m._canonical(metadata)
        candidate=m.MAGIC+bytes([m.VERSION])+len(encoded).to_bytes(2,'big')+encoded+self.blob[end:]
        with m.SyntheticRecovery() as recovery,patch.object(m,'_key',side_effect=AssertionError('KDF must not run')):
            with self.assertRaises(m.RejectedBackup):recovery.restore(candidate,self.passphrase)

    def test_existing_destination_and_interruption_are_safe(self):
        with m.SyntheticRecovery() as recovery:
            recovery.target.write_bytes(b'SYNTHETIC existing target')
            with self.assertRaises(m.RecoveryFailed):recovery.restore(self.blob,self.passphrase)
            self.assertEqual(recovery.target.read_bytes(),b'SYNTHETIC existing target')
        with m.SyntheticRecovery() as recovery:
            with patch.object(m.os,'link',side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):recovery.restore(self.blob,self.passphrase)
            self.assertFalse(recovery.target.exists())
            self.assertEqual(list(recovery._root.glob('.synthetic-recovery-*')),[])

    def test_ciphertext_does_not_contain_synthetic_records_or_passphrase(self):
        self.assertNotIn(b'SYNTHETIC nausea',self.blob)
        self.assertNotIn(self.passphrase,self.blob)
        self.assertNotIn(b'SQLite format 3',self.blob)


if __name__=='__main__':unittest.main()
