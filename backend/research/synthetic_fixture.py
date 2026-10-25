"""Deterministic SOFTWARE TEST data, with no clinical or population interpretation."""
import argparse
from datetime import timedelta
from pathlib import Path
from .contract import aware
from .dataset import HORIZON
from .revision_contract import RevisionBundle


def make_synthetic(windows=240, all_negative=False):
    if not isinstance(windows,int) or isinstance(windows,bool) or not 1 <= windows <= 1000:
        raise ValueError('Fixture size must be 1–1000')
    start = aware('2024-01-01T00:00:00Z')
    daily, outcomes = [], []
    for i in range(windows):
        cutoff = start+i*HORIZON
        event = cutoff-HORIZON+timedelta(hours=12)
        recorded = cutoff-timedelta(hours=1)
        daily.append({'account_key':'synthetic-a','record_id':f'd{i}','revision':1,'action':'creation',
            'recorded_at':recorded,'values':{'date':event.date(),'timezone_name':'UTC','status':'unknown',
                'event_at':event,'observed_at':event,'status_recorded_at':recorded,'stress':i%7}})
        positive = not all_negative and i%4 == 0
        left = cutoff+timedelta(hours=6) if positive else cutoff
        right = cutoff+timedelta(hours=7) if positive else cutoff+HORIZON
        outcomes.append({'account_key':'synthetic-a','record_id':f'o{i}','revision':1,'action':'creation',
            'recorded_at':right+timedelta(hours=1),'values':{'kind':'onset' if positive else 'no_episode_interval',
                'start_at':left,'end_at':right,'verified':True,'independently_verified':True,'verification_reference':f'synthetic-evidence-{i}', 'complete':not positive}})
        if positive:
            outcomes.append({'account_key':'synthetic-a','record_id':f'coverage{i}','revision':1,'action':'creation',
                'recorded_at':cutoff+HORIZON+timedelta(hours=1), 'values':{'kind':'observation_interval',
                    'start_at':cutoff,'end_at':cutoff+HORIZON,'verified':True,'independently_verified':True,
                    'verification_reference':f'synthetic-surveillance-{i}','complete':True}})
    return RevisionBundle(account_key='synthetic-a',captured_at=start+(windows+3)*HORIZON,
        provenance={'source_kind':'synthetic','source_reference':'deterministic-software-fixture/v1',
            'provenance_verified':True,'outcome_history_complete':True},
        daily_revisions=daily,outcome_revisions=outcomes)


def main(argv=None):
    parser=argparse.ArgumentParser(description='Write explicitly synthetic software test cases, never clinical data.')
    parser.add_argument('--output',type=Path,required=True,help='Private/ignored destination; refuses overwrite')
    args=parser.parse_args(argv)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as output:
        output.write(make_synthetic().model_dump_json(indent=2))
    print('Synthetic SOFTWARE TEST fixture written; no real-world evidence created.')


if __name__=='__main__': main()
