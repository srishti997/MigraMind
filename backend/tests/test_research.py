"""All fixtures in this file are synthetic and exist only for automated tests."""
from datetime import datetime, timedelta, timezone
import copy
import json
import math
import pytest
from research.contract import Bundle, Snapshot, Coverage, aware
from research.dataset import Example, FEATURE_NAMES, HORIZON, build_dataset, point_features, chronological_split
from research.evaluation import evaluate, choose_threshold
from research.models import eligibility, HistoricalFrequency
from research.experiment import run

def stamp(value):return aware(value)
def fixture_bundle():
    historical={'id':1,'date':'2026-01-01','started_at':'2026-01-01T08:00:00Z','ended_at':'2026-01-01T10:00:00Z'}
    wellness={'id':1,'date':'2026-01-02','timezone_name':'UTC','recorded_at':'2026-01-03T08:00:00Z','sleep_hours':7.,'stress':2,'missed_meals':False}
    early={'id':1,'onset_at':'2026-01-03T10:00:00Z','recorded_at':'2026-01-03T10:15:00Z'}
    before=Snapshot(exported_at='2026-01-03T11:00:00Z',episodes=[historical],wellness=[wellness],early_symptoms=[early])
    after=Snapshot(exported_at='2026-01-05T12:00:00Z',episodes=[historical,{'id':2,'date':'2026-01-03','started_at':'2026-01-03T15:00:00Z','ended_at':'2026-01-03T16:00:00Z'}])
    return Bundle(provenance={'source_kind':'synthetic'},snapshots=[before,after],coverage=[{'start_at':'2026-01-03T12:00:00Z','end_at':'2026-01-04T12:00:00Z','confirmed_at':'2026-01-04T14:00:00Z','complete':True}])

def test_point_in_time_features_and_positive_label():
    b=fixture_bundle();rows,excluded=build_dataset(b,stamp('2026-01-03T12:00Z'),stamp('2026-01-04T12:00Z'),'UTC')
    assert excluded=={} and len(rows)==1 and rows[0].target==1
    f=rows[0].features
    assert f['episode_onsets_7d']==1 and f['episode_onsets_30d']==1
    assert f['previous_sleep_hours']==7 and f['previous_stress']==2
    assert f['previous_missed_meals']==0 and f['previous_hydration_ml'] is None
    assert f['early_symptom_observations_24h']==1
    assert rows[0].snapshot_at<rows[0].prediction_at
    assert rows[0].label_available_at>=rows[0].horizon_end+HORIZON

def test_future_changes_and_final_outcomes_never_enter_features():
    b=fixture_bundle();t=stamp('2026-01-03T12:00Z')
    f,_=point_features(b.snapshots[0],t,'UTC')
    changed=b.model_copy(deep=True)
    changed.snapshots[-1].wellness=[{'id':3,'date':'2026-01-02','recorded_at':'2026-01-05T10:00Z','timezone_name':'UTC','stress':10}]
    changed.snapshots[-1].early_symptoms=[{'id':5,'onset_at':'2026-01-03T10:00Z','recorded_at':'2026-01-05T11:00Z'}]
    rows,_=build_dataset(changed,t,t+HORIZON,'UTC')
    assert rows[0].features==f
    with pytest.raises(ValueError):point_features(b.snapshots[-1],t,'UTC')

def test_late_logged_and_same_day_wellness_not_available():
    b=fixture_bundle();before=b.snapshots[0].model_copy(deep=True);t=stamp('2026-01-03T12:00Z')
    before.wellness[0]['recorded_at']='2026-01-04T12:00Z'
    f,_=point_features(before,t,'UTC');assert f['previous_sleep_hours'] is None
    before.wellness[0]['recorded_at']='2026-01-03T08:00Z';before.wellness[0]['date']='2026-01-03'
    f,_=point_features(before,t,'UTC');assert f['previous_stress'] is None
    before.early_symptoms[0]['recorded_at']='2026-01-05T12:00Z'
    f,_=point_features(before,t,'UTC');assert f['early_symptom_observations_24h']==0

def test_missing_diary_does_not_create_negative_labels():
    b=fixture_bundle();b.coverage=[]
    rows,reasons=build_dataset(b,stamp('2026-01-03T12:00Z'),stamp('2026-01-04T12:00Z'),'UTC')
    assert rows==[] and reasons=={'unconfirmed_observation_window':1}
    b=fixture_bundle();b.snapshots[-1].episodes=b.snapshots[0].episodes.copy()
    rows,_=build_dataset(b,stamp('2026-01-03T12:00Z'),stamp('2026-01-04T12:00Z'),'UTC')
    assert rows[0].target==0 # Explicit coverage, not absent logs, establishes this observed negative.

