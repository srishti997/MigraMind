"""Synthetic-only passphrase recovery; never accepts database or backup paths."""
from contextlib import closing
import os
from pathlib import Path
import secrets
import sqlite3
import tempfile

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from prototype import RejectedBackup, RecoveryFailed, _canonical, _json

MAGIC=b'MM-SYNTH-RECOVERABLE\x00'
VERSION=1
N=2**14
R=8
P=1
MAX_METADATA=2048
MAX_IMAGE=1024*1024
USERS=((1,'synthetic@example.test'),)
EPISODES=((1,1,'2025-01-02',6),)
SYMPTOMS=((1,1,'SYNTHETIC nausea'),)
TRIGGERS=((1,1,'SYNTHETIC light'),)


def _key(passphrase, salt):
    if type(passphrase) is not bytes or not 16<=len(passphrase)<=128 or len(salt)!=16:
        raise ValueError('Invalid synthetic passphrase')
    return Scrypt(salt=salt,length=32,n=N,r=R,p=P).derive(passphrase)


def _inspect(raw):
    """Check fixed synthetic fixture and foreign keys in a private memory DB."""
    if not 0<len(raw)<=MAX_IMAGE: raise ValueError()
    with closing(sqlite3.connect(':memory:')) as connection:
        connection.deserialize(raw)
        connection.execute('PRAGMA trusted_schema=OFF')
        if connection.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]: raise ValueError()
        if connection.execute('PRAGMA foreign_key_check').fetchall()!=[]: raise ValueError()
        objects=connection.execute("SELECT type,name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name").fetchall()
        if objects!=[('table','episodes'),('table','sessions'),('table','symptoms'),('table','triggers'),('table','users')]: raise ValueError()
        expected={'users':USERS,'episodes':EPISODES,'symptoms':SYMPTOMS,'triggers':TRIGGERS,'sessions':()}
        for name,rows in expected.items():
            if tuple(connection.execute('SELECT * FROM '+name+' ORDER BY id'))!=rows: raise ValueError()
        for table,parent,column in (('episodes','users','user_id'),('sessions','users','user_id'),
                                    ('symptoms','episodes','episode_id'),('triggers','episodes','episode_id')):
            fks=connection.execute('PRAGMA foreign_key_list('+table+')').fetchall()
            if len(fks)!=1 or fks[0][2:5]!=(parent,column,'id'): raise ValueError()


class SyntheticBackup:
    """Creates its own source and a recoverable encrypted byte string."""
    _schema = 'synthetic-relational/1'
    _session_table = 'sessions'
    _inspect = staticmethod(_inspect)
    def __enter__(self):
        self._temp=tempfile.TemporaryDirectory(prefix='migramind-recoverable-source-')
        self._root=Path(self._temp.name);self._source=None
        try:
            path=self._root/'synthetic-source.sqlite'
            with path.open('xb'): pass
            self._source=sqlite3.connect(path)
            if self._source.execute('PRAGMA journal_mode=WAL').fetchone()[0].lower()!='wal': raise RuntimeError('Synthetic WAL unavailable')
            self._source.execute('PRAGMA wal_autocheckpoint=0')
            self._source.executescript('''
                PRAGMA foreign_keys=ON;
                CREATE TABLE users(id INTEGER PRIMARY KEY,email TEXT NOT NULL);
                CREATE TABLE episodes(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id),day TEXT NOT NULL,severity INTEGER NOT NULL);
                CREATE TABLE symptoms(id INTEGER PRIMARY KEY,episode_id INTEGER NOT NULL REFERENCES episodes(id),label TEXT NOT NULL);
                CREATE TABLE triggers(id INTEGER PRIMARY KEY,episode_id INTEGER NOT NULL REFERENCES episodes(id),label TEXT NOT NULL);
                CREATE TABLE sessions(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id),token TEXT NOT NULL);
                ''')
            self._source.executemany('INSERT INTO users VALUES (?,?)',USERS)
            self._source.executemany('INSERT INTO episodes VALUES (?,?,?,?)',EPISODES)
            self._source.executemany('INSERT INTO symptoms VALUES (?,?,?)',SYMPTOMS)
            self._source.executemany('INSERT INTO triggers VALUES (?,?,?)',TRIGGERS)
            self._source.execute("INSERT INTO sessions VALUES (1,1,'SYNTHETIC revoked session')")
            self._source.commit()
            return self
        except BaseException:
            self.__exit__(None,None,None);raise

    def __exit__(self,*_args):
        try:
            if self._source is not None:self._source.close()
        finally:
            self._source=None
            temporary,self._temp=self._temp,None
            if temporary is not None:temporary.cleanup()

    def encrypt(self,passphrase):
        if self._source is None: raise RuntimeError('Synthetic source closed')
        path=self._root/('snapshot-'+secrets.token_hex(16)+'.sqlite')
        with path.open('xb'): pass
        try:
            with closing(sqlite3.connect(path)) as snapshot:
                self._source.backup(snapshot)
                snapshot.execute('PRAGMA secure_delete=ON')
                snapshot.execute('DELETE FROM ' + self._session_table);snapshot.commit()
                if snapshot.execute('PRAGMA journal_mode=DELETE').fetchone()[0].lower()!='delete':raise ValueError()
                snapshot.execute('VACUUM')
            raw=path.read_bytes();self._inspect(raw)
        finally:
            path.unlink(missing_ok=True)
        salt=os.urandom(16);nonce=os.urandom(12)
        metadata=_canonical({'classification':'SYNTHETIC_ONLY','schema':self._schema,
            'kdf':'scrypt','n':N,'r':R,'p':P,'salt':salt.hex(),'nonce':nonce.hex(),
            'cipher':'AES-256-GCM','sessions':'excluded'})
        aad=MAGIC+bytes([VERSION])+len(metadata).to_bytes(2,'big')+metadata
        return aad+AESGCM(_key(passphrase,salt)).encrypt(nonce,raw,aad)


