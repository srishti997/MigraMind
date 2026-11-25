import {describe,expect,it} from 'vitest';
import {emptyHistoryFilters,episodeOnDate,filterHistory} from './historyFilters';
import type {Episode} from './tracking';

const record=(id:number,date:string,changes:Partial<Episode>={}):Episode=>({id,date,severity:null,duration:null,trigger:'Unknown',notes:'',symptoms:[],...changes});
const rows=[record(1,'2024-12-31',{severity:0,trigger:'Stress',symptoms:['Nausea']}),record(2,'2025-01-01',{severity:null,trigger:'Poor sleep',symptoms:['Aura']}),record(3,'2025-01-01',{started_at:new Date(2025,0,1,23).toISOString(),ended_at:new Date(2025,0,2,0).toISOString(),severity:7,symptoms:['Nausea']})];

describe('historical dates and filters',()=>{
 it('uses local dates for timed intervals and preserves date-only records across years',()=>{
  expect(episodeOnDate(rows[0],'2024-12-31')).toBe(true);
  expect(episodeOnDate(rows[2],'2025-01-01')).toBe(true);
  expect(episodeOnDate(rows[2],'2025-01-02')).toBe(false); // Exact midnight end.
  const extended={...rows[2],ended_at:new Date(2025,0,2,1).toISOString()};
  expect(episodeOnDate(extended,'2025-01-02')).toBe(true);
  expect(episodeOnDate({...extended,ended_at:null},'2025-01-02')).toBe(false);
 });
 it('filters inclusively by overlapping dates, 0 versus unknown, symptoms and factors',()=>{
  expect(filterHistory(rows,{...emptyHistoryFilters,from:'2025-01-01',to:'2025-01-01'}).map(row=>row.id)).toEqual([3,2]);
  expect(filterHistory(rows,{...emptyHistoryFilters,severity:'0'}).map(row=>row.id)).toEqual([1]);
  expect(filterHistory(rows,{...emptyHistoryFilters,severity:'unknown'}).map(row=>row.id)).toEqual([2]);
  expect(filterHistory(rows,{...emptyHistoryFilters,symptom:'nau',order:'oldest'}).map(row=>row.id)).toEqual([1,3]);
  expect(filterHistory(rows,{...emptyHistoryFilters,factor:'SLEEP'}).map(row=>row.id)).toEqual([2]);
  expect(filterHistory(rows,{...emptyHistoryFilters,from:'2025-01-02'})).toEqual([]);
 });
});
