"""Synthetic SQLite/WAL backup exercise; no application or caller-selected paths."""
import hashlib
from contextlib import closing
import os
from pathlib import Path
import secrets
import sqlite3
import sys
import tempfile

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Isolated Python (-I) does not automatically add the script's own directory.
if __name__ == '__main__': sys.path.insert(0,str(Path(__file__).resolve().parent))
from prototype import RejectedBackup, RecoveryFailed, _canonical, _json

MAGIC = b'MM-SYNTH-SQLITE\x00'
MAX_SNAPSHOT = 1024 * 1024
MAX_META = 1024


class SyntheticSQLiteExercise:
    """Owns every path/connection and an ephemeral key; never accepts input paths."""
    def __init__(self):
        self._temp = self._source = self._key = self._backup = None

    def __enter__(self):
        if self._temp is not None: raise RuntimeError('Use a new synthetic exercise')
        self._temp = tempfile.TemporaryDirectory(prefix='migramind-synthetic-sqlite-')
        try:
            self._root = Path(self._temp.name)
            self._source_path = self._root/'synthetic-source.sqlite'
            # Reserve the name exclusively before SQLite opens the new file.
            with self._source_path.open('xb'): pass
            self._source = sqlite3.connect(self._source_path)
            if self._source.execute('PRAGMA journal_mode=WAL').fetchone()[0].lower() != 'wal':
                raise RuntimeError('Synthetic WAL mode unavailable')
            self._source.execute('PRAGMA wal_autocheckpoint=0')
            self._source.execute('CREATE TABLE synthetic_records (id INTEGER PRIMARY KEY, label TEXT NOT NULL, severity INTEGER NOT NULL)')
            self._records = ((1,'SYNTHETIC migraine example alpha',4),(2,'SYNTHETIC migraine example beta',7))
            self._source.executemany('INSERT INTO synthetic_records VALUES (?,?,?)',self._records)
            self._source.commit()
            self._key=AESGCM.generate_key(bit_length=256)
            self._backup_id=secrets.token_hex(16)
            return self
        except BaseException:
            self.__exit__(None,None,None)
            raise

    def __exit__(self,*_args):
        try:
            if self._source is not None: self._source.close()
        finally:
            self._source=None;self._key=None;self._backup=None
            temporary,self._temp=self._temp,None
            if temporary is not None: temporary.cleanup()

    def _active(self):
        if self._temp is None: raise RuntimeError('Synthetic exercise is closed')

    @property
    def recovery_target(self):
        self._active()
        return self._root/'synthetic-restored.sqlite'

    def backup(self):
        """Snapshot committed source state with SQLite's online backup API."""
        self._active()
        snapshot_path=self._root/'synthetic-snapshot.sqlite'
        with snapshot_path.open('xb'): pass
        try:
            with closing(sqlite3.connect(snapshot_path)) as snapshot:
                self._source.backup(snapshot)
                # Normalize the standalone copy, not the WAL-mode source. An
                # in-memory deserializer cannot open a WAL-header image.
                if snapshot.execute('PRAGMA journal_mode=DELETE').fetchone()[0].lower()!='delete':
                    raise RecoveryFailed('Synthetic snapshot journal mode rejected')
                if snapshot.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:
                    raise RecoveryFailed('Synthetic snapshot failed integrity check')
                rows=tuple(snapshot.execute('SELECT id,label,severity FROM synthetic_records ORDER BY id'))
                if rows!=self._records: raise RecoveryFailed('Unexpected synthetic snapshot')
            raw=snapshot_path.read_bytes()
        finally:
            snapshot_path.unlink(missing_ok=True)
        if not 0<len(raw)<=MAX_SNAPSHOT: raise RecoveryFailed('Synthetic snapshot size rejected')
        self._digest=hashlib.sha256(raw).digest()
        metadata=_canonical({'classification':'SYNTHETIC_ONLY','format':'synthetic-sqlite/1',
                             'backup_id':self._backup_id,'algorithm':'AES-256-GCM'})
        nonce=os.urandom(12)
        aad=MAGIC+len(metadata).to_bytes(2,'big')+metadata+nonce
        self._backup=aad+AESGCM(self._key).encrypt(nonce,raw,aad)
        with (self._root/'synthetic-sqlite-backup.bin').open('xb') as output:
            output.write(self._backup)
        return self._backup

    def _authenticate(self, blob):
        try:
            if type(blob) is not bytes or self._backup is None or len(blob)>MAX_SNAPSHOT+MAX_META+64:
                raise ValueError()
            offset=len(MAGIC)
            if blob[:offset]!=MAGIC or len(blob)<offset+2+12+16: raise ValueError()
            size=int.from_bytes(blob[offset:offset+2],'big')
            if not 1<=size<=MAX_META: raise ValueError()
            start=offset+2;end=start+size
            if end+12+16>=len(blob): raise ValueError()
            nonce=blob[end:end+12];aad=blob[:end+12]
            raw=AESGCM(self._key).decrypt(nonce,blob[end+12:],aad)
            metadata=_json(blob[start:end])
            expected={'classification':'SYNTHETIC_ONLY','format':'synthetic-sqlite/1',
                      'backup_id':self._backup_id,'algorithm':'AES-256-GCM'}
            if metadata!=expected or _canonical(metadata)!=blob[start:end] or not 0<len(raw)<=MAX_SNAPSHOT:
                raise ValueError()
            if hashlib.sha256(raw).digest()!=self._digest: raise ValueError()
            with closing(sqlite3.connect(':memory:')) as candidate:
                candidate.deserialize(raw)
                if candidate.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]: raise ValueError()
                objects=candidate.execute("SELECT type,name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name").fetchall()
                if objects!=[('table','synthetic_records')]: raise ValueError()
                if tuple(candidate.execute('SELECT id,label,severity FROM synthetic_records ORDER BY id'))!=self._records:
                    raise ValueError()
            return raw
        except (InvalidTag,ValueError,TypeError,KeyError,UnicodeError,OverflowError,RecursionError,sqlite3.Error):
            raise RejectedBackup('Synthetic backup rejected') from None

    def restore(self, candidate=None):
        """Authenticate and inspect in memory, then publish an exclusively new file."""
        self._active()
        raw=self._authenticate(self._backup if candidate is None else candidate)
        stage=None
        try:
            fd,stage=tempfile.mkstemp(prefix='.sqlite-verified-',dir=self._root)
            with os.fdopen(fd,'wb') as stream:
                stream.write(raw);stream.flush();os.fsync(stream.fileno())
            os.link(stage,self.recovery_target)  # Atomic no-clobber; no overwrite fallback.
        except OSError:
            raise RecoveryFailed('Synthetic recovery could not be published') from None
        finally:
            if stage is not None:
                try: os.unlink(stage)
                except OSError: pass
        return {'synthetic_only':True,'records':len(self._records)}


def main():
    if len(sys.argv)!=1:
        print('No paths, keys or input arguments are accepted',file=sys.stderr);return 2
    try:
        with SyntheticSQLiteExercise() as exercise:
            exercise.backup();result=exercise.restore()
        print('Synthetic SQLite backup and restore completed:',result['records'],'records')
        return 0
    except Exception:
        print('Synthetic SQLite exercise failed',file=sys.stderr);return 1


if __name__=='__main__': raise SystemExit(main())
