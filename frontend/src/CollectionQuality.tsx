import {useState} from 'react';
import {api} from './api';
import {deviceZone} from './tracking';
type Quality={window_start:string,window_end:string,observed_days:number,explicit_no_episode_days:number,unknown_days:number,explicit_unknown_days:number,
 same_day_observations:number,retrospective_observations:number,other_timezone_reports:number,discrepancies:number,correction_count:number,deleted_reports:number,missing_fields:Record<string,number>};
export function CollectionQuality(){
 const [data,setData]=useState<Quality|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function load(){setBusy(true);setData(null);setError('');try{const result=await api('v1/collection-quality?timezone_name='+encodeURIComponent(deviceZone()));if(result?.status!=='insufficient_evidence_for_forecasting')throw new Error();setData(result)}catch{setError('Collection quality could not be loaded. Try again.')}finally{setBusy(false)}}
 return <details><summary>Daily collection quality</summary><p>Review the last 30 dates. Counts describe your reports; they do not establish clinical readiness.</p>
 <button className="secondary" disabled={busy} onClick={load}>{busy?'Loading quality…':'Review collection quality'}</button>{error&&<p role="alert">{error}</p>}
 {data&&<div aria-live="polite"><h3>Insufficient evidence for forecasting</h3><p>{data.window_start} to {data.window_end} · {deviceZone()}</p>
 <dl>{Object.entries({ 'Observed days (including explicit unknown)':data.observed_days,'Completed explicit no-episode days without conflicts':data.explicit_no_episode_days,
 'Unknown days (absent or explicitly unsure)':data.unknown_days,'Explicit unknown reports':data.explicit_unknown_days,
 'Same-day collection':data.same_day_observations,'Retrospective reports':data.retrospective_observations,'Reports in other timezones':data.other_timezone_reports,
 'Discrepancies to review':data.discrepancies,'Corrections':data.correction_count,'Deleted reports':data.deleted_reports}).map(([key,value])=><div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl>
 <p>Same-day collection supports future prospective research but is not a verified prospective forecast outcome. Today’s negative reports remain provisional. Reports in other timezones are shown separately, without remapping local dates. Conflicts remain unresolved evidence.</p>
 <div className="table-wrap"><table><caption>Missing optional fields in current daily reports</caption><thead><tr><th scope="col">Field</th><th scope="col">Missing</th></tr></thead><tbody>{Object.entries(data.missing_fields).map(([key,value])=><tr key={key}><th scope="row">{key.replaceAll('_',' ')}</th><td>{value}</td></tr>)}</tbody></table></div>
 <p>No validated research criteria exist for forecasting in this app. Research consent, complete surveillance and leakage-safe outcome evaluation remain necessary. Older wellness and symptom forms remain outside this new audit trail.</p></div>}
 </details>
}
