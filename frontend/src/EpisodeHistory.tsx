import {useState,type ReactNode} from 'react';
import type {Episode} from './tracking';
import {emptyHistoryFilters,filterHistory,type HistoryFilters} from './historyFilters';

export function EpisodeHistory({episodes,renderEntries,ready=true}:{episodes:Episode[],renderEntries:(rows:Episode[])=>ReactNode,ready?:boolean}){
 const [filters,setFilters]=useState<HistoryFilters>({...emptyHistoryFilters});
 const update=(change:Partial<HistoryFilters>)=>setFilters(previous=>({...previous,...change}));
 const invalidRange=!!filters.from&&!!filters.to&&filters.from>filters.to;
 const active=!!(filters.from||filters.to||filters.severity||filters.symptom.trim()||filters.factor.trim());
 const rows=invalidRange?[]:filterHistory(episodes,filters);
 if(!ready)return null;
 return <><details className="history-filters"><summary>Filter and sort history</summary>
  <p className="helper">Filters apply to loaded records. Date ranges include episodes that overlap the selected dates. Times use your device timezone.</p>
  <div className="history-filter-grid">
   <label>From date<input type="date" value={filters.from} onChange={event=>update({from:event.target.value})}/></label>
   <label>Through date<input type="date" value={filters.to} onChange={event=>update({to:event.target.value})}/></label>
   <label>Pain intensity<select value={filters.severity} onChange={event=>update({severity:event.target.value})}><option value="">Any intensity</option><option value="unknown">Not recorded</option>{Array.from({length:11},(_,i)=><option key={i} value={String(i)}>{i} / 10</option>)}</select></label>
   <label>Symptom contains<input value={filters.symptom} onChange={event=>update({symptom:event.target.value})}/></label>
   <label>Associated factor contains<input value={filters.factor} onChange={event=>update({factor:event.target.value})}/></label>
   <label>Order<select value={filters.order} onChange={event=>update({order:event.target.value as HistoryFilters['order']})}><option value="newest">Newest first</option><option value="oldest">Oldest first</option></select></label>
  </div><button type="button" className="secondary" onClick={()=>setFilters({...emptyHistoryFilters})}>Clear all filters</button>
 </details>
 {invalidRange?<p role="alert">The start date must not be after the end date.</p>:<p className="helper" role="status">Showing {rows.length} of {episodes.length} loaded episodes.</p>}
 {!invalidRange&&(rows.length?renderEntries(rows):active?<p className="empty">No episodes match these filters.</p>:renderEntries(rows))}</>;
}
