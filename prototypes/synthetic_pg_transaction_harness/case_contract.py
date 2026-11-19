"""Offline case mapping and maintenance request review; no I/O or authority."""
from case_design import Case, Refused, review_maintenance

CASE_NAMES = (
    'test_two_connections_final_account_slot',
    'test_two_connections_final_ip_slot',
    'test_two_connections_missing_key_creation',
    'test_action_sharing_normalization_and_all_or_nothing',
    'test_shared_ip_and_exact_expiry',
    'test_rollback_of_partial_and_complete_staged_pair',
    'test_cleanup_is_bounded_independent_and_active_safe',
    'test_cleanup_rollback',
    'test_cleanup_rejects_untrusted_evidence_without_deleting',
    'test_backward_clock_quarantines_without_reset',
    'test_known_untrusted_forward_clock_does_not_reopen',
    'test_trusted_forward_clock_is_not_automatically_detected',
    'test_primary_generation_change_is_not_a_reset',
    'test_stale_snapshot_flag_is_not_actual_restore_detection',
    'test_capacity_unavailable_no_active_eviction',
    'test_binding_and_guard_rejections_do_not_count',
    'test_two_connection_lock_timeout_does_not_charge',
)
MAINTENANCE_CASES = frozenset(CASE_NAMES[6:9])


def case_for_test(nonce, test_name):
    if test_name not in CASE_NAMES: raise Refused('Unknown synthetic test')
    return Case(nonce,CASE_NAMES.index(test_name)+1)


def maintenance_request(case, test_name, expected, observed, assertions, operation):
    """Validate a proposal only; no authentication, execution or credentials."""
    if not isinstance(case,Case) or test_name not in MAINTENANCE_CASES or case != case_for_test(case.nonce,test_name):
        raise Refused('Wrong maintenance case')
    review_maintenance(case,expected,observed,assertions)
    fields={'sample_ms','after_ms','batch','fault','test_fresh'}
    if type(operation) is not dict or set(operation)!=fields: raise Refused('Exact operation required')
    if type(operation['sample_ms']) is not int or not 0<=operation['sample_ms']<=9223372036853875807:
        raise Refused('Invalid test clock')
    if operation['after_ms'] is not None and (type(operation['after_ms']) is not int or not 0<=operation['after_ms']<=9223372036853875807):
        raise Refused('Invalid second test clock')
    if type(operation['batch']) is not int or not 1<=operation['batch']<=100:
        raise Refused('Invalid batch')
    if operation['fault'] not in (None,'before_commit') or type(operation['test_fresh']) is not bool:
        raise Refused('Invalid synthetic injection')
    if operation['fault']=='before_commit' and test_name!='test_cleanup_rollback':
        raise Refused('Fault outside rollback case')
    if operation['test_fresh'] is False and test_name!='test_cleanup_rejects_untrusted_evidence_without_deleting':
        raise Refused('Freshness injection outside negative case')
    return 'REVIEW_ONLY_NO_CLEANUP_AUTHORIZED'
