import type {Episode,Insights} from './tracking';

type Frequency={label:string,count:number};
type RecordedFrequencies={episodes:number,symptoms:Frequency[],factors:Frequency[],withoutSymptoms:number,withoutFactors:number,excluded:number};
function validDate(value:string){
 if(!/^\d{4}-\d{2}-\d{2}$/.test(value))return false;
 const date=new Date(value+'T00:00:00Z');
 return Number.isFinite(date.getTime())&&date.toISOString().slice(0,10)===value;
}

// Counts describe episode onsets in the server's existing reporting window.
// They do not count early-symptom observations or imply a cause.
export function recordedFrequencies(episodes:Episode[],insights:Insights):RecordedFrequencies|null{
 const {window_start:start,window_end:end,timezone_name:zone}=insights;
 if(!start||!end||!zone||!validDate(start)||!validDate(end)||start>end)return null;
 let formatter:Intl.DateTimeFormat;
 try{formatter=new Intl.DateTimeFormat('en-CA',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit'})}catch{return null}
 const symptoms=new Map<string,Frequency>(),factors=new Map<string,Frequency>();
 let total=0,withoutSymptoms=0,withoutFactors=0,excluded=0;
 function count(map:Map<string,Frequency>,values:string[]){
  const inEpisode=new Set<string>();
  for(const raw of values){
   const label=raw.trim(),key=label.toLocaleLowerCase();
   if(!key||inEpisode.has(key))continue;
   inEpisode.add(key);
   const existing=map.get(key);
   if(existing)existing.count++;else map.set(key,{label,count:1});
  }
  return inEpisode.size>0;
 }
 for(const episode of episodes){
  let date=episode.date;
  if(episode.started_at){
   const instant=new Date(episode.started_at);
   if(!Number.isFinite(instant.getTime())){excluded++;continue}
   const values=Object.fromEntries(formatter.formatToParts(instant).map(part=>[part.type,part.value]));
   date=`${values.year}-${values.month}-${values.day}`;
  }
  if(!date||!validDate(date)){excluded++;continue}
  if(date<start||date>end)continue;
  total++;
  if(!count(symptoms,Array.isArray(episode.symptoms)?episode.symptoms.filter((s):s is string=>typeof s==='string'):[]))withoutSymptoms++;
  const factor=typeof episode.trigger==='string'?episode.trigger:'';
  if(!count(factors,factor.split(',').filter(value=>value.trim().toLocaleLowerCase()!=='unknown')))withoutFactors++;
 }
 const sorted=(map:Map<string,Frequency>)=>[...map.values()].sort((a,b)=>b.count-a.count||a.label.localeCompare(b.label));
 return {episodes:total,symptoms:sorted(symptoms),factors:sorted(factors),withoutSymptoms,withoutFactors,excluded};
}
