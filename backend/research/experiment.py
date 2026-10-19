"""Reproducible offline comparison. Nothing here registers a deployed model."""
import importlib.metadata
import importlib.util
from .dataset import PIPELINE_VERSION, FEATURE_NAMES, build_dataset, chronological_split
from .models import eligibility, HistoricalFrequency, make_logistic, make_xgboost, matrix
from .evaluation import evaluate, choose_threshold


def run(bundle,start,end,timezone_name='Asia/Kolkata',train=False):
    rows,excluded=build_dataset(bundle,start,end,timezone_name)
    splits=chronological_split(rows)
    reasons=eligibility(bundle,rows,splits)
    report={'pipeline_version':PIPELINE_VERSION,'status':'insufficient_data' if reasons else 'prepared',
        'clinical_validation':False,'model_served':False,'eligible_windows':len(rows),'excluded_windows':excluded,
        'split_counts':{name:len(part) for name,part in splits.items()},'blocking_reasons':reasons,
        'feature_names':list(FEATURE_NAMES),'models':{},'threshold_rule':'Validation-only maximum sensitivity under FPR <= 0.10; never-alert tie preference.',
        'limitations':['Engineering sample gates are not clinical sufficiency.','No prospective or external validation.','Coverage and provenance require independent verification.','Calibration bins are descriptive, not a fitted calibration model.','Serial dependence and missing-not-at-random bias remain.']}
    if reasons or not train:return report,rows
    if importlib.util.find_spec('sklearn') is None:
        report['status']='dependencies_unavailable';return report,rows
    training,validation,test=splits['train'],splits['validation'],splits['test']
    y_validation=[r.target for r in validation];y_test=[r.target for r in test]
    baseline=HistoricalFrequency().fit(training)
    candidates={'historical_frequency':baseline,'logistic_regression':make_logistic()}
    xgb=make_xgboost()
    if xgb is not None:candidates['xgboost']=xgb
    else:report['models']['xgboost']={'status':'dependency_unavailable'}
    for name,model in candidates.items():
        if name=='historical_frequency':vp=model.predict(validation);tp=model.predict(test)
        else:
            # All imputation/scaling parameters fit ONLY on training observations.
            model.fit(matrix(training),[r.target for r in training])
            vp=model.predict_proba(matrix(validation))[:,1].tolist()
            tp=model.predict_proba(matrix(test))[:,1].tolist()
        threshold=choose_threshold(y_validation,vp)
        report['models'][name]={'status':'research_only','validation':evaluate(y_validation,vp,threshold),'test':evaluate(y_test,tp,threshold)}
    report['status']='research_complete_not_validated'
    report['package_versions']={name:importlib.metadata.version(name) for name in ['numpy','scikit-learn']}
    if xgb is not None:report['package_versions']['xgboost']=importlib.metadata.version('xgboost')
    return report,rows
