"""Deterministic in-memory examples, NOT database integration/locking tests."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import unittest

from model import Model, State, Window, Time, Evidence, Status, WINDOW_MS, keys, serial_orderings


def attempt(model, **values):
    defaults = dict(action='login', ip='192.0.2.1', account='synthetic@example.test')
    return model.reserve(**(defaults | values))


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.clock = Time(0)
        self.model = Model(self.clock)

    def fill(self, count=10):
        for _ in range(count): self.assertEqual(attempt(self.model).status, Status.ALLOWED)

    def test_shared_login_registration_normalized_account_and_rejection(self):
        for index in range(10):
            self.assertEqual(attempt(self.model, action='register' if index % 2 else 'login',
                account=' SYNTHETIC@example.test ').status, Status.ALLOWED)
        before = self.model.snapshot()
        denied = attempt(self.model)
        self.assertEqual(denied.status, Status.LIMITED); self.assertEqual(denied.retry_after_seconds,900)
        self.assertEqual(self.model.snapshot(),before)

    def test_ip_limit_and_no_missing_key_created_on_denial(self):
        for index in range(30):
            self.assertEqual(attempt(self.model,account=f'person-{index}@example.test').status,Status.ALLOWED)
        before=self.model.snapshot()
        self.assertEqual(attempt(self.model,account='missing@example.test').status,Status.LIMITED)
        self.assertEqual(self.model.snapshot(),before)

    def test_denial_can_advance_control_metadata_without_charging_counters(self):
        self.fill();before=self.model.snapshot()
        self.clock.value=100
        self.assertEqual(attempt(self.model,ip='198.51.100.2').status,Status.LIMITED)
        self.assertEqual(self.model.state.high_water_ms,100)
        self.assertEqual(self.model.state.windows,before.windows)
        self.assertEqual(self.model.state.key_count,before.key_count)

    def test_two_accounts_share_ip_but_have_independent_account_limits(self):
        self.fill()
        for _ in range(10):self.assertEqual(attempt(self.model,account='other@example.test').status,Status.ALLOWED)
        ip_key=keys('192.0.2.1','synthetic@example.test')[0]
        self.assertEqual(len(self.model.state.windows[ip_key].stamps),20)
        self.assertEqual(attempt(self.model).status,Status.LIMITED)

    def test_one_account_across_ips_still_has_ten_global_slots(self):
        self.fill()
        before=self.model.snapshot()
        self.assertEqual(attempt(self.model,ip='198.51.100.2').status,Status.LIMITED)
        self.assertEqual(self.model.snapshot(),before)

    def test_exact_cutoff_partial_ageing_and_same_ms_attempts(self):
        self.fill(5);self.clock.value=500000;self.fill(5)
        self.clock.value=WINDOW_MS-1
        self.assertEqual(attempt(self.model).status,Status.LIMITED)
        self.clock.value=WINDOW_MS
        self.assertEqual(attempt(self.model).status,Status.ALLOWED)
        self.assertEqual([len(r.stamps) for r in self.model.state.windows.values()],[6,6])
        self.clock.value=WINDOW_MS+1
        self.assertEqual(attempt(self.model).status,Status.ALLOWED)

    def test_fixed_bucket_boundary_would_violate_rolling_policy(self):
        self.clock.value=WINDOW_MS-1;self.fill()
        self.clock.value=WINDOW_MS
        self.assertEqual(attempt(self.model).status,Status.LIMITED)

    def test_all_serial_orders_of_four_final_account_contenders(self):
        self.fill(9)
        requests=[dict(action='login' if i%2 else 'register',ip='192.0.2.1',account='synthetic@example.test') for i in range(4)]
        outcomes=serial_orderings(self.model.snapshot(),requests)
        self.assertEqual(len(outcomes),24)
        for _,results,state in outcomes:
            self.assertEqual(sum(r.status==Status.ALLOWED for r in results),1)
            self.assertEqual(sum(r.status==Status.LIMITED for r in results),3)
            self.assertEqual([len(r.stamps) for r in state.windows.values()],[10,10])

    def test_all_serial_orders_of_four_final_ip_contenders(self):
        for i in range(29):attempt(self.model,account=f'prefill-{i}@example.test')
        requests=[dict(action='login',ip='192.0.2.1',account=f'contender-{i}@example.test') for i in range(4)]
        for _,results,state in serial_orderings(self.model.snapshot(),requests):
            self.assertEqual(sum(r.status==Status.ALLOWED for r in results),1)
            self.assertEqual(state.key_count,31)  # One IP plus 30 admitted accounts.

    def test_missing_same_key_serial_creators_do_not_duplicate_rows(self):
        request=dict(action='login',ip='192.0.2.1',account='synthetic@example.test')
        for _,results,state in serial_orderings(self.model.snapshot(),[request,request]):
            self.assertTrue(all(r.status==Status.ALLOWED for r in results))
            self.assertEqual(state.key_count,2)
            self.assertTrue(all(len(r.stamps)==2 for r in state.windows.values()))

    def test_final_capacity_slot_is_atomic_for_different_missing_pairs(self):
        seed=State(max_keys=2)
        requests=[dict(action='login',ip=ip,account=account) for ip,account in
            [('192.0.2.1','one@example.test'),('198.51.100.2','two@example.test')]]
        for _,results,state in serial_orderings(seed,requests):
            self.assertEqual(sum(r.status==Status.ALLOWED for r in results),1)
            self.assertEqual(sum(r.status==Status.UNAVAILABLE for r in results),1)
            self.assertEqual(state.key_count,2)

    def test_confirmed_rollback_after_first_write_and_before_commit(self):
        for fault in ('after_ip_write','before_commit','deadlock','pool','lock_timeout','statement_timeout'):
            with self.subTest(fault=fault):
                before=self.model.snapshot()
                self.assertEqual(attempt(self.model,fault=fault).status,Status.UNAVAILABLE)
                self.assertEqual(self.model.snapshot(),before)
        self.assertEqual(attempt(self.model).status,Status.ALLOWED)

    def test_aborted_contender_leaves_final_slot_for_next_ordered_request(self):
        self.fill(9)
        self.assertEqual(attempt(self.model,fault='after_ip_write').status,Status.UNAVAILABLE)
        self.assertEqual(attempt(self.model).status,Status.ALLOWED)
        self.assertEqual(attempt(self.model).status,Status.LIMITED)

    def test_unknown_commit_retains_charge_without_automatic_retry(self):
        self.assertEqual(attempt(self.model,fault='lost_commit_ack').reason,'commit_unknown_no_retry')
        self.assertTrue(all(len(r.stamps)==1 for r in self.model.state.windows.values()))
        self.assertEqual(attempt(self.model).status,Status.ALLOWED)  # Explicit new attempt.
        self.assertTrue(all(len(r.stamps)==2 for r in self.model.state.windows.values()))

    def test_later_password_failure_is_not_a_refund_operation(self):
        attempt(self.model);before=self.model.snapshot()
        self.assertFalse(hasattr(self.model,'refund'))
        self.assertEqual(self.model.snapshot(),before)

    def test_lock_trace_is_explicit_session_control_budget_then_time_assumption(self):
        attempt(self.model,session_ids=(3,1))
        self.assertEqual(self.model.trace[:7],['preliminary_guards','session:1','session:3','control:for_update',
            'budget:0:missing_under_control','budget:1:missing_under_control','recheck_guards'])
        self.assertEqual(self.model.trace[7:9],['primary_time_after_locks','commit_pair'])

    def test_guards_before_accounting_and_after_wait(self):
        before=self.model.snapshot()
        self.clock.value=None
        self.assertEqual(attempt(self.model,guards_ok=False,evidence=Evidence(available=False)).status,Status.GUARD_REJECTED)
        self.assertEqual(attempt(self.model,guards_after_wait=False).status,Status.GUARD_REJECTED)
        self.assertEqual(self.model.snapshot(),before)

    def test_cleanup_commits_independently_of_later_denial_or_rollback(self):
        attempt(self.model,ip='198.51.100.2',account='expired@example.test')
        self.clock.value=500000;self.fill()
        self.clock.value=WINDOW_MS
        result,count=self.model.cleanup()
        self.assertEqual((result.status,count),(Status.ALLOWED,2))
        active=self.model.snapshot().windows
        self.assertEqual(attempt(self.model).status,Status.LIMITED)
        self.assertEqual(self.model.snapshot().windows,active)
        self.assertEqual(attempt(self.model,ip='203.0.113.2',account='fresh@example.test',fault='before_commit').status,Status.UNAVAILABLE)
        self.assertEqual(self.model.snapshot().windows,active)

    def test_cleanup_batch_capacity_and_active_window_preservation(self):
        self.model=Model(self.clock,State(max_keys=4))
        attempt(self.model);self.clock.value=500000
        attempt(self.model,ip='198.51.100.2',account='active@example.test')
        before=self.model.snapshot()
        self.assertEqual(attempt(self.model,account='new@example.test').reason,'capacity')
        self.assertEqual(self.model.snapshot(),before)
        self.clock.value=WINDOW_MS
        self.assertEqual(self.model.cleanup(batch=1)[1],1)
        self.assertEqual(self.model.cleanup(batch=1)[1],1)
        self.assertEqual(self.model.cleanup(batch=1)[1],0)
        self.assertTrue(all(r.stamps==(500000,) for r in self.model.state.windows.values()))

    def test_cleanup_abort_does_not_partially_delete(self):
        attempt(self.model);self.clock.value=WINDOW_MS
        before=self.model.snapshot()
        self.assertEqual(self.model.cleanup(fault='before_commit')[0].status,Status.UNAVAILABLE)
        self.assertEqual(self.model.snapshot(),before)

    def test_cleanup_rechecks_time_after_assumed_lock_wait(self):
        attempt(self.model);self.clock.value=500000
        attempt(self.model,ip='198.51.100.2',account='active@example.test')
        before=self.model.snapshot().windows
        class SequenceTime:
            def __init__(self):self.values=iter([900000,899999])
            def read(self):return next(self.values)
        self.model.clock=SequenceTime()
        result,count=self.model.cleanup()
        self.assertEqual((result.reason,count),('backward_time',0))
        self.assertEqual(self.model.state.mode,'QUARANTINED')
        self.assertEqual(self.model.state.windows,before)

    def test_backward_time_quarantines_without_reset(self):
        self.clock.value=1000;self.fill()
        before=self.model.snapshot().windows
        self.clock.value=999
        self.assertEqual(attempt(self.model).reason,'backward_time')
        self.assertEqual(self.model.state.mode,'QUARANTINED')
        self.assertEqual(self.model.state.windows,before)
        self.clock.value=1000000
        self.assertEqual(attempt(self.model).reason,'quarantined')

    def test_known_forward_clock_uncertainty_is_quarantined(self):
        self.fill();self.clock.value=WINDOW_MS
        before=self.model.snapshot().windows
        self.assertEqual(attempt(self.model,evidence=Evidence(time_trusted=False)).status,Status.UNAVAILABLE)
        self.assertEqual(self.model.state.mode,'QUARANTINED')
        self.assertEqual(self.model.state.windows,before)

    def test_trusted_forward_jump_is_NOT_detected_automatically(self):
        self.fill();self.clock.value=WINDOW_MS
        self.assertEqual(attempt(self.model).status,Status.ALLOWED)

    def test_changed_primary_or_generation_quarantines_without_reset(self):
        for evidence in (Evidence(generation='synthetic-generation-2'),Evidence(writer='synthetic-primary-2')):
            with self.subTest(evidence=evidence):
                model=Model(Time(0));attempt(model);before=model.snapshot().windows
                self.assertEqual(attempt(model,evidence=evidence).status,Status.UNAVAILABLE)
                self.assertEqual(model.state.mode,'QUARANTINED');self.assertEqual(model.state.windows,before)

    def test_stale_snapshot_fails_only_when_external_freshness_is_withheld(self):
        attempt(self.model);stale=self.model.snapshot();self.fill(9)
        refused=Model(Time(0),stale)
        self.assertEqual(attempt(refused,evidence=Evidence(freshness_verified=False)).status,Status.UNAVAILABLE)
        # Same-generation old state is structurally valid; trusted evidence is an assumption.
        trusted=Model(Time(0),stale)
        self.assertEqual(attempt(trusted).status,Status.ALLOWED)

    def test_model_restart_preserves_snapshot_but_is_not_database_durability(self):
        self.fill();reopened=Model(Time(0),self.model.snapshot())
        self.assertEqual(attempt(reopened).status,Status.LIMITED)

    def test_unavailable_readonly_replica_do_not_charge_or_fallback(self):
        for evidence in (Evidence(available=False),Evidence(primary=False),Evidence(writable=False)):
            with self.subTest(evidence=evidence):
                before=self.model.snapshot()
                self.assertEqual(attempt(self.model,evidence=evidence).status,Status.UNAVAILABLE)
                self.assertEqual(self.model.snapshot(),before)

    def test_invalid_time_evidence_and_sample_failure_never_admit(self):
        for value in (True,-1,'900000',2**63):
            with self.subTest(value_type=type(value).__name__):
                model=Model(Time(value))
                self.assertEqual(attempt(model).reason,'invalid_time')
                self.assertEqual(model.state.windows,{})
        self.assertEqual(attempt(self.model,evidence=Evidence(primary='yes')).reason,'invalid_evidence')
        class FailingTime:
            def read(self):raise RuntimeError('Synthetic sample failure')
        self.assertEqual(attempt(Model(FailingTime())).reason,'time_unavailable')

    def test_failed_quarantine_commit_is_not_global_quarantine_proof(self):
        attempt(self.model);before=self.model.snapshot()
        result=attempt(self.model,evidence=Evidence(time_trusted=False),fault='quarantine_commit')
        self.assertEqual(result.reason,'quarantine_unconfirmed')
        self.assertEqual(self.model.snapshot(),before)

    def test_corrupt_missing_negative_and_expired_untrusted_state_fails_safely(self):
        self.fill(1);seed=self.model.snapshot()
        variants=[]
        for value in (-1,0,'bad',10001):
            bad=deepcopy(seed);bad.key_count=value;variants.append(bad)
        bad=deepcopy(seed);bad.windows.pop(next(iter(bad.windows)));variants.append(bad)
        bad=deepcopy(seed);bad.windows[next(iter(bad.windows))]=Window((True,),900001);variants.append(bad)
        for index,bad in enumerate(variants):
            with self.subTest(case=index):
                model=Model(Time(WINDOW_MS),bad);before=model.snapshot()
                self.assertEqual(attempt(model).reason,'untrusted_state')
                self.assertEqual(model.cleanup()[0].status,Status.UNAVAILABLE)
                self.assertEqual(model.snapshot(),before)

    def test_synthetic_restrictions_and_no_raw_identifier_storage(self):
        attempt(self.model)
        self.assertNotIn('192.0.2.1',repr(self.model.snapshot()))
        self.assertNotIn('synthetic@example.test',repr(self.model.snapshot()))
        self.assertEqual(keys('2001:db8::1',' SYNTHETIC@example.test '),keys('2001:0db8:0:0:0:0:0:1','synthetic@example.test'))
        with self.assertRaises(ValueError):attempt(self.model,ip='127.0.0.1')
        with self.assertRaises(ValueError):attempt(self.model,account='real@invalid.test')

    def test_malformed_window_invariants_cannot_be_cleaned_into_trust(self):
        attempt(self.model);seed=self.model.snapshot();key=next(iter(seed.windows))
        variants=[Window((),900000),Window((0,0)*16,900000),Window((1,0),900000),
            Window((-1,),899999),Window((1,),900001),Window((0,),900001)]
        for index,row in enumerate(variants):
            with self.subTest(case=index):
                bad=deepcopy(seed);bad.windows[key]=row
                model=Model(Time(WINDOW_MS),bad);before=model.snapshot()
                self.assertEqual(model.cleanup()[0].reason,'untrusted_state')
                self.assertEqual(model.snapshot(),before)


class SqlShapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.text=Path(__file__).with_name('SQL_SHAPE.md').read_text(encoding='utf-8')

    def test_explicit_non_executable_design_and_required_schema_shape(self):
        for marker in ('NOT APPLIED OR EXECUTABLE','<dedicated_control>','<dedicated_windows>',
            'PRIMARY KEY (scope_rank, key_digest)','CREATE INDEX <expiry_index>',
            'cardinality(times_ms)','octet_length(key_digest) = 32','<reviewed_sorted_nonnegative_bounded_array_predicate>'):
            self.assertIn(marker,self.text)

    def test_primary_lock_order_sample_after_locks_and_commit(self):
        shape=self.text.split('-- BEGIN ADMISSION SHAPE')[1].split('-- END ADMISSION SHAPE')[0]
        markers=['BEGIN ISOLATION LEVEL READ COMMITTED','pg_is_in_recovery()',
            'FOR SHARE','-- LOCK 2','-- LOCK 3','ORDER BY scope_rank, key_digest FOR UPDATE',
            'RECHECK_ACTUAL_GUARDS_AFTER_WAITS','clock_timestamp()','COMMIT;']
        self.assertEqual([shape.index(v) for v in markers],sorted(shape.index(v) for v in markers))
        self.assertNotIn('SKIP LOCKED',shape);self.assertNotIn('now()',shape)

    def test_cleanup_is_separate_bounded_and_resamples_after_locks(self):
        shape=self.text.split('-- BEGIN MAINTENANCE SHAPE')[1].split('-- END MAINTENANCE SHAPE')[0]
        self.assertIn('LIMIT 100',shape);self.assertEqual(shape.count('clock_timestamp()'),2)
        self.assertLess(shape.index('FOR UPDATE;'),shape.index('candidate_ms'))
        self.assertIn('DELETE_ONLY_VALID_CANDIDATES_STILL_EXPIRED',shape)


if __name__=='__main__':unittest.main()
