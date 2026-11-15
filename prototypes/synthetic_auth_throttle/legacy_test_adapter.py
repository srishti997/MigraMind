"""Only generated temporary prototype databases and documentation identities."""
from contextlib import closing
import multiprocessing
from pathlib import Path
import sqlite3
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

from legacy_adapter import (ReservationAdapter, SyntheticDatabase, SyntheticHandle, GuardRejected,
                     StorageUnavailable, StorageBusy, synthetic_keys, WINDOW_MS)


def reserve(adapter, *, ip='192.0.2.1', account='synthetic@example.test', action='login', guard=lambda: True):
    return adapter.reserve(action=action, ip=ip, account=account, guard=guard)


def snapshot(handle):
    with closing(sqlite3.connect(handle.path)) as connection:
        return (connection.execute('SELECT * FROM prototype_control').fetchall(),
                connection.execute('SELECT * FROM prototype_windows ORDER BY namespace,key_digest').fetchall())


def process_contender(handle, ready, start, output, account):
    try:
        adapter = ReservationAdapter(handle, clock=lambda: 1000, busy_ms=1000)
        ready.put(True)
        if not start.wait(10): raise RuntimeError('Synthetic barrier deadline')
        output.put(('decision', reserve(adapter, account=account).allowed))
    except Exception as error:
        output.put(('error', type(error).__name__))


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.store = SyntheticDatabase()
        self.addCleanup(self.store.close)
        self.clock = [1000]
        self.adapter = ReservationAdapter(self.store.handle, clock=lambda: self.clock[0])

    def test_schema_is_dedicated_new_and_connections_do_not_reinitialize(self):
        with closing(sqlite3.connect(self.store.handle.path)) as connection:
            tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertEqual(tables, {'prototype_control', 'prototype_windows'})
            self.assertEqual(connection.execute('SELECT key_count,version FROM prototype_control').fetchone(), (0, 1))
            self.assertEqual(connection.execute('PRAGMA integrity_check').fetchone(), ('ok',))
        self.assertTrue(reserve(self.adapter).allowed)
        before = snapshot(self.store.handle)
        ReservationAdapter(self.store.handle)
        self.assertEqual(snapshot(self.store.handle), before)

    def test_two_store_creations_never_reuse_a_database(self):
        with SyntheticDatabase() as other:
            self.assertNotEqual(other.handle.path, self.store.handle.path)
            self.assertNotEqual(other.handle.marker, self.store.handle.marker)
            self.assertEqual(snapshot(other.handle)[1], [])

    def test_account_limit_shared_by_login_registration_and_normalization(self):
        for index in range(10):
            self.assertTrue(reserve(self.adapter, action='register' if index % 2 else 'login',
                account=' SYNTHETIC@example.test ').allowed)
        before = snapshot(self.store.handle)
        result = reserve(self.adapter, action='register')
        self.assertFalse(result.allowed)
        self.assertEqual(result.retry_after_seconds, 900)
        self.assertEqual(snapshot(self.store.handle), before)  # No partial IP charge.

    def test_ip_limit_and_rejection_do_not_create_new_account_key(self):
        for index in range(30):
            self.assertTrue(reserve(self.adapter, account=f'synthetic-{index}@example.test').allowed)
        before = snapshot(self.store.handle)
        self.assertFalse(reserve(self.adapter, account='other@example.test').allowed)
        self.assertEqual(snapshot(self.store.handle), before)

    def test_account_limit_across_ips_does_not_charge_second_ip(self):
        for _ in range(10): reserve(self.adapter)
        before = snapshot(self.store.handle)
        self.assertFalse(reserve(self.adapter, ip='198.51.100.2').allowed)
        self.assertEqual(snapshot(self.store.handle), before)

    def test_unrelated_ip_and_account_still_admitted(self):
        for _ in range(10): reserve(self.adapter)
        self.assertTrue(reserve(self.adapter, ip='198.51.100.2', account='other@example.test').allowed)

    def test_exact_window_boundaries_and_partial_ageing(self):
        self.clock[0] = 0
        for _ in range(5): reserve(self.adapter)
        self.clock[0] = 500_000
        for _ in range(5): reserve(self.adapter)
        self.clock[0] = WINDOW_MS - 1
        self.assertFalse(reserve(self.adapter).allowed)
        self.clock[0] = WINDOW_MS
        self.assertTrue(reserve(self.adapter).allowed)
        with closing(sqlite3.connect(self.store.handle.path)) as connection:
            import json
            counts = [len(json.loads(r[0])) for r in connection.execute('SELECT stamps FROM prototype_windows')]
        self.assertEqual(counts, [6, 6])
        self.clock[0] = WINDOW_MS + 1
        self.assertTrue(reserve(self.adapter).allowed)

    def test_backward_clock_is_clamped_across_adapter_instances(self):
        for _ in range(10): reserve(self.adapter)
        other = ReservationAdapter(self.store.handle, clock=lambda: 0)
        self.assertFalse(reserve(other).allowed)
        self.assertEqual(snapshot(self.store.handle)[0][0][3], 1000)

    def test_invalid_clock_fails_without_admission(self):
        before = snapshot(self.store.handle)
        for value in (True, -1, float('nan'), '1000'):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(StorageUnavailable): reserve(ReservationAdapter(self.store.handle, clock=lambda: value))
        self.assertEqual(snapshot(self.store.handle), before)

    def test_independent_instances_connections_and_reopening_preserve_counters(self):
        for _ in range(10): reserve(ReservationAdapter(self.store.handle, clock=lambda: 1000))
        self.assertFalse(reserve(ReservationAdapter(self.store.handle, clock=lambda: 1000)).allowed)

    def _process_race(self, *, ip_boundary=False):
        if ip_boundary:
            for index in range(29): reserve(self.adapter, account=f'prefill-{index}@example.test')
        else:
            for _ in range(9): reserve(self.adapter)
        context = multiprocessing.get_context('spawn')
        ready, output = context.Queue(), context.Queue()
        start = context.Event()
        processes = [context.Process(target=process_contender, args=(self.store.handle, ready, start, output,
            f'contender-{index}@example.test' if ip_boundary else 'synthetic@example.test')) for index in range(4)]
        try:
            for process in processes: process.start()
            for _ in processes: self.assertTrue(ready.get(timeout=20))
            start.set()
            results = [output.get(timeout=20) for _ in processes]
            self.assertEqual(sorted(results), [('decision', False)] * 3 + [('decision', True)])
            for process in processes:
                process.join(10)
                self.assertEqual(process.exitcode, 0)
            # A later fresh process must observe the exhausted durable account/IP budget.
            late = context.Process(target=process_contender, args=(self.store.handle, ready, start, output,
                'late@example.test' if ip_boundary else 'synthetic@example.test'))
            processes.append(late); late.start()
            self.assertTrue(ready.get(timeout=20))
            self.assertEqual(output.get(timeout=20), ('decision', False))
            late.join(10); self.assertEqual(late.exitcode, 0)
            with closing(sqlite3.connect(self.store.handle.path)) as connection:
                import json
                values = connection.execute("SELECT stamps FROM prototype_windows WHERE namespace='ip'").fetchone()[0]
            self.assertEqual(len(json.loads(values)), 30 if ip_boundary else 10)
        finally:
            start.set()
            for process in processes:
                if process.is_alive(): process.terminate()
                process.join(5)
                process.close()
            for queue in (ready, output): queue.close(); queue.join_thread()

    def test_independent_processes_contest_final_account_slot(self): self._process_race()
    def test_independent_processes_contest_final_ip_slot(self): self._process_race(ip_boundary=True)

    def test_threads_use_independent_adapters_not_a_python_mutex(self):
        for _ in range(9): reserve(self.adapter)
        barrier = threading.Barrier(4)
        def contender(_):
            other = ReservationAdapter(self.store.handle, clock=lambda: 1000, busy_ms=1000)
            barrier.wait(timeout=5)
            return reserve(other).allowed
        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(sorted(pool.map(contender, range(4))), [False, False, False, True])

    def test_actual_transaction_holds_sqlite_writer_lock(self):
        store = self.store
        stages = []
        class Probe(ReservationAdapter):
            def _checkpoint(self, stage, connection):
                stages.append(stage)
                self_test.assertTrue(connection.in_transaction)
                with closing(sqlite3.connect(store.handle.path, timeout=0, isolation_level=None)) as probe:
                    with self_test.assertRaises(sqlite3.OperationalError) as caught:
                        probe.execute('BEGIN IMMEDIATE')
                    self_test.assertEqual(caught.exception.sqlite_errorcode & 255, sqlite3.SQLITE_BUSY)
        self_test = self
        self.assertTrue(reserve(Probe(store.handle, clock=lambda: 1000)).allowed)
        self.assertEqual(stages, ['after_first_write', 'before_commit'])

    def test_busy_fails_closed_before_clock_and_can_recover_after_release(self):
        calls = []
        before = snapshot(self.store.handle)
        other = ReservationAdapter(self.store.handle, clock=lambda: calls.append(True) or 1000, busy_ms=0)
        with closing(sqlite3.connect(self.store.handle.path, isolation_level=None)) as blocker:
            blocker.execute('BEGIN IMMEDIATE')
            with self.assertRaises(StorageBusy): reserve(other)
            blocker.rollback()
        self.assertEqual(calls, [])
        self.assertEqual(snapshot(self.store.handle), before)
        self.assertTrue(reserve(other).allowed)

    def test_rollback_after_first_write_and_before_commit(self):
        for failing_stage in ('after_first_write', 'before_commit'):
            class Broken(ReservationAdapter):
                def _checkpoint(self, stage, connection):
                    if stage == failing_stage: raise RuntimeError('Synthetic injected failure')
            before = snapshot(self.store.handle)
            with self.assertRaises(StorageUnavailable): reserve(Broken(self.store.handle, clock=lambda: 1000))
            self.assertEqual(snapshot(self.store.handle), before)
        self.assertTrue(reserve(self.adapter).allowed)

    def test_locked_sqlite_error_is_also_storage_unavailable(self):
        class Locked(ReservationAdapter):
            def _checkpoint(self, stage, connection):
                error = sqlite3.OperationalError('Synthetic locked injection')
                error.sqlite_errorcode = sqlite3.SQLITE_LOCKED
                raise error
        before = snapshot(self.store.handle)
        with self.assertRaises(StorageBusy): reserve(Locked(self.store.handle, clock=lambda: 1000))
        self.assertEqual(snapshot(self.store.handle), before)

    def test_corrupt_state_and_wrong_marker_fail_closed(self):
        self.assertTrue(reserve(self.adapter).allowed)
        with closing(sqlite3.connect(self.store.handle.path)) as connection:
            connection.execute("UPDATE prototype_windows SET stamps='not-json' WHERE namespace='account'"); connection.commit()
        before = snapshot(self.store.handle)
        with self.assertRaises(StorageUnavailable): reserve(self.adapter)
        self.assertEqual(snapshot(self.store.handle), before)
        wrong = SyntheticHandle(self.store.handle.directory, '0' * 64)
        with self.assertRaises(StorageUnavailable): reserve(ReservationAdapter(wrong))

    def test_missing_store_is_not_recreated(self):
        with SyntheticDatabase() as owned:
            handle = owned.handle
        with self.assertRaises(StorageUnavailable): reserve(ReservationAdapter(handle))
        self.assertFalse(handle.path.exists())

    def test_capacity_is_atomic_and_does_not_evict_active_windows(self):
        with SyntheticDatabase(max_keys=2) as owned:
            adapter = ReservationAdapter(owned.handle, clock=lambda: 1000)
            self.assertTrue(reserve(adapter).allowed)
            before = snapshot(owned.handle)
            with self.assertRaises(StorageUnavailable): reserve(adapter, account='new@example.test')
            self.assertEqual(snapshot(owned.handle), before)
            self.assertTrue(reserve(adapter).allowed)  # Existing pair needs no allocation.

    def test_cleanup_is_bounded_and_does_not_change_active_counters(self):
        with SyntheticDatabase(cleanup_batch=1) as owned:
            tick = [0]; adapter = ReservationAdapter(owned.handle, clock=lambda: tick[0])
            reserve(adapter)
            tick[0] = 500_000
            reserve(adapter, ip='198.51.100.2', account='active@example.test')
            active_keys = synthetic_keys('198.51.100.2', 'active@example.test')
            tick[0] = WINDOW_MS
            self.assertEqual(adapter.cleanup(), 1)
            self.assertEqual(adapter.cleanup(), 1)
            self.assertEqual(adapter.cleanup(), 0)
            rows = snapshot(owned.handle)
            self.assertEqual(rows[0][0][4], 2)
            self.assertEqual({(r[0], r[1]) for r in rows[1]}, set(active_keys))
            self.assertTrue(all(r[2] == '[500000]' for r in rows[1]))

    def test_expired_capacity_is_reclaimed_with_bounded_work(self):
        with SyntheticDatabase(max_keys=2, cleanup_batch=1) as owned:
            tick = [0]; adapter = ReservationAdapter(owned.handle, clock=lambda: tick[0])
            reserve(adapter); tick[0] = WINDOW_MS
            before = snapshot(owned.handle)
            with self.assertRaises(StorageUnavailable): reserve(adapter, ip='198.51.100.2', account='new@example.test')
            self.assertEqual(snapshot(owned.handle), before)
            self.assertEqual(adapter.cleanup(), 1)
            self.assertTrue(reserve(adapter, ip='198.51.100.2', account='new@example.test').allowed)

    def test_privacy_and_synthetic_input_restrictions(self):
        reserve(self.adapter)
        text = repr(snapshot(self.store.handle))
        self.assertNotIn('192.0.2.1', text)
        self.assertNotIn('synthetic@example.test', text)
        before = snapshot(self.store.handle)
        for ip, account in [('127.0.0.1', 'synthetic@example.test'), ('192.0.2.1', 'not-synthetic@invalid.test')]:
            with self.assertRaises(ValueError): reserve(self.adapter, ip=ip, account=account)
        with self.assertRaises(ValueError): reserve(self.adapter, action='password-reset')
        with self.assertRaises(ValueError): ReservationAdapter(Path('existing-database.sqlite'))
        self.assertEqual(snapshot(self.store.handle), before)

    def test_guard_rejection_before_open_or_after_wait_never_charges(self):
        before = snapshot(self.store.handle)
        with self.assertRaises(GuardRejected): reserve(self.adapter, guard=lambda: False)
        checks = iter([True, False])
        with self.assertRaises(GuardRejected): reserve(self.adapter, guard=lambda: next(checks))
        self.assertEqual(snapshot(self.store.handle), before)
        self.assertTrue(reserve(self.adapter).allowed)


if __name__ == '__main__': unittest.main()
