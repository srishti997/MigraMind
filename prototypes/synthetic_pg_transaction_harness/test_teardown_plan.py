"""Pure offline tests; no I/O, database, commands or resource deletion."""
import ast
from pathlib import Path
import unittest
from teardown_plan import plan, Refused, FIELDS


class PlannerTests(unittest.TestCase):
    def setUp(self):
        n='a'*32
        self.record=dict(run_id='synthetic-run',nonce=n,container_id='b'*64,image_digest='sha256:'+'c'*64,
            server_version='reviewed-version',volume_id='migramind-pg-harness-'+n,port=55432,
            database='synthetic-case',fixture_role='fixture',maintenance_role='maintenance',owner='owner',
            generation='synthetic-generation-1',writer='synthetic-primary-1',state='STOPPED',revision=1)
        common=dict(observed_ms=1000,revision=1,state='STOPPED',isolated=True)
        self.runtime={k:self.record[k] for k in ('run_id','nonce','container_id','image_digest','server_version','volume_id','port')}|common
        self.database={k:self.record[k] for k in ('run_id','nonce','database','fixture_role','maintenance_role','owner','generation','writer')}|common
        self.approvals=dict.fromkeys(('generation','writer','time_approved','freshness_approved','teardown_approved','lease_held'),True)

    def test_only_review_result(self):
        self.assertEqual(plan(self.record,self.runtime,self.database,self.approvals,1000),'REVIEW_ONLY_NO_DELETION_AUTHORIZED')

    def test_missing_false_stale_and_mismatched_refused(self):
        for key in FIELDS:
            bad=self.record.copy();bad.pop(key)
            with self.subTest(key=key),self.assertRaises(Refused):plan(bad,self.runtime,self.database,self.approvals,1000)
        for key in self.approvals:
            with self.subTest(key=key),self.assertRaises(Refused):plan(self.record,self.runtime,self.database,self.approvals|{key:False},1000)
        for key in ('container_id','image_digest','volume_id','state','revision','isolated'):
            with self.subTest(key=key),self.assertRaises(Refused):plan(self.record,self.runtime|{key:None},self.database,self.approvals,1000)
        for key in ('database','fixture_role','maintenance_role','owner','generation','writer','state','revision','isolated'):
            with self.subTest(key=key),self.assertRaises(Refused):plan(self.record,self.runtime,self.database|{key:None},self.approvals,1000)
        for value in ('NEW','BOOTSTRAPPED','TESTING','REVIEW_REQUIRED','REMOVED'):
            with self.assertRaises(Refused):plan(self.record|{'state':value},self.runtime,self.database,self.approvals,1000)
        with self.assertRaises(Refused):plan(self.record,self.runtime,self.database,self.approvals,31001)

    def test_module_has_no_io_or_dynamic_execution(self):
        tree=ast.parse(Path(__file__).with_name('teardown_plan.py').read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):self.assertEqual([a.name for a in node.names],['re'])
            self.assertFalse(isinstance(node,ast.ImportFrom))
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
                self.assertNotIn(node.func.id,('open','exec','eval','__import__','compile'))


if __name__=='__main__':unittest.main()
