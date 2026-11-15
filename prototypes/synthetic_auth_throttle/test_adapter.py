"""Generated synthetic stores only. No application imports or input database paths."""
from contextlib import closing
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import socket
import sqlite3
import threading
import unittest
from unittest.mock import patch

from adapter import (SyntheticDatabase, ReservationAdapter, Ownership, ElapsedClock,
                     StorageUnavailable, StorageBusy, ContinuityLost, GuardRejected, WINDOW_MS, synthetic_keys)
from authority import _send, _receive, Wire


def reserve(adapter, **values):
    defaults = dict(action='login', ip='192.0.2.1', account='synthetic@example.test', guard=lambda: True)
    return adapter.reserve(**(defaults | values))


def snapshot(handle):
    with closing(sqlite3.connect(handle.path)) as connection:
        return (connection.execute('SELECT * FROM prototype_control').fetchall(),
                connection.execute('SELECT * FROM prototype_windows ORDER BY namespace,key_digest').fetchall())


def contender(handle, ready, start, output, account):
    try:
        adapter = ReservationAdapter(handle, busy_ms=1000)
        ready.put(True)
        if not start.wait(10): raise RuntimeError('Synthetic barrier deadline')
        output.put(('decision', reserve(adapter, account=account).allowed))
    except Exception as error: output.put(('error', type(error).__name__))


def claim_contender(handle, key, barrier, release, output):
    owner = None
    try:
        barrier.wait(10)
        owner = Ownership(handle, key)
        output.put('owned')
        if not release.wait(10): raise RuntimeError('Synthetic owner deadline')
    except StorageBusy: output.put('busy')
    except Exception: output.put('unavailable')
    finally:
        if owner is not None: owner.close()


