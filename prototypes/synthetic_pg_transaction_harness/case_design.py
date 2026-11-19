"""Offline case and maintenance proposals; no I/O, connection or authorization."""
from dataclasses import dataclass
import re


class Refused(ValueError):
    pass


@dataclass(frozen=True)
class Case:
    nonce: str
    ordinal: int

    def __post_init__(self):
        if not isinstance(self.nonce,str) or re.fullmatch('[0-9a-f]{32}',self.nonce) is None:
            raise Refused('Invalid nonce')
        if type(self.ordinal) is not int or not 1<=self.ordinal<=999:
            raise Refused('Invalid case ordinal')

    @property
    def suffix(self): return self.nonce+'_'+str(self.ordinal).zfill(3)
    @property
    def database(self): return 'mm_case_'+self.suffix
    @property
    def fixture(self): return 'mm_fixture_'+self.suffix
    @property
    def maintenance(self): return 'mm_maint_'+self.suffix
    @property
    def owner(self): return 'mm_owner_'+self.nonce


def propose_case(case, inventory, state):
    """Compare an externally supplied complete inventory; never allocate resources."""
    if not isinstance(case,Case) or type(inventory) is not dict or set(inventory)!={'databases','roles','complete'}:
        raise Refused('Exact inventory required')
    if inventory['complete'] is not True or state!='NEW': raise Refused('Unknown, partial or stale state')
    if any(type(inventory[k]) is not tuple or any(type(x) is not str for x in inventory[k]) for k in ('databases','roles')):
        raise Refused('Invalid inventory')
    if case.database in inventory['databases'] or any(x in inventory['roles'] for x in (case.fixture,case.maintenance)):
        raise Refused('Case identity collision')
    return (case.database,case.fixture,case.maintenance,case.owner)


def review_maintenance(case, expected, observed, assertions):
    """Compare assertions only; cannot authenticate a caller or invoke cleanup."""
    keys={'database','owner','fixture','maintenance','generation','writer'}
    if not isinstance(case,Case) or type(expected) is not dict or type(observed) is not dict:
        raise Refused('Case evidence required')
    if set(expected)!=keys or set(observed)!=keys or any(type(expected[k]) is not str or not expected[k] for k in keys):
        raise Refused('Complete identity required')
    identities={'database':case.database,'owner':case.owner,'fixture':case.fixture,'maintenance':case.maintenance}
    if any(expected[k]!=v for k,v in identities.items()) or observed!=expected:
        raise Refused('Case identity mismatch')
    required={'independent_maintenance_authority','time_approved','freshness_approved','case_verified'}
    if type(assertions) is not dict or set(assertions)!=required or any(assertions[k] is not True for k in required):
        raise Refused('Affirmative evidence required')
    return 'REVIEW_ONLY_NO_CLEANUP_AUTHORIZED'
