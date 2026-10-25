"""Historical features use pre-cutoff versions; outcomes use a fixed, mature freeze."""
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from .contract import aware, zone
from .dataset import HORIZON
from .revision_contract import groups

VERSION = 'revision-onset-24h/v2.1'
FEATURES = ('sleep_hours', 'sleep_quality', 'stress', 'hydration_ml',
    'observation_age_hours', 'daily_reports_7d', 'migraine_reports_7d',
    'verified_onsets_7d', 'verified_onsets_30d')


@dataclass(frozen=True)
class ResearchExample:
    account_key: str
    prediction_at: datetime
    horizon_end: datetime
    label_available_at: datetime
    target: int
    features: dict[str, float | None]
    snapshot_at: datetime
    outcome_as_of: datetime
    eligibility_as_of: datetime


def latest(chains, boundary, inclusive=False):
    result = {}
    for key, chain in chains.items():
        known = [r for r in chain if r.recorded_at < boundary or (inclusive and r.recorded_at == boundary)]
        if known: result[key] = known[-1]
    return result


def features_at(bundle, cutoff):
    cutoff = aware(cutoff)
    daily = latest(groups(bundle.daily_revisions), cutoff)
    outcomes = latest(groups(bundle.outcome_revisions), cutoff)
    selected = [r for r in daily.values() if r.values is not None]
    past = [r for r in outcomes.values() if r.values and r.values.kind == 'onset'
        and verified(r.values) and r.values.start_at < cutoff]
    if any(r.values.end_at is None or r.values.end_at > cutoff for r in past):
        return None, None, 'ongoing_or_unresolved_episode'
    if not selected and not past: return None, None, 'no_historical_observations'
    features = {key:None for key in FEATURES}
    valid = []
    for revision in selected:
        value = revision.values
        day_end = datetime.combine(value.date + timedelta(days=1), time.min, zone(value.timezone_name))
        if day_end <= cutoff and cutoff - timedelta(days=7) <= value.event_at < cutoff:
            valid.append(revision)
    # Latest event, not latest correction; tie-break by opaque ID, never input ordering.
    valid.sort(key=lambda r:(r.values.event_at, r.record_id))
    if valid:
        value = valid[-1].values
        for key in ('sleep_hours', 'sleep_quality', 'stress', 'hydration_ml'):
            features[key] = float(getattr(value, key)) if getattr(value, key) is not None else None
        features['observation_age_hours'] = (cutoff - value.event_at).total_seconds()/3600
    features['daily_reports_7d'] = float(len(valid))
    features['migraine_reports_7d'] = float(sum(r.values.status == 'migraine' for r in valid))
    # Dedupe verified starts; daily migraine reports never become exact onset events.
    starts = {r.values.start_at for r in past}
    if bundle.provenance.outcome_history_complete:
        for days in (7, 30):
            features[f'verified_onsets_{days}d'] = float(sum(cutoff-timedelta(days=days) <= t < cutoff for t in starts))
    available = max([r.recorded_at for r in selected+past])
    return features, available, None


def verified(value):
    return value.verified and value.independently_verified and bool(value.verification_reference)


def touches(value, start, end):
    if value.kind == 'onset' and start <= value.start_at < end: return True
    return value.start_at < end and (value.end_at is None or value.end_at > start)


