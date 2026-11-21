"""Stage A preparation. PostgreSQL import/connection requires explicit Stage B CLI."""
from contextlib import contextmanager
from dataclasses import dataclass
import argparse
import getpass
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile
import unittest

CLASSIFICATION = 'SYNTHETIC_ONLY_DISPOSABLE'
ACK = 'I_ACCEPT_STAGE_B_DISPOSABLE_SYNTHETIC_SQL'
SCHEMA_TAG = 'migramind-throttle-harness-v1'
ACTIVE_CONTEXT = None
_EXECUTION_PERMIT = None
# The original fixture role owns its database and therefore does not meet the
# Stage 9I-C privilege boundary. Never enable without an independently reviewed
# non-owner design and corresponding PostgreSQL validation authorization.
EXECUTION_BLOCKED = True


class SafetyError(Exception): pass


@dataclass(frozen=True)
class Target:
    nonce: str
    port: int
    ordinal: int = 1

    def __post_init__(self):
        if not isinstance(self.nonce, str) or re.fullmatch('[0-9a-f]{32}', self.nonce) is None:
            raise SafetyError('Synthetic nonce required')
        if type(self.port) is not int or not 49152 <= self.port <= 65535:
            raise SafetyError('Explicit disposable high port required')
        if type(self.ordinal) is not int or not 1 <= self.ordinal <= 17:
            raise SafetyError('Case ordinal required')

    @property
    def database(self): return 'mm_case_' + self.nonce + '_' + str(self.ordinal).zfill(3)
    @property
    def role(self): return 'mm_fixture_' + self.nonce + '_' + str(self.ordinal).zfill(3)
    @property
    def owner(self): return 'mm_owner_' + self.nonce
    @property
    def maintenance(self): return 'mm_maint_' + self.nonce + '_' + str(self.ordinal).zfill(3)
    @property
    def directory(self): return Path(tempfile.gettempdir()) / ('migramind-pg-harness-' + self.nonce)


def parse_manifest(payload):
    if (not isinstance(payload, dict) or set(payload) != {'format','classification','nonce','port'}
            or type(payload['format']) is not int or payload['format'] != 1
            or payload['classification'] != CLASSIFICATION):
        raise SafetyError('Exact synthetic manifest required; no DSN/host/credentials accepted')
    return Target(payload['nonce'], payload['port'])


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise SafetyError('Duplicate manifest key')
        result[key] = value
    return result


def load_manifest(path):
    path = Path(path)
    # Reject arbitrary paths BEFORE reading any file, including symlink targets.
    if (not path.is_absolute() or path.name != 'target.json'
            or re.fullmatch('migramind-pg-harness-[0-9a-f]{32}', path.parent.name) is None
            or path.parent.parent != Path(tempfile.gettempdir())):
        raise SafetyError('Owned synthetic manifest location required')
    if (path.is_symlink() or path.parent.is_symlink()
            or path.parent.resolve().parent != Path(tempfile.gettempdir()).resolve()):
        raise SafetyError('Owned synthetic manifest location required')
    if path.stat().st_size > 4096: raise SafetyError('Bounded manifest required')
    target = parse_manifest(json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=_unique_object))
    if path.parent.resolve() != target.directory.resolve(): raise SafetyError('Manifest nonce/path mismatch')
    return target


def approval(ack, stage_b):
    if ack != ACK or stage_b is not True: raise SafetyError('Stage B acknowledgement and opt-in required')


