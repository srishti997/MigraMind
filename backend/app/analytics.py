from datetime import datetime, date, timedelta, timezone, time
from zoneinfo import ZoneInfo

def summarize(episodes, wellness, as_of: date, timezone_name: str):
    zone=ZoneInfo(timezone_name); first=as_of-timedelta(days=29)
    days={}; recent=[]; headache=set()
    for row in episodes:
        start=datetime.fromisoformat(row.started_at).astimezone(zone) if row.started_at else None
        onset=start.date() if start else date.fromisoformat(row.date)
        if first<=onset<=as_of:
            recent.append(row); days[onset.isoformat()]=days.get(onset.isoformat(),0)+1
        # A zero severity entry is not a reported headache day. Unknown remains unknown.
        if row.severity is not None and row.severity>0:
            last=onset
            if start and row.ended_at:
                end=datetime.fromisoformat(row.ended_at).astimezone(zone)
                last=(end-timedelta(microseconds=1)).date() if end>start else onset
            current=max(onset,first); last=min(last,as_of)
            while current<=last:
                headache.add(current.isoformat()); current+=timedelta(days=1)
    severity=[r.severity for r in recent if r.severity is not None]
    durations=[r.duration for r in recent if r.duration is not None]
    checkins=[w for w in wellness if first<=date.fromisoformat(w.date)<=as_of]
    # Optional check-ins do not imply a headache-free day or complete surveillance.
    state='recorded_episodes' if recent or headache else 'no_episodes_recorded' if checkins else 'insufficient_data'
    return {'window_start':first.isoformat(),'window_end':as_of.isoformat(),'timezone_name':timezone_name,
        'data_status':state,'headache_days':len(headache) if severity or headache or (checkins and not recent) else None,
        'episode_count':len(recent) if recent or checkins or headache else None,
        'average_severity':round(sum(severity)/len(severity),2) if severity else None,
        'severity_count':len(severity),'average_duration_minutes':round(sum(durations)/len(durations),1) if durations else None,
        'duration_count':len(durations),'wellness_days':len(checkins),
        'daily':[{'date':(first+timedelta(days=i)).isoformat(),'episodes':days.get((first+timedelta(days=i)).isoformat(),0),'headache_reported':(first+timedelta(days=i)).isoformat() in headache} for i in range(30)],
        'limitations':'Recorded entries only. Missing logs are not headache-free days. Unknown ends are not extrapolated. Associations are not causes.'}
