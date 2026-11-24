"""Only newly generated SQLite fixtures; no app imports or input paths."""
from contextlib import closing
from pathlib import Path
import sqlite3
import subprocess
import sys
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import sqlite_exercise as module


class SQLiteExerciseTests(unittest.TestCase):
    def test_cli_rejects_input_paths_without_opening_them(self):
        result=subprocess.run([sys.executable,'-I','-B',module.__file__,'--input','not-opened.sqlite'],
                              capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,2)
        self.assertEqual(result.stdout,'')
        self.assertIn('No paths, keys or input arguments',result.stderr)

    def test_snapshot_excludes_other_connection_uncommitted_wal_write(self):
        with module.SyntheticSQLiteExercise() as exercise:
            with closing(sqlite3.connect(exercise._source_path)) as writer:
                writer.execute('BEGIN IMMEDIATE')
                writer.execute("INSERT INTO synthetic_records VALUES (3,'SYNTHETIC uncommitted',2)")
                exercise.backup()
                writer.rollback()
            exercise.restore()
            with closing(sqlite3.connect(exercise.recovery_target)) as recovered:
                self.assertEqual(tuple(recovered.execute('SELECT id,label,severity FROM synthetic_records ORDER BY id')),exercise._records)

    def test_wal_snapshot_and_restore_preserve_committed_records(self):
        with module.SyntheticSQLiteExercise() as exercise:
            self.assertTrue(Path(str(exercise._source_path)+'-wal').exists())
            blob=exercise.backup()
            self.assertEqual((exercise._root/'synthetic-sqlite-backup.bin').read_bytes(),blob)
            self.assertNotIn(b'SYNTHETIC migraine example',blob)
            self.assertNotIn(b'SQLite format 3',blob)
            exercise._source.execute("INSERT INTO synthetic_records VALUES (3,'SYNTHETIC later',2)")
            exercise._source.commit()
            self.assertEqual(exercise.restore(),{'synthetic_only':True,'records':2})
            with closing(sqlite3.connect(exercise.recovery_target)) as recovered:
                self.assertEqual(recovered.execute('PRAGMA integrity_check').fetchall(),[('ok',)])
                self.assertEqual(tuple(recovered.execute('SELECT id,label,severity FROM synthetic_records ORDER BY id')),exercise._records)
                self.assertEqual(recovered.execute('SELECT count(*) FROM synthetic_records').fetchone()[0],2)

    def test_wrong_key_rejected_before_staging(self):
        with module.SyntheticSQLiteExercise() as exercise:
            blob=exercise.backup()
            with patch.object(exercise,'_key',AESGCM.generate_key(bit_length=256)), \
                 patch.object(module.tempfile,'mkstemp',side_effect=AssertionError('No staging')):
                with self.assertRaises(module.RejectedBackup):exercise.restore(blob)
            self.assertFalse(exercise.recovery_target.exists())

    def test_corrupt_and_truncated_rejected_before_staging(self):
        with module.SyntheticSQLiteExercise() as exercise:
            blob=exercise.backup()
            corrupt=bytearray(blob);corrupt[-1]^=1
            with patch.object(module.tempfile,'mkstemp',side_effect=AssertionError('No staging')):
                for candidate in (bytes(corrupt),blob[:-1],blob[:20],b'',blob+b'extra'):
                    with self.subTest(length=len(candidate)),self.assertRaises(module.RejectedBackup):exercise.restore(candidate)
            self.assertFalse(exercise.recovery_target.exists())

    def test_existing_destination_never_overwritten(self):
        with module.SyntheticSQLiteExercise() as exercise:
            exercise.backup();exercise.recovery_target.write_bytes(b'SYNTHETIC existing')
            with self.assertRaises(module.RecoveryFailed):exercise.restore()
            self.assertEqual(exercise.recovery_target.read_bytes(),b'SYNTHETIC existing')

    def test_failed_restore_never_publishes_or_leaves_stage(self):
        for operation in ('fsync','link'):
            with self.subTest(operation=operation),module.SyntheticSQLiteExercise() as exercise:
                exercise.backup()
                with patch.object(module.os,operation,side_effect=OSError('synthetic fault')):
                    with self.assertRaises(module.RecoveryFailed):exercise.restore()
                self.assertFalse(exercise.recovery_target.exists())
                self.assertEqual(list(exercise._root.glob('.sqlite-verified-*')),[])

    def test_interrupted_restore_removes_staging(self):
        with module.SyntheticSQLiteExercise() as exercise:
            exercise.backup()
            with patch.object(module.os,'link',side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):exercise.restore()
            self.assertFalse(exercise.recovery_target.exists())
            self.assertEqual(list(exercise._root.glob('.sqlite-verified-*')),[])

    def test_missing_snapshot_and_other_exercise_backup_refused(self):
        with module.SyntheticSQLiteExercise() as first,module.SyntheticSQLiteExercise() as second:
            with self.assertRaises(module.RejectedBackup):first.restore()
            other=second.backup();first.backup()
            with self.assertRaises(module.RejectedBackup):first.restore(other)

    def test_existing_published_recovery_survives_repeated_restore(self):
        with module.SyntheticSQLiteExercise() as exercise:
            blob=exercise.backup();exercise.restore();before=exercise.recovery_target.read_bytes()
            with self.assertRaises(module.RecoveryFailed):exercise.restore(blob)
            self.assertEqual(exercise.recovery_target.read_bytes(),before)

    def test_publication_race_does_not_replace_competing_file(self):
        with module.SyntheticSQLiteExercise() as exercise:
            exercise.backup();real_link=module.os.link
            def competing(stage,target):
                Path(target).write_bytes(b'SYNTHETIC competing output')
                real_link(stage,target)
            with patch.object(module.os,'link',side_effect=competing):
                with self.assertRaises(module.RecoveryFailed):exercise.restore()
            self.assertEqual(exercise.recovery_target.read_bytes(),b'SYNTHETIC competing output')

    def test_ephemeral_key_is_not_written_to_exercise_files(self):
        exercise=module.SyntheticSQLiteExercise()
        with exercise:
            exercise.backup();exercise.restore()
            self.assertFalse(any(exercise._key in path.read_bytes() for path in exercise._root.iterdir() if path.is_file()))
        self.assertIsNone(exercise._key)


if __name__=='__main__':unittest.main()