def lifecycle_evidence(target, evidence):
    """Offline evidence shape only; never provisions, connects or deletes."""
    fields = {'version','nonce','container_id','image_digest','volume_id','port',
              'database','role','generation','writer','container_owned','volume_owned',
              'exclusive_loopback','privileges_reviewed','objects_reviewed',
              'time_approved','freshness_approved','setup_complete'}
    if not isinstance(evidence,dict) or set(evidence)!=fields:
        raise SafetyError('Complete lifecycle evidence required')
    if (type(evidence['version']) is not int or evidence['version']!=1
            or evidence['nonce']!=target.nonce or evidence['port']!=target.port
            or type(evidence['port']) is not int or evidence['database']!=target.database
            or evidence['role']!=target.role):
        raise SafetyError('Lifecycle identity mismatch')
    for key,pattern in (('container_id',r'[0-9a-f]{64}'),('image_digest',r'sha256:[0-9a-f]{64}'),
                        ('volume_id',r'migramind-pg-harness-[0-9a-f]{32}'),
                        ('generation',r'synthetic-generation-[a-z0-9-]+'),
                        ('writer',r'synthetic-primary-[a-z0-9-]+')):
        if not isinstance(evidence[key],str) or re.fullmatch(pattern,evidence[key]) is None:
            raise SafetyError('Invalid lifecycle identity')
    if evidence['volume_id']!='migramind-pg-harness-'+target.nonce:
        raise SafetyError('Volume identity mismatch')
    for key in ('container_owned','volume_owned','exclusive_loopback','privileges_reviewed',
                'objects_reviewed','time_approved','freshness_approved','setup_complete'):
        if evidence[key] is not True: raise SafetyError('Incomplete lifecycle assertion')
    return True  # Assertions require independent verification; this is not proof.


def finish_contender(transaction_context, observed):
    """Commit only after observed blocking; otherwise request transaction rollback."""
    if observed is True:
        return transaction_context.__exit__(None,None,None)
    return transaction_context.__exit__(RuntimeError,RuntimeError('Contention not confirmed'),None)


def connection_arguments(target, password):
    # Every target field is derived, never a DSN or application environment value.
    return dict(host='127.0.0.1', hostaddr='127.0.0.1', port=target.port,
        dbname=target.database, user=target.role, password=password, passfile=os.devnull,
        connect_timeout=3, sslmode='disable', application_name='migramind-synthetic-throttle-harness',
        options='-c search_path=pg_catalog -c statement_timeout=5000 -c lock_timeout=1000', autocommit=True)


def clean_environment(environment):
    allowed = {'SYSTEMROOT','WINDIR','PATH','COMSPEC','PATHEXT','SYSTEMDRIVE',
               'PROCESSOR_ARCHITECTURE','NUMBER_OF_PROCESSORS','TEMP','TMP'}
    result = {k:environment[k] for k in environment if k.upper() in allowed}
    result.update(PYTHONDONTWRITEBYTECODE='1', PYTHON_DOTENV_DISABLED='1')
    return result


def validate_server_identity(target,identity):
    expected = (target.database, target.role, target.role, target.owner, False, 'off', False, False, False, False, False)
    if (not isinstance(identity,(tuple,list)) or len(identity)!=11
            or any(type(identity[i]) is not bool for i in (4,6,7,8,9,10)) or tuple(identity) != expected):
        raise SafetyError('Database/owner/primary/role isolation mismatch')


def validate_identity(target, identity, marker, unexpected_objects):
    validate_server_identity(target,identity)
    if (not isinstance(marker,(tuple,list)) or len(marker)!=9 or marker[3] is not True
            or tuple(marker) != (target.nonce,target.ordinal,CLASSIFICATION,True,target.database,target.owner,target.role,target.maintenance,SCHEMA_TAG)):
        raise SafetyError('Synthetic-only bootstrap marker mismatch')
    if type(unexpected_objects) is not int or unexpected_objects!=0:
        raise SafetyError('Unexpected database objects; refusing target')


