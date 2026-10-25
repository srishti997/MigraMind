"""Fixed offline baselines. No model artifacts, live DB reads, or runtime integration."""
from collections import Counter
from dataclasses import asdict
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
from .models import HistoricalFrequency, make_logistic
from .evaluation import evaluate
from .revision_dataset import VERSION, FEATURES, build_revision_dataset, split_account


def counts(rows):
    values = Counter(r.target for r in rows)
    return {'n':len(rows), 'positive':values[1], 'negative':values[0],
        'positive_fraction':values[1]/len(rows) if rows else None}


def gates(bundle, rows, splits, allow_synthetic=False):
    reasons = []
    source = bundle.provenance
    if source.source_kind == 'synthetic' and not allow_synthetic:
        reasons.append('synthetic_fit_requires_explicit_opt_in')
    if source.source_kind == 'consented' and not source.consent_reference:
        reasons.append('research_consent_required')
    if not source.provenance_verified: reasons.append('source_provenance_unverified')
    if not source.outcome_history_complete: reasons.append('outcome_history_unverified')
    if len(rows) < 180: reasons.append('fewer_than_180_valid_windows')
    if not rows or (rows[-1].prediction_at-rows[0].prediction_at).days < 179:
        reasons.append('less_than_180_day_span')
    total = counts(rows)
    if total['positive'] == 0 or total['negative'] == 0: reasons.append('single_class_or_empty_dataset')
    if total['positive'] < 30 or total['negative'] < 60: reasons.append('insufficient_class_counts')
    for name, minimum, per_class in [('train',90,10),('validation',20,5),('test',20,5)]:
        part = counts(splits[name])
        if part['n'] < minimum or min(part['positive'],part['negative']) < per_class:
            reasons.append(f'insufficient_{name}_samples_or_classes')
    return reasons


def matrix(rows):
    import numpy as np
    return np.asarray([[float('nan') if r.features[key] is None else r.features[key] for key in FEATURES]
        + [float(r.features[key] is None) for key in FEATURES] for r in rows], dtype=float)


def run_baselines(bundle, start, end, *, label_lag_hours=24, train=False, allow_synthetic=False, dataset_as_of=None):
    rows, excluded = build_revision_dataset(bundle, start, end, label_lag_hours, dataset_as_of=dataset_as_of)
    splits = split_account(rows, grid_start=start, grid_end=end)
    reasons = gates(bundle, rows, splits, allow_synthetic)
    report = {'pipeline_version':VERSION, 'research_schema_version':2,
        'status':'insufficient_data' if reasons else 'prepared', 'trained':False,
        'model_served':False, 'clinical_validation':False,
        'evidence_scope':'synthetic_software_test_only' if bundle.provenance.source_kind == 'synthetic' else 'consented_offline_research_only',
        'samples':counts(rows), 'excluded_windows':excluded,
        'candidate_windows':len(rows)+sum(excluded.values()),
        'splits':{key:counts(part) for key,part in splits.items()},
        'purged_windows':len(rows)-sum(len(part) for part in splits.values()),
        'blocking_reasons':reasons, 'models':{}, 'feature_names':list(FEATURES),
        'missing_fields':{key:sum(r.features[key] is None for r in rows) for key in FEATURES},
        'configuration':{'horizon_hours':24, 'cadence_hours':24, 'label_lag_hours':label_lag_hours,
            'split_boundary_policy':'fixed_candidate_grid_not_retained_rows', 'grid_start':str(start), 'grid_end':str(end),
            'split_fractions':[.6,.2,.2], 'threshold':.5, 'random_seed':0,
            'logistic':{'C':1.,'max_iter':1000,'imputation':'train_median_with_missing_indicators','scaling':'train_only'}},
        'snapshot':{'dataset_as_of':str(dataset_as_of or bundle.captured_at),
            'feature_policy':'strictly_before_prediction_cutoff',
            'outcome_policy':'horizon_end_plus_reporting_lag_inclusive',
            'eligibility_policy':'same_as_outcome_freeze_no_future_veto',
            'post_freeze_revisions':'ignored_for_frozen_decisions_not_current_truth',
            'policy_version':VERSION},
        'python_version':platform.python_version(),
        'dataset_sha256':hashlib.sha256(json.dumps([asdict(r) for r in rows],sort_keys=True,default=str,allow_nan=False).encode()).hexdigest(),
        'limitations':['Sample gates are engineering stop rules, not clinical sample-size justification.',
            'Verification and consent references are attestations requiring independent review.',
            'Labels and eligibility freeze after the reporting lag; subsequent corrections do not rewrite frozen decisions.',
            'No prospective or external validation; serial dependence and selective logging remain.',
            'Synthetic metrics test software only and cannot establish clinical effectiveness.']}
    if reasons or not train: return report, rows
    if importlib.util.find_spec('sklearn') is None or importlib.util.find_spec('numpy') is None:
        report['status'] = 'dependencies_unavailable'; return report, rows
    training = splits['train']
    frequency = HistoricalFrequency().fit(training)
    logistic = make_logistic()
    logistic.fit(matrix(training), [r.target for r in training])
    for name in ('always_no_onset', 'always_onset', 'historical_frequency', 'logistic_regression'):
        result = {}
        for split in ('validation','test'):
            part = splits[split]
            if name == 'always_no_onset': probabilities = [0.]*len(part)
            elif name == 'always_onset': probabilities = [1.]*len(part)
            elif name == 'historical_frequency': probabilities = frequency.predict(part)
            else: probabilities = logistic.predict_proba(matrix(part))[:,1].tolist()
            result[split] = evaluate([r.target for r in part], probabilities, threshold=.5)
        report['models'][name] = result
    report['brier_improvement_over_frequency'] = {split:
        report['models']['historical_frequency'][split]['brier_score']-
        report['models']['logistic_regression'][split]['brier_score'] for split in ('validation','test')}
    report['package_versions'] = {key:importlib.metadata.version(key) for key in ('numpy','scikit-learn')}
    report.update(status='synthetic_software_test_complete' if bundle.provenance.source_kind == 'synthetic'
        else 'offline_research_complete_not_validated', trained=True)
    return report, rows
