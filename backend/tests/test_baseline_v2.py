"""Synthetic software fixtures only. Never open the application's health database."""
import copy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import pytest
from research.contract import aware
from research.dataset import HORIZON
from research.revision_contract import RevisionBundle
from research.revision_dataset import build_revision_dataset, features_at, split_account
from research.baseline_v2 import run_baselines, matrix
from research.baseline_cli import main

T = aware('2025-01-03T00:00:00Z')


def stamp(value): return value.isoformat()


def daily(day, *, id='d1', stress=0):
    event = day+timedelta(hours=12)
    recorded = day+timedelta(hours=23)
    return {'account_key':'synthetic-a','record_id':id,'revision':1,'action':'creation',
        'recorded_at':stamp(recorded), 'values':{'date':day.date().isoformat(),
            'timezone_name':'UTC','status':'unknown','event_at':stamp(event),'observed_at':stamp(event),
            'status_recorded_at':stamp(recorded),'stress':stress}}


def outcome(start, end, *, kind='no_episode_interval', id='o1'):
    recorded = end+timedelta(hours=1)
    return {'account_key':'synthetic-a','record_id':id,'revision':1,'action':'creation',
        'recorded_at':stamp(recorded),'values':{'kind':kind,'start_at':stamp(start),
            'end_at':stamp(end),'verified':True,'independently_verified':True,'verification_reference':'synthetic-independent-evidence',
            'complete':kind in ('no_episode_interval','observation_interval')}}


def fixture():
    return {'research_schema_version':2,'account_key':'synthetic-a','captured_at':stamp(T+3*HORIZON),
        'provenance':{'source_kind':'synthetic','source_reference':'generated-in-test-only',
            'provenance_verified':True,'outcome_history_complete':True},
        'daily_revisions':[daily(T-HORIZON)],'outcome_revisions':[outcome(T,T+HORIZON)]}


def bundle(data=None): return RevisionBundle.model_validate(data or fixture())


def correction(row, when, **changes):
    updated = copy.deepcopy(row)
    updated.update(revision=row['revision']+1,action='correction',recorded_at=stamp(when))
    updated['values'].update(changes)
    if 'status_recorded_at' in updated['values']: updated['values']['status_recorded_at']=stamp(when)
    return updated


def deletion(row, when):
    return {**row,'revision':row['revision']+1,'action':'deletion','recorded_at':stamp(when),'values':None}


def test_completed_negative_missing_fields_and_explicit_zero():
    rows,excluded=build_revision_dataset(bundle(),T,T+HORIZON)
    assert excluded=={} and len(rows)==1 and rows[0].target==0
    assert rows[0].features['stress']==0 and rows[0].features['sleep_hours'] is None
    assert rows[0].features['migraine_reports_7d']==0
    assert rows[0].snapshot_at<T and rows[0].horizon_end-T==HORIZON
    assert rows[0].label_available_at==T+2*HORIZON


def test_verified_onset_positive_without_guessing_negative_coverage():
    data=fixture();data['outcome_revisions']=[outcome(T+timedelta(hours=3),T+timedelta(hours=5),kind='onset')]
    rows,excluded=build_revision_dataset(bundle(data),T,T+HORIZON)
    assert rows==[] and excluded=={'no_complete_observation_coverage':1}
    data['outcome_revisions'].append(outcome(T,T+HORIZON,kind='observation_interval',id='coverage'))
    rows,excluded=build_revision_dataset(bundle(data),T,T+HORIZON)
    assert excluded=={} and rows[0].target==1
    assert rows[0].features['verified_onsets_7d']==0 # outcome never enters its own features


def test_daily_migraine_event_time_is_not_a_verified_onset():
    data=fixture();data['daily_revisions'][0]['values']['status']='migraine';data['outcome_revisions']=[]
    rows,excluded=build_revision_dataset(bundle(data),T,T+HORIZON)
    assert rows==[] and excluded=={'no_complete_no_episode_coverage':1}


@pytest.mark.parametrize('mutation,reason',[
    ('missing','no_complete_no_episode_coverage'),('gap','no_complete_no_episode_coverage'),
    ('unverified','unverified_outcome'),('incomplete','incomplete_outcome_coverage'),
    ('unknown','unknown_outcome_interval'),('history','outcome_history_unverified'),
    ('immature','outcome_not_mature'),('deleted','deleted_outcome')])