def verify_target(connection, target):
    # Only Stage B calls this, on every independent connection before harness DDL/DML.
    identity = connection.execute('''SELECT current_database(),session_user,current_user,
        pg_get_userbyid(d.datdba),pg_is_in_recovery(),current_setting('transaction_read_only'),
        r.rolsuper,r.rolcreatedb,r.rolcreaterole,r.rolreplication,r.rolbypassrls
        FROM pg_catalog.pg_database d JOIN pg_catalog.pg_roles r ON r.rolname=current_user
        WHERE d.datname=current_database()''').fetchone()
    validate_server_identity(target,identity)  # Reject wrong target before marker contents.
    memberships=connection.execute('''SELECT count(*) FROM pg_catalog.pg_auth_members m
        JOIN pg_catalog.pg_roles r ON r.oid=m.member WHERE r.rolname=current_user''').fetchone()[0]
    schemas=connection.execute('''SELECT count(*) FROM pg_catalog.pg_namespace n
        WHERE n.nspname NOT IN ('pg_catalog','information_schema','public','harness_bootstrap','synthetic_throttle')
        AND n.nspname NOT LIKE 'pg_toast%' AND n.nspname NOT LIKE 'pg_temp%' ''').fetchone()[0]
    extensions=connection.execute("SELECT count(*) FROM pg_catalog.pg_extension WHERE extname<>'plpgsql'").fetchone()[0]
    if any(type(value) is not int or value!=0 for value in (memberships,schemas,extensions)):
        raise SafetyError('Unexpected membership, schema or extension')
    relation=connection.execute('''SELECT c.relkind,pg_get_userbyid(c.relowner),pg_get_userbyid(n.nspowner)
        FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='harness_bootstrap' AND c.relname='identity' ''').fetchone()
    if relation!=('r',target.owner,target.owner):raise SafetyError('Owned plain bootstrap table required')
    owned=connection.execute('''SELECT count(*) FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname IN ('harness_bootstrap','synthetic_throttle')
        AND pg_get_userbyid(c.relowner)<>%s''',(target.owner,)).fetchone()[0]
    if type(owned) is not int or owned!=0:raise SafetyError('Unexpected fixture object ownership')
    rows = connection.execute('''SELECT nonce,case_ordinal,classification,synthetic_only,db_name,owner_name,fixture_role,maintenance_role,schema_tag
        FROM harness_bootstrap.identity WHERE id=1''').fetchall()
    marker_count = connection.execute('SELECT count(*) FROM harness_bootstrap.identity').fetchone()[0]
    unexpected = connection.execute('''SELECT count(*) FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname NOT IN ('pg_catalog','information_schema')
        AND n.nspname NOT LIKE 'pg_toast%' AND n.nspname NOT LIKE 'pg_temp%'
        AND c.relkind IN ('r','p','v','m','f','S') AND
        NOT (n.nspname='harness_bootstrap' AND c.relname='identity') AND
        NOT (n.nspname='synthetic_throttle' AND c.relname IN ('control','windows','bindings'))''').fetchone()[0]
    if len(rows) != 1 or marker_count != 1: raise SafetyError('Exactly one bootstrap marker required')
    validate_identity(target, identity, rows[0], unexpected)


class Context:
    def __init__(self, target, password):
        self.target, self._password = target, password
        self.initialized=False

    def require_case(self, case):
        # A shape comparison is not independently authenticated evidence.
        raise SafetyError('Independently verified fresh per-test case required')

    @contextmanager
    def connect(self):
        if EXECUTION_BLOCKED: raise SafetyError('PostgreSQL execution blocked pending role separation and lifecycle review')
        if _EXECUTION_PERMIT is None: raise SafetyError('No Stage B execution permit')
        if any(k.upper().startswith('PG') or k.upper() in ('DATABASE_URL','APP_ENV','DATA_MODE') for k in os.environ):
            raise SafetyError('Worker environment not isolated')
        # Deliberately lazy: Stage A import/discovery/static tests never import a driver.
        from importlib.metadata import version
        if version('psycopg')!='3.3.6':raise SafetyError('Reviewed psycopg 3.3.6 required; do not install automatically')
        import psycopg
        connection=None
        try:
            connection = psycopg.connect(**connection_arguments(self.target,self._password))
            verify_target(connection,self.target)
            yield connection
        except psycopg.Error as error:
            state=getattr(error,'sqlstate',None)
            safe=state if isinstance(state,str) and re.fullmatch('[A-Z0-9]{5}',state) else 'UNKNOWN'
            raise SafetyError('Synthetic database operation failed; SQLSTATE '+safe) from None
        finally:
            if connection is not None:
                try:connection.close()
                except Exception:raise SafetyError('Synthetic connection cleanup failed') from None


def synthetic_keys(ip='192.0.2.1', account='synthetic@example.test'):
    address = ipaddress.ip_address(ip)
    if not any(address in ipaddress.ip_network(n) for n in ('192.0.2.0/24','198.51.100.0/24','203.0.113.0/24','2001:db8::/32')):
        raise SafetyError('Documentation IPs only')
    if not isinstance(account,str) or not 3 <= len(account) <= 254: raise SafetyError('Synthetic account required')
    account=account.strip().lower()
    if account.count('@')!=1 or not account.split('@')[0] or account.split('@')[1]!='example.test' or any(c.isspace() for c in account):
        raise SafetyError('Synthetic example.test accounts only')
    return (hashlib.sha256(('synthetic-ip:'+str(address)).encode()).digest(),
            hashlib.sha256(('synthetic-account:'+account).encode()).digest())


