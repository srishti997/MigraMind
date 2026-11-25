import {describe,expect,it} from 'vitest';
import {recordedFrequencies} from './recordedFrequencies';
import type {Episode,Insights} from './tracking';

const window:Insights={window_start:'2025-01-02',window_end:'2025-01-08',timezone_name:'Asia/Kolkata',data_status:'recorded_episodes',headache_days:1,episode_count:3,average_severity:0,average_duration_minutes:null,severity_count:1,duration_count:0,wellness_days:0,daily:[],limitations:''};
const episode=(id:number,date:string,changes:Partial<Episode>={}):Episode=>({id,date,severity:null,duration:null,trigger:'Unknown',notes:'',...changes});

describe('recorded episode frequencies',()=>{
 it('uses inclusive server dates and reporting timezone, with one count per episode',()=>{
  const rows=[
   episode(1,'2025-01-01',{started_at:'2025-01-01T20:00:00Z',symptoms:['Nausea','nausea','Fatigue'],trigger:'Stress, stress, Poor sleep'}),
   episode(2,'2025-01-02',{symptoms:['NAUSEA'],trigger:'stress'}),
   episode(3,'2025-01-08',{severity:0,duration:0}),
   episode(4,'2025-01-09',{symptoms:['Excluded'],trigger:'Excluded'}),
   episode(5,'2025-01-01',{symptoms:['Excluded'],trigger:'Excluded'}),
   episode(6,'2025-01-02',{started_at:'not-a-date'})
  ];
  expect(recordedFrequencies(rows,window)).toEqual({episodes:3,excluded:1,withoutSymptoms:1,withoutFactors:1,
   symptoms:[{label:'Nausea',count:2},{label:'Fatigue',count:1}],factors:[{label:'Stress',count:2},{label:'Poor sleep',count:1}]});
  expect(recordedFrequencies(rows,{...window,timezone_name:'UTC'})?.episodes).toBe(2);
 });
 it('returns empty counts without inventing zeros for unrecorded data',()=>{
  expect(recordedFrequencies([],window)).toMatchObject({episodes:0,symptoms:[],factors:[]});
  expect(recordedFrequencies([episode(1,'2025-01-02')],window)).toMatchObject({episodes:1,withoutSymptoms:1,withoutFactors:1});
 });
 it('refuses missing or invalid window metadata',()=>{
  expect(recordedFrequencies([],{...window,timezone_name:'not/a-zone'})).toBeNull();
  expect(recordedFrequencies([],{...window,window_start:undefined})).toBeNull();
  expect(recordedFrequencies([],{...window,window_start:'2025-01-09'})).toBeNull();
  expect(recordedFrequencies([],{...window,window_start:'2025-02-30'})).toBeNull();
 });
});
