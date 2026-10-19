"""Point-in-time features and labels for fixed elapsed-24-hour decision windows."""
from dataclasses import dataclass
from datetime import datetime, timedelta, date
import math
from .contract import Bundle, Snapshot, aware, zone

PIPELINE_VERSION='migraine-onset-24h/v1'
HORIZON=timedelta(hours=24)
LABEL_LAG=timedelta(hours=24)
FEATURE_NAMES=('episode_onsets_7d','episode_onsets_30d','hours_since_observed_onset',
    'previous_sleep_hours','previous_sleep_quality','previous_stress','previous_hydration_ml',
    'previous_missed_meals','previous_screen_hours','wellness_age_days','stress_mean_7d',
    'wellness_observations_7d','early_symptom_observations_24h')

@dataclass(frozen=True)
class Example:
    prediction_at: datetime
    horizon_end: datetime
    label_available_at: datetime
    target: int
    features: dict[str,float|None]
    snapshot_at: datetime


def episodes(snapshot:Snapshot):
    result=[];legacy=[]
    for row in snapshot.episodes:
        if not row.get('started_at'):
            legacy.append(date.fromisoformat(row['date']));continue
        start=aware(row['started_at']);end=aware(row['ended_at']) if row.get('ended_at') else None
        if start>aware(snapshot.exported_at):continue
        if end and end>aware(snapshot.exported_at):end=None
        if end and end<start:raise ValueError('Invalid episode chronology')
        result.append((start,end))
    # Exact duplicate / overlapping episode intervals are one onset event.
    # Touching intervals remain distinct; unknown end means potentially still active.
    merged=[]
    for start,end in sorted(result,key=lambda pair:pair[0]):
        if merged and (merged[-1][1] is None or start<merged[-1][1] or start==merged[-1][0]):
            oldstart,oldend=merged[-1]
            merged[-1]=(oldstart,None if end is None or oldend is None else max(oldend,end))
        else:merged.append((start,end))
    return merged,legacy


def point_features(snapshot:Snapshot,t:datetime,timezone_name:str):
    t=aware(t);tz=zone(timezone_name)
    if aware(snapshot.exported_at)>=t:raise ValueError('Features require a snapshot strictly before prediction time')
    history,legacy=episodes(snapshot)
    # Never turn date-only entries into midnight onsets or assume an unknown end is recovery.
    if any(day<=t.astimezone(tz).date() for day in legacy):return None,'legacy_episode_time_unknown'
    if any(start<t and (end is None or end>t) for start,end in history):return None,'ongoing_or_unresolved_episode'
    past=[start for start,_ in history if start<t]
    features={key:None for key in FEATURE_NAMES}
    features['episode_onsets_7d']=float(sum(t-timedelta(days=7)<=s<t for s in past))
    features['episode_onsets_30d']=float(sum(t-timedelta(days=30)<=s<t for s in past))
    features['hours_since_observed_onset']=(t-max(past)).total_seconds()/3600 if past else None
    valid=[]
    for w in snapshot.wellness:
        day=date.fromisoformat(w['date'])
        # Original creation time alone cannot establish edit availability; snapshot is the upper bound.
        if not w.get('recorded_at') or aware(w['recorded_at'])>=t or aware(w['recorded_at'])>aware(snapshot.exported_at):continue
        if not w.get('timezone_name'):continue
        local_day=t.astimezone(zone(w['timezone_name'])).date()
        age=(local_day-day).days
        if 1<=age<=7:valid.append((day,w,age))
    valid.sort(key=lambda item:item[0])
    if valid:
        _,last,age=valid[-1]
        for source in ['sleep_hours','sleep_quality','stress','hydration_ml','missed_meals','screen_hours']:
            value=last.get(source)
            features['previous_'+source]=float(value) if value is not None else None
        features['wellness_age_days']=float(age)
    stresses=[float(w['stress']) for _,w,_ in valid if w.get('stress') is not None]
    features['stress_mean_7d']=sum(stresses)/len(stresses) if stresses else None
    features['wellness_observations_7d']=float(len(valid))
    early=0
    for row in snapshot.early_symptoms:
        if not row.get('recorded_at'):continue
        onset=aware(row['onset_at']);recorded=aware(row['recorded_at'])
        if t-HORIZON<=onset<t and recorded<t and max(onset,recorded)<=aware(snapshot.exported_at):early+=1
    features['early_symptom_observations_24h']=float(early)
    for value in features.values():
        if value is not None and not math.isfinite(value):raise ValueError('Feature values must be finite')
    return features,None


