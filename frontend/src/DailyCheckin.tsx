import {useEffect,useState,useRef} from 'react';
import {api} from './api';
import {deviceZone,localInput,timestamp} from './tracking';
import {localDate} from './utils';

type Values={date:string,timezone_name:string,status:'migraine'|'no_migraine'|'unknown',observed_at:string,event_at:string,
 sleep_hours:number|null,sleep_quality:number|null,stress:number|null,hydration_ml:number|null,routine_changes:string|null,early_symptoms:string|null};
type Checkin={id:number,date:string,timezone_name:string,created_at:string,revision:number,deleted_at:string|null,values:Values|null,
 retrospective:boolean,day_complete:boolean,whole_day_confirmed:boolean,episode_discrepancy:string|null,wellness_discrepancy:boolean};
type Revision={id:number,revision:number,action:string,recorded_at:string,values:Values|null};
const statusLabel={migraine:'Migraine occurred',no_migraine:'No migraine reported',unknown:'Unknown / not sure'};
const optionalNumbers=[['sleep_hours','Sleep duration (hours)',24],['sleep_quality','Sleep quality (0–10)',10],['stress','Stress (0–10)',10],['hydration_ml','Hydration (ml)',20000]] as const;

export function DailyCheckin(){
 const [rows,setRows]=useState<Checkin[]>([]),[loading,setLoading]=useState(true),[loaded,setLoaded]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
 const [editing,setEditing]=useState<Checkin|null>(null),[formKey,setFormKey]=useState(0),[busy,setBusy]=useState(false);
 const [history,setHistory]=useState<{id:number,revisions:Revision[]}|null>(null);
 const formRef=useRef<HTMLFormElement>(null);
 async function load(){setLoading(true);try{const data=await api('daily-checkins?include_deleted=true');if(!Array.isArray(data))throw new Error();setRows(data);setLoaded(true);setError('')}catch{setLoaded(false);setError('Check-ins could not be loaded. Retry before saving.')}finally{setLoading(false)}}
 useEffect(()=>{load()},[]);
 useEffect(()=>{if(editing)formRef.current?.querySelector<HTMLSelectElement>('select[name="status"]')?.focus()},[editing,formKey]);
 const values=editing?.values;
 async function save(e:React.FormEvent<HTMLFormElement>){
  e.preventDefault();setBusy(true);setError('');setNotice('');
  const f=new FormData(e.currentTarget);
  try{
   const data={date:f.get('date'),timezone_name:editing?.timezone_name||deviceZone(),status:f.get('status'),
    observed_at:timestamp(f.get('observed_at'),values?.observed_at),event_at:timestamp(f.get('event_at'),values?.event_at),
    ...Object.fromEntries(optionalNumbers.map(([key])=>[key,f.get(key)===''?null:Number(f.get(key))])),
    routine_changes:f.get('routine_changes')||null,early_symptoms:f.get('early_symptoms')||null,
    ...(editing?{expected_revision:editing.revision}:{})};
   await api(`daily-checkins${editing?'/'+editing.id:''}`,editing?'PUT':'POST',data);
   setEditing(null);setFormKey(k=>k+1);setHistory(null);await load();setNotice('Daily check-in saved.');
  }catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }
 async function showHistory(row:Checkin){setError('');try{setHistory({id:row.id,revisions:await api(`daily-checkins/${row.id}/history`)})}catch(e){setError((e as Error).message)}}
 async function remove(row:Checkin){
  if(!confirm('Delete this check-in? Earlier values remain in your private history until account deletion.'))return;
  setBusy(true);try{await api(`daily-checkins/${row.id}?expected_revision=${row.revision}`,'DELETE');setEditing(null);setFormKey(k=>k+1);setHistory(null);await load();setNotice('Check-in deleted. Private revision history retained.')}catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }
 return <section className="panel daily-checkin"><h2>Daily migraine check-in</h2>
 <p>A quick daily report, separate from your diary. Missing entries stay unknown. Optional observations are not proven triggers.</p>
 {loading&&<p role="status">Loading check-ins…</p>}{error&&<p role="alert">{error} <button type="button" onClick={load}>Reload check-ins</button></p>}{notice&&<p role="status">{notice}</p>}
 <form ref={formRef} key={formKey} onSubmit={save} aria-label="Daily migraine check-in">
 <fieldset disabled={loading||busy||!loaded}><legend>{editing?'Correct your check-in':'How was your day?'}</legend>
 <label>Report date<input name="date" type="date" required readOnly={!!editing} defaultValue={editing?.date||localDate(new Date())}/></label>
 <p className="helper">Recorded timezone: {editing?.timezone_name||deviceZone()}. Date and timezone stay fixed when correcting an entry.</p>
 <label>Migraine status<select name="status" defaultValue={values?.status||'unknown'}><option value="unknown">Unknown / not sure</option><option value="migraine">Migraine occurred</option><option value="no_migraine">No migraine</option></select></label>
 <p className="helper">Today's report stays provisional. Reconfirm it after the day ends to report a complete no-migraine day. “No migraine” never removes a diary episode. Earlier dates are labeled retrospective.</p>
 <details><summary>Timing and optional observations</summary>
 <p>Report all optional values for the event time below. Use separate existing wellness or early-symptom forms for other observations; those older forms do not have this revision history.</p>
 <label>Event time<input name="event_at" type="datetime-local" step="1" required defaultValue={localInput(values?.event_at||new Date().toISOString())}/></label>
 <label>Observation time<input name="observed_at" type="datetime-local" step="1" required defaultValue={localInput(values?.observed_at||new Date().toISOString())}/></label>
 <p className="helper">Event time: when this report applies. Observation time: when you noticed it. Server entry time is saved separately. When backdating, change the event time to the report date. Times use your device timezone ({deviceZone()}); an unchanged saved time preserves its exact instant across daylight-saving changes.</p>
 {optionalNumbers.map(([key,label,max])=><label key={key}>{label}<input name={key} type="number" min="0" max={max} step={key==='sleep_hours'?'0.1':'1'} defaultValue={values?.[key]??''}/></label>)}
 <label>Routine changes (optional)<textarea name="routine_changes" maxLength={1000} defaultValue={values?.routine_changes||''}/></label>
 <label>Early symptoms (optional)<textarea name="early_symptoms" maxLength={1000} defaultValue={values?.early_symptoms||''}/></label>
 </details>
 <div className="actions"><button className="primary" type="submit">{busy?'Saving…':editing?'Save correction':'Save daily check-in'}</button>{editing&&<button type="button" className="secondary" onClick={()=>{setEditing(null);setFormKey(k=>k+1)}}>Cancel correction</button>}</div>
 </fieldset></form>
 {!loading&&!rows.length&&<p className="empty">No daily reports yet. Choose a status and save; every health observation is optional.</p>}
 {rows.map(row=><article className="tracking-entry" key={row.id}><h3>{row.date} — {row.deleted_at?'Deleted check-in':statusLabel[row.values!.status]}</h3>
 <p>{row.retrospective?'Retrospective entry':'Same-day collection'} · {row.timezone_name} · Revision {row.revision}{!row.day_complete?' · Day still in progress':!row.deleted_at&&!row.whole_day_confirmed?' · Reconfirm status for the completed day':''}</p>
 <p>First entered: {new Date(row.created_at).toLocaleString()}</p>
 {row.values&&<p>Event: {new Date(row.values.event_at).toLocaleString()} · Observed: {new Date(row.values.observed_at).toLocaleString()}</p>}
 {(row.episode_discrepancy||row.wellness_discrepancy)&&<p role="status">Discrepancy: {row.episode_discrepancy==='no_migraine_with_diary_episode'?'a diary episode overlaps this no-migraine report.':row.episode_discrepancy==='migraine_without_diary_episode'?'migraine reported without a diary episode.':''} {row.wellness_discrepancy?'The older wellness status differs.':''} Review both records; neither has been overwritten.</p>}
 <div className="actions">{!row.deleted_at&&<><button className="secondary" disabled={busy} onClick={()=>{setEditing(row);setFormKey(k=>k+1);setNotice('');document.querySelector<HTMLFormElement>('form[aria-label="Daily migraine check-in"]')?.scrollIntoView?.({block:'start'})}}>Edit {row.date}</button><button className="secondary" disabled={busy} onClick={()=>remove(row)}>Delete {row.date}</button></>}
 <button className="secondary" onClick={()=>showHistory(row)}>History {row.date}</button></div>
 {history?.id===row.id&&<section aria-label={`History ${row.date}`}><h4>Private revision history</h4><button className="secondary" onClick={()=>setHistory(null)}>Close history</button>{history.revisions.map(rev=><details key={rev.id}><summary>Revision {rev.revision}: {rev.action} — {new Date(rev.recorded_at).toLocaleString()}</summary>{rev.values?<dl>{Object.entries(rev.values).map(([key,value])=><div key={key}><dt>{key.replaceAll('_',' ')}</dt><dd>{value===null?'Not recorded':String(value)}</dd></div>)}</dl>:<p>Deletion tombstone. Earlier values remain in prior revisions.</p>}</details>)}</section>}
 </article>)}
 <p className="helper">Deletion hides current values but retains private audit history and reserves the date. Account deletion removes both. Download your records from Settings to include revision history.</p>
 </section>
}
