import {useState} from 'react';
import {api} from './api';
import {deviceZone} from './tracking';

type Readiness={version:string,window_start:string,window_end:string,days:number,completed_days:number,
 coverage:Record<string,number>,wellness_checkins:number,early_observations:number,missingness:Record<string,{missing:number,available:number}>,
 labeled_outcomes:{positive:number,negative:number},training_justified:false,evaluation_justified:false,
 preparation:{prediction_cutoff:string,horizon_end:string,eligibility:string},limitations:string[]};
const labels:Record<string,string>={severity:'Reported severity',sleep_hours:'Sleep duration',sleep_quality:'Sleep quality',
 stress:'Stress',hydration_ml:'Hydration',missed_meals:'Missed meals',screen_hours:'Screen exposure'};
export function DataReadiness(){
 const [data,setData]=useState<Readiness|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function load(){setBusy(true);setError('');setData(null);try{
  const result=await api(`v1/data-readiness?timezone_name=${encodeURIComponent(deviceZone())}`);
  if(result?.version!=='account-preparation/v1')throw new Error('Unavailable');
  setData(result);
 }catch{setError('Data readiness could not be loaded. Please try again.')}finally{setBusy(false)}}
 return <details><summary>Your data readiness</summary>
 <p>Review your account's observation coverage and missing values. This read-only check does not train a model or save research snapshots.</p>
 <button className="secondary" disabled={busy} onClick={load}>{busy?'Checking your records...':'Review data readiness'}</button>
 {error&&<p role="alert">{error}</p>}
 {data&&<div aria-live="polite"><h3>Not ready for forecasting research</h3>
 <p>{data.window_start} to {data.window_end} - {deviceZone()}. {data.completed_days} completed dates in this {data.days}-date window.</p>
 <dl><dt>Dates with a recorded episode</dt><dd>{data.coverage.episode_recorded}</dd>
 <dt>Explicit whole-day no-episode reports</dt><dd>{data.coverage.no_episode_reported}</dd>
 <dt>Dates with unknown episode status</dt><dd>{data.coverage.unknown}</dd>
 <dt>Conflicting observation dates</dt><dd>{data.coverage.conflict}</dd>
 <dt>Episode reported without a timed onset</dt><dd>{data.coverage.episode_reported_without_onset}</dd>
 <dt>Timed early symptom observations</dt><dd>{data.early_observations}</dd>
 <dt>Wellness check-ins</dt><dd>{data.wellness_checkins}</dd>
 <dt>Established prospective labels</dt><dd>{data.labeled_outcomes.positive} positive; {data.labeled_outcomes.negative} negative</dd></dl>
 <p>These dates are descriptive coverage, not prediction outcomes. We need immutable record history, prospective outcome confirmation, research consent and provenance review before training or evaluation is justified.</p>
 <p className="helper">Severity availability counts timed onsets in this window; wellness availability counts check-ins. These denominators differ. Blank values stay unknown, and a reported zero stays zero.</p>
 <div className="table-wrap"><table><caption>Recorded values and missing fields</caption><thead><tr><th scope="col">Observation</th><th scope="col">Available</th><th scope="col">Missing</th></tr></thead><tbody>
 {Object.entries(data.missingness).map(([key,value])=><tr key={key}><th scope="row">{labels[key]||key}</th><td>{value.available}</td><td>{value.missing}</td></tr>)}
 </tbody></table></div>
 <p className="helper">The preparation cutoff is {new Date(data.preparation.prediction_cutoff).toLocaleString()}; the next-24-hour horizon ends {new Date(data.preparation.horizon_end).toLocaleString()}. No outcome or probability is assigned.</p>
 <ul>{data.limitations.map(text=><li key={text}>{text}</li>)}</ul></div>}
 </details>
}