def test_missing_unknown_unverified_deleted_and_late_labels_are_excluded(mutation,reason):
    data=fixture();row=data['outcome_revisions'][0]
    if mutation=='missing': data['outcome_revisions']=[]
    if mutation=='gap': row['values']['end_at']=stamp(T+HORIZON-timedelta(seconds=1))
    if mutation=='unverified': row['values']['verified']=False
    if mutation=='incomplete': row['values']['complete']=False
    if mutation=='unknown': row['values']['kind']='unknown_interval'
    if mutation=='history': data['provenance']['outcome_history_complete']=False
    if mutation=='immature': data['captured_at']=stamp(T+HORIZON+timedelta(hours=2))
    if mutation=='deleted': data['outcome_revisions'].append(deletion(row,T+timedelta(hours=47)))
    rows,excluded=build_revision_dataset(bundle(data),T,T+HORIZON)
    assert rows==[] and excluded=={reason:1}


def test_interval_union_requires_no_gaps_and_conflicts_do_not_become_negatives():
    data=fixture();mid=T+timedelta(hours=10)
    data['outcome_revisions']=[outcome(T,mid,id='a'),outcome(mid,T+HORIZON,id='b')]
    assert build_revision_dataset(bundle(data),T,T+HORIZON)[0][0].target==0
    data['outcome_revisions'].append(outcome(T+timedelta(hours=2),T+timedelta(hours=3),kind='onset',id='c'))
    assert build_revision_dataset(bundle(data),T,T+HORIZON)[1]=={'conflicting_outcome_evidence':1}


def test_cutoff_revisions_corrections_and_tombstones_do_not_leak_backwards():
    data=fixture();original=data['daily_revisions'][0]
    before=features_at(bundle(data),T)[0]
    data['daily_revisions'].append(correction(original,T,stress=10))
    assert features_at(bundle(data),T)[0]==before # equality at cutoff is unavailable
    assert features_at(bundle(data),T+timedelta(seconds=1))[0]['stress']==10
    data['daily_revisions'].append(deletion(data['daily_revisions'][-1],T+timedelta(hours=1)))
    assert features_at(bundle(data),T)[0]==before
    assert features_at(bundle(data),T+timedelta(hours=2))[2]=='no_historical_observations'


def test_backdating_cannot_backdate_feature_availability():
    data=fixture();data['daily_revisions'][0]['recorded_at']=stamp(T+timedelta(hours=1))
    data['daily_revisions'][0]['values']['status_recorded_at']=stamp(T+timedelta(hours=1))
    assert features_at(bundle(data),T)[2]=='no_historical_observations'


def test_revised_onset_and_withdrawal_never_silently_create_negative():
    data=fixture();onset=outcome(T+timedelta(hours=3),T+timedelta(hours=4),kind='onset',id='onset')
    data['outcome_revisions'].append(onset)
    shifted=correction(onset,T+timedelta(hours=30),start_at=stamp(T-HORIZON),end_at=stamp(T-HORIZON+timedelta(hours=1)))
    data['outcome_revisions'].append(shifted)
    assert build_revision_dataset(bundle(data),T,T+HORIZON)[1]=={'retracted_or_moved_outcome':1}
    data['outcome_revisions']=[onset,deletion(onset,T+timedelta(hours=47))]
    assert build_revision_dataset(bundle(data),T,T+HORIZON)[1]=={'deleted_outcome':1}


def test_positive_boundaries_and_retrospective_ongoing_attacks():
    data=fixture();data['outcome_revisions']=[outcome(T,T+timedelta(hours=1),kind='onset')]
    data['outcome_revisions'].append(outcome(T,T+HORIZON,kind='observation_interval',id='coverage'))
    assert build_revision_dataset(bundle(data),T,T+HORIZON)[0][0].target==1
    data['outcome_revisions']=[outcome(T+HORIZON,T+HORIZON+timedelta(hours=1),kind='onset')]
    assert build_revision_dataset(bundle(data),T,T+HORIZON)[0]==[] # end is exclusive
    data['outcome_revisions']=[outcome(T-timedelta(hours=1),T+timedelta(hours=1),kind='onset')]
    assert build_revision_dataset(bundle(data),T,T+HORIZON)[1]=={'retrospectively_ongoing_episode':1}


