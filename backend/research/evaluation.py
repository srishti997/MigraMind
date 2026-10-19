"""Dependency-light metrics with explicit denominators and undefined cases."""
import math

def evaluate(y,probabilities,threshold=.5):
    if len(y)!=len(probabilities):raise ValueError('Labels and predictions differ in length')
    if any(v not in [0,1] for v in y):raise ValueError('Binary labels required')
    if any(not math.isfinite(p) or not 0<=p<=1 for p in probabilities):raise ValueError('Probabilities must be finite and in [0,1]')
    if not math.isfinite(threshold) or threshold<0:raise ValueError('Invalid threshold')
    n=len(y);pos=sum(y);neg=n-pos
    tp=sum(label==1 and p>=threshold for label,p in zip(y,probabilities))
    fp=sum(label==0 and p>=threshold for label,p in zip(y,probabilities))
    alerts=tp+fp
    auc=pr_auc=ap=None
    if pos and neg:
        # ROC concordance with half credit for tied scores.
        ordered=sorted(zip(probabilities,y));lower_neg=0;concordant=0.;i=0
        while i<n:
            score=ordered[i][0];j=i
            while j<n and ordered[j][0]==score:j+=1
            group=ordered[i:j];gp=sum(label for _,label in group);gn=len(group)-gp
            concordant+=gp*(lower_neg+.5*gn);lower_neg+=gn;i=j
        auc=concordant/(pos*neg)
        # Group equal scores at one threshold. Report trapezoidal PR AUC AND AP explicitly.
        ordered=sorted(zip(probabilities,y),reverse=True);tp_curve=fp_curve=0
        recall_old=0.;precision_old=1.;pr_auc=ap=0.;i=0
        while i<n:
            score=ordered[i][0];j=i
            while j<n and ordered[j][0]==score:j+=1
            group=ordered[i:j];gp=sum(label for _,label in group)
            tp_curve+=gp;fp_curve+=len(group)-gp
            recall=tp_curve/pos;precision=tp_curve/(tp_curve+fp_curve)
            pr_auc+=(recall-recall_old)*(precision+precision_old)/2
            ap+=(recall-recall_old)*precision
            recall_old,precision_old=recall,precision;i=j
    calibration=[];ece=0.
    for i in range(5):
        indices=[j for j,p in enumerate(probabilities) if i/5<=p<(i+1)/5 or (i==4 and p==1)]
        if indices:
            prediction=sum(probabilities[j] for j in indices)/len(indices);observed=sum(y[j] for j in indices)/len(indices)
            ece+=len(indices)/max(1,n)*abs(prediction-observed)
            calibration.append({'lower':i/5,'upper':(i+1)/5,'n':len(indices),'mean_probability':prediction,'observed_frequency':observed})
    return {'n':n,'positives':pos,'negatives':neg,'threshold':threshold,
        'roc_auc':auc,'pr_auc_trapezoidal':pr_auc,'average_precision':ap,
        'ranking_metric_status':'available' if pos and neg else 'undefined_single_class_or_empty',
        'brier_score':sum((p-label)**2 for label,p in zip(y,probabilities))/n if n else None,
        'sensitivity':tp/pos if pos else None,'false_positive_rate':fp/neg if neg else None,
        'false_alerts_per_100_windows':100*fp/n if n else None,
        'false_discovery_rate':fp/alerts if alerts else None,'alert_rate':alerts/n if n else None,
        'true_positives':tp,'false_positives':fp,'calibration_bins':calibration,
        'expected_calibration_error':ece if n else None,
        'sample_status':'small_sample_descriptive_only' if n<20 or min(pos,neg)<5 else 'research_only_not_clinical_validation'}


def choose_threshold(y,probabilities,max_false_positive_rate=.1):
    if not y or len(set(y))<2:raise ValueError('Threshold selection needs both validation classes')
    # This validation-only engineering rule is not a clinical action threshold.
    candidates=[i/100 for i in range(5,100,5)]+[1.0,1.000001]
    eligible=[]
    for threshold in candidates:
        result=evaluate(y,probabilities,threshold)
        if result['false_positive_rate']<=max_false_positive_rate:
            eligible.append((result['sensitivity'],threshold))
    return max(eligible)[1]
