import {useState} from 'react';
import type {Episode,Wellness,Early} from './tracking';
import {deviceZone,localInput} from './tracking';
import {localDate} from './utils';
import type {AttackSession} from './assistance';
const symptomSuggestions=['Throbbing pain','Nausea','Vomiting','Light sensitivity','Sound sensitivity','Smell sensitivity','Dizziness','Visual aura','Fatigue','Difficulty concentrating'];
const factorSuggestions=['Stress','Poor sleep','Skipped meals','Dehydration','Screen exposure','Weather changes','Hormonal changes','Caffeine','Bright lights','Strong smells'];
const parts=(text:string)=>text.split(',').map(value=>value.trim()).filter(Boolean);
const same=(a:string,b:string)=>a.toLocaleLowerCase()===b.toLocaleLowerCase();
function toggle(text:string,choice:string){
 const values=parts(text);
 return (values.some(value=>same(value,choice))?values.filter(value=>!same(value,choice)):[...values,choice]).join(', ');
}
function parseSymptoms(text:string,original:string[]){
 const tokens=parts(text),values:string[]=[];
 for(let i=0;i<tokens.length;i++){
  const match=original.find(value=>{const fragments=parts(value);return fragments.length>1&&fragments.every((fragment,j)=>tokens[i+j]!==undefined&&same(fragment,tokens[i+j]))});
  if(match){values.push(match);i+=parts(match).length-1}else values.push(tokens[i]);
 }
 const used=new Map<string,number>();
 return values.filter(value=>{
  const key=value.toLocaleLowerCase(),count=used.get(key)||0;
  const originalCount=original.filter(item=>same(item,value)).length;
  if(count>=Math.max(1,originalCount))return false;
  used.set(key,count+1);return true;
 });
}
function Suggestions({label,options,value,onChange,maxLength,maxItems,selectedValues,onToggle}:{label:string,options:string[],value:string,onChange:(next:string)=>void,maxLength:number,maxItems?:number,selectedValues?:string[],onToggle?:(choice:string)=>void}){
 const selected=selectedValues||parts(value);
 return <fieldset className="suggestion-group"><legend>{label} · optional</legend><div className="suggestion-chips">{options.map(option=>{
  const active=selected.some(item=>same(item,option));
  const next=active?selected.filter(item=>!same(item,option)):[...selected,option];
  const disabled=!active&&(next.join(', ').length>maxLength||(maxItems!==undefined&&next.length>maxItems));
  return <button key={option} type="button" className="suggestion-chip" aria-pressed={active} disabled={disabled} onClick={()=>onToggle?onToggle(option):onChange(toggle(value,option))}>{option}</button>;
 })}</div>{maxItems&&<p className="helper">Up to {maxItems} symptoms; each may contain up to 100 characters.</p>}</fieldset>
}
export function EpisodeFields({entry,date,sessions}:{entry?:Episode,date:string,sessions:AttackSession[]}){
 const [end,setEnd]=useState(localInput(entry?.ended_at));
 const [meds,setMeds]=useState((entry?.medications||[]).map((m,i)=>({...m,key:i})));
 const [symptoms,setSymptoms]=useState((entry?.symptoms||[]).join(', '));
 const [symptomValues,setSymptomValues]=useState(entry?.symptoms||[]);
 const [factors,setFactors]=useState(entry?.trigger==='Unknown'?'':entry?.trigger||'');
 return <><p className="helper">Quick entry: {entry&&!entry.started_at?'the date is required; exact start time is optional for this older entry.':'attack start is required.'} Everything else is optional. Times use {deviceZone()} and are saved in UTC.</p>
 {entry&&!entry.started_at?<label>Legacy date · exact time unknown<input autoFocus required type="date" name="date" defaultValue={entry.date}/></label>:<input type="hidden" name="date" value={entry?.date||date}/>}
 <label>Attack started<input autoFocus={!entry||!!entry.started_at} type="datetime-local" step="1" name="started_at" required={!entry||!!entry.started_at} defaultValue={entry?.started_at?localInput(entry.started_at):entry?'':`${date}T${localInput(new Date().toISOString()).split('T')[1]}`}/></label>
 <label>Pain severity · optional (0–10)<input type="number" inputMode="numeric" min="0" max="10" step="1" name="severity" defaultValue={entry?.severity??''} placeholder="Not recorded" aria-describedby="severity-help"/><small id="severity-help">0 means no pain; 10 is the highest pain on this scale. Leave blank if not recorded.</small></label>
 <details className="detailed-entry" open={!!entry}><summary>Optional details · now or later</summary>
 <label>Attack ended · leave blank if unknown<input type="datetime-local" step="1" name="ended_at" value={end} onChange={e=>setEnd(e.target.value)}/></label>
 <label>Duration in minutes · if exact end is unknown<input type="number" name="duration" disabled={!!end} min="0" max="525600" defaultValue={entry?.duration??''}/><small>Start and end times determine duration when both are known.</small></label>
 <label>Pain location<input name="pain_location" maxLength={200} defaultValue={entry?.pain_location} placeholder="In your own words"/></label>
 <Suggestions label="Symptoms" options={symptomSuggestions} value={symptoms} onChange={setSymptoms} selectedValues={symptomValues} onToggle={option=>{const next=symptomValues.some(value=>same(value,option))?symptomValues.filter(value=>!same(value,option)):[...symptomValues,option];setSymptomValues(next);setSymptoms(next.join(', '))}} maxLength={3000} maxItems={30}/>
 <label>Symptoms · separate with commas<input name="symptoms" maxLength={3000} value={symptoms} onChange={e=>{setSymptoms(e.target.value);setSymptomValues(parseSymptoms(e.target.value,entry?.symptoms||[]))}} placeholder="Add your own symptoms"/></label>
 <input type="hidden" name="symptom_selection" value={JSON.stringify(symptomValues)}/>
 <label>Impact on daily activities<select name="functional_impact" defaultValue={entry?.functional_impact||''}><option value="">Not recorded</option>{['No disruption','Some activities limited','Most activities limited','Unable to do usual activities'].map(v=><option key={v}>{v}</option>)}</select></label>
 <Suggestions label="Possible associated factors" options={factorSuggestions} value={factors} onChange={setFactors} maxLength={100}/>
 <p className="helper" id="factor-help">These are your observations, not medically confirmed causes. The combined factor text can be up to 100 characters ({factors.length}/100). Suggestions that would exceed this limit are unavailable.</p>
 <label>Possible associated factor · not a proven trigger<input name="trigger" maxLength={100} value={factors} onChange={e=>setFactors(e.target.value)} aria-describedby="factor-help" placeholder="Add your own factors, separated by commas"/></label>
 <fieldset><legend>Medication taken · optional</legend><p className="helper">Record only what you took and when. No medication or dosage recommendations.</p>{meds.map((m,i)=><div className="medication-row" key={m.key}><label>Medication name<input name="medication_name" maxLength={200} defaultValue={m.name}/></label><label>Time taken<input type="datetime-local" step="1" name="medication_time" defaultValue={localInput(m.taken_at)}/></label><button type="button" className="secondary" onClick={()=>setMeds(meds.filter((_,n)=>n!==i))}>Remove medication {i+1}</button></div>)}<button type="button" className="secondary" onClick={()=>setMeds([...meds,{name:'',taken_at:'',key:Math.max(-1,...meds.map(m=>m.key))+1}])}>Add medication</button></fieldset>
 <label>Related attack session · optional<select name="attack_session_id" defaultValue={entry?.attack_session_id||''}><option value="">No linked session</option>{sessions.map(s=><option key={s.id} value={s.id}>Session {s.id} · {new Date(s.started_at).toLocaleString()}</option>)}</select><small>Linking does not start or end a session.</small></label>
 <label>Your notes<textarea name="notes" rows={3} maxLength={3000} defaultValue={entry?.notes}/></label></details></>
}
export function WellnessFields({entry,date}:{entry?:Wellness,date:string}){return <><p className="helper">Every wellness field is optional. Blank means unknown, not zero.</p><label>Check-in date<input autoFocus required name="date" type="date" defaultValue={entry?.date||date}/></label><label>Whole-day episode observation (optional)<select name="episode_observation" defaultValue={entry?.episode_observation||''}><option value="">Unknown / not recorded</option><option value="episode">An episode occurred</option><option value="no_episode">No episode occurred for the whole day</option></select><small>Only confirm a completed date. Blank diary days are never assumed episode-free.</small></label><div className="form-row"><label>Sleep duration (hours)<input name="sleep_hours" type="number" min="0" max="24" step="0.1" defaultValue={entry?.sleep_hours??''}/></label><label>Sleep quality (0 poor–10 good)<input name="sleep_quality" type="number" min="0" max="10" defaultValue={entry?.sleep_quality??''}/></label><label>Stress (0 low–10 high)<input name="stress" type="number" min="0" max="10" defaultValue={entry?.stress??''}/></label><label>Hydration estimate (ml)<input name="hydration_ml" type="number" min="0" max="20000" defaultValue={entry?.hydration_ml??''}/></label><label>Screen exposure (hours)<input name="screen_hours" type="number" min="0" max="24" step="0.1" defaultValue={entry?.screen_hours??''}/></label><label>Missed meals<select name="missed_meals" defaultValue={entry?.missed_meals===null||entry?.missed_meals===undefined?'':String(entry.missed_meals)}><option value="">Not recorded</option><option value="true">Yes</option><option value="false">No</option></select></label></div><details><summary>Optional menstrual-cycle information</summary><label>Cycle observations<textarea name="menstrual_notes" maxLength={1000} defaultValue={entry?.menstrual_notes||''} placeholder="Only if relevant and comfortable to share"/></label></details><input type="hidden" name="timezone_name" value={entry?.timezone_name||deviceZone()}/></>}
export function EarlyFields({entry,date}:{entry?:Early,date:string}){return <><p className="helper">Record possible early symptoms separately from attacks. These are observations, not proven triggers or predictions. Times use {deviceZone()}.</p><label>Symptom<input autoFocus name="symptom" required maxLength={200} defaultValue={entry?.symptom}/></label><label>First noticed<input name="onset_at" required type="datetime-local" step="1" defaultValue={entry?localInput(entry.onset_at):`${date}T${localInput(new Date().toISOString()).split('T')[1]}`}/></label><label>Notes · optional<textarea name="notes" maxLength={3000} defaultValue={entry?.notes}/></label></>}