def reserve(connection, *, action='login', ip='192.0.2.1', account='synthetic@example.test',
            stamp=0, generation='synthetic-generation-1', writer='synthetic-primary-1',
            guard=True, time_trusted=True, fresh=True, fault=None):
    if _EXECUTION_PERMIT is None: raise SafetyError('No Stage B execution permit')
    ip_key,account_key=synthetic_keys(ip,account)
    return connection.execute('SELECT synthetic_throttle.reserve_attempt(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
        (action,1,ip_key,account_key,generation,writer,stamp,guard,time_trusted,fresh,fault)).fetchone()[0]


def initialize(context):
    raise SafetyError('Fixture bootstrap is owned by independent authority')


@contextmanager
def transaction(connection, lock_ms=1000):
    if _EXECUTION_PERMIT is None:raise SafetyError('No Stage B execution permit')
    if type(lock_ms) is not int or not 0 <= lock_ms <= 3000:raise SafetyError('Bounded lock wait required')
    with connection.transaction():
        connection.execute('SET TRANSACTION ISOLATION LEVEL READ COMMITTED')
        connection.execute("SELECT set_config('lock_timeout',%s,true)",(str(lock_ms)+'ms',))
        connection.execute("SELECT set_config('statement_timeout','5000ms',true)")
        yield


def create_manifest(port):
    target=Target(secrets.token_hex(16),port)
    target.directory.mkdir(mode=0o700,exist_ok=False)
    path=target.directory/'target.json'
    with path.open('x',encoding='utf-8') as stream:
        json.dump(dict(format=1,classification=CLASSIFICATION,nonce=target.nonce,port=target.port),stream,indent=2)
    return path


def main(argv=None):
    parser=argparse.ArgumentParser(description='Synthetic harness. Stage A: static tests only; no database setup.')
    sub=parser.add_subparsers(dest='command',required=True)
    plan=sub.add_parser('create-manifest',help='STAGE B ONLY: creates a NEW temporary manifest, no PostgreSQL setup')
    plan.add_argument('--port',type=int,required=True)
    for name in ('run-postgres','_worker'):
        run=sub.add_parser(name,help='STAGE B ONLY: explicit disposable PostgreSQL SQL execution')
        run.add_argument('--manifest',required=True);run.add_argument('--ack',required=True)
        run.add_argument('--stage-b-approved',action='store_true')
    args=parser.parse_args(argv)
    if args.command=='create-manifest':
        print(create_manifest(args.port));return 0
    approval(args.ack,args.stage_b_approved)
    if EXECUTION_BLOCKED: raise SafetyError('PostgreSQL execution blocked pending role separation and lifecycle review')
    target=load_manifest(args.manifest)
    if args.command=='run-postgres':
        return subprocess.run([sys.executable,'-I','-B',str(Path(__file__).resolve()),'_worker',
            '--manifest',str(Path(args.manifest).resolve()),'--ack',ACK,'--stage-b-approved'],
            env=clean_environment(os.environ),check=False,timeout=180).returncode
    # Names only: never inspect inherited application connection-string values.
    if any(k.upper().startswith('PG') or k.upper() in ('DATABASE_URL','APP_ENV','DATA_MODE') for k in os.environ):
        raise SafetyError('Forbidden worker configuration')
    global _EXECUTION_PERMIT,ACTIVE_CONTEXT
    _EXECUTION_PERMIT=object()
    password=getpass.getpass('Fresh disposable synthetic role password (not stored): ')
    ACTIVE_CONTEXT=Context(target,password)
    try:
        initialize(ACTIVE_CONTEXT)
        sys.path.insert(0,str(Path(__file__).resolve().parent))
        # Running as a script must share the permit/context with the test module import.
        sys.modules['harness']=sys.modules[__name__]
        suite=unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent),pattern='test_database.py')
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    finally:
        ACTIVE_CONTEXT=None;_EXECUTION_PERMIT=None;password=None


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception:
        # No DSN, password, SQL parameters, transcript or driver exception logging.
        print('Synthetic harness refused or failed. No production action authorized.',file=sys.stderr)
        raise SystemExit(2)
