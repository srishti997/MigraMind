"""Synthetic-only, no app integration, user-file input, key files or persistent recovery.

Requires Python 3.10+. All paths are created internally beneath a new sandbox.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"MM-SYNTH-AEAD\x00"
VERSION = 1
MAX_BLOB = 64 * 1024
MAX_METADATA = 2048
SCHEMA = "migramind.synthetic-json/1"


class RejectedBackup(Exception):
    """Value-free failure; do not attach keys, input or raw library exceptions."""


class RecoveryFailed(Exception):
    """No successful publication; existing targets are never replaced."""


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def _unique_pairs(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError()
        result[name] = value
    return result


def _invalid_constant(_value):
    raise ValueError()


def _json(raw):
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs,
                      parse_constant=_invalid_constant)


class SyntheticExercise:
    """A single fresh data set, fresh 256-bit key, single backup and fixed target.

    Private Python attributes are not a security boundary against a debugger.
    Do not adapt this class to read real records or take caller-selected paths.
    """

    def __init__(self):
        self._temp = None
        self._key = self._payload = self._backup_id = self._backup = None

    def __enter__(self):
        if self._temp is not None:
            raise RuntimeError("Use a new synthetic exercise")
        self._temp = tempfile.TemporaryDirectory(prefix="migramind-synthetic-aead-")
        try:
            self._root = Path(self._temp.name)
            self._key = AESGCM.generate_key(bit_length=256)
            self._backup_id = secrets.token_hex(16)
            self._count = 4 + secrets.randbelow(5)
            records = [{"synthetic_id": secrets.token_hex(16),
                        "day_index": secrets.randbelow(365),
                        "severity_example": secrets.randbelow(11)}
                       for _ in range(self._count)]
            self._payload = _canonical({"classification": "SYNTHETIC_ONLY",
                                       "schema": SCHEMA, "backup_id": self._backup_id,
                                       "records": records})
            metadata = {"algorithm": "AES-256-GCM", "backup_id": self._backup_id,
                        "classification": "SYNTHETIC_ONLY", "payload_schema": SCHEMA,
                        "record_count": self._count, "version": VERSION}
            encoded = _canonical(metadata)
            nonce = os.urandom(12)
            # Exact prefix + version + length + metadata + nonce is associated data.
            aad = MAGIC + bytes([VERSION]) + len(encoded).to_bytes(2, "big") + encoded + nonce
            self._backup = aad + AESGCM(self._key).encrypt(nonce, self._payload, aad)
            self._backup_path = self._root / "synthetic-backup.bin"
            with self._backup_path.open("xb") as stream:
                stream.write(self._backup)
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *_args):
        # Drop references; immutable Python bytes cannot be reliably zeroized.
        self._key = self._payload = self._backup_id = self._backup = None
        temporary, self._temp = self._temp, None
        if temporary is not None:
            temporary.cleanup()

    def _active(self):
        if self._temp is None:
            raise RuntimeError("Synthetic exercise is closed")

    @property
    def backup(self):
        self._active()
        return self._backup

    @property
    def recovery_target(self):
        self._active()
        return self._root / "recovered-synthetic.json"

    def _authenticate(self, blob):
        try:
            if type(blob) is not bytes or not len(MAGIC) + 1 + 2 + 12 + 16 < len(blob) <= MAX_BLOB:
                raise ValueError()
            offset = len(MAGIC)
            if blob[:offset] != MAGIC or blob[offset] != VERSION:
                raise ValueError()
            size = int.from_bytes(blob[offset + 1:offset + 3], "big")
            if not 1 <= size <= MAX_METADATA:
                raise ValueError()
            start = offset + 3
            end = start + size
            if end + 12 + 16 >= len(blob):
                raise ValueError()
            encoded = blob[start:end]
            nonce = blob[end:end + 12]
            aad = blob[:end + 12]
            # Authenticate before trusting or parsing metadata/plaintext.
            plaintext = AESGCM(self._key).decrypt(nonce, blob[end + 12:], aad)
            metadata = _json(encoded)
            expected = {"algorithm": "AES-256-GCM", "backup_id": self._backup_id,
                        "classification": "SYNTHETIC_ONLY", "payload_schema": SCHEMA,
                        "record_count": self._count, "version": VERSION}
            if (type(metadata) is not dict or _canonical(metadata) != encoded
                    or metadata != expected or type(metadata.get("version")) is not int
                    or type(metadata.get("record_count")) is not int):
                raise ValueError()
            payload = _json(plaintext)
            if (type(payload) is not dict
                    or set(payload) != {"classification", "schema", "backup_id", "records"}
                    or payload["classification"] != "SYNTHETIC_ONLY"
                    or payload["schema"] != SCHEMA or payload["backup_id"] != self._backup_id
                    or type(payload["records"]) is not list
                    or len(payload["records"]) != self._count):
                raise ValueError()
            for record in payload["records"]:
                if (type(record) is not dict
                        or set(record) != {"synthetic_id", "day_index", "severity_example"}
                        or type(record["synthetic_id"]) is not str
                        or len(record["synthetic_id"]) != 32
                        or any(c not in "0123456789abcdef" for c in record["synthetic_id"])
                        or type(record["day_index"]) is not int or not 0 <= record["day_index"] < 365
                        or type(record["severity_example"]) is not int
                        or not 0 <= record["severity_example"] <= 10):
                    raise ValueError()
            if (_canonical(payload) != plaintext
                    or hashlib.sha256(plaintext).digest() != hashlib.sha256(self._payload).digest()):
                raise ValueError()
            return plaintext
        except (InvalidTag, ValueError, TypeError, KeyError, UnicodeError, RecursionError, OverflowError):
            raise RejectedBackup("Synthetic backup rejected") from None

    def restore(self, candidate=None):
        """Authenticate/validate entirely before staging; atomically publish NEW only.

        os.link is an atomic no-clobber publication on supported local filesystems.
        No os.replace fallback: unavailable hard links fail closed. A concurrent
        or pre-existing target is never overwritten, even for a valid backup.
        """
        self._active()
        plaintext = self._authenticate(self.backup if candidate is None else candidate)
        stage = None
        try:
            fd, stage = tempfile.mkstemp(prefix=".verified-", dir=self._root)
            with os.fdopen(fd, "wb") as stream:
                stream.write(plaintext)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(stage, self.recovery_target)
        except OSError:
            raise RecoveryFailed("Synthetic recovery could not be published") from None
        finally:
            if stage is not None:
                # Only a file freshly created by mkstemp in our own sandbox.
                try:
                    os.unlink(stage)
                except OSError:
                    pass  # Context cleanup retries; never claim secure erasure.
        return {"synthetic_only": True, "records": self._count, "round_trip": True}


def main():
    if len(sys.argv) != 1:
        print("No paths, keys or input arguments are accepted", file=sys.stderr)
        return 2
    try:
        with SyntheticExercise() as exercise:
            result = exercise.restore()
        print(json.dumps(result))
        return 0
    except Exception:
        print("Synthetic exercise failed; no key or payload diagnostics emitted", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
