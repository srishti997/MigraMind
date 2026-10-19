import {test,expect} from '@playwright/test';
test('tracking forms, calendar and export use synthetic records',async({page})=>{
 await page.setViewportSize({width:390,height:844});
 let episodes:any[]=[{id:1,date:'2026-10-19',severity:3,duration:60,trigger:'Unknown',notes:'Synthetic first episode',started_at:null,ended_at:null,timezone_name:null,symptoms:[],medications:[]}];let wellness:any[]=[];let early:any[]=[];
 await page.route('**/api/**',async route=>{
  const request=route.request(),path=new URL(request.url()).pathname,method=request.method();
  let data:any=null;
  if(path==='/api/profile')data={name:'Alex',support:'Quiet',avoid:'Noise',communication:'Text'};
  if(path==='/api/contacts'||path==='/api/attack-sessions')data=[];
  for(const [resource,records] of [['episodes',episodes],['wellness',wellness],['early-symptoms',early]] as const){
   if(!path.startsWith('/api/'+resource))continue;
   const id=Number(path.split('/')[3]);
   if(method==='POST'){const p=request.postDataJSON();const row={...p,id:records.length+1};records.push(row);data=row}
   else if(method==='PUT'){const i=records.findIndex(r=>r.id===id);records[i]={...request.postDataJSON(),id};data=records[i]}
   else if(method==='DELETE'){records.splice(records.findIndex(r=>r.id===id),1);return route.fulfill({status:204})}
   else data=records;
  }
  if(path==='/api/export')data={schema_version:3,episodes,wellness,early_symptoms:early};
  return route.fulfill({json:data});
 });
 await page.goto('/');await page.getByRole('navigation').getByRole('button',{name:'Migraine diary',exact:true}).click();
 await page.getByRole('button',{name:'Log an episode',exact:true}).click();
 await page.getByLabel('Attack started',{exact:true}).fill('2026-10-19T10:30');
 await page.getByLabel('Pain severity',{exact:false}).fill('0');
 await page.getByText('Optional details · now or later',{exact:true}).click();
 await page.getByLabel('Attack ended',{exact:false}).fill('2026-10-19T11:30');
 await page.getByLabel('Symptoms · separate with commas').fill('Nausea, Fatigue');
 await page.getByRole('button',{name:'Add medication',exact:true}).click();
 await page.getByLabel('Medication name').fill('Synthetic medication');await page.getByLabel('Time taken').fill('2026-10-19T10:45');
 await page.getByRole('button',{name:'Save episode',exact:true}).click();await expect(page.getByRole('dialog')).not.toBeVisible();
 expect(episodes).toHaveLength(2);expect(episodes[1].severity).toBe(0);expect(episodes[1].started_at).toMatch(/Z$/);
 await page.getByRole('navigation').getByRole('button',{name:'Wellness',exact:true}).click();
 await page.getByRole('button',{name:'Daily check-in'}).click();await page.getByLabel('Check-in date').fill('2026-10-19');
 await page.getByLabel('Stress (0 low–10 high)').fill('0');await page.getByRole('button',{name:'Save check-in'}).click();
 await expect(page.getByRole('dialog')).not.toBeVisible();expect(wellness[0].stress).toBe(0);expect(wellness[0].sleep_hours).toBeNull();
 await page.getByRole('button',{name:'Edit check-in'}).click();await page.getByLabel('Sleep duration (hours)').fill('7.5');await page.getByRole('button',{name:'Save check-in'}).click();await expect(page.getByText('7.5 hours')).toBeVisible();
 await page.getByRole('navigation').getByRole('button',{name:'Early symptoms',exact:true}).click();await page.getByRole('button',{name:'Log early symptom'}).click();
 await page.getByLabel('Symptom',{exact:true}).fill('Synthetic yawning');await page.getByLabel('First noticed').fill('2026-10-19T09:30');await page.getByRole('button',{name:'Save observation'}).click();await expect(page.getByRole('heading',{name:'Synthetic yawning'})).toBeVisible();
 await page.getByRole('navigation').getByRole('button',{name:'Calendar',exact:true}).click();
 // Move to the recorded month, independent of the browser's current month.
 const target=new Date(2026,9,1),now=new Date();const months=(now.getFullYear()-target.getFullYear())*12+now.getMonth()-target.getMonth();
 for(let i=0;i<Math.abs(months);i++)await page.getByRole('button',{name:months>0?'Previous month':'Next month'}).click();
 await page.getByRole('button',{name:'2026-10-19: 2 episodes, 1 wellness check-ins',exact:true}).click();
 await expect(page.locator('.entries .entry')).toHaveCount(2);await expect(page.getByText('Wellness · 2026-10-19')).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'test-results/tracking-calendar-mobile.png',fullPage:true});
 await page.getByRole('navigation').getByRole('button',{name:'Settings',exact:true}).click();const downloadPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Export my records (JSON)'}).click();const download=await downloadPromise;expect(download.suggestedFilename()).toBe('migramind-records.json');
 await page.getByRole('navigation').getByRole('button',{name:'Early symptoms',exact:true}).click();page.once('dialog',d=>d.accept());await page.getByRole('button',{name:'Delete observation'}).click();await expect(page.getByText('No early symptom observations yet.')).toBeVisible();
});

test.describe('daylight saving timestamp preservation',()=>{
 test.use({timezoneId:'America/New_York'});
 test('editing notes preserves the later repeated-hour instant',async({page})=>{
  const original='2026-11-01T06:30:00+00:00'; // 01:30 EST, after the clock rolls back.
  let updated:any=null;
  const row={id:1,date:'2026-11-01',started_at:original,ended_at:null,timezone_name:'America/New_York',severity:4,duration:null,trigger:'Unknown',notes:'Synthetic DST entry',symptoms:[],medications:[]};
  await page.route('**/api/**',route=>{
   const path=new URL(route.request().url()).pathname;let data:any=[];
   if(path==='/api/profile')data={name:'Alex',support:'',avoid:'',communication:''};
   if(path==='/api/episodes')data=[row];
   if(path==='/api/episodes/1'){updated=route.request().postDataJSON();data={...updated,id:1}}
   if(path==='/api/insights')data=null;
   return route.fulfill({json:data});
  });
  await page.goto('/');await page.getByRole('navigation').getByRole('button',{name:'Migraine diary',exact:true}).click();await page.getByRole('button',{name:'Edit episode'}).click();
  await expect(page.getByLabel('Attack started',{exact:true})).toHaveValue('2026-11-01T01:30');
  await page.getByLabel('Your notes').fill('Synthetic updated note');await page.getByRole('button',{name:'Save episode'}).click();await expect(page.getByRole('dialog')).not.toBeVisible();
  expect(updated.started_at).toBe('2026-11-01T06:30:00.000Z');expect(updated.timezone_name).toBe('America/New_York');
 });
});