def test_incomplete_legacy_ongoing_and_unmatured_windows_excluded():
    t=stamp('2026-01-03T12:00Z')
    b=fixture_bundle();b.snapshots[0].episodes[0]['ended_at']=None
    assert build_dataset(b,t,t+HORIZON,'UTC')[1]=={'ongoing_or_unresolved_episode':1}
    b=fixture_bundle();b.snapshots[0].episodes[0]['started_at']=None
    assert build_dataset(b,t,t+HORIZON,'UTC')[1]=={'legacy_episode_time_unknown':1}
    b=fixture_bundle();b.snapshots=b.snapshots[:1]
    assert build_dataset(b,t,t+HORIZON,'UTC')[1]=={'label_not_mature':1}
    b=fixture_bundle();b.coverage[0].complete=False
    assert build_dataset(b,t,t+HORIZON,'UTC')[1]=={'unconfirmed_observation_window':1}

def test_overlap_dedup_and_half_open_target_boundary():
    b=fixture_bundle();t=stamp('2026-01-03T12:00Z')
    b.snapshots[0].episodes.append({'id':2,'date':'2026-01-01','started_at':'2026-01-01T09:00Z','ended_at':'2026-01-01T11:00Z'})
    f,_=point_features(b.snapshots[0],t,'UTC');assert f['episode_onsets_7d']==1
    b.snapshots[-1].episodes[-1]['started_at']='2026-01-04T12:00Z';b.snapshots[-1].episodes[-1]['ended_at']='2026-01-04T13:00Z'
    assert build_dataset(b,t,t+HORIZON,'UTC')[0][0].target==0
    b.snapshots[-1].episodes[-1]['started_at']='2026-01-03T12:00Z'
    assert build_dataset(b,t,t+HORIZON,'UTC')[0][0].target==1

def test_offset_equivalence_and_dst_elapsed_horizon():
    assert stamp('2026-01-03T17:30:00+05:30')==stamp('2026-01-03T12:00:00Z')
    start=stamp('2026-03-08T00:00:00-05:00')
    assert (start+HORIZON-start).total_seconds()==86400
    with pytest.raises(ValueError):stamp('2026-01-03T12:00')
    with pytest.raises(ValueError):Bundle(snapshots=[{'exported_at':'2026-01-03T12:00'}])
    with pytest.raises(ValueError):Coverage(start_at='2026-01-03T12:00Z',end_at='2026-01-04T12:00Z',confirmed_at='2026-01-03T12:00Z',complete=True)

def fake_rows(n=210):
    start=stamp('2025-01-01T12:00Z')
    return [Example(start+i*HORIZON,start+(i+1)*HORIZON,start+(i+2)*HORIZON,int(i%4==0),
        {k:float(i%8) if k=='previous_stress' else None for k in FEATURE_NAMES},start+i*HORIZON-timedelta(minutes=1)) for i in range(n)]

def test_chronological_splits_purge_horizons_and_label_availability():
    rows=fake_rows();parts=chronological_split(list(reversed(rows)),grid_start=rows[0].prediction_at,grid_end=rows[-1].horizon_end)
    train,val,test=parts['train'],parts['validation'],parts['test']
    assert train and val and test
    assert max(r.label_available_at for r in train)<min(r.prediction_at for r in val)
    assert max(r.horizon_end for r in val)<min(r.prediction_at for r in test)
    assert max(r.label_available_at for r in val)<min(r.prediction_at for r in test)
    with pytest.raises(ValueError):chronological_split(rows+[rows[0]],grid_start=rows[0].prediction_at,grid_end=rows[-1].horizon_end)

def test_synthetic_provenance_and_insufficient_data_block_training():
    b=fixture_bundle();t=stamp('2026-01-03T12:00Z')
    report,_=run(b,t,t+HORIZON,'UTC',train=True)
    assert report['status']=='insufficient_data' and report['models']=={}
    assert 'real_longitudinal_provenance_required' in report['blocking_reasons']
    rows=fake_rows();reasons=eligibility(b,rows,chronological_split(rows,grid_start=rows[0].prediction_at,grid_end=rows[-1].horizon_end))
    assert 'real_longitudinal_provenance_required' in reasons # Even a large synthetic fixture cannot pass.

def test_historical_frequency_uses_training_labels_only():
    rows=fake_rows(12);model=HistoricalFrequency().fit(rows[:8]);expected=sum(r.target for r in rows[:8])/8
    assert model.predict(rows[8:])==[expected]*4

def test_metrics_and_single_class_denominators():
    result=evaluate([0,0,1,1],[.1,.2,.8,.9])
    assert result['roc_auc']==1 and result['pr_auc_trapezoidal']==1 and result['average_precision']==1
    assert result['sensitivity']==1 and result['false_positive_rate']==0
    assert result['brier_score']==pytest.approx(.025)
    for labels in [[],[0,0],[1,1]]:
        r=evaluate(labels,[.2]*len(labels));assert r['roc_auc'] is None and r['pr_auc_trapezoidal'] is None
        assert r['sample_status']=='small_sample_descriptive_only'
    assert evaluate([0,0],[.1,.1])['sensitivity'] is None
    assert evaluate([1,1],[.9,.9])['false_positive_rate'] is None
    assert evaluate([0,0],[.1,.1])['false_discovery_rate'] is None
    assert evaluate([],[])['brier_score'] is None
    with pytest.raises(ValueError):evaluate([1],[math.nan])

