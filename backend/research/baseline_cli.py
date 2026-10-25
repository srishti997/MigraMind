"""python -m research.baseline_cli: v2 revision-based experiments, never live records."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
from .contract import aware
from .revision_contract import RevisionBundle
from .baseline_v2 import run_baselines


def main(argv=None):
    parser = argparse.ArgumentParser(description='Offline, account-isolated research baselines; never serves models.')
    parser.add_argument('--input',type=Path,required=True,help='Private research-schema-2 bundle, not a raw app export')
    parser.add_argument('--start',required=True,help='Inclusive offset-bearing cutoff')
    parser.add_argument('--end',required=True,help='Exclusive offset-bearing grid boundary')
    parser.add_argument('--label-lag-hours',type=int,default=24)
    parser.add_argument('--dataset-as-of',help='Immutable journal snapshot boundary; defaults to captured_at')
    parser.add_argument('--train',action='store_true')
    parser.add_argument('--allow-synthetic-fit',action='store_true',help='Software verification only, never clinical evidence')
    parser.add_argument('--output-dir',type=Path)
    parser.add_argument('--write-dataset',action='store_true',help='Sensitive local feature/label export; explicit opt-in')
    args = parser.parse_args(argv)
    if (args.train or args.write_dataset) and not args.output_dir:
        parser.error('Fitting/dataset output requires an explicit private --output-dir')
    try:
        content = args.input.read_bytes()
        bundle = RevisionBundle.model_validate_json(content.decode('utf-8-sig'))
        report, rows = run_baselines(bundle, aware(args.start), aware(args.end),
            dataset_as_of=aware(args.dataset_as_of) if args.dataset_as_of else None,
            label_lag_hours=args.label_lag_hours, train=args.train, allow_synthetic=args.allow_synthetic_fit)
        report['input_sha256'] = hashlib.sha256(content).hexdigest()
        source = hashlib.sha256()
        for path in sorted(Path(__file__).parent.glob('*.py')):
            source.update(path.name.encode()); source.update(path.read_bytes())
        report['research_source_sha256'] = source.hexdigest()
        report['grid'] = {'start':aware(args.start).isoformat(), 'end':aware(args.end).isoformat(),
            'captured_at':bundle.captured_at.isoformat()}
        if args.output_dir:
            args.output_dir.mkdir(parents=True,exist_ok=True)
            (args.output_dir/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
            if args.write_dataset:
                (args.output_dir/'dataset.json').write_text(json.dumps([asdict(r) for r in rows],
                    default=lambda value:value.isoformat(),indent=2,allow_nan=False),encoding='utf-8')
        print(json.dumps({key:report[key] for key in ('status','trained','model_served','evidence_scope')}))
        return 0
    except (ValueError, TypeError, KeyError, OSError):
        # No raw validation exception or path/health payload reaches logs/stdout.
        print(json.dumps({'status':'invalid_private_research_input','trained':False,'model_served':False}),file=sys.stderr)
        return 2


if __name__ == '__main__': raise SystemExit(main())