class OwnerTests(unittest.TestCase):
    def setUp(self):
        self.store = SyntheticDatabase(manual_clock=True)
        self.addCleanup(self.store.close)
        self.adapter = ReservationAdapter(self.store.handle)

    def test_schema_dedicated_version_two_and_no_reinitialization(self):
        with closing(sqlite3.connect(self.store.handle.path)) as connection:
            self.assertEqual({r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")},
                {'prototype_control', 'prototype_windows'})
            self.assertEqual(connection.execute('SELECT version,state FROM prototype_control').fetchone(), (2, 'ACTIVE'))
            self.assertEqual(connection.execute('PRAGMA integrity_check').fetchone(), ('ok',))
        reserve(self.adapter)
        before = snapshot(self.store.handle)
        ReservationAdapter(self.store.handle)
        self.assertEqual(snapshot(self.store.handle), before)

    def test_normalized_login_registration_budget_and_all_or_nothing(self):
        for index in range(10):
            self.assertTrue(reserve(self.adapter, action='login' if index % 2 else 'register', account=' SYNTHETIC@example.test ').allowed)
        before = snapshot(self.store.handle)[1]
        result = reserve(self.adapter, action='register', ip='198.51.100.2')
        self.assertFalse(result.allowed); self.assertEqual(result.retry_after_seconds, 900)
        self.assertEqual(snapshot(self.store.handle)[1], before)

    def test_ip_thirty_and_unrelated_pair(self):
        for index in range(30): self.assertTrue(reserve(self.adapter, account=f'synthetic-{index}@example.test').allowed)
        before = snapshot(self.store.handle)[1]
        self.assertFalse(reserve(self.adapter, account='new@example.test').allowed)
        self.assertEqual(snapshot(self.store.handle)[1], before)
        self.assertTrue(reserve(self.adapter, ip='198.51.100.2', account='other@example.test').allowed)

    def test_exact_boundaries_and_partial_ageing(self):
        for _ in range(5): reserve(self.adapter)
        self.store.advance(500000)
        for _ in range(5): reserve(self.adapter)
        self.store.advance(399999)
        self.assertFalse(reserve(self.adapter).allowed)
        self.store.advance(1)
        self.assertTrue(reserve(self.adapter).allowed)
        import json
        self.assertEqual([len(json.loads(r[2])) for r in snapshot(self.store.handle)[1]], [6, 6])
        self.store.advance(1); self.assertTrue(reserve(self.adapter).allowed)

    def test_forward_backward_worker_wall_jumps_cannot_advance_authority(self):
        for _ in range(10): reserve(self.adapter)
        before = snapshot(self.store.handle)[1]
        for wall in (10**20, -10**20, 0):
            with patch('time.time_ns', return_value=wall), patch('time.time', return_value=wall):
                self.assertFalse(reserve(ReservationAdapter(self.store.handle)).allowed)
        self.assertEqual(snapshot(self.store.handle)[1], before)
        with self.assertRaises(TypeError): ReservationAdapter(self.store.handle, clock=lambda: WINDOW_MS)

    def test_real_elapsed_clock_ignores_wall_and_rejects_monotonic_reversal(self):
        with patch('time.monotonic_ns', side_effect=[1_000_000, 2_000_000, 2_000_000, 1_000_000]):
            clock = ElapsedClock()
            with patch('time.time_ns', return_value=10**20): self.assertEqual(clock.read(), 1)
            with patch('time.time_ns', return_value=-10**20): self.assertEqual(clock.read(), 1)
            with self.assertRaises(ContinuityLost): clock.read()

    def test_backward_authority_anomaly_seals_instead_of_clamping(self):
        reserve(self.adapter); before = snapshot(self.store.handle)[1]
        with self.assertRaises(StorageUnavailable): self.store.advance(-1)
        with self.assertRaises(StorageUnavailable): reserve(self.adapter)
        self.assertEqual(snapshot(self.store.handle)[1], before)
        self.assertEqual(snapshot(self.store.handle)[0][0][8], 'SEALED')

    def test_worker_cannot_advance_clock_or_use_wrong_epoch_capability(self):
        from authority import request
        for handle in (replace(self.store.handle, epoch='0'*64), replace(self.store.handle, capability='0'*64)):
            with self.assertRaises(StorageUnavailable): reserve(ReservationAdapter(handle))
        with self.assertRaises(StorageUnavailable): request(self.store.handle, 'advance', delta=WINDOW_MS)
        self.assertTrue(reserve(self.adapter).allowed)

    def _race(self, ip_limit=False):
        for index in range(29 if ip_limit else 9):
            reserve(self.adapter, account=f'prefill-{index}@example.test' if ip_limit else 'synthetic@example.test')
        context = multiprocessing.get_context('spawn')
        ready, output, start = context.Queue(), context.Queue(), context.Event()
        processes = [context.Process(target=contender, args=(self.store.handle, ready, start, output,
            f'contender-{i}@example.test' if ip_limit else 'synthetic@example.test')) for i in range(4)]
        try:
            for p in processes: p.start()
            for _ in processes: self.assertTrue(ready.get(timeout=15))
            start.set()
            self.assertEqual(sorted(output.get(timeout=15) for _ in processes), [('decision', False)]*3+[('decision', True)])
            for p in processes: p.join(5); self.assertEqual(p.exitcode, 0)
            late = context.Process(target=contender, args=(self.store.handle, ready, start, output,
                'late@example.test' if ip_limit else 'synthetic@example.test'))
            processes.append(late); late.start()
            self.assertTrue(ready.get(timeout=15))
            self.assertEqual(output.get(timeout=15), ('decision', False))
            late.join(5); self.assertEqual(late.exitcode, 0)
        finally:
            start.set()
            for p in processes:
                if p.is_alive(): p.terminate()
                p.join(5); p.close()
            for q in (ready, output): q.close(); q.join_thread()

    def test_four_process_final_account_slot_and_worker_restart(self): self._race()
    def test_four_process_final_ip_slot_and_worker_restart(self): self._race(True)

    def test_independent_connections_threads_use_sqlite_atomicity(self):
        for _ in range(9): reserve(self.adapter)
        barrier = threading.Barrier(4)
        def work(_):
            barrier.wait(5)
            return reserve(ReservationAdapter(self.store.handle, busy_ms=1000)).allowed
        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(sorted(pool.map(work, range(4))), [False, False, False, True])
        # Server-side probe must observe actual SQLITE_BUSY under its reservation.
        self.store.advance(WINDOW_MS)
        self.store.inject_fault('probe_lock')
        self.assertTrue(reserve(self.adapter).allowed)

    def test_two_concurrent_owner_claims_only_one_winner(self):
        with SyntheticDatabase(manual_clock=True, autostart=False) as fresh:
            context = multiprocessing.get_context('spawn')
            barrier, release, output = context.Barrier(2), context.Event(), context.Queue()
            processes = [context.Process(target=claim_contender, args=(fresh.handle, fresh._key, barrier, release, output)) for _ in range(2)]
            try:
                for p in processes: p.start()
                self.assertEqual(sorted(output.get(timeout=15) for _ in processes), ['busy', 'owned'])
            finally:
                release.set()
                for p in processes:
                    p.join(5)
                    if p.is_alive(): p.terminate(); p.join(5)
                    p.close()
                output.close(); output.join_thread()
            with self.assertRaises(ContinuityLost): fresh.start_owner()

    def test_active_owner_claim_is_exclusive(self):
        with self.assertRaises(StorageBusy): Ownership(self.store.handle, self.store._key)
        self.assertTrue(reserve(self.adapter).allowed)

    def test_owner_crash_never_resumes_old_store(self):
        for _ in range(10): reserve(self.adapter)
        before = snapshot(self.store.handle)[1]
        self.store.crash_owner()
        with self.assertRaises(StorageUnavailable): reserve(self.adapter)
        with self.assertRaises(ContinuityLost): self.store.start_owner()
        self.assertEqual(snapshot(self.store.handle)[1], before)

    def test_fence_blocks_still_running_stale_owner_and_open_client(self):
        stream = socket.create_connection(self.store.handle.endpoint, timeout=3)
        self.addCleanup(stream.close); stream.settimeout(3)
        wire = Wire(stream,self.store.handle)
        self.store.fence()
        self.assertTrue(self.store._process.is_alive())
        wire.send(dict(op='reserve',
            keys=synthetic_keys('192.0.2.1','synthetic@example.test'), action='login', busy_ms=250))
        self.assertEqual(wire.receive()['status'], 'unavailable')
        with self.assertRaises(StorageUnavailable): reserve(self.adapter)
        self.assertEqual(snapshot(self.store.handle)[1], [])

    def test_inflight_commit_linearizes_before_fence_then_all_stale_work_fails(self):
        with socket.create_connection(self.store.handle.endpoint, timeout=3) as stream:
            stream.settimeout(3); stream.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            wire = Wire(stream,self.store.handle)
            wire.send(dict(op='reserve',
                keys=synthetic_keys('192.0.2.1','synthetic@example.test'), action='login', busy_ms=1000))
            self.assertEqual(wire.receive()['kind'], 'guard'); wire.send({'guard':True})
            self.assertEqual(wire.receive()['kind'], 'guard')  # Reservation writer lock now held.
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(self.store.fence)
                wire.send({'guard':True})
                self.assertTrue(wire.receive()['allowed'])
                future.result(timeout=5)
        with self.assertRaises(StorageUnavailable): reserve(self.adapter)

    def test_owner_death_with_open_transaction_rolls_back(self):
        with socket.create_connection(self.store.handle.endpoint, timeout=3) as stream:
            stream.settimeout(3)
            wire = Wire(stream,self.store.handle)
            wire.send(dict(op='reserve',
                keys=synthetic_keys('192.0.2.1','synthetic@example.test'), action='login', busy_ms=250))
            self.assertEqual(wire.receive()['kind'], 'guard'); wire.send({'guard':True})
            self.assertEqual(wire.receive()['kind'], 'guard')
            self.store.crash_owner()
            with self.assertRaises((StorageUnavailable, OSError)): wire.receive()
        self.assertEqual(snapshot(self.store.handle)[1], [])

    def test_denied_reservation_commits_cleanup_and_preserves_active_counters(self):
        reserve(self.adapter, ip='198.51.100.2', account='expired@example.test')
        self.store.advance(500000)
        for _ in range(10): reserve(self.adapter)
        active = [r for r in snapshot(self.store.handle)[1] if r[3] == 1400000]
        self.store.advance(400000)
        self.assertFalse(reserve(self.adapter).allowed)
        self.assertEqual(snapshot(self.store.handle)[1], active)

    def test_cleanup_batches_are_independent_bounded_and_reclaim_capacity(self):
        with SyntheticDatabase(max_keys=4, cleanup_batch=1, manual_clock=True) as store:
            adapter = ReservationAdapter(store.handle)
            reserve(adapter); reserve(adapter,ip='198.51.100.2',account='old@example.test')
            store.advance(WINDOW_MS)
            self.assertEqual(adapter.cleanup(),1)
            self.assertEqual(snapshot(store.handle)[0][0][4],3)
            self.assertTrue(reserve(adapter,ip='203.0.113.1',account='new@example.test').allowed)
            self.assertEqual(snapshot(store.handle)[0][0][4],4)

    def test_capacity_failure_never_evicts_active_windows(self):
        with SyntheticDatabase(max_keys=2, manual_clock=True) as store:
            adapter = ReservationAdapter(store.handle); reserve(adapter)
            before = snapshot(store.handle)[1]
            with self.assertRaises(StorageUnavailable): reserve(adapter, account='new@example.test')
            self.assertEqual(snapshot(store.handle)[1], before)
            self.assertTrue(reserve(adapter).allowed)

    def test_corrupt_in_range_count_cannot_bypass_capacity(self):
        reserve(self.adapter)
        with closing(sqlite3.connect(self.store.handle.path)) as connection:
            connection.execute('UPDATE prototype_control SET key_count=0'); connection.commit()
        before = snapshot(self.store.handle)
        with self.assertRaises(StorageUnavailable): reserve(self.adapter,ip='198.51.100.2',account='other@example.test')
        self.assertEqual(snapshot(self.store.handle), before)

    def test_deleted_active_window_is_detected_even_with_trigger_count_update(self):
        reserve(self.adapter)
        with closing(sqlite3.connect(self.store.handle.path)) as connection:
            connection.execute("DELETE FROM prototype_windows WHERE namespace='account'"); connection.commit()
        with self.assertRaises(StorageUnavailable): reserve(self.adapter)

    def test_negative_impossible_malformed_missing_control_fail_closed(self):
        statements = ['UPDATE prototype_control SET key_count=-1', 'UPDATE prototype_control SET key_count=10001',
            "UPDATE prototype_control SET key_count='bad'", 'DELETE FROM prototype_control']
        for statement in statements:
            with self.subTest(statement=statement), SyntheticDatabase(manual_clock=True) as store:
                adapter = ReservationAdapter(store.handle); reserve(adapter)
                with closing(sqlite3.connect(store.handle.path)) as connection:
                    connection.execute('PRAGMA ignore_check_constraints=ON'); connection.execute(statement); connection.commit()
                with self.assertRaises(StorageUnavailable): reserve(adapter)

    def test_expired_malformed_state_is_not_silently_cleaned(self):
        reserve(self.adapter)
        with closing(sqlite3.connect(self.store.handle.path)) as connection:
            connection.execute("UPDATE prototype_windows SET stamps='bad'"); connection.commit()
        self.store.advance(WINDOW_MS)
        with self.assertRaises(StorageUnavailable): self.adapter.cleanup()
        self.assertEqual(len(snapshot(self.store.handle)[1]),2)

    def test_missing_or_modified_schema_objects_fail_before_admission(self):
        for statement in ('DROP TRIGGER prototype_insert','DROP INDEX prototype_expiry'):
            with self.subTest(statement=statement), SyntheticDatabase(manual_clock=True) as store:
                adapter = ReservationAdapter(store.handle); reserve(adapter)
                with closing(sqlite3.connect(store.handle.path)) as connection:
                    connection.execute(statement); connection.commit()
                before = snapshot(store.handle)[1]
                with self.assertRaises(StorageUnavailable): reserve(adapter,account='other@example.test')
                self.assertEqual(snapshot(store.handle)[1],before)

    def test_rollback_faults_leave_both_budgets_unchanged(self):
        for stage in ('after_first_write','before_commit'):
            self.store.inject_fault(stage)
            before = snapshot(self.store.handle)[1]
            with self.assertRaises(StorageUnavailable): reserve(self.adapter)
            self.assertEqual(snapshot(self.store.handle)[1],before)
        self.assertTrue(reserve(self.adapter).allowed)

    def test_busy_and_locked_fail_closed_without_fallback(self):
        with closing(sqlite3.connect(self.store.handle.path,isolation_level=None)) as blocker:
            blocker.execute('BEGIN IMMEDIATE')
            with self.assertRaises(StorageBusy): reserve(ReservationAdapter(self.store.handle,busy_ms=0))
            blocker.rollback()
        self.store.inject_fault('locked')
        with self.assertRaises(StorageBusy): reserve(self.adapter)
        self.assertEqual(snapshot(self.store.handle)[1],[])
        self.assertTrue(reserve(self.adapter).allowed)

    def test_guard_rejections_before_rpc_and_after_writer_lock_never_charge(self):
        before = snapshot(self.store.handle)[1]
        with self.assertRaises(GuardRejected): reserve(self.adapter,guard=lambda:False)
        sequence = iter([True,False])
        with self.assertRaises(GuardRejected): reserve(self.adapter,guard=lambda:next(sequence))
        sequence = iter([True,True,False])
        with self.assertRaises(GuardRejected): reserve(self.adapter,guard=lambda:next(sequence))
        self.assertEqual(snapshot(self.store.handle)[1],before)

    def test_privacy_identifiers_and_keys_never_persist_raw_or_print_in_handle(self):
        reserve(self.adapter)
        text = repr(snapshot(self.store.handle))
        self.assertNotIn('192.0.2.1',text); self.assertNotIn('synthetic@example.test',text)
        self.assertFalse(self.store.handle.capability in repr(self.store.handle))
        self.assertFalse(self.store._key.hex() in text)
        with self.assertRaises(ValueError): reserve(self.adapter,ip='127.0.0.1')
        with self.assertRaises(ValueError): reserve(self.adapter,account='real@invalid.test')
        with self.assertRaises(ValueError): ReservationAdapter('existing.sqlite')

    def test_reused_or_unsigned_endpoint_cannot_forge_authority_success(self):
        received = []
        with socket.socket() as listener:
            listener.bind(('127.0.0.1',0)); listener.listen(1); listener.settimeout(3)
            def fake():
                stream,_ = listener.accept()
                with stream:
                    stream.settimeout(3)
                    received.append(_receive(stream))
                    _send(stream,{'status':'ok','allowed':True})
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(fake)
                with self.assertRaises(StorageUnavailable):
                    reserve(ReservationAdapter(replace(self.store.handle,endpoint=listener.getsockname())))
                future.result(timeout=5)
        import json
        self.assertFalse(self.store.handle.capability in json.dumps(received))

    def test_replayed_authority_frame_from_different_call_is_rejected(self):
        client,server = socket.socketpair()
        with client,server:
            client.settimeout(3); server.settimeout(3)
            wire = Wire(client,self.store.handle)
            wire.send({'op':'cleanup'}); _receive(server)
            stale = Wire(server,self.store.handle,nonce='0'*64,sequence=1)
            stale.send({'status':'ok','removed':0})
            with self.assertRaises(StorageUnavailable): wire.receive()

    def test_client_supplied_clock_is_rejected_without_expiry(self):
        from authority import request
        for _ in range(10): reserve(self.adapter)
        with self.assertRaises(StorageUnavailable):
            request(self.store.handle,'reserve',action='login',keys=synthetic_keys('192.0.2.1','synthetic@example.test'),
                busy_ms=250,stamp=WINDOW_MS)
        self.assertFalse(reserve(self.adapter).allowed)


if __name__ == '__main__': unittest.main()
