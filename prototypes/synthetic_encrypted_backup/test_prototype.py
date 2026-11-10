"""Random synthetic fixtures only; no user files, app imports or secret output."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import prototype as p


def altered(blob, offset):
    output = bytearray(blob)
    output[offset] ^= 1
    return bytes(output)


def reseal(exercise, *, metadata=None, encoded_metadata=None, payload=None):
    """Valid-tag invalid-content fixture; ALWAYS fresh nonce, never reuse GCM nonce."""
    start = len(p.MAGIC) + 3
    size = int.from_bytes(exercise.backup[start - 2:start], "big")
    original = exercise.backup[start:start + size]
    if encoded_metadata is None:
        encoded_metadata = p._canonical(metadata) if metadata is not None else original
    nonce = os.urandom(12)
    aad = p.MAGIC + bytes([p.VERSION]) + len(encoded_metadata).to_bytes(2, "big") + encoded_metadata + nonce
    return aad + AESGCM(exercise._key).encrypt(
        nonce, exercise._payload if payload is None else payload, aad)


class SyntheticBackupTests(unittest.TestCase):
    def rejected(self, exercise, candidate):
        target = exercise.recovery_target
        before = target.read_bytes() if target.exists() else None
        with patch.object(p.tempfile, "mkstemp", side_effect=AssertionError("Unvalidated staging")):
            with self.assertRaises(p.RejectedBackup) as error:
                exercise.restore(candidate)
        self.assertEqual(str(error.exception), "Synthetic backup rejected")
        if before is None:
            self.assertFalse(target.exists())
        else:
            self.assertTrue(target.read_bytes() == before)
        self.assertFalse(list(exercise._root.glob(".verified-*")))

    def test_authenticated_round_trip_and_encrypted_file(self):
        with p.SyntheticExercise() as exercise:
            self.assertTrue(exercise._backup_path.read_bytes() == exercise.backup)
            self.assertFalse(exercise._payload in exercise.backup)
            self.assertEqual(exercise.restore()["synthetic_only"], True)
            self.assertTrue(exercise.recovery_target.read_bytes() == exercise._payload)

    def test_fresh_random_keys_nonces_and_records(self):
        with p.SyntheticExercise() as a, p.SyntheticExercise() as b:
            self.assertTrue(a._key != b._key)  # Never display key operands on failure.
            self.assertTrue(a._backup_id != b._backup_id)
            self.assertTrue(a._payload != b._payload)
            def nonce(blob):
                start = len(p.MAGIC) + 3
                end = start + int.from_bytes(blob[start - 2:start], "big")
                return blob[end:end + 12]
            self.assertTrue(nonce(a.backup) != nonce(b.backup))

    def test_wrong_key_rejected_with_no_output(self):
        with p.SyntheticExercise() as exercise:
            with patch.object(exercise, "_key", AESGCM.generate_key(bit_length=256)):
                self.rejected(exercise, exercise.backup)

    def test_ciphertext_tag_and_nonce_tampering(self):
        with p.SyntheticExercise() as exercise:
            start = len(p.MAGIC) + 3
            end = start + int.from_bytes(exercise.backup[start - 2:start], "big")
            for offset in (end, end + 12, len(exercise.backup) - 1):
                with self.subTest(component=offset - end):
                    self.rejected(exercise, altered(exercise.backup, offset))

    def test_metadata_bytes_are_authenticated(self):
        with p.SyntheticExercise() as exercise:
            # Still-valid JSON, same byte length: fail AEAD before JSON is trusted.
            candidate = exercise.backup.replace(b"AES-256-GCM", b"AES-128-GCM", 1)
            with patch.object(p, "_json", side_effect=AssertionError("Unauthenticated parsing")):
                self.rejected(exercise, candidate)

    def test_magic_version_and_length_validation(self):
        with p.SyntheticExercise() as exercise:
            for offset in (0, len(p.MAGIC), len(p.MAGIC) + 1, len(p.MAGIC) + 2):
                with self.subTest(header_offset=offset):
                    self.rejected(exercise, altered(exercise.backup, offset))

    def test_truncated_appended_and_oversized_inputs(self):
        with p.SyntheticExercise() as exercise:
            for blob in (b"", exercise.backup[:10], exercise.backup[:-1],
                         exercise.backup[:-16], exercise.backup + b"extra",
                         b"x" * (p.MAX_BLOB + 1), "not bytes", bytearray(exercise.backup)):
                self.rejected(exercise, blob)

    def test_metadata_length_bounds(self):
        with p.SyntheticExercise() as exercise:
            offset = len(p.MAGIC) + 1
            for size in (0, p.MAX_METADATA + 1, 65535):
                blob = exercise.backup[:offset] + size.to_bytes(2, "big") + exercise.backup[offset + 2:]
                self.rejected(exercise, blob)

    def test_valid_tag_does_not_bypass_metadata_contract(self):
        with p.SyntheticExercise() as exercise:
            start = len(p.MAGIC) + 3
            size = int.from_bytes(exercise.backup[start - 2:start], "big")
            original = json.loads(exercise.backup[start:start + size])
            variants = ({**original, "version": 2}, {**original, "version": True},
                        {**original, "algorithm": "AES-128-GCM"},
                        {**original, "classification": "other"},
                        {**original, "record_count": 0}, {**original, "extra": "unexpected"},
                        {**original, "payload_schema": "future/2"},
                        {**original, "backup_id": "0" * 32})
            for metadata in variants:
                self.rejected(exercise, reseal(exercise, metadata=metadata))

    def test_duplicate_noncanonical_and_invalid_json_metadata(self):
        with p.SyntheticExercise() as exercise:
            for encoded in (b'{"version":1,"version":1}', b"{} ", b"null", b"[]",
                            b'{"x":NaN}', b"\xff", b"{"):
                self.rejected(exercise, reseal(exercise, encoded_metadata=encoded))

    def test_authenticated_payload_validation_before_any_output(self):
        with p.SyntheticExercise() as exercise:
            original = json.loads(exercise._payload)
            variants = (b"not-json", p._canonical({}),
                        p._canonical({**original, "classification": "other"}),
                        p._canonical({**original, "schema": "future/2"}),
                        p._canonical({**original, "records": []}),
                        p._canonical({**original, "backup_id": "0" * 32}),
                        p._canonical({**original, "extra": True}),
                        p._canonical({**original, "records": [None] * exercise._count}))
            for payload in variants:
                self.rejected(exercise, reseal(exercise, payload=payload))

    def test_record_types_ranges_and_original_batch_binding(self):
        with p.SyntheticExercise() as exercise:
            original = json.loads(exercise._payload)
            first = original["records"][0]
            for changes in ({"day_index": True}, {"day_index": 365},
                            {"severity_example": 11}, {"severity_example": False},
                            {"synthetic_id": "x" * 32}, {"extra": "field"},
                            {"severity_example": (first["severity_example"] + 1) % 11}):
                payload = {**original, "records": [{**first, **changes}, *original["records"][1:]]}
                self.rejected(exercise, reseal(exercise, payload=p._canonical(payload)))

    def test_another_exercise_backup_is_not_accepted(self):
        with p.SyntheticExercise() as a, p.SyntheticExercise() as b:
            self.rejected(a, b.backup)

    def test_failures_never_modify_existing_valid_recovery(self):
        with p.SyntheticExercise() as exercise:
            exercise.restore()
            before = hashlib.sha256(exercise.recovery_target.read_bytes()).digest()
            for blob in (altered(exercise.backup, -1), exercise.backup[:-1],
                         reseal(exercise, payload=b"{}")):
                self.rejected(exercise, blob)
            with patch.object(exercise, "_key", AESGCM.generate_key(bit_length=256)):
                self.rejected(exercise, exercise.backup)
            with self.assertRaises(p.RecoveryFailed):
                exercise.restore()  # Even a VALID repeated restore cannot overwrite.
            self.assertTrue(hashlib.sha256(exercise.recovery_target.read_bytes()).digest() == before)

    def test_staging_and_publication_fail_closed(self):
        for where in ("fsync", "link"):
            with self.subTest(operation=where), p.SyntheticExercise() as exercise:
                with patch.object(p.os, where, side_effect=OSError("synthetic injected failure")):
                    with self.assertRaises(p.RecoveryFailed):
                        exercise.restore()
                self.assertFalse(exercise.recovery_target.exists())
                self.assertFalse(list(exercise._root.glob(".verified-*")))

    def test_publication_race_preserves_other_complete_target(self):
        with p.SyntheticExercise() as exercise:
            real_link = os.link
            def competing_publish(stage, target):
                Path(target).write_bytes(b"SYNTHETIC competing recovery, not user data")
                real_link(stage, target)
            with patch.object(p.os, "link", side_effect=competing_publish):
                with self.assertRaises(p.RecoveryFailed):
                    exercise.restore()
            self.assertTrue(exercise.recovery_target.read_bytes() ==
                            b"SYNTHETIC competing recovery, not user data")
            self.assertFalse(list(exercise._root.glob(".verified-*")))

    def test_io_failures_preserve_existing_valid_target(self):
        with p.SyntheticExercise() as exercise:
            exercise.restore()
            before = exercise.recovery_target.read_bytes()
            for where in ("fsync", "link"):
                with patch.object(p.os, where, side_effect=OSError("synthetic injected failure")):
                    with self.assertRaises(p.RecoveryFailed):
                        exercise.restore()
                self.assertTrue(exercise.recovery_target.read_bytes() == before)
                self.assertFalse(list(exercise._root.glob(".verified-*")))

    def test_keys_are_never_persisted_and_context_drops_references(self):
        exercise = p.SyntheticExercise()
        with exercise:
            root = exercise._root
            exercise.restore()
            files = [path for path in root.iterdir() if path.is_file()]
            self.assertEqual({path.name for path in files},
                             {"synthetic-backup.bin", "recovered-synthetic.json"})
            self.assertFalse(any(exercise._key in path.read_bytes() for path in files))
        self.assertIsNone(exercise._key)
        self.assertIsNone(exercise._payload)
        self.assertFalse(root.exists())
        with self.assertRaises(RuntimeError):
            exercise.restore()

    def test_cli_refuses_paths_and_key_arguments(self):
        result = subprocess.run([sys.executable, "-B", str(Path(p.__file__)),
                                 "--input", "not-opened.json"], capture_output=True,
                                text=True, timeout=20)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("No paths, keys or input arguments", result.stderr)


if __name__ == "__main__":
    unittest.main()