@pytest.mark.parametrize('mutation',['account','missing_revision','duplicate','date','future','naive','resurrect','invalid_status'])
def test_rejects_mixed_accounts_broken_journals_and_invalid_times(mutation):
    data=fixture();row=data['daily_revisions'][0]
    if mutation=='account': row['account_key']='synthetic-b'
    if mutation=='missing_revision': row['revision']=2
    if mutation=='duplicate': data['daily_revisions'].append(copy.deepcopy(row))
    if mutation=='date': row['values']['date']='2020-01-01'
    if mutation=='future': data['captured_at']=stamp(T-2*HORIZON)
    if mutation=='naive': row['recorded_at']='2025-01-02T23:00:00'
    if mutation=='resurrect':
        removed=deletion(row,T)
        revived=correction(row,T+HORIZON);revived['revision']=3
        data['daily_revisions'] += [removed,revived]
    if mutation=='invalid_status': row['values']['status']='missing'
    with pytest.raises(ValueError):bundle(data)


def test_dst_source_completion_and_exact_elapsed_horizon():
    cutoff=aware('2025-11-03T04:30:00Z') # source Nov 2 has not ended in NY (25-hour day)
    data=fixture();data['captured_at']=stamp(cutoff+3*HORIZON)
    row=data['daily_revisions'][0]
    row.update(recorded_at='2025-11-02T23:00:00Z')
    row['values'].update(date='2025-11-02',timezone_name='America/New_York',
        event_at='2025-11-02T01:30:00-04:00',observed_at='2025-11-02T01:30:00-05:00',status_recorded_at=row['recorded_at'])
    assert features_at(bundle(data),cutoff)[0]['stress'] is None
    assert features_at(bundle(data),aware('2025-11-03T05:00:00Z'))[0]['stress']==0
    data['outcome_revisions']=[outcome(cutoff,cutoff+HORIZON)]
    rows,_=build_revision_dataset(bundle(data),cutoff,cutoff+HORIZON)
    assert rows[0].horizon_end-rows[0].prediction_at==timedelta(seconds=86400)


def long_fixture(n=240, single_class=False):
    from research.synthetic_fixture import make_synthetic
    start=aware('2024-01-01T00:00:00Z')
    return make_synthetic(n,all_negative=single_class),start,start+n*HORIZON


def test_split_purges_horizon_label_availability_and_rejects_pooling_or_overlap():
    b,start,end=long_fixture();rows,_=build_revision_dataset(b,start,end);parts=split_account(rows,grid_start=start,grid_end=end)
    for left,right in [('train','validation'),('validation','test')]:
        boundary=parts[right][0].prediction_at
        assert all(r.horizon_end<boundary and r.label_available_at<boundary for r in parts[left])
    with pytest.raises(ValueError):split_account(rows+[replace(rows[-1],account_key='synthetic-b')],grid_start=start,grid_end=end)
    with pytest.raises(ValueError):split_account([rows[0],replace(rows[1],prediction_at=rows[0].prediction_at+timedelta(hours=1))],grid_start=start,grid_end=end)


def test_synthetic_fitting_is_opt_in_and_single_class_stops_without_metrics():
    b,start,end=long_fixture()
    report,_=run_baselines(b,start,end,train=True)
    assert not report['trained'] and report['models']=={}
    assert 'synthetic_fit_requires_explicit_opt_in' in report['blocking_reasons']
    b,start,end=long_fixture(single_class=True)
    report,_=run_baselines(b,start,end,train=True,allow_synthetic=True)
    assert 'single_class_or_empty_dataset' in report['blocking_reasons']
    assert report['models']=={} and report['samples']['positive_fraction']==0


def test_consented_source_without_review_or_consent_does_not_build_or_train():
    data=fixture();data['provenance'].update(source_kind='consented',provenance_verified=False)
    report,rows=run_baselines(bundle(data),T,T+HORIZON,train=True)
    assert rows==[] and not report['trained']
    assert report['excluded_windows']=={'consent_or_provenance_unverified':1}


