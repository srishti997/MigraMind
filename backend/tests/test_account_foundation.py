"""Synthetic fixtures only: no clinical evidence, training or user database access."""
from datetime import datetime, timedelta, timezone
import pytest
from research.account_foundation import account_snapshot, prepare, assess
from research.contract import aware
from test_auth import clients, register

NOW=aware('2026-11-02T12:00:00Z')

def records():
    return {'episodes':[{'owner_id':1,'id':1,'date':'2026-11-01',
        'started_at':'2026-11-01T10:00:00Z','ended_at':'2026-11-01T11:00:00Z','severity':None}],
        'wellness':[{'owner_id':1,'id':1,'date':'2026-11-01','timezone_name':'UTC',
        'recorded_at':'2026-11-02T09:00:00Z','sleep_hours':None,'stress':0,'missed_meals':False}],
        'early_symptoms':[{'owner_id':1,'id':1,'onset_at':'2026-11-02T10:00:00Z','recorded_at':'2026-11-02T10:15:00Z'}]}


def test_account_projection_rejects_mixed_unassigned_and_omits_private_fields():
    source=records();source['episodes'][0]['notes']='Synthetic private note'
    snapshot,invalid=account_snapshot(1,source,NOW)
    assert 'notes' not in snapshot.episodes[0] and 'owner_id' not in snapshot.episodes[0]
    assert all(value==0 for value in invalid.values())
    for owner in (2,None):
        source['episodes'][0]['owner_id']=owner
        with pytest.raises(ValueError,match='Account-scoped'):account_snapshot(1,source,NOW)


def test_snapshot_must_precede_cutoff_and_late_records_never_become_features():
    source=records()
    # Even a retrospectively dated check-in is unavailable if logged after capture.
    source['wellness'][0]['recorded_at']='2026-11-03T09:00:00Z'
    source['early_symptoms'][0]['recorded_at']='2026-11-03T10:00:00Z'
    snapshot,_=account_snapshot(1,source,NOW)
    with pytest.raises(ValueError):prepare(snapshot,NOW)
    with pytest.raises(ValueError):prepare(snapshot,NOW-timedelta(seconds=1))
    data=prepare(snapshot,NOW+timedelta(seconds=1))
    assert data['features']['previous_stress'] is None
    assert data['features']['early_symptom_observations_24h']==0
    # Changes to the original live rows cannot revise this copied capture.
    source['episodes'][0]['severity']=9
    assert data['features']['reported_severity_mean_30d'] is None
    assert prepare(snapshot,NOW+timedelta(seconds=1))==data


def test_missing_severity_not_zero_and_no_unlogged_negatives_or_training():
    source=records();data=assess(1,source,NOW)
    assert data['preparation']['features']['reported_severity_mean_30d'] is None
    assert data['preparation']['missing']['reported_severity_mean_30d'] is True
    assert data['preparation']['features']['previous_stress']==0
    assert data['preparation']['features']['previous_missed_meals']==0
    assert data['preparation']['features']['previous_sleep_hours'] is None
    assert data['coverage']['unknown']==29
    assert data['labeled_outcomes']['positive']==data['labeled_outcomes']['negative']==0
    assert data['training_justified'] is data['evaluation_justified'] is False
    source['episodes'][0]['severity']=0
    zero=assess(1,source,NOW)
    assert zero['preparation']['features']['reported_severity_mean_30d']==0
    assert zero['preparation']['missing']['reported_severity_mean_30d'] is False


def test_unknown_end_and_invalid_history_prevent_at_risk_feature_preparation():
    source=records();source['episodes'][0]['ended_at']=None
    data=assess(1,source,NOW)
    assert data['preparation']['eligibility']=='ongoing_or_unresolved_episode'
    assert data['preparation']['features'] is None
    source['episodes'][0]['started_at']='naive-invalid'
    data=assess(1,source,NOW)
    assert data['preparation']['eligibility']=='invalid_episode_history'
    assert data['invalid_records']['episodes']==1
    assert data['preparation']['features'] is None


@pytest.mark.parametrize('cutoff,eligible',[
    ('2026-11-02T04:59:59Z',False), # Still November 1 in New York.
    ('2026-11-02T05:00:00Z',True),  # Completed 25-hour local day.
])
def test_wellness_completion_uses_source_timezone_and_horizon_is_24_elapsed_hours(cutoff,eligible):
    cutoff=aware(cutoff);source=records();source['episodes']=[];source['early_symptoms']=[]
    source['wellness'][0].update(timezone_name='America/New_York',recorded_at='2026-11-01T20:00:00Z')
    snapshot,_=account_snapshot(1,source,cutoff-timedelta(seconds=1))
    data=prepare(snapshot,cutoff,'Asia/Kolkata')
    assert (data['features']['previous_stress']==0) is eligible
    assert aware(data['horizon_end'])-aware(data['prediction_cutoff'])==timedelta(hours=24)


