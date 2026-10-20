"""Descriptive, account-local summaries. No inferred negatives or forecasting."""
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

MIN_GROUP = 3  # UI display safeguard, not a clinically validated sample threshold.
FACTORS = {'sleep_hours':('Sleep duration','hours'), 'sleep_quality':('Sleep quality','/10'),
           'stress':('Stress','/10'), 'hydration_ml':('Hydration estimate','ml'),
           'screen_hours':('Screen exposure','hours'), 'missed_meals':('Missed meals','proportion')}

def instant(value):
    if not value:return None
    try:
        parsed=datetime.fromisoformat(value)
        return parsed.astimezone(timezone.utc) if parsed.tzinfo and parsed.utcoffset() is not None else None
    except (TypeError,ValueError):return None

def day_bounds(day,zone):
    return (datetime.combine(day,time.min,zone).astimezone(timezone.utc),
            datetime.combine(day+timedelta(days=1),time.min,zone).astimezone(timezone.utc))

def mean(values):return round(sum(values)/len(values),2) if values else None

def describe(episodes,wellness,early,timezone_name,days,now):
    zone=ZoneInfo(timezone_name); now=now.astimezone(timezone.utc)
    today=now.astimezone(zone).date(); first=today-timedelta(days=days-1)
    start=day_bounds(first,zone)[0]
    warnings=Counter(); attacks=[]; legacy=[]; events=[]
    for row in episodes:
        onset=instant(row.started_at);end=instant(row.ended_at)
        if row.started_at and not onset:warnings['invalid_episode_timestamps']+=1
        if onset:
            if onset>now:continue
            if row.ended_at and (not end or end<onset):
                warnings['invalid_episode_ends']+=1;end=None
            attacks.append((row,onset,end))
            if start<=onset<=now:
                events.append({'kind':'attack','id':row.id,'label':'Recorded migraine episode',
                    'at':onset.isoformat(),'ended_at':end.isoformat() if end and end<=now else None,
                    'relation':'Recorded onset','hours_before':None})
        else:
            try:day=date.fromisoformat(row.date)
            except (ValueError,TypeError):warnings['invalid_episode_dates']+=1;continue
            if day<=today+timedelta(days=1):legacy.append(day)
    recent=[a for a in attacks if start<=a[1]<=now]
    severity=[r.severity for r,_,_ in recent if r.severity is not None]
    durations=[(end-onset).total_seconds()/60 for _,onset,end in recent if end and end<=now]
    warnings['legacy_date_only_episodes']=sum(first<=day<=today for day in legacy)
    warnings['legacy_unresolved_history']=sum(day<first for day in legacy)
    warnings['missing_episode_ends']=sum(end is None or end>now for _,_,end in recent)
    warnings['missing_severity']=sum(r.severity is None for r,_,_ in recent)
    # Day summaries use the reporting zone. Daily aggregates from other zones are
    # not shifted to a new date unless both civil-day boundaries match exactly.
    daily={}
    for offset in range(days):
        day=first+timedelta(days=offset);left,right=day_bounds(day,zone)
        onsets=sum(left<=onset<right for _,onset,_ in attacks)
        overlap=any(onset<right and end is not None and end<=now and end>left for _,onset,end in attacks)
        unresolved=any(onset<right and (end is None or end>now) for _,onset,end in attacks)
        uncertain=any(abs((day-d).days)<=1 for d in legacy)
        daily[day.isoformat()]={'date':day.isoformat(),'episodes':onsets,
            'status':'episode_recorded' if onsets or overlap else 'unknown',
            'completed':right<=now,'legacy_uncertain':uncertain,'unresolved_overlap':unresolved,
            'legacy_unresolved':any(d<=day+timedelta(days=1) for d in legacy)}
    observed=[]; positive=[]; negative=[]
    for row in wellness:
        recorded=instant(row.recorded_at)
        try:
            own_zone=ZoneInfo(row.timezone_name);own_day=date.fromisoformat(row.date)
            left,right=day_bounds(own_day,own_zone)
        except (ValueError,TypeError,KeyError):warnings['invalid_wellness_dates']+=1;continue
        if right<=start or left>now:continue
        if not recorded or recorded>now:warnings['unavailable_wellness_timestamps']+=1;continue
        report_day=left.astimezone(zone).date()
        aligned=(left,right)==day_bounds(report_day,zone)
        status=getattr(row,'episode_observation',None)
        confirmation=instant(getattr(row,'observation_recorded_at',None))
        values={field:getattr(row,field,None) for field in FACTORS}
        observed.append({'id':row.id,'date':row.date,'timezone_name':row.timezone_name,
            'recorded_at':recorded.isoformat(),'exposure_at':None,'values':values,
            'episode_observation':status,'observation_recorded_at':confirmation.isoformat() if confirmation else None})
        if not aligned:warnings['unaligned_wellness_days']+=1;continue
        entry=daily.get(report_day.isoformat())
        if not entry:continue
        if not entry['completed']:warnings['incomplete_calendar_days']+=1;continue
        if entry['legacy_uncertain']:warnings['legacy_timing_exclusions']+=1;continue
        if entry['episodes']:
            if status=='no_episode':
                entry['status']='conflict';warnings['conflicting_observations']+=1
            else:positive.append(values)
        elif status=='no_episode':
            # Explicit, post-day confirmation plus no conflicting known/possibly
            # ongoing interval. An unknown end never becomes an invented recovery.
            if entry['legacy_unresolved']:
                warnings['legacy_timing_exclusions']+=1
            elif not confirmation or not right<=confirmation<=now:
                warnings['unconfirmed_observation_dates']+=1
            elif entry['unresolved_overlap']:
                warnings['unresolved_overlap_exclusions']+=1
            elif entry['status']=='episode_recorded':
                entry['status']='conflict';warnings['conflicting_observations']+=1
            else:
                entry['status']='no_episode_reported';negative.append(values)
        elif status=='episode' and entry['status']=='unknown':
            entry['status']='episode_reported_without_onset';warnings['reported_episode_without_onset']+=1
    factors=[]
    for field,(label,unit) in FACTORS.items():
        available=[r['values'][field] for r in observed if r['values'][field] is not None]
        yes=[r[field] for r in positive if r[field] is not None]
        no=[r[field] for r in negative if r[field] is not None]
        enough=len(yes)>=MIN_GROUP and len(no)>=MIN_GROUP
        factors.append({'key':field,'label':label,'unit':unit,'count':len(available),
            'missing_count':len(observed)-len(available),'mean':mean(available),
            'comparison_status':'available' if enough else 'insufficient_data',
            'episode_days':len(yes),'non_episode_days':len(no),
            'episode_mean':mean(yes) if enough else None,'non_episode_mean':mean(no) if enough else None})
    symptoms=Counter();preceding=0;uncertain_early=0
    for row in early:
        onset=instant(row.onset_at);recorded=instant(row.recorded_at)
        if not onset or not recorded:warnings['invalid_early_timestamps']+=1;continue
        if not start<=onset<=now or recorded>now:continue
        symptoms[row.symptom]+=1
        ongoing=[(a,s,e) for a,s,e in attacks if s<=onset and (e is None or e>onset)]
        later=[s for _,s,_ in attacks if onset<s<=onset+timedelta(hours=24)]
        hours=None
        if ongoing:
            relation='Overlap uncertain (episode end unknown)' if any(e is None for _,_,e in ongoing) else 'During a recorded episode'
            uncertain_early+=any(e is None for _,_,e in ongoing)
        elif any(d<=onset.astimezone(zone).date()+timedelta(days=1) for d in legacy):
            relation='Timing uncertain (date-only episode)';uncertain_early+=1
        elif later:
            hours=round((min(later)-onset).total_seconds()/3600,2);preceding+=1
            relation='Before a recorded onset within 24 hours; not a confirmed prodrome'
        else:relation='No recorded onset in the following 24 hours; observation coverage unknown'
        events.append({'kind':'early_symptom','id':row.id,'label':row.symptom,'at':onset.isoformat(),
            'ended_at':None,'relation':relation,'hours_before':hours})
    ordered=sorted(events,key=lambda r:(r['at'],r['kind'],r['id']))
    warnings['days_without_explicit_episode_status']=sum(r['status']=='unknown' for r in daily.values())
    status='descriptive_records' if len(recent)>=3 else 'insufficient_data'
    return {'version':'descriptive-v1','window_start':first.isoformat(),'window_end':today.isoformat(),
        'generated_at':now.isoformat(),'timezone_name':timezone_name,'days':days,'data_status':status,
        'summary':{'timed_episodes':len(recent),'average_severity':mean(severity),'severity_count':len(severity),
            'average_duration_minutes':mean(durations),'duration_count':len(durations),'wellness_checkins':len(observed),
            'early_observations':sum(symptoms.values()),'early_before_onset':preceding,
            'early_timing_uncertain':uncertain_early,
            'cycle_notes_checkins':sum(bool(r.menstrual_notes) for r in wellness if any(o['id']==r.id for o in observed))},
        'warnings':dict(warnings),'factors':factors,'daily':list(daily.values()),
        'symptoms':[{'symptom':name,'count':count} for name,count in sorted(symptoms.items(),key=lambda p:(-p[1],p[0]))[:8]],
        'timeline':ordered[-100:],'timeline_total':len(ordered),'daily_observations':sorted(observed,key=lambda r:(r['date'],r['id'])),
        'comparison_minimum_per_group':MIN_GROUP,
        'comparison_basis':'Completed days with a timed recorded onset versus explicitly confirmed whole days without an episode. Same-day daily aggregates: their timing relative to onset is unknown.',
        'limitations':['Recorded experiences only; missing entries are unknown, never episode-free days.',
            'Daily wellness values have dates, not exposure onset times. Recording time is not exposure time.',
            'Early symptoms are possible observations, not established prodromes or proven triggers.',
            'Comparisons are descriptive associations, not causes, risk estimates or clinical evidence.',
            'Three observations per group is a display safeguard, not a validated sufficiency threshold.',
            'Editable and retrospective records cannot reconstruct what was known before an attack. No forecasting model is used.']}
