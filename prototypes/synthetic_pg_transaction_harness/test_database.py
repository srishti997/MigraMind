"""PREPARED STAGE B ONLY. Discovery without the runner context skips safely."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
import threading
import time
import unittest
import harness
from case_contract import case_for_test


class TransactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if harness.ACTIVE_CONTEXT is None or harness._EXECUTION_PERMIT is None:
            raise unittest.SkipTest('Stage B explicit disposable-target runner required; no connection attempted')
        cls.context=harness.ACTIVE_CONTEXT

    def setUp(self):
        # Selection is deterministic; the context still refuses until a real
        # independent verifier and one-use case registry exist.
        case=case_for_test(self.context.target.nonce,self._testMethodName)
        self.context.require_case(case)

    def attempt(self,**values):
        with self.context.connect() as connection, harness.transaction(connection):
            result=harness.reserve(connection,**values)
        return result  # Confirmation is AFTER commit.

    def snapshot(self):
        with self.context.connect() as connection:
            return connection.execute('SELECT scope,digest,times_ms,expires_ms FROM synthetic_throttle.windows ORDER BY scope,digest').fetchall()

    def cleanup(self,stamp,after=None,batch=100,fault=None, generation='synthetic-generation-1',
                writer='synthetic-primary-1',time_trusted=True,fresh=True):
        raise harness.SafetyError('Independent maintenance process not implemented')

    def _race(self,*,ip_boundary=False,new_keys=False):
        for index in range(0 if new_keys else (29 if ip_boundary else 9)):
            self.assertEqual(self.attempt(account=f'prefill-{index}@example.test' if ip_boundary else 'synthetic@example.test'),'allowed')
        started=threading.Event()
        with ExitStack() as stack:
            first=stack.enter_context(self.context.connect());second=stack.enter_context(self.context.connect())
            tx=harness.transaction(first,lock_ms=3000);tx.__enter__()
            open_tx=True
            try:
                self.assertEqual(harness.reserve(first,account='winner@example.test' if ip_boundary else 'synthetic@example.test'),'allowed')
                second_pid=second.info.backend_pid
                def loser():
                    with harness.transaction(second,lock_ms=3000):
                        started.set()
                        return harness.reserve(second,account='loser@example.test' if ip_boundary else 'synthetic@example.test')
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future=pool.submit(loser)
                    observed=False
                    try:
                        self.assertTrue(started.wait(1))
                        deadline=time.monotonic()+2
                        blocked=False
                        while time.monotonic()<deadline:
                            blockers=first.execute('SELECT pg_blocking_pids(%s)',(second_pid,)).fetchone()[0]
                            if first.info.backend_pid in blockers:blocked=True;break
                            threading.Event().wait(0.01)  # Bounded polling, no retry of admission.
                        self.assertTrue(blocked,'Second connection must actually wait on a held lock')
                        observed=True
                    finally:
                        open_tx=False
                        harness.finish_contender(tx,observed)
                    self.assertEqual(future.result(timeout=5),'allowed' if new_keys else 'limited')
            finally:
                if open_tx:tx.__exit__(RuntimeError,RuntimeError('Synthetic abort'),None)
        rows=self.snapshot()
        if new_keys:
            self.assertEqual(len(rows),2);self.assertTrue(all(len(r[2])==2 for r in rows))
        else:
            ip_rows=[r for r in rows if r[0]==0]
            self.assertEqual(len(ip_rows[0][2]),30 if ip_boundary else 10)

    def test_two_connections_final_account_slot(self):self._race()
    def test_two_connections_final_ip_slot(self):self._race(ip_boundary=True)
    def test_two_connections_missing_key_creation(self):self._race(new_keys=True)

    def test_action_sharing_normalization_and_all_or_nothing(self):
        for i in range(10):self.assertEqual(self.attempt(action='register' if i%2 else 'login',account=' SYNTHETIC@example.test '),'allowed')
        before=self.snapshot()
        self.assertEqual(self.attempt(ip='198.51.100.2'),'limited')
        self.assertEqual(self.snapshot(),before)

    def test_shared_ip_and_exact_expiry(self):
        for index in range(30):self.assertEqual(self.attempt(account=f'person-{index}@example.test'),'allowed')
        self.assertEqual(self.attempt(account='new@example.test',stamp=899999),'limited')
        self.assertEqual(self.attempt(account='new@example.test',stamp=900000),'allowed')
        self.assertEqual(self.attempt(account='new@example.test',stamp=900001),'allowed')

    def test_rollback_of_partial_and_complete_staged_pair(self):
        for fault in ('after_ip_write','before_commit'):
            with self.assertRaises(harness.SafetyError) as caught:self.attempt(fault=fault)
            self.assertIn('SQLSTATE P0001',str(caught.exception))
            self.assertEqual(self.snapshot(),[])
        self.assertEqual(self.attempt(),'allowed')

    def test_cleanup_is_bounded_independent_and_active_safe(self):
        self.attempt(ip='198.51.100.2',account='expired@example.test')
        for _ in range(10):self.attempt(stamp=500000)
        self.assertEqual(self.cleanup(900000,batch=1),1)
        self.assertEqual(self.cleanup(900000,batch=1),1)
        active=self.snapshot()
        self.assertEqual(self.attempt(stamp=900000),'limited')
        self.assertEqual(self.snapshot(),active)
        self.assertTrue(all(r[2]==[500000]*10 for r in active))

    def test_cleanup_rollback(self):
        self.attempt();before=self.snapshot()
        with self.assertRaises(harness.SafetyError) as caught:self.cleanup(900000,fault='before_commit')
        self.assertIn('SQLSTATE P0001',str(caught.exception))
        self.assertEqual(self.snapshot(),before)

    def test_cleanup_rejects_untrusted_evidence_without_deleting(self):
        self.attempt();before=self.snapshot()
        self.assertEqual(self.cleanup(900000,fresh=False),-1)
        self.assertEqual(self.snapshot(),before)
        self.assertEqual(self.cleanup(900000),-1)  # Quarantine persists.

    def test_backward_clock_quarantines_without_reset(self):
        self.attempt(stamp=1000);before=self.snapshot()
        self.assertEqual(self.attempt(stamp=999),'unavailable')
        self.assertEqual(self.snapshot(),before)
        self.assertEqual(self.attempt(stamp=900000),'unavailable')

    def test_known_untrusted_forward_clock_does_not_reopen(self):
        for _ in range(10):self.attempt()
        before=self.snapshot()
        self.assertEqual(self.attempt(stamp=900000,time_trusted=False),'unavailable')
        self.assertEqual(self.snapshot(),before)

    def test_trusted_forward_clock_is_not_automatically_detected(self):
        for _ in range(10):self.attempt()
        self.assertEqual(self.attempt(stamp=900000),'allowed')  # Explicit residual trust assumption.

    def test_primary_generation_change_is_not_a_reset(self):
        self.attempt();before=self.snapshot()
        self.assertEqual(self.attempt(generation='synthetic-generation-2'),'unavailable')
        self.assertEqual(self.snapshot(),before)

    def test_stale_snapshot_flag_is_not_actual_restore_detection(self):
        self.attempt();before=self.snapshot()
        self.assertEqual(self.attempt(fresh=False),'unavailable')
        self.assertEqual(self.snapshot(),before)  # No backup/snapshot restoration is performed.

    def test_capacity_unavailable_no_active_eviction(self):
        with self.context.connect() as connection,harness.transaction(connection):
            connection.execute('UPDATE synthetic_throttle.control SET max_keys=2 WHERE id=1')
        self.attempt();before=self.snapshot()
        self.assertEqual(self.attempt(account='other@example.test'),'unavailable')
        self.assertEqual(self.snapshot(),before)

    def test_binding_and_guard_rejections_do_not_count(self):
        self.assertEqual(self.attempt(guard=False),'guard_rejected')
        with self.context.connect() as connection,harness.transaction(connection):
            connection.execute('UPDATE synthetic_throttle.bindings SET valid=false WHERE id=1')
        self.assertEqual(self.attempt(),'guard_rejected')
        self.assertEqual(self.snapshot(),[])

    def test_two_connection_lock_timeout_does_not_charge(self):
        with self.context.connect() as blocker,harness.transaction(blocker):
            blocker.execute('SELECT id FROM synthetic_throttle.control WHERE id=1 FOR UPDATE')
            with self.context.connect() as second:
                with self.assertRaises(Exception) as caught:
                    with harness.transaction(second,lock_ms=50):harness.reserve(second)
                self.assertEqual(getattr(caught.exception,'sqlstate',None),'55P03')
        self.assertEqual(self.snapshot(),[])
