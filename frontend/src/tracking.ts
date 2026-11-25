import {localDate} from './utils';
export type Medication={name:string,taken_at:string};
export type Episode={id:number,date:string,severity:number|null,duration:number|null,trigger:string,notes:string,started_at?:string|null,ended_at?:string|null,timezone_name?:string|null,pain_location?:string,symptoms?:string[],functional_impact?:string,medications?:Medication[],attack_session_id?:number|null};
export type Wellness={id:number,date:string,timezone_name:string,recorded_at:string,sleep_hours:number|null,sleep_quality:number|null,stress:number|null,hydration_ml:number|null,missed_meals:boolean|null,screen_hours:number|null,menstrual_notes:string|null,episode_observation?:'episode'|'no_episode'|null,observation_recorded_at?:string|null};
export type Early={id:number,symptom:string,onset_at:string,timezone_name:string,notes:string};
export type Insights={data_status:string,headache_days:number|null,episode_count:number|null,average_severity:number|null,average_duration_minutes:number|null,severity_count:number,duration_count:number,wellness_days:number,daily:{date:string,episodes:number,headache_reported:boolean}[],limitations:string,window_start?:string,window_end?:string,timezone_name?:string};
export const deviceZone=()=>Intl.DateTimeFormat().resolvedOptions().timeZone||'UTC';
export function localInput(value?:string|null){if(!value)return '';const d=new Date(value);return `${localDate(d)}T${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`;}
export function timestamp(value:FormDataEntryValue|null,original?:string|null){if(!value)return null;const normalized=String(value).length===16?String(value)+':00':String(value);if(original&&normalized===localInput(original))return new Date(original).toISOString();const text=String(value),d=new Date(text);if(!Number.isFinite(d.getTime())||localInput(d.toISOString()).slice(0,16)!==text.slice(0,16))throw new Error('This local time is invalid in your device timezone. Choose a valid time.');return d.toISOString();}
export function episodePayload(form:HTMLFormElement,original?:Episode){
 const f=new FormData(form);const number=(key:string)=>f.get(key)===''||!f.has(key)?null:Number(f.get(key));
 const started=timestamp(f.get('started_at'),original?.started_at),ended=timestamp(f.get('ended_at'),original?.ended_at);
 const now=Date.now();
 if(started&&new Date(started).getTime()>now)throw new Error('Episode start cannot be in the future.');
 if(ended&&(!started||new Date(ended).getTime()<=new Date(started).getTime()))throw new Error('Episode end must be after start.');
 if(ended&&new Date(ended).getTime()>now)throw new Error('Episode end cannot be in the future.');
 const legacyZone=original?.timezone_name||null;
 const today=legacyZone?new Intl.DateTimeFormat('en-CA',{timeZone:legacyZone,year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(now)):new Date(now).toISOString().slice(0,10);
 if(!started&&f.get('date')&&String(f.get('date'))>today)throw new Error('Episode date cannot be in the future.');
 const names=f.getAll('medication_name'),times=f.getAll('medication_time');
 const medications=names.flatMap((name,i)=>{
  if(!name&&!times[i])return [];
  if(!name||!times[i])throw new Error('Medication entries need both a name and time taken.');
  const taken=timestamp(times[i],original?.medications?.find(m=>m.name===String(name)&&localInput(m.taken_at).slice(0,16)===String(times[i]).slice(0,16))?.taken_at);
  if(taken&&new Date(taken).getTime()>now)throw new Error('Medication observation cannot be in the future.');
  return [{name:String(name),taken_at:taken}];
 });
 const severity=number('severity'),duration=started&&ended?null:number('duration');
 const unique=(text:string)=>{const seen=new Set<string>();return text.split(',').map(value=>value.trim()).filter(value=>{const key=value.toLocaleLowerCase();if(!key||seen.has(key))return false;seen.add(key);return true})};
 const symptomText=String(f.get('symptoms')||'');
 const selected=f.get('symptom_selection');
 let symptoms:string[];
 if(selected!==null){
  try{const parsed:unknown=JSON.parse(String(selected));if(!Array.isArray(parsed)||parsed.some(value=>typeof value!=='string'||!value.trim()))throw new Error();symptoms=parsed}
  catch{throw new Error('Symptoms could not be read. Please review your selections.')}
 }else symptoms=original&&symptomText===(original.symptoms||[]).join(', ')?(original.symptoms||[]):unique(symptomText);
 if(symptoms.length>30||symptoms.some(value=>value.length>100))throw new Error('Use up to 30 symptoms, with at most 100 characters each.');
 const factorText=String(f.get('trigger')||'');
 const originalFactor=original?.trigger==='Unknown'?'':original?.trigger;
 const trigger=original&&factorText===originalFactor?factorText:unique(factorText).join(', ');
 if(trigger.length>100)throw new Error('Possible associated factors must fit within 100 characters.');
 if(severity!==null&&(!Number.isInteger(severity)||severity<0||severity>10))throw new Error('Severity must be a whole number from 0 to 10.');
 if(duration!==null&&(!Number.isInteger(duration)||duration<0||duration>525600))throw new Error('Duration must be a whole number from 0 to 525600 minutes.');
 if(started&&ended&&(new Date(ended).getTime()-new Date(started).getTime())/60000>525600)throw new Error('Episode interval exceeds the supported duration.');
 return {date:started?null:f.get('date'),started_at:started,ended_at:ended,timezone_name:started?(original?.started_at&&localInput(original.started_at).slice(0,16)===String(f.get('started_at')).slice(0,16)?original.timezone_name||deviceZone():deviceZone()):legacyZone,
  severity,duration,trigger:trigger||'Unknown',notes:f.get('notes')||'',pain_location:f.get('pain_location')||'',symptoms,functional_impact:f.get('functional_impact')||'',medications,attack_session_id:number('attack_session_id')};
}
