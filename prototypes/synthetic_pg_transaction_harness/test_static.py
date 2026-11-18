"""Stage A ONLY: pure validation, AST and text checks. No driver or connection."""
import ast
from contextlib import redirect_stderr
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import harness
import test_database


class SafetyChecks(unittest.TestCase):
    def setUp(self):self.target=harness.Target('a'*32,55432)

    def marker(self):
        t=self.target
        return (t.nonce,harness.CLASSIFICATION,True,t.database,t.role,harness.SCHEMA_TAG)

    def identity(self):
        t=self.target
        return (t.database,t.role,t.role,t.role,False,'off',False,False,False,False,False)

    def test_target_is_derived_high_port_and_bounded_identifier(self):
        self.assertTrue(self.target.database.startswith('migramind_throttle_synthetic_'))
        self.assertLessEqual(len(self.target.database),63);self.assertLessEqual(len(self.target.role),63)
        self.assertEqual(set(harness.Target.__dataclass_fields__),{'nonce','port'})

    def test_rejects_connection_string_host_or_credential_manifest_fields(self):
        valid=dict(format=1,classification=harness.CLASSIFICATION,nonce='a'*32,port=55432)
        self.assertEqual(harness.parse_manifest(valid),self.target)
        for extra in ('dsn','host','dbname','user','password','DATABASE_URL'):
            with self.subTest(field=extra),self.assertRaises(harness.SafetyError):
                harness.parse_manifest(valid|{extra:'not-used'})

    def test_missing_or_malformed_manifest_fields_fail_closed(self):
        valid=dict(format=1,classification=harness.CLASSIFICATION,nonce='a'*32,port=55432)
        for field in valid:
            bad=valid.copy();bad.pop(field)
            with self.assertRaises(harness.SafetyError):harness.parse_manifest(bad)
        for bad in (valid|{'format':True},valid|{'classification':'local'},valid|{'port':5432},valid|{'nonce':'../unsafe'}):
            with self.assertRaises(harness.SafetyError):harness.parse_manifest(bad)

    def test_default_and_bool_ports_and_bad_nonces_are_refused(self):
        for port in (5432,8015,49151,65536,True,'55432'):
            with self.assertRaises(harness.SafetyError):harness.Target('a'*32,port)
        for nonce in ('A'*32,'a'*31,'a'*33,'postgres','a/b',''):
            with self.assertRaises(harness.SafetyError):harness.Target(nonce,55432)

    def test_duplicate_manifest_keys_are_refused(self):
        with self.assertRaises(harness.SafetyError):
            json.loads('{"nonce":"a","nonce":"b"}',object_pairs_hook=harness._unique_object)

    def test_arbitrary_path_is_rejected_before_any_file_read(self):
        with patch.object(Path,'read_text',side_effect=AssertionError('File must not be read')):
            with self.assertRaises(harness.SafetyError):harness.load_manifest(Path.cwd()/'not-a-target.json')

    def test_both_stage_b_optins_are_required(self):
        harness.approval(harness.ACK,True)
        for ack,flag in (('',True),(harness.ACK,False),('yes',True),(harness.ACK,1)):
            with self.assertRaises(harness.SafetyError):harness.approval(ack,flag)

    def test_execution_blocked_before_manifest_or_password(self):
        with (patch.object(harness,'load_manifest',side_effect=AssertionError('No read')),
              patch.object(harness.getpass,'getpass',side_effect=AssertionError('No prompt'))):
            with self.assertRaises(harness.SafetyError):
                harness.main(['run-postgres','--manifest','unused','--ack',harness.ACK,'--stage-b-approved'])

    def test_lifecycle_requires_exact_complete_identity_and_assertions(self):
        t=self.target
        e=dict(version=1,nonce=t.nonce,container_id='b'*64,image_digest='sha256:'+'c'*64,
            volume_id='migramind-pg-harness-'+t.nonce,port=t.port,database=t.database,role=t.role,
            generation='synthetic-generation-1',writer='synthetic-primary-1',container_owned=True,
            volume_owned=True,exclusive_loopback=True,privileges_reviewed=True,objects_reviewed=True,
            time_approved=True,freshness_approved=True,setup_complete=True)
        self.assertTrue(harness.lifecycle_evidence(t,e))
        for key in e:
            bad=e.copy();bad.pop(key)
            with self.subTest(missing=key),self.assertRaises(harness.SafetyError):harness.lifecycle_evidence(t,bad)
        for key in ('container_owned','volume_owned','exclusive_loopback','privileges_reviewed',
                    'objects_reviewed','time_approved','freshness_approved','setup_complete'):
            for value in (False,None,1):
                with self.subTest(key=key,value=value),self.assertRaises(harness.SafetyError):
                    harness.lifecycle_evidence(t,e|{key:value})
        for key in ('nonce','container_id','image_digest','volume_id','database','role','generation','writer'):
            with self.subTest(mismatch=key),self.assertRaises(harness.SafetyError):
                harness.lifecycle_evidence(t,e|{key:'mismatch'})

    def test_contender_rolls_back_on_unobserved_contention(self):
        class FakeTransaction:
            def __init__(self): self.args=None
            def __exit__(self,*args): self.args=args
        for observed in (False,None,1):
            tx=FakeTransaction();harness.finish_contender(tx,observed)
            self.assertIs(tx.args[0],RuntimeError)
        tx=FakeTransaction();harness.finish_contender(tx,True)
        self.assertEqual(tx.args,(None,None,None))

    def test_main_missing_ack_never_loads_manifest_or_requests_password(self):
        with (patch.object(harness,'load_manifest',side_effect=AssertionError('No read')),
              patch.object(harness.getpass,'getpass',side_effect=AssertionError('No secret prompt'))):
            with self.assertRaises(harness.SafetyError):
                harness.main(['run-postgres','--manifest','unused','--ack','wrong','--stage-b-approved'])

    def test_no_default_cli_execution(self):
        with redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as caught:harness.main([])
        self.assertEqual(caught.exception.code,2)

    def test_no_execution_permit_means_no_driver_import_or_connection(self):
        before=set(sys.modules)
        context=harness.Context(self.target,object())
        self.assertFalse(context.initialized)
        with self.assertRaises(harness.SafetyError):
            with context.connect():self.fail('Unreachable')
        self.assertFalse(any(n.startswith('psycopg') for n in set(sys.modules)-before))

    def test_static_discovery_has_not_loaded_driver_or_application(self):
        self.assertFalse(any(n=='app' or n.startswith('app.') or n.startswith('psycopg') for n in sys.modules))

    def test_reservation_and_transaction_helpers_are_inert_without_permit(self):
        class Forbidden:
            def execute(self,*args,**kwargs):raise AssertionError('No SQL execution')
            def transaction(self):raise AssertionError('No transaction')
        with self.assertRaises(harness.SafetyError):harness.reserve(Forbidden())
        with self.assertRaises(harness.SafetyError):
            with harness.transaction(Forbidden()):self.fail('Unreachable')

    def test_database_test_class_is_inert_without_runner(self):
        self.assertIsNone(harness.ACTIVE_CONTEXT);self.assertIsNone(harness._EXECUTION_PERMIT)
        with self.assertRaises(unittest.SkipTest):test_database.TransactionTests.setUpClass()

    def test_connection_arguments_are_explicit_not_environment_derived(self):
        sentinel=object();args=harness.connection_arguments(self.target,sentinel)
        self.assertEqual(args['host'],'127.0.0.1');self.assertEqual(args['hostaddr'],'127.0.0.1')
        self.assertEqual(args['dbname'],self.target.database);self.assertEqual(args['user'],self.target.role)
        self.assertIs(args['password'],sentinel);self.assertEqual(args['passfile'],harness.os.devnull)
        self.assertNotIn('dsn',args);self.assertEqual(args['connect_timeout'],3)

    def test_child_environment_cannot_inherit_pg_or_application_settings(self):
        fake={'PATH':'synthetic-path','PGHOST':'not-used','PGSERVICE':'not-used','PGPASSWORD':'not-used',
              'DATABASE_URL':'not-used','APP_ENV':'production','HOME':'not-used','TEMP':'synthetic-temp'}
        cleaned=harness.clean_environment(fake)
        self.assertEqual(cleaned['PATH'],'synthetic-path')
        self.assertFalse(any(k.startswith('PG') or k in ('DATABASE_URL','APP_ENV','HOME') for k in cleaned))
        self.assertEqual(fake['APP_ENV'],'production')  # Caller environment not changed.

    def test_server_identity_marker_and_object_checks_fail_closed(self):
        harness.validate_identity(self.target,self.identity(),self.marker(),0)
        for index in range(len(self.identity())):
            bad=list(self.identity());bad[index]=True if index>=6 else 'mismatch'
            with self.subTest(identity=index),self.assertRaises(harness.SafetyError):
                harness.validate_identity(self.target,bad,self.marker(),0)
        for index in range(len(self.marker())):
            bad=list(self.marker());bad[index]=None
            with self.subTest(marker=index),self.assertRaises(harness.SafetyError):
                harness.validate_identity(self.target,self.identity(),bad,0)
        with self.assertRaises(harness.SafetyError):harness.validate_identity(self.target,self.identity(),self.marker(),1)

    def test_synthetic_identifiers_normalize_and_never_accept_real_inputs(self):
        a=harness.synthetic_keys('2001:db8::1',' SYNTHETIC@example.test ')
        b=harness.synthetic_keys('2001:0db8:0:0:0:0:0:1','synthetic@example.test')
        self.assertEqual(a,b);self.assertTrue(all(len(k)==32 for k in a))
        with self.assertRaises(harness.SafetyError):harness.synthetic_keys('127.0.0.1')
        with self.assertRaises(harness.SafetyError):harness.synthetic_keys(account='real@invalid.test')


class SqlAndSourceChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql=Path(__file__).with_name('schema.sql').read_text(encoding='utf-8')
        cls.source=Path(__file__).with_name('harness.py').read_text(encoding='utf-8')
        cls.prepared=Path(__file__).with_name('test_database.py').read_text(encoding='utf-8')
        cls.design=Path(__file__).with_name('NON_OWNER_DESIGN.md').read_text(encoding='utf-8')

    def test_non_owner_design_requires_separate_authorities_and_no_reset(self):
        for token in ('UNAPPLIED DESIGN ONLY','OWNER <bootstrap_owner>',
                      'NOCREATEDB NOCREATEROLE','NOBYPASSRLS NOINHERIT',
                      'Owns no database','No runner reset command is granted',
                      'No SECURITY DEFINER helper is introduced',
                      'EXECUTION_BLOCKED'):
            self.assertIn(token,self.design)
        self.assertNotIn('GRANT TRUNCATE',self.design)
        self.assertNotIn('GRANT CREATE',self.design)
        self.assertTrue(harness.EXECUTION_BLOCKED)

    def test_teardown_contract_requires_independent_evidence_and_refusal(self):
        for token in ('independent runtime and database observations',
                      'one-use teardown authorization','exclusive lifecycle lease',
                      'generation, writer','time/freshness',
                      'causes refusal and manual review','no fallback by name',
                      'REVIEW_REQUIRED','No automatic cleanup or force-delete'):
            self.assertIn(token,self.design)

    def test_grant_manifest_is_bounded_to_synthetic_objects(self):
        for token in ('GRANT CONNECT ON DATABASE <case_database>',
                      'GRANT SELECT, UPDATE ON synthetic_throttle.control',
                      'GRANT SELECT, UPDATE ON synthetic_throttle.bindings',
                      'GRANT SELECT, INSERT, UPDATE, DELETE ON synthetic_throttle.windows',
                      'REVOKE ALL ON ALL FUNCTIONS IN SCHEMA synthetic_throttle FROM PUBLIC'):
            self.assertIn(token,self.design)
        self.assertIn('Existing lifecycle',self.design)

    def test_sql_guard_precedes_ddl_and_has_no_application_or_database_provisioning(self):
        self.assertLess(self.sql.index('DO $guard$'),self.sql.index('CREATE SCHEMA'))
        for token in ('harness_bootstrap.identity','SYNTHETIC_ONLY_DISPOSABLE','Privileged role refused',
                      'pg_is_in_recovery()','transaction_read_only'):
            self.assertIn(token,self.sql)
        import re
        self.assertIsNone(re.search(r'^\s*(DROP\s|CREATE\s+(DATABASE|ROLE|EXTENSION)\b|TRUNCATE\s)',self.sql,re.M|re.I))
        self.assertNotIn('public.',self.sql);self.assertNotIn('SECURITY DEFINER',self.sql)

    def test_explicit_constraints_indexes_and_no_empty_key_placeholder(self):
        for token in ('PRIMARY KEY(scope,digest)','octet_length(digest)=32','valid_window(scope,times_ms)',
                      'CREATE INDEX synthetic_throttle_expiry','array_ndims','generate_subscripts','cardinality',
                      'max_keys BETWEEN 2 AND 10000','v_count<>c.key_count'):
            self.assertIn(token,self.sql)
        self.assertNotIn('ON CONFLICT',self.sql)

    def test_lock_order_and_post_wait_primary_time_shape(self):
        reserve_sql=self.sql.split('CREATE FUNCTION synthetic_throttle.reserve_attempt')[1].split('$reserve$;')[0]
        markers=['LOCK ORDER 1','FOR SHARE','LOCK ORDER 2','LOCK ORDER 3','ORDER BY scope,digest FOR UPDATE','clock_timestamp()']
        self.assertEqual([reserve_sql.index(s) for s in markers],sorted(reserve_sql.index(s) for s in markers))
        self.assertNotIn('SKIP LOCKED',reserve_sql);self.assertNotIn('now()',reserve_sql)
        self.assertLess(reserve_sql.index('cardinality(ip_values)>=30'),reserve_sql.index('INSERT INTO synthetic_throttle.windows'))
        self.assertIn("p_action IS NULL",reserve_sql)
        self.assertIn('IS DISTINCT FROM p_generation',reserve_sql)

    def test_cleanup_is_bounded_and_resamples_no_recovery_reset(self):
        cleanup=self.sql.split('CREATE FUNCTION synthetic_throttle.cleanup')[1]
        self.assertIn('p_batch NOT BETWEEN 1 AND 100',cleanup)
        self.assertIn('LIMIT p_batch',cleanup);self.assertIn('FOR UPDATE OF w',cleanup)
        self.assertGreaterEqual(cleanup.count('clock_timestamp()'),2)
        self.assertIn('v_now<v_first',cleanup);self.assertIn("state='QUARANTINED'",cleanup)
        for token in ('c.generation IS DISTINCT FROM p_generation','c.writer_hint IS DISTINCT FROM p_writer',
                      'p_time_trusted IS DISTINCT FROM true','p_fresh IS DISTINCT FROM true'):
            self.assertLess(cleanup.index(token),cleanup.index('DELETE FROM synthetic_throttle.windows'))
        self.assertIn('test_cleanup_rejects_untrusted_evidence_without_deleting',self.prepared)

    def test_driver_import_is_lazy_and_source_has_no_dsn_input(self):
        tree=ast.parse(self.source)
        self.assertFalse(any(isinstance(n,ast.Import) and any(a.name.startswith('psycopg') for a in n.names) for n in tree.body))
        self.assertIn("if _EXECUTION_PERMIT is None",self.source)
        self.assertNotIn("add_argument('--dsn'",self.source)
        self.assertIn("sys.executable,'-I','-B'",self.source)
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):self.assertFalse((node.module or '').startswith('app'))

    def test_prepared_two_connection_tests_require_actual_blocking_observation(self):
        for token in ('pg_blocking_pids','second.info.backend_pid','ThreadPoolExecutor','future.result(timeout=5)',
                      'test_two_connections_final_account_slot','test_two_connections_missing_key_creation',
                      "'55P03'","'SQLSTATE P0001'"):
            self.assertIn(token,self.prepared)
        ast.parse(self.prepared)  # Syntax only, not PostgreSQL execution.


if __name__=='__main__':unittest.main()
