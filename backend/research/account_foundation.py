"""Read-only, account-scoped preparation. Current snapshots never reconstruct past knowledge."""
from datetime import date, timedelta
from types import SimpleNamespace
from math import isfinite
from .contract import Snapshot, aware, zone
from .dataset import point_features, HORIZON
from app.pattern_insights import describe

VERSION = 'account-preparation/v1'
FIELDS = {
    'episodes': ('id', 'date', 'started_at', 'ended_at', 'severity'),
    'wellness': ('id', 'date', 'timezone_name', 'recorded_at', 'sleep_hours',
        'sleep_quality', 'stress', 'hydration_ml', 'missed_meals', 'screen_hours',
        'episode_observation', 'observation_recorded_at'),
    'early_symptoms': ('id', 'onset_at', 'recorded_at'),
}


def account_snapshot(account_id, records, captured_at):
    """The caller captures after the read. Reject mixed/unclaimed input; copy only safe fields."""
    if not isinstance(account_id, int) or isinstance(account_id, bool) or account_id <= 0:
        raise ValueError('A positive account ID is required')
    captured_at = aware(captured_at)
    sources = {}
    invalid = {key: 0 for key in FIELDS}
    for source, fields in FIELDS.items():
        sources[source] = []
        for row in records.get(source, []):
            if row.get('owner_id') != account_id:
                raise ValueError('Account-scoped records required')
            selected = {key: row.get(key) for key in fields}
            try:
                if source == 'episodes':
                    if selected['started_at']:
                        onset = aware(selected['started_at'])
                        if selected['ended_at'] and aware(selected['ended_at']) < onset:
                            raise ValueError('Invalid chronology')
                    else:
                        date.fromisoformat(selected['date'])
                    if selected['severity'] is not None and not 0 <= selected['severity'] <= 10:
                        raise ValueError('Invalid severity')
                elif source == 'wellness':
                    date.fromisoformat(selected['date']); zone(selected['timezone_name'])
                    aware(selected['recorded_at'])
                    for field in ('sleep_hours','sleep_quality','stress','hydration_ml','screen_hours'):
                        if selected[field] is not None and not isfinite(selected[field]):
                            raise ValueError('Nonfinite observation')
                    if selected['observation_recorded_at']:
                        aware(selected['observation_recorded_at'])
                else:
                    onset = aware(selected['onset_at']); recorded = aware(selected['recorded_at'])
                    if onset > recorded:
                        raise ValueError('Symptom onset after recording')
            except (ValueError, TypeError, KeyError):
                invalid[source] += 1
                # Invalid attack timing must not silently establish at-risk eligibility.
                continue
            sources[source].append(selected)
    return Snapshot(exported_at=captured_at, **sources), invalid


def prepare(snapshot, cutoff, timezone_name='UTC'):
    """Use an actual pre-cutoff capture; never substitute a later editable export."""
    cutoff = aware(cutoff); zone(timezone_name)
    features, reason = point_features(snapshot, cutoff, timezone_name)
    if features is not None:
        rated = [row['severity'] for row in snapshot.episodes
            if row.get('severity') is not None and row.get('started_at')
            and cutoff-timedelta(days=30) <= aware(row['started_at']) < cutoff
            and aware(row['started_at']) <= aware(snapshot.exported_at)]
        features['reported_severity_mean_30d'] = sum(rated)/len(rated) if rated else None
        features['severity_observations_30d'] = float(len(rated))
    return {'pipeline_version': VERSION, 'snapshot_at': aware(snapshot.exported_at).isoformat(),
        'prediction_cutoff': cutoff.isoformat(), 'horizon_end': (cutoff+HORIZON).isoformat(),
        'timezone_name': timezone_name, 'eligibility': reason or 'eligible_for_preparation_only',
        'features': features, 'missing': {key: value is None for key, value in features.items()} if features else {},
        'target': None, 'probability': None, 'model_available': False}


def assess(account_id, records, captured_at, timezone_name='UTC', days=30):
    """No writes, training, historical backfill, or inferred outcome labels."""
    if not 7 <= days <= 90:
        raise ValueError('Reporting days must be between 7 and 90')
    zone(timezone_name)
    snapshot, invalid = account_snapshot(account_id, records, captured_at)
    # Capture is available strictly before this prospective preparation boundary.
    cutoff = aware(captured_at)+timedelta(microseconds=1)
    preparation = prepare(snapshot, cutoff, timezone_name)
    if invalid['episodes']:
        preparation.update(eligibility='invalid_episode_history', features=None, missing={})
    episodes = [SimpleNamespace(**row) for row in snapshot.episodes]
    wellness = [SimpleNamespace(**row, menstrual_notes=None) for row in snapshot.wellness]
    # Coverage is descriptive only; these observations do not reconstruct past versions.
    early = [SimpleNamespace(**row, symptom='Recorded early observation') for row in snapshot.early_symptoms]
    description = describe(episodes, wellness, early, timezone_name, days, aware(captured_at))
    daily = description['daily']
    coverage = {status: sum(day['status'] == status for day in daily) for status in (
        'episode_recorded', 'no_episode_reported', 'unknown', 'conflict', 'episode_reported_without_onset')}
    missingness = {'severity': {'missing': description['warnings'].get('missing_severity', 0),
        'available': description['summary']['severity_count']}}
    missingness.update({factor['key']: {'missing': factor['missing_count'], 'available': factor['count']}
        for factor in description['factors']})
    reasons = ['no_immutable_historical_versions', 'no_prospectively_established_labels',
        'unverified_research_consent_and_provenance', 'no_validated_model']
    return {'version': VERSION, 'status': 'not_ready', 'training_justified': False,
        'evaluation_justified': False, 'window_start': description['window_start'],
        'window_end': description['window_end'], 'days': days, 'coverage': coverage,
        'completed_days': sum(day['completed'] for day in daily),
        'wellness_checkins': description['summary']['wellness_checkins'],
        'early_observations': description['summary']['early_observations'],
        'missingness': missingness, 'invalid_records': invalid,
        'warnings': description['warnings'], 'labeled_outcomes': {'positive': 0, 'negative': 0,
        'unlabeled': None, 'candidate_windows': 0, 'basis': 'Reporting dates are not prospective labeled windows.'},
        'preparation': preparation, 'blocking_reasons': reasons,
        'limitations': ['Missing diary dates are unknown, not migraine-free.',
            'Zero observed onset counts do not establish zero attacks.',
            'This current capture is not persisted and cannot reconstruct past feature availability.',
            'Daily wellness is not an exact exposure timestamp; early symptoms are not proven prodromes.',
            'Whole-day reports are descriptive self-reports, not independently verified continuous surveillance.',
            'No model is trained or served; preparation eligibility is not training readiness.']}
