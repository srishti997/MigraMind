"""Models stay offline. Runtime service has no model-loading or prediction path."""
from collections import Counter
import importlib.util
from .dataset import FEATURE_NAMES

class HistoricalFrequency:
    """Train-only observed positive-window frequency; never attacks divided by unobserved days."""
    def fit(self,rows):
        if not rows:raise ValueError('Training observations required')
        self.frequency=sum(row.target for row in rows)/len(rows);return self
    def predict(self,rows):return [self.frequency for _ in rows]


def matrix(rows):
    import numpy as np
    # Explicit missing indicators preserve unknown vs zero, even for all-empty columns.
    return np.asarray([[float('nan') if row.features[k] is None else row.features[k] for k in FEATURE_NAMES]+
        [float(row.features[k] is None) for k in FEATURE_NAMES] for row in rows],dtype=float)


def make_logistic():
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    return Pipeline([('impute',SimpleImputer(strategy='median',keep_empty_features=True)),
        ('scale',StandardScaler()),('model',LogisticRegression(C=1.0,max_iter=1000,random_state=0))])


def make_xgboost():
    if importlib.util.find_spec('xgboost') is None:return None
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from xgboost import XGBClassifier
    return Pipeline([('impute',SimpleImputer(strategy='median',keep_empty_features=True)),
        ('model',XGBClassifier(n_estimators=100,max_depth=2,learning_rate=.05,subsample=1.,colsample_bytree=1.,objective='binary:logistic',eval_metric='logloss',n_jobs=1,random_state=0))])


def eligibility(bundle,rows,splits):
    reasons=[];p=bundle.provenance
    if p.source_kind!='real_longitudinal':reasons.append('real_longitudinal_provenance_required')
    if not p.participant_key or not p.source_description:reasons.append('documented_single_participant_source_required')
    if not p.consent_confirmed:reasons.append('consent_required')
    if not p.point_in_time_verified:reasons.append('immutable_snapshot_verification_required')
    if any('synthetic demo episode' in str(row.get('notes','')).lower() for s in bundle.snapshots for row in s.episodes):
        reasons.append('demo_records_detected')
    # Engineering stop rules, not a sample-size calculation or validation standard.
    if len(rows)<180:reasons.append('minimum_180_labeled_windows_required')
    if not rows or (max(r.prediction_at for r in rows)-min(r.prediction_at for r in rows)).days<179:
        reasons.append('minimum_180_day_span_required')
    counts=Counter(r.target for r in rows)
    if counts[1]<30 or counts[0]<60:reasons.append('insufficient_positive_or_negative_windows')
    for name,minimum,per_class in [('train',90,10),('validation',20,5),('test',20,5)]:
        part=splits[name];counts=Counter(r.target for r in part)
        if len(part)<minimum or min(counts[0],counts[1])<per_class:
            reasons.append(f'insufficient_{name}_samples_or_classes')
    return reasons
