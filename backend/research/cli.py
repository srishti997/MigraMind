"""Local-only CLI: source audit, reproducible preparation, opt-in offline experiments."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import sys
from .contract import Bundle, aware
from .dataset import PIPELINE_VERSION
from .experiment import run


def audit_current_database():
    # Read only; use existing SQLAlchemy session configuration. Never infer real provenance.
    from app.main import SessionLocal, Episode, Wellness, EarlySymptom, AttackSession
    now=datetime.now(timezone.utc).isoformat()
    with SessionLocal() as s:
        def records(model):return [{col.name:getattr(row,col.name) for col in model.__table__.columns} for row in s.query(model).all()]
        snapshot={'schema_version':3,'exported_at':now,'episodes':records(Episode),'wellness':records(Wellness),
            'early_symptoms':records(EarlySymptom),'attack_sessions':records(AttackSession)}
    data=Bundle(snapshots=[snapshot])
    return data,{'pipeline_version':PIPELINE_VERSION,'status':'insufficient_data','trained':False,
        'local_only':True,'row_counts':{key:len(snapshot[key]) for key in ['episodes','wellness','early_symptoms','attack_sessions']},
        'timed_episode_count':sum(bool(r.get('started_at')) for r in snapshot['episodes']),
        'seed_marked_episode_count':sum('synthetic demo episode' in str(r.get('notes','')).lower() for r in snapshot['episodes']),
        'provenance':'unknown_or_mixed_demo','explicit_observation_intervals':0,
        'blocking_reasons':['provenance_unverified','no_complete_observation_windows','no_point_in_time_snapshot_history','no_validated_model']}


def main(argv=None):
    parser=argparse.ArgumentParser(description='Local migraine research; no predictions, publishing, or emergency actions.')
    parser.add_argument('--audit-db',action='store_true',help='Read-only aggregate audit; never trains')
    parser.add_argument('--input',type=Path,help='Local version-1 research bundle, not a raw final export')
    parser.add_argument('--start',help='First UTC-offset-bearing prediction time, inclusive')
    parser.add_argument('--end',help='Last prediction boundary, exclusive')
    parser.add_argument('--timezone',default='Asia/Kolkata')
    parser.add_argument('--train',action='store_true',help='Offline fitting only if provenance and data gates pass')
    parser.add_argument('--output-dir',type=Path,help='Explicit private output directory for aggregate report')
    parser.add_argument('--write-dataset',action='store_true',help='Also save sensitive derived features locally')
    args=parser.parse_args(argv)
    if args.audit_db and (args.input or args.train or args.write_dataset):parser.error('Audit is read-only and cannot train or emit a dataset')
    if args.write_dataset and not args.output_dir:parser.error('Sensitive dataset output requires --output-dir')
    if args.train and not args.output_dir:parser.error('Research fitting requires a private --output-dir')
    try:
        if args.audit_db:
            _,report=audit_current_database();rows=[]
        else:
            if not args.input or not args.start or not args.end:parser.error('Supply --input, --start and --end, or use --audit-db')
            content=args.input.read_bytes()
            bundle=Bundle.model_validate_json(content.decode('utf-8-sig'))
            report,rows=run(bundle,aware(args.start),aware(args.end),args.timezone,train=args.train)
            report['source_sha256']=hashlib.sha256(content).hexdigest()
            source=hashlib.sha256()
            for module in sorted(Path(__file__).parent.glob('*.py')):
                source.update(module.name.encode());source.update(module.read_bytes())
            report['research_source_sha256']=source.hexdigest()
            report['provenance_kind']=bundle.provenance.source_kind
            report['prediction_grid']={'start':aware(args.start).isoformat(),'end':aware(args.end).isoformat(),'step_hours':24,'timezone':args.timezone}
        if args.output_dir:
            args.output_dir.mkdir(parents=True,exist_ok=True)
            # Only aggregate report by default. Do not serialize models/pickles or patient notes.
            (args.output_dir/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
            if args.write_dataset:
                (args.output_dir/'dataset.json').write_text(json.dumps([asdict(row) for row in rows],default=lambda v:v.isoformat(),indent=2,allow_nan=False),encoding='utf-8')
        # stdout contains status only, never feature rows, probabilities or health details.
        print(json.dumps({'status':report['status'],'trained':report.get('status')=='research_complete_not_validated','model_served':False}))
        return 0
    except (ValueError,KeyError,TypeError,OSError):
        # Validation errors can embed input health records: do not print raw exceptions.
        print(json.dumps({'status':'invalid_local_input','trained':False,'model_served':False}),file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