def test_future_onsets_and_outcome_window_symptoms_are_not_history():
    source=records();source['episodes'][0]['started_at']='2026-11-03T10:00:00Z'
    source['episodes'][0]['ended_at']='2026-11-03T11:00:00Z'
    source['early_symptoms'][0].update(onset_at='2026-11-03T09:00:00Z',recorded_at='2026-11-03T09:15:00Z')
    snapshot,_=account_snapshot(1,source,NOW)
    data=prepare(snapshot,NOW+timedelta(seconds=1))
    assert data['features']['episode_onsets_30d']==0
    assert data['features']['early_symptom_observations_24h']==0
    assert data['target'] is data['probability'] is None


def test_api_scopes_every_source_and_never_accepts_account_or_cutoff_override(clients):
    a,b,factory=clients;register(a);register(b,'foundation-b@example.test')
    yesterday=(datetime.now(timezone.utc)-timedelta(days=1)).date().isoformat()
    assert a.post('/api/episodes',json={'started_at':yesterday+'T10:00:00Z','ended_at':yesterday+'T11:00:00Z','timezone_name':'UTC'}).status_code==201
    assert a.post('/api/wellness',json={'date':yesterday,'timezone_name':'UTC','stress':8}).status_code==201
    assert a.post('/api/early-symptoms',json={'symptom':'Synthetic private marker','onset_at':yesterday+'T09:00:00Z','timezone_name':'UTC'}).status_code==201
    a_report=a.get('/api/v1/data-readiness').json()
    other=b.get('/api/v1/data-readiness?owner_id=1&cutoff=2000-01-01T00:00Z')
    assert other.status_code==200 and other.headers['cache-control']=='no-store'
    assert a_report['coverage']['episode_recorded']==1
    assert a_report['missingness']['severity']=={'missing':1,'available':0}
    assert other.json()['coverage']['episode_recorded']==0
    assert a_report['early_observations']==1
    assert other.json()['early_observations']==0
    assert other.json()['wellness_checkins']==0
    assert other.json()['preparation']['features']['early_symptom_observations_24h']==0
    assert 'Synthetic private marker' not in a_report.__str__()
    assert a.get('/api/v1/data-readiness?timezone_name=bad').status_code==422
    assert a.get('/api/v1/data-readiness?days=91').status_code==422
    assert a.get('/api/v1/data-readiness',headers={'X-CSRF-Token':''}).status_code==401
    a.cookies.clear();assert a.get('/api/v1/data-readiness').status_code==401


def test_local_audit_requires_account_and_does_not_pool_records(clients,monkeypatch):
    from app import main
    from research.cli import audit_current_database
    a,b,factory=clients;user_a=register(a);user_b=register(b,'audit-b@example.test')
    a.post('/api/episodes',json={'date':'2026-01-01','severity':0,'notes':'Synthetic private A'})
    monkeypatch.setattr(main,'SessionLocal',factory)
    snapshot,report=audit_current_database(user_b['id'])
    assert snapshot.snapshots[0].episodes==[]
    assert report['row_counts']['episodes']==0
    snapshot,_=audit_current_database(user_a['id'])
    assert len(snapshot.snapshots[0].episodes)==1
    with pytest.raises(ValueError):audit_current_database(None)


def test_invalid_wellness_is_counted_not_zero_filled_and_future_dates_stay_unknown():
    source=records();source['wellness'][0]['stress']=float('nan')
    data=assess(1,source,NOW)
    assert data['invalid_records']['wellness']==1
    assert data['preparation']['features']['previous_stress'] is None
    assert data['wellness_checkins']==0
    assert data['coverage']['no_episode_reported']==0


def test_whole_day_confirmations_are_coverage_not_prospective_labels():
    source=records();source['episodes']=[];source['early_symptoms']=[]
    source['wellness'][0].update(episode_observation='no_episode',observation_recorded_at='2026-11-02T09:00:00Z')
    data=assess(1,source,NOW)
    assert data['coverage']['no_episode_reported']==1
    assert data['coverage']['unknown']==29
    assert data['labeled_outcomes']['positive']==data['labeled_outcomes']['negative']==0
    assert data['labeled_outcomes']['candidate_windows']==0
    assert data['labeled_outcomes']['unlabeled'] is None
    assert data['training_justified'] is data['evaluation_justified'] is False