def test_reproducible_synthetic_software_fit_and_naive_baseline_metrics():
    pytest.importorskip('sklearn');pytest.importorskip('numpy')
    b,start,end=long_fixture()
    first,rows=run_baselines(b,start,end,train=True,allow_synthetic=True)
    second,_=run_baselines(b,start,end,train=True,allow_synthetic=True)
    assert first==second and first['trained'] and not first['model_served']
    assert first['status']=='synthetic_software_test_complete'
    assert first['evidence_scope']=='synthetic_software_test_only'
    assert first['samples']=={'n':240,'positive':60,'negative':180,'positive_fraction':.25}
    assert first['purged_windows']>0
    for model in first['models'].values():
        for split,result in model.items():
            assert result['n']==first['splits'][split]['n']
            assert result['brier_score'] is not None and result['average_precision'] is not None
            assert sum(v['n'] for v in result['calibration_bins'])==result['n']
    baseline=first['models']['historical_frequency']['test']
    assert baseline['roc_auc']==.5
    # Holdout-only changes cannot alter training preprocessing.
    from research.models import make_logistic
    parts=split_account(rows,grid_start=start,grid_end=end);model=make_logistic().fit(matrix(parts['train']),[r.target for r in parts['train']])
    mean=model.named_steps['scale'].mean_.copy()
    heldout=[replace(r,features={**r.features,'stress':10.}) for r in parts['test']]
    model.predict_proba(matrix(heldout))
    assert (mean==model.named_steps['scale'].mean_).all()


def test_cli_reports_no_private_values_and_has_reproducible_hashes(tmp_path,capsys):
    source=tmp_path/'bundle.json';out=tmp_path/'private-report'
    source.write_text(json.dumps(fixture()),encoding='utf-8')
    args=['--input',str(source),'--start',stamp(T),'--end',stamp(T+HORIZON),'--output-dir',str(out)]
    assert main(args)==0
    first=(out/'report.json').read_bytes();assert main(args)==0
    assert first==(out/'report.json').read_bytes()
    assert not (out/'dataset.json').exists()
    assert 'stress' not in capsys.readouterr().out
    source.write_text('{"private":"Synthetic private sentinel"}',encoding='utf-8')
    assert main(args)==2
    assert 'Synthetic private sentinel' not in capsys.readouterr().err


def test_empty_single_class_metrics_are_null_and_wrong_export_schema_is_rejected():
    from research.evaluation import evaluate
    for labels in ([],[0,0],[1,1]):
        result=evaluate(labels,[.25]*len(labels))
        assert result['pr_auc_trapezoidal'] is None and result['average_precision'] is None
        assert (result['brier_score'] is None)==(not labels)
    with pytest.raises(ValueError):RevisionBundle.model_validate({'schema_version':5,'episodes':[]})


def test_input_order_does_not_change_current_versions_or_dataset_hash():
    data=fixture();change=correction(data['daily_revisions'][0],T-timedelta(minutes=1),stress=3)
    data['daily_revisions'].append(change)
    original,rows=run_baselines(bundle(data),T,T+HORIZON)
    data['daily_revisions'].reverse()
    reordered,other=run_baselines(bundle(data),T,T+HORIZON)
    assert original==reordered and rows==other and rows[0].features['stress']==3


def test_synthetic_generator_is_explicit_deterministic_and_refuses_overwrite(tmp_path,capsys):
    from research.synthetic_fixture import main as generate
    left,right=tmp_path/'one.json',tmp_path/'two.json'
    generate(['--output',str(left)]);generate(['--output',str(right)])
    assert left.read_bytes()==right.read_bytes()
    assert bundle(json.loads(left.read_text())).provenance.source_kind=='synthetic'
    with pytest.raises(FileExistsError):generate(['--output',str(left)])
    assert 'no real-world evidence' in capsys.readouterr().out


def test_adapter_refuses_unconsented_real_source_before_querying_any_records():
    from research.sprint9_adapter import project_account
    class Unreadable:
        def get(self,*args):raise AssertionError('No records should be queried')
    source={**fixture()['provenance'],'source_kind':'consented'}
    with pytest.raises(ValueError,match='consent'):
        project_account(Unreadable(),1,'a',source,T)


@pytest.mark.parametrize('lag',[-1,169,1.5,True])
def test_invalid_reporting_lags_are_rejected(lag):
    with pytest.raises(ValueError):build_revision_dataset(bundle(),T,T+HORIZON,lag)


def test_sprint9_projection_is_read_only_isolated_and_cannot_manufacture_labels(clients):
    from test_auth import register
    from research.sprint9_adapter import project_account
    from app.main import CheckinRevision
    a,b,factory=clients;owner=register(a);register(b,'sprint10-b@example.test')
    from test_prospective import report
    a.post('/api/daily-checkins',json=report(stress=0,routine_changes='Synthetic private text A'))
    b.post('/api/daily-checkins',json=report(stress=9,early_symptoms='Synthetic private text B'))
    with factory() as session:
        count=session.query(CheckinRevision).count()
        projected=project_account(session,owner['id'],'synthetic-a',fixture()['provenance'],datetime.now(timezone.utc))
        assert session.query(CheckinRevision).count()==count
    assert len(projected.daily_revisions)==1 and projected.daily_revisions[0].values.stress==0
    assert projected.outcome_revisions==[] and not projected.provenance.outcome_history_complete
    assert 'Synthetic private text' not in projected.model_dump_json()


