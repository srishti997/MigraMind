import type {Page} from '@playwright/test';
import {patternFixture} from './patterns';

/** UI-only manual review: every API request is intercepted; no backend or persistence. */
export async function installManualAccessibilityFixture(page:Page,options:{baseURL:string,anonymous?:boolean,readOnly?:boolean,delayMs?:number,failPaths?:string[]}){
 const target=new URL(options.baseURL);
 if(target.protocol!=='http:'||!['127.0.0.1','localhost','[::1]'].includes(target.hostname))throw new Error('Manual review requires an explicit loopback fixture origin');
 const stamp='2026-01-03T12:00:00Z';
 const values={date:'2026-01-03',timezone_name:'UTC',status:'unknown',event_at:stamp,observed_at:stamp,
  sleep_hours:null,sleep_quality:null,stress:null,hydration_ml:null,routine_changes:null,early_symptoms:null};
 const contacts=[{id:1,name:'Synthetic contact',relationship:'Fictional friend',phone:'+12025550100'}];
 const checkins=['2026-01-01','2026-01-02','2026-01-03'].map((date,index)=>({
  id:index+1,date,timezone_name:'UTC',created_at:stamp,revision:1,deleted_at:null,
  values:{...values,date,status:['no_migraine','migraine','unknown'][index],event_at:date+'T12:00:00Z',observed_at:date+'T12:00:00Z'},
  retrospective:true,day_complete:true,whole_day_confirmed:index===0,episode_discrepancy:null,wellness_discrepancy:false,
 }));
 await page.addInitScript(()=>{
  // Never open a real telephone/SMS handler, external page, clipboard, share sheet or GPS.
  document.addEventListener('click',event=>{
   const link=event.target instanceof Element?event.target.closest<HTMLAnchorElement>('a[href]'):null;
   if(link&&/^(tel:|sms:|https?:)/.test(link.href)&&!link.href.startsWith(location.origin+'/'))event.preventDefault();
  },true);
  Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{}}});
  Object.defineProperty(navigator,'share',{configurable:true,value:async()=>{}});
  Object.defineProperty(navigator,'geolocation',{configurable:true,value:{getCurrentPosition:(success:PositionCallback)=>success({coords:{latitude:12.34,longitude:56.78,accuracy:75,altitude:null,altitudeAccuracy:null,heading:null,speed:null},timestamp:0} as GeolocationPosition)}});
 });
 await page.route('**/*',route=>{
  const url=new URL(route.request().url());
  if(['http:','https:'].includes(url.protocol)&&url.origin!==target.origin)return route.abort();
  return route.fallback();
 });
 await page.route('**/api/**',async route=>{
  const request=route.request(),url=new URL(request.url()),path=url.pathname;
  if(options.delayMs)await new Promise(resolve=>setTimeout(resolve,Math.min(Math.max(options.delayMs!,0),10000)));
  if(!['GET','HEAD'].includes(request.method()))return route.fulfill({status:422,json:{detail:'Synthetic manual fixture error. No data saved.'}});
  if(options.failPaths?.includes(path))return route.fulfill({status:503,json:{detail:'Synthetic manual fixture outage'}});
  let data:unknown;
  if(path==='/api/auth/session')data={user:options.anonymous?null:{id:1,email:'synthetic@example.test',display_name:'Review'},csrf_token:'synthetic-fixture-token',demo_mode:!!options.readOnly};
  else if(path==='/api/profile')data={name:'Review',environment:'Synthetic dim room',support:'Synthetic quiet preference',avoid:'Noise',communication:'Text first'};
  else if(path==='/api/contacts')data=contacts;
  else if(path==='/api/support/preferences')data={};
  else if(path==='/api/episodes')data=[{id:1,date:'2026-01-02',started_at:'2026-01-02T10:00:00Z',ended_at:'2026-01-02T11:00:00Z',timezone_name:'UTC',duration:60,severity:3,trigger:'Unknown',notes:'Synthetic accessibility fixture only.',symptoms:[],medications:[]}];
  else if(path==='/api/daily-checkins')data=checkins;
  else if(/^\/api\/daily-checkins\/\d+\/history$/.test(path)){
   const row=checkins.find(item=>item.id===Number(path.split('/')[3]));
   data=row?[{id:row.id,revision:1,action:'creation',recorded_at:stamp,values:row.values}]:[];
  }
  else if(path==='/api/pattern-insights')data=patternFixture(url.searchParams.get('days')==='90',url.searchParams.get('timezone_name')||'UTC');
  else if(path==='/api/v1/forecast')data={status:'insufficient_data',probability:null,clinically_validated:false};
  else if(['/api/insights','/api/attack-sessions/current','/api/support/recommendations'].includes(path))data=null;
  else if(['/api/wellness','/api/early-symptoms','/api/attack-sessions','/api/support/feedback','/api/account/consents'].includes(path))data=[];
  else return route.fulfill({status:404,json:{detail:'No manual accessibility fixture for this endpoint'}});
  return route.fulfill({json:data});
 });
}
