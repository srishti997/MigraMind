import {test,expect} from '@playwright/test';
import {DEFAULT_PREFERENCES,fallbackRecommendations} from '../src/support';
const contacts=[{id:1,name:'Jamie demo',relationship:'Friend',phone:'+12025550101'},{id:2,name:'Sam demo',relationship:'Partner',phone:'+12025550102'}];
const profile={name:'Alex',support:'Quiet, please',avoid:'Strong scents',communication:'Text me first'};
test.beforeEach(async({page})=>{
 let preferences={...DEFAULT_PREFERENCES};let sessions:any[]=[];let feedback:any[]=[];let nextSession=1;
 await page.addInitScript(()=>{
  (window as any).__supportShares=[];(window as any).__supportCopies=[];
  Object.defineProperty(navigator,'share',{configurable:true,value:async(value:unknown)=>{(window as any).__supportShares.push(value)}});
  Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async(value:string)=>{(window as any).__supportCopies.push(value)}}});
 });
 await page.route('**/api/**',async route=>{
  const request=route.request(),path=new URL(request.url()).pathname,method=request.method();let data:any=null;
  if(path==='/api/contacts')data=contacts;if(path==='/api/profile')data=profile;
  if(['/api/episodes','/api/wellness','/api/early-symptoms'].includes(path))data=[];
  if(path==='/api/support/preferences'){if(method==='PUT')preferences=request.postDataJSON();data=preferences;}
  if(path==='/api/support/preferences/reset'){preferences={...DEFAULT_PREFERENCES};data=preferences;}
  if(path==='/api/support/recommendations')data={algorithm_version:'explicit-feedback-v1',actions:fallbackRecommendations(preferences,contacts),recommended_action:null};
  if(path==='/api/attack-sessions')data=sessions;
  if(path==='/api/attack-sessions/current')data=sessions[0]||null;
  if(path==='/api/attack-sessions/start'){const row={id:nextSession++,started_at:'2026-10-19T12:00:00Z',ended_at:null};sessions.unshift(row);data=row;}
  if(/\/attack-sessions\/\d+\/end$/.test(path)){const id=Number(path.split('/')[3]);const row=sessions.find(s=>s.id===id);row.ended_at='2026-10-19T13:00:00Z';data=row;}
  if(path==='/api/support/feedback'){if(method==='POST')feedback.unshift({id:feedback.length+1,...request.postDataJSON(),created_at:'2026-10-19T14:00:00Z'});data=method==='POST'?feedback[0]:feedback;}
  if(method==='DELETE'&&path.startsWith('/api/support/feedback/')){feedback=feedback.filter(f=>f.id!==Number(path.split('/')[4]));return route.fulfill({status:204})}
  return route.fulfill({json:data});
 });
});
test('saved support choices, active-session suppression and optional feedback lifecycle',async({page})=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/');
 await page.getByRole('navigation').getByRole('button',{name:'Caregiver profile',exact:true}).click();
 await page.getByLabel('Preferred trusted contact').selectOption('2');await page.getByLabel('Preferred contact method').selectOption('sms');
 await page.getByLabel('First support action').selectOption('prepare_sms');await page.getByLabel('Use my optional feedback to rank other support actions').check();
 await page.getByRole('button',{name:'Save support choices'}).click();await expect(page.getByText('Support choices saved. Nothing was shared.')).toBeVisible();
 await page.reload();await page.getByRole('button',{name:'Enter Attack Mode'}).click();
 await expect(page.getByLabel('Trusted contact')).toHaveValue('2');await expect(page.locator('.recommended-action').getByRole('link',{name:'Prepare SMS'})).toHaveAttribute('href',/^sms:\+12025550102[?&]body=/);
 await expect(page.getByRole('link',{name:/Emergency call/})).toBeInViewport();
 await page.getByRole('button',{name:'Start attack session'}).click();await expect(page.getByText(/Session active/)).toBeVisible();
 await expect(page.getByRole('button',{name:'Review support feedback'})).toHaveCount(0);
 await page.getByRole('button',{name:'Exit Attack Mode'}).click();await page.getByRole('navigation').getByRole('button',{name:'Support feedback',exact:true}).click();
 await expect(page.getByText('Feedback can wait until your active attack session has ended.')).toBeVisible();
 await page.getByRole('button',{name:'Enter Attack Mode'}).click();await page.getByRole('button',{name:'Open my support card'}).click();
 await expect(page.getByText('Quiet, please',{exact:true})).toBeVisible();
 await expect(page.getByRole('link',{name:/Emergency call/})).toBeInViewport();
 await page.getByRole('button',{name:'End attack session'}).click();await page.getByRole('button',{name:'Review support feedback'}).click();
 await expect(page.getByLabel('Ended attack session')).toHaveValue('1');await expect(page.getByLabel('Support action you used')).toHaveValue('support_card');
 await page.getByLabel('Was this support action helpful?').selectOption('yes');await page.getByRole('button',{name:'Save optional feedback'}).click();await expect(page.getByText('Feedback saved. You can delete it at any time.')).toBeVisible();
 page.once('dialog',d=>d.accept());await page.getByRole('button',{name:'Delete feedback 1'}).click();await expect(page.getByText('No feedback saved.')).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
test('sharing is reviewed and user initiated; large-text layout retains emergency access',async({page})=>{
 await page.setViewportSize({width:320,height:740});await page.emulateMedia({reducedMotion:'reduce'});await page.goto('/');
 await page.getByRole('navigation').getByRole('button',{name:'Caregiver profile',exact:true}).click();
 await page.getByLabel('Larger text').check();await page.getByLabel('Reduce motion',{exact:true}).check();await page.getByLabel('Simplified Attack Mode').check();
 await page.getByRole('button',{name:'Save support choices'}).click();await expect(page.locator('html')).toHaveAttribute('data-large-text','true');
 await page.getByRole('button',{name:'Review card for sharing'}).click();
 expect(await page.evaluate(()=>(window as any).__supportShares)).toEqual([]);expect(await page.evaluate(()=>(window as any).__supportCopies)).toEqual([]);
 await page.getByLabel('Card text to share').fill('Only this approved synthetic text');await page.getByRole('button',{name:'Copy card text'}).click();
 expect(await page.evaluate(()=>(window as any).__supportCopies)).toEqual(['Only this approved synthetic text']);
 await page.getByRole('button',{name:'Open device share…'}).click();expect(await page.evaluate(()=>(window as any).__supportShares[0].text)).toBe('Only this approved synthetic text');
 await page.getByRole('button',{name:'Enter Attack Mode'}).click();await expect(page.getByRole('link',{name:/Emergency call/})).toBeInViewport();
 await expect(page.getByRole('button',{name:'Exit Attack Mode'})).toBeInViewport();
 await expect(page.getByRole('heading',{name:'One thing at a time.'})).toBeFocused();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 const motion=await page.getByRole('button',{name:'Exit Attack Mode'}).evaluate(el=>({animation:getComputedStyle(el).animationName,transition:getComputedStyle(el).transitionDuration}));expect(motion).toEqual({animation:'none',transition:'0s'});
 await page.screenshot({path:'test-results/personalized-support-mobile.png',fullPage:true});
});
