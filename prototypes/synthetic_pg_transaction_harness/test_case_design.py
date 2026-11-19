"""Pure offline tests; supplied inventories are not actual resource observations."""
import ast
from pathlib import Path
import unittest
from case_design import Case, Refused, propose_case, review_maintenance


class CaseDesignTests(unittest.TestCase):
    def setUp(self):
        self.case=Case('a'*32,1)
        self.inventory={'databases':(), 'roles':(), 'complete':True}
        self.expected=dict(database=self.case.database,owner=self.case.owner,fixture=self.case.fixture,
            maintenance=self.case.maintenance,generation='synthetic-generation-1',writer='synthetic-primary-1')
        self.assertions=dict.fromkeys(('independent_maintenance_authority','time_approved','freshness_approved','case_verified'),True)

    def test_distinct_bounded_identity(self):
        self.assertEqual(len(set(propose_case(self.case,self.inventory,'NEW'))),4)
        self.assertTrue(all(len(x)<=63 for x in propose_case(self.case,self.inventory,'NEW')))
        self.assertNotEqual(Case('a'*32,2).database,self.case.database)
        for ordinal in (0,1000,True):
            with self.assertRaises(Refused):Case('a'*32,ordinal)

    def test_collision_partial_and_stale_refuse(self):
        for key,value in (('databases',self.case.database),('roles',self.case.fixture),('roles',self.case.maintenance)):
            with self.assertRaises(Refused):propose_case(self.case,self.inventory|{key:(value,)},'NEW')
        for state in ('PARTIAL','READY','STALE','NEWER',None):
            with self.assertRaises(Refused):propose_case(self.case,self.inventory,state)
        with self.assertRaises(Refused):propose_case(self.case,self.inventory|{'complete':False},'NEW')

    def test_maintenance_is_advisory_and_refuses_mismatches(self):
        self.assertEqual(review_maintenance(self.case,self.expected,self.expected,self.assertions),'REVIEW_ONLY_NO_CLEANUP_AUTHORIZED')
        for key in self.expected:
            with self.subTest(key=key),self.assertRaises(Refused):
                review_maintenance(self.case,self.expected,self.expected|{key:'mismatch'},self.assertions)
        for key in self.assertions:
            with self.subTest(key=key),self.assertRaises(Refused):
                review_maintenance(self.case,self.expected,self.expected,self.assertions|{key:False})
        with self.assertRaises(Refused):review_maintenance(self.case,self.expected|{'maintenance':self.case.fixture},self.expected,self.assertions)

    def test_interface_has_no_io(self):
        tree=ast.parse(Path(__file__).with_name('case_design.py').read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):self.assertEqual([a.name for a in node.names],['re'])
            if isinstance(node,ast.ImportFrom):self.assertEqual(node.module,'dataclasses')
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
                self.assertNotIn(node.func.id,('open','exec','eval','__import__','compile'))

    def test_legacy_ownership_is_still_incompatible_and_execution_blocked(self):
        root=Path(__file__).parent
        sql=(root/'schema.sql').read_text(encoding='utf-8')
        source=(root/'harness.py').read_text(encoding='utf-8')
        self.assertIn('IS DISTINCT FROM current_user',sql)
        self.assertIn("expected = (target.database, target.role, target.role, target.role",source)
        self.assertIn('EXECUTION_BLOCKED = True',source)
        self.assertIn("if EXECUTION_BLOCKED: raise SafetyError",source)