# Reuse the existing isolated, synthetic auth fixture; never the configured application DB.
from test_auth import clients


@pytest.mark.parametrize('kind',['onset','no_episode_interval'])
@pytest.mark.parametrize('field,value',[('verification_reference',None),('independently_verified',False)])
def test_independent_evidence_is_required_for_both_classes(kind,field,value):
    data=fixture()
    if kind=='onset':
        data['outcome_revisions']=[outcome(T,T+timedelta(hours=1),kind=kind),
            outcome(T,T+HORIZON,kind='observation_interval',id='coverage')]
    data['outcome_revisions'][0]['values'][field]=value
    assert build_revision_dataset(bundle(data),T,T+HORIZON)==([] ,{'unverified_outcome':1})


def test_observation_coverage_alone_cannot_prove_a_negative():
    data=fixture();data['outcome_revisions'][0]['values']['kind']='observation_interval'
    assert build_revision_dataset(bundle(data),T,T+HORIZON)==([] ,{'no_complete_no_episode_coverage':1})


def test_august_18_correction_preserves_frozen_earlier_training_windows():
    b,start,end=long_fixture()
    original,_=build_revision_dataset(b,start,end)
    data=b.model_dump(mode='json');first=next(r for r in data['outcome_revisions'] if r['record_id']=='o0')
    august18=aware('2024-08-18T00:00:00Z')
    data['outcome_revisions'].append(correction(first,august18))
    changed=RevisionBundle.model_validate(data)
    after,_=build_revision_dataset(changed,start,end)
    before_train=split_account(original,grid_start=start,grid_end=end)['train'];after_train=split_account(after,grid_start=start,grid_end=end)['train']
    assert len(before_train)==len(after_train)==142 and before_train==after_train
    assert all(r.eligibility_as_of==r.outcome_as_of==r.label_available_at for r in after)
    snapshot=aware('2024-08-17T00:00:00Z')
    left,_=run_baselines(b,start,end,dataset_as_of=snapshot)
    right,_=run_baselines(changed,start,end,dataset_as_of=snapshot)
    assert left==right
    # A later deletion also cannot alter a previously frozen decision.
    data['outcome_revisions'][-1]=deletion(first,august18)
    assert build_revision_dataset(RevisionBundle.model_validate(data),start,end)[0]==original


def test_snapshot_must_exist_and_cannot_label_unmatured_windows():
    with pytest.raises(ValueError):build_revision_dataset(bundle(),T,T+HORIZON,dataset_as_of=T+4*HORIZON)
    assert build_revision_dataset(bundle(),T,T+HORIZON,dataset_as_of=T+HORIZON)[1]=={'outcome_not_mature':1}


def test_future_holdout_exclusion_cannot_move_training_split_boundaries():
    b,start,end=long_fixture()
    original,_=run_baselines(b,start,end)
    data=b.model_dump(mode='json')
    last=next(r for r in data['outcome_revisions'] if r['record_id']=='o239')
    when=aware(last['recorded_at'])+timedelta(hours=1)
    data['outcome_revisions'].append(deletion(last,when))
    changed,_=run_baselines(RevisionBundle.model_validate(data),start,end)
    assert original['splits']['train']==changed['splits']['train']
    assert original['splits']['validation']==changed['splits']['validation']
    assert changed['splits']['test']['n']==original['splits']['test']['n']-1


@pytest.mark.parametrize('mutation',['gap','incomplete','unknown','unverified'])
def test_positive_requires_reliable_complete_observation_horizon(mutation):
    data=fixture()
    coverage=outcome(T,T+HORIZON,kind='observation_interval',id='coverage')
    data['outcome_revisions']=[outcome(T,T+timedelta(hours=1),kind='onset'),coverage]
    if mutation=='gap':coverage['values']['end_at']=stamp(T+HORIZON-timedelta(seconds=1))
    if mutation=='incomplete':coverage['values']['complete']=False
    if mutation=='unknown':coverage['values']['kind']='unknown_interval'
    if mutation=='unverified':coverage['values']['independently_verified']=False
    rows,excluded=build_revision_dataset(bundle(data),T,T+HORIZON)
    assert rows==[] and sum(excluded.values())==1
