"""Offline contract checks only, not PostgreSQL or privilege verification."""
import ast
from pathlib import Path
import unittest
from case_contract import CASE_NAMES, MAINTENANCE_CASES, case_for_test, maintenance_request
from case_design import Refused


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.name='test_cleanup_rollback';self.case=case_for_test('a'*32,self.name)
        self.expected=dict(database=self.case.database,owner=self.case.owner,fixture=self.case.fixture,
            maintenance=self.case.maintenance,generation='synthetic-generation-1',writer='synthetic-primary-1')
        self.assertions=dict.fromkeys(('independent_maintenance_authority','time_approved','freshness_approved','case_verified'),True)
        self.op=dict(sample_ms=900000,after_ms=None,batch=100,fault='before_commit',test_fresh=True)

    def test_mapping_exactly_matches_17_methods_and_unique_identities(self):
        tree=ast.parse(Path(__file__).with_name('test_database.py').read_text(encoding='utf-8'))
        names={n.name for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
        self.assertEqual(set(CASE_NAMES),names);self.assertEqual(len(CASE_NAMES),17)
        cases=[case_for_test('a'*32,n) for n in CASE_NAMES]
        self.assertEqual(len({c.database for c in cases}),17)
        self.assertEqual(len({c.fixture for c in cases}),17)
        self.assertEqual(len({c.maintenance for c in cases}),17)
        self.assertEqual(len(MAINTENANCE_CASES),3)

    def test_contract_is_review_only_and_refuses_bad_evidence(self):
        self.assertEqual(maintenance_request(self.case,self.name,self.expected,self.expected,self.assertions,self.op),'REVIEW_ONLY_NO_CLEANUP_AUTHORIZED')
        for k in self.assertions:
            with self.subTest(k=k),self.assertRaises(Refused):maintenance_request(self.case,self.name,self.expected,self.expected,self.assertions|{k:False},self.op)
        for k in self.expected:
            with self.subTest(k=k),self.assertRaises(Refused):maintenance_request(self.case,self.name,self.expected,self.expected|{k:'mismatch'},self.assertions,self.op)
        for change in ({'batch':101},{'batch':True},{'fault':'other'},{'sample_ms':-1},{'test_fresh':False}):
            with self.assertRaises(Refused):maintenance_request(self.case,self.name,self.expected,self.expected,self.assertions,self.op|change)
        with self.assertRaises(Refused):maintenance_request(self.case,CASE_NAMES[0],self.expected,self.expected,self.assertions,self.op)