def outcome_at(bundle, start, end, freeze):
    if freeze > bundle.captured_at: return None, 'outcome_not_mature'
    if not bundle.provenance.outcome_history_complete:
        return None, 'outcome_history_unverified'
    # Never let evidence recorded after this decision alter historical eligibility.
    chains = groups([r for r in bundle.outcome_revisions if r.recorded_at <= freeze])
    selected = latest(chains, freeze, inclusive=True)
    # Withdrawals/moved evidence KNOWN BY freeze exclude, never manufacture negatives.
    for key, chain in chains.items():
        relevant = any(r.values and touches(r.values, start, end) for r in chain)
        if not relevant: continue
        if chain[-1].action == 'deletion': return None, 'deleted_outcome'
        if (chain[-1].values.kind == 'onset' and
            not touches(chain[-1].values, start, end)):
            return None, 'retracted_or_moved_outcome'
    values = [r.values for r in selected.values() if r.values and touches(r.values, start, end)]
    for value in values:
        if not verified(value): return None, 'unverified_outcome'
        if value.kind == 'unknown_interval': return None, 'unknown_outcome_interval'
        if value.kind in ('no_episode_interval', 'observation_interval') and not value.complete:
            return None, 'incomplete_outcome_coverage'
        if value.kind == 'onset' and value.start_at < start:
            return None, 'retrospectively_ongoing_episode'
    positives = [v for v in values if v.kind == 'onset' and start <= v.start_at < end]
    negatives = [v for v in values if v.kind == 'no_episode_interval']
    # Conflicting independent evidence requires adjudication, not precedence rules.
    if any(v.start_at <= p.start_at < v.end_at for v in negatives for p in positives):
        return None, 'conflicting_outcome_evidence'
    coverage = [v for v in values if v.kind in ('observation_interval', 'no_episode_interval')] if positives else negatives
    cursor = start
    for interval in sorted(coverage, key=lambda v:(v.start_at, v.end_at)):
        if interval.start_at > cursor: break
        cursor = max(cursor, interval.end_at)
        if cursor >= end: return int(bool(positives)), None
    # Earlier onset corrections moving outside this horizon cannot silently create a negative.
    return None, 'no_complete_observation_coverage' if positives else 'no_complete_no_episode_coverage'


def build_revision_dataset(bundle, start, end, label_lag_hours=24, *, dataset_as_of=None):
    start, end = aware(start), aware(end)
    dataset_as_of = aware(dataset_as_of) if dataset_as_of is not None else bundle.captured_at
    if dataset_as_of > bundle.captured_at: raise ValueError("Dataset snapshot exceeds journal capture")
    bundle = bundle.model_copy(update={"captured_at":dataset_as_of,
        "daily_revisions":[r for r in bundle.daily_revisions if r.recorded_at <= dataset_as_of],
        "outcome_revisions":[r for r in bundle.outcome_revisions if r.recorded_at <= dataset_as_of]})
    if start >= end or not isinstance(label_lag_hours, int) or isinstance(label_lag_hours,bool) or not 0 <= label_lag_hours <= 168:
        raise ValueError('Invalid prediction grid or reporting lag')
    rows, excluded = [], {}
    cutoff = start
    while cutoff < end:
        horizon = cutoff + HORIZON
        freeze = horizon + timedelta(hours=label_lag_hours)
        if bundle.provenance.source_kind == 'consented' and (not bundle.provenance.consent_reference or not bundle.provenance.provenance_verified):
            features, available, reason = None, None, 'consent_or_provenance_unverified'
        else:
            features, available, reason = features_at(bundle, cutoff)
        if reason is None: target, reason = outcome_at(bundle, cutoff, horizon, freeze)
        if reason: excluded[reason] = excluded.get(reason, 0)+1
        else: rows.append(ResearchExample(bundle.account_key, cutoff, horizon, freeze, target, features, available, freeze, freeze))
        cutoff += HORIZON
    return rows, excluded


def split_account(rows, *, grid_start, grid_end):
    if len({r.account_key for r in rows}) > 1: raise ValueError('Cross-account split forbidden')
    ordered = sorted(rows, key=lambda r:r.prediction_at)
    if any(right.prediction_at < left.horizon_end for left,right in zip(ordered, ordered[1:])):
        raise ValueError('Overlapping prediction horizons forbidden')
    start, end = aware(grid_start), aware(grid_end)
    if start >= end: raise ValueError('Invalid split grid')
    # Boundaries derive from the planned grid, never from retained outcome labels.
    n = (end-start+HORIZON-timedelta(microseconds=1)) // HORIZON
    validation_at = start + int(n*.6)*HORIZON
    test_at = start + int(n*.8)*HORIZON
    if any(r.prediction_at < start or r.prediction_at >= end or
        (r.prediction_at-start) % HORIZON != timedelta(0) or
        r.snapshot_at >= r.prediction_at or r.horizon_end != r.prediction_at+HORIZON or
        r.label_available_at < r.horizon_end for r in ordered):
        raise ValueError('Invalid point-in-time example/grid')
    return {'train':[r for r in ordered if r.prediction_at < validation_at and
                r.horizon_end < validation_at and r.label_available_at < validation_at],
        'validation':[r for r in ordered if validation_at <= r.prediction_at < test_at and
                r.horizon_end < test_at and r.label_available_at < test_at],
        'test':[r for r in ordered if r.prediction_at >= test_at]}
