"""Offline comparison only: no resource inspection, authorization or deletion."""
import re


class Refused(ValueError):
    pass


FIELDS = ('run_id','nonce','container_id','image_digest','server_version','volume_id',
          'port','database','fixture_role','maintenance_role','owner','generation','writer')


def plan(record, runtime, database, approvals, now_ms):
    """Validate caller-supplied observations; never grant execution authority.

    The caller must independently authenticate and protect all inputs. This pure
    function cannot establish provenance, persist a lease, or prevent replay.
    """
    if not all(type(v) is dict for v in (record,runtime,database,approvals)):
        raise Refused('Evidence objects required')
    if set(record)!=set(FIELDS)|{'state','revision'} or record['state']!='STOPPED':
        raise Refused('Stopped complete record required')
    if type(record['revision']) is not int or record['revision']<1:
        raise Refused('Invalid record revision')
    if any(not isinstance(record[k],str) or not record[k] for k in FIELDS if k!='port'):
        raise Refused('Missing identity')
    if (not re.fullmatch('[0-9a-f]{32}',record['nonce'])
            or not re.fullmatch('[0-9a-f]{64}',record['container_id'])
            or not re.fullmatch('sha256:[0-9a-f]{64}',record['image_digest'])
            or type(record['port']) is not int or not 49152<=record['port']<=65535):
        raise Refused('Malformed target')
    if record['volume_id']!='migramind-pg-harness-'+record['nonce']:
        raise Refused('Volume does not match nonce')
    if len({record['owner'],record['fixture_role'],record['maintenance_role']})!=3:
        raise Refused('Authorities must be distinct')
    runtime_fields=('run_id','nonce','container_id','image_digest','server_version','volume_id','port')
    database_fields=('run_id','nonce','database','fixture_role','maintenance_role','owner','generation','writer')
    for observation, keys in ((runtime,runtime_fields),(database,database_fields)):
        if set(observation)!=set(keys)|{'observed_ms','revision','state','isolated'}:
            raise Refused('Incomplete observation')
        if any(observation[k]!=record[k] for k in keys): raise Refused('Identity mismatch')
        if (type(observation['revision']) is not int or observation['revision']!=record['revision'] or observation['state']!='STOPPED'
                or observation['isolated'] is not True): raise Refused('Lifecycle mismatch')
        stamp=observation['observed_ms']
        if type(now_ms) is not int or type(stamp) is not int or not 0<=now_ms-stamp<=30000:
            raise Refused('Stale or invalid observation')
    required={'generation','writer','time_approved','freshness_approved','teardown_approved','lease_held'}
    if set(approvals)!=required or any(approvals[k] is not True for k in required):
        raise Refused('All approvals required')
    return 'REVIEW_ONLY_NO_DELETION_AUTHORIZED'