def test_metric_ties_and_threshold_selection_only_validation():
    result=evaluate([0,1,0,1],[.5]*4)
    assert result['roc_auc']==.5 and result['average_precision']==.5
    threshold=choose_threshold([0,0,1,1],[.1,.3,.8,.9])
    assert evaluate([0,0,1,1],[.1,.3,.8,.9],threshold)['false_positive_rate']==0
    with pytest.raises(ValueError):choose_threshold([0,0],[.1,.2])

def test_logistic_imputation_and_scaling_fit_only_training():
    pytest.importorskip('sklearn');pytest.importorskip('numpy')
    from research.models import make_logistic, matrix
    rows=fake_rows(20);model=make_logistic()
    model.fit(matrix(rows[:12]),[r.target for r in rows[:12]])
    mean=model.named_steps['scale'].mean_.copy()
    model.predict_proba(matrix(rows[12:]))
    assert (model.named_steps['scale'].mean_==mean).all()
    assert model.named_steps['impute'].n_features_in_==2*len(FEATURE_NAMES)

def test_optional_xgboost_has_explicit_unavailable_path():
    import importlib.util
    from research.models import make_xgboost
    if importlib.util.find_spec('xgboost') is None:assert make_xgboost() is None
    else:assert make_xgboost() is not None

def test_cli_invalid_input_does_not_print_health_records(tmp_path,capsys):
    from research.cli import main
    path=tmp_path/'invalid.json';path.write_text(json.dumps({'private_notes':'SENSITIVE FIXTURE ONLY'}))
    assert main(['--input',str(path),'--start','2026-01-01T00:00Z','--end','2026-01-02T00:00Z'])==2
    captured=capsys.readouterr();assert 'SENSITIVE' not in captured.err+captured.out

def test_missing_episode_collection_is_not_an_observed_negative():
    with pytest.raises(ValueError):Snapshot(exported_at='2026-01-03T11:00Z')

def test_values_recorded_after_snapshot_cannot_be_backdated_features():
    b=fixture_bundle();s=b.snapshots[0].model_copy(deep=True)
    s.wellness[0]['recorded_at']='2026-01-03T11:30Z'
    s.early_symptoms[0]['recorded_at']='2026-01-03T11:30Z'
    f,_=point_features(s,stamp('2026-01-03T12:00Z'),'UTC')
    assert f['previous_stress'] is None and f['early_symptom_observations_24h']==0

def test_metric_implementation_matches_reference_library():
    pytest.importorskip('sklearn')
    from sklearn.metrics import roc_auc_score,average_precision_score,precision_recall_curve,auc,brier_score_loss
    y=[0,1,0,1,1,0];p=[.2,.2,.6,.8,.6,.3]
    r=evaluate(y,p);precision,recall,_=precision_recall_curve(y,p)
    assert r['roc_auc']==pytest.approx(roc_auc_score(y,p))
    assert r['average_precision']==pytest.approx(average_precision_score(y,p))
    assert r['pr_auc_trapezoidal']==pytest.approx(auc(recall,precision))
    assert r['brier_score']==pytest.approx(brier_score_loss(y,p))

def test_full_offline_experiment_only_with_simulated_verified_contract_in_test():
    """Synthetic fixture simulates a reviewed contract; output is never a research finding."""
    pytest.importorskip('sklearn')
    start=stamp('2025-01-01T12:00Z');snapshots=[];coverage=[]
    for i in range(215):
        when=start+i*HORIZON-timedelta(hours=1)
        events=[{'id':j+1,'date':(start+j*HORIZON).date().isoformat(),
                 'started_at':(start+j*HORIZON+timedelta(hours=2)).isoformat(),
                 'ended_at':(start+j*HORIZON+timedelta(hours=3)).isoformat()}
                for j in range(i) if j%4==0]
        snapshots.append({'exported_at':when,'episodes':events})
    for i in range(210):
        t=start+i*HORIZON
        coverage.append({'start_at':t,'end_at':t+HORIZON,'confirmed_at':t+HORIZON+timedelta(hours=1),'complete':True})
    b=Bundle(provenance={'source_kind':'real_longitudinal','participant_key':'SYNTHETIC_TEST_ONLY',
        'source_description':'Simulated verification only inside automated test; not real research data',
        'consent_confirmed':True,'point_in_time_verified':True},snapshots=snapshots,coverage=coverage)
    report,rows=run(b,start,start+210*HORIZON,'UTC',train=True)
    assert report['status']=='research_complete_not_validated'
    assert report['clinical_validation'] is False and report['model_served'] is False
    for model in ['historical_frequency','logistic_regression']:
        assert report['models'][model]['test']['n']>20
        assert report['models'][model]['test']['brier_score'] is not None
    assert len(rows)==210
