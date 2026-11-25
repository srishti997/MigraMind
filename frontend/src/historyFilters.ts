import type {Episode} from './tracking';
import {localDate} from './utils';

export type HistoryFilters={from:string,to:string,severity:string,symptom:string,factor:string,order:'newest'|'oldest'};
export const emptyHistoryFilters:HistoryFilters={from:'',to:'',severity:'',symptom:'',factor:'',order:'newest'};

// Timed episodes use the device timezone. Date-only records use their saved
// date. Unknown ends stop at onset; an exact midnight end excludes that day.
export function episodeDays(episode:Episode):{start:string,end:string}|null{
 if(!episode.started_at)return episode.date?{start:episode.date,end:episode.date}:null;
 const start=new Date(episode.started_at);
 if(!Number.isFinite(start.getTime()))return null;
 const end=episode.ended_at?new Date(episode.ended_at):null;
 const last=end&&Number.isFinite(end.getTime())&&end.getTime()>start.getTime()?new Date(end.getTime()-1):start;
 return {start:localDate(start),end:localDate(last)};
}
export function episodeOnDate(episode:Episode,date:string){
 const days=episodeDays(episode);return !!date&&!!days&&date>=days.start&&date<=days.end;
}
export function filterHistory(episodes:Episode[],filters:HistoryFilters){
 const symptom=filters.symptom.trim().toLocaleLowerCase(),factor=filters.factor.trim().toLocaleLowerCase();
 return episodes.filter(episode=>{
  const days=episodeDays(episode);
  if((filters.from||filters.to)&&(!days||(filters.from&&days.end<filters.from)||(filters.to&&days.start>filters.to)))return false;
  if(filters.severity==='unknown'&&episode.severity!==null)return false;
  if(filters.severity&&filters.severity!=='unknown'&&episode.severity!==Number(filters.severity))return false;
  if(symptom&&!(episode.symptoms||[]).some(value=>value.toLocaleLowerCase().includes(symptom)))return false;
  if(factor&&(episode.trigger==='Unknown'||!episode.trigger.toLocaleLowerCase().includes(factor)))return false;
  return true;
 }).slice().sort((a,b)=>{
  const ad=episodeDays(a)?.start||'',bd=episodeDays(b)?.start||'';
  const dateOrder=ad.localeCompare(bd);
  // Time is unknown for legacy dates; place those at the start of their date.
  const at=a.started_at?new Date(a.started_at).getTime():0,bt=b.started_at?new Date(b.started_at).getTime():0;
  const timeOrder=(Number.isFinite(at)?at:0)-(Number.isFinite(bt)?bt:0);
  return (dateOrder||timeOrder||a.id-b.id)*(filters.order==='newest'?-1:1);
 });
}