def covered(bundle:Bundle,start:datetime,end:datetime):
    intervals=sorted([c for c in bundle.coverage if c.complete and aware(c.start_at)<end and aware(c.end_at)>start],key=lambda c:c.start_at)
    cursor=start;confirmation=None
    for c in intervals:
        left,right=aware(c.start_at),aware(c.end_at)
        if left>cursor:break
        if right<=cursor:continue
        cursor=max(cursor,right);confirmation=max(confirmation or aware(c.confirmed_at),aware(c.confirmed_at))
        if cursor>=end:return confirmation
    return None


def build_dataset(bundle:Bundle,start:datetime,end:datetime,timezone_name='Asia/Kolkata'):
    start,end=aware(start),aware(end);tz=zone(timezone_name)
    if start>=end:raise ValueError('Prediction range must be increasing')
    rows=[];excluded={};t=start
    def skip(reason):excluded[reason]=excluded.get(reason,0)+1
    while t<end:
        # Fixed UTC cadence: each target is exactly 24 elapsed hours, including DST changes.
        known=[s for s in bundle.snapshots if aware(s.exported_at)<t]
        if not known:skip('no_point_in_time_snapshot');t+=HORIZON;continue
        features,reason=point_features(known[-1],t,timezone_name)
        if reason:skip(reason);t+=HORIZON;continue
        horizon=t+HORIZON;confirmation=covered(bundle,t,horizon)
        if confirmation is None:skip('unconfirmed_observation_window');t+=HORIZON;continue
        mature=max(horizon+LABEL_LAG,confirmation)
        label_snapshots=[s for s in bundle.snapshots if aware(s.exported_at)>=mature]
        if not label_snapshots:skip('label_not_mature');t+=HORIZON;continue
        label_snapshot=label_snapshots[0]
        onset_intervals,legacy=episodes(label_snapshot)
        if any(t.astimezone(tz).date()<=d<=(horizon-timedelta(microseconds=1)).astimezone(tz).date() for d in legacy):
            skip('target_onset_time_unknown');t+=HORIZON;continue
        # Retrospective outcome reconciliation may reveal an attack already underway at t.
        if any(s<t and (e is None or e>t) for s,e in onset_intervals):
            skip('retrospectively_ineligible_ongoing');t+=HORIZON;continue
        label=int(any(t<=s<horizon for s,_ in onset_intervals))
        rows.append(Example(t,horizon,aware(label_snapshot.exported_at),label,features,aware(known[-1].exported_at)))
        t+=HORIZON
    return rows,excluded


def chronological_split(rows,train_fraction=.6,validation_fraction=.2):
    if not 0<train_fraction<1 or not 0<validation_fraction<1 or train_fraction+validation_fraction>=1:
        raise ValueError('Invalid split fractions')
    ordered=sorted(rows,key=lambda r:r.prediction_at)
    if len({r.prediction_at for r in ordered})!=len(ordered):raise ValueError('Duplicate prediction times')
    if any(r.snapshot_at>=r.prediction_at or r.horizon_end!=r.prediction_at+HORIZON or r.label_available_at<r.horizon_end for r in ordered):
        raise ValueError('Invalid point-in-time example')
    a=int(len(ordered)*train_fraction);b=int(len(ordered)*(train_fraction+validation_fraction))
    train,validation,test=ordered[:a],ordered[a:b],ordered[b:]
    if validation:
        boundary=validation[0].prediction_at
        train=[r for r in train if r.horizon_end<boundary and r.label_available_at<boundary]
    if test:
        boundary=test[0].prediction_at
        validation=[r for r in validation if r.horizon_end<boundary and r.label_available_at<boundary]
    return {'train':train,'validation':validation,'test':test}