class SyntheticRecovery:
    """A new context with a fixed fresh target; no input or destination paths."""
    _schema = 'synthetic-relational/1'
    _inspect = staticmethod(_inspect)
    def __enter__(self):
        self._temp=tempfile.TemporaryDirectory(prefix='migramind-recoverable-restore-')
        self._root=Path(self._temp.name)
        return self

    def __exit__(self,*_args):
        temporary,self._temp=self._temp,None
        if temporary is not None:temporary.cleanup()

    @property
    def target(self):
        if self._temp is None:raise RuntimeError('Recovery context closed')
        return self._root/'synthetic-recovered.sqlite'

    def _open(self,blob,passphrase):
        try:
            if type(blob) is not bytes or not len(MAGIC)+3+16<len(blob)<=MAX_IMAGE+MAX_METADATA+64:raise ValueError()
            offset=len(MAGIC)
            if blob[:offset]!=MAGIC or blob[offset]!=VERSION:raise ValueError()
            size=int.from_bytes(blob[offset+1:offset+3],'big')
            if not 1<=size<=MAX_METADATA:raise ValueError()
            end=offset+3+size
            if end+16>=len(blob):raise ValueError()
            encoded=blob[offset+3:end];metadata=_json(encoded)
            if type(metadata) is not dict or set(metadata)!={'classification','schema','kdf','n','r','p','salt','nonce','cipher','sessions'}:raise ValueError()
            if any(type(metadata[k]) is not int for k in ('n','r','p')):raise ValueError()
            expected={'classification':'SYNTHETIC_ONLY','schema':self._schema,
                'kdf':'scrypt','n':N,'r':R,'p':P,'cipher':'AES-256-GCM','sessions':'excluded'}
            if any(metadata[k]!=v for k,v in expected.items()) or _canonical(metadata)!=encoded:raise ValueError()
            salt=bytes.fromhex(metadata['salt']);nonce=bytes.fromhex(metadata['nonce'])
            if len(salt)!=16 or len(nonce)!=12 or metadata['salt']!=salt.hex() or metadata['nonce']!=nonce.hex():raise ValueError()
            raw=AESGCM(_key(passphrase,salt)).decrypt(nonce,blob[end:],blob[:end])
            self._inspect(raw)
            return raw
        except (InvalidTag,ValueError,TypeError,KeyError,UnicodeError,OverflowError,RecursionError,sqlite3.Error):
            raise RejectedBackup('Synthetic backup rejected') from None

    def restore(self,blob,passphrase):
        target=self.target
        raw=self._open(blob,passphrase)
        stage=None
        try:
            fd,stage=tempfile.mkstemp(prefix='.synthetic-recovery-',dir=self._root)
            with os.fdopen(fd,'wb') as stream:
                stream.write(raw);stream.flush();os.fsync(stream.fileno())
            os.link(stage,target)
        except OSError:
            raise RecoveryFailed('Synthetic recovery could not be published') from None
        finally:
            if stage is not None:
                try:os.unlink(stage)
                except OSError:pass
        return {'synthetic_only':True,'sessions_restored':0}
