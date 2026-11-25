import {navigate} from './navigation';
import {test,expect,type Page} from '@playwright/test';
import {installManualAccessibilityFixture} from '../test-fixtures/manual-accessibility';

const START=Date.parse('2026-01-01T12:00:00Z'),MINUTE=60000;
async function open(page:Page){await page.goto('/');await expect(page.getByRole('heading',{name:'A gentler day, Review.'})).toBeVisible()}
function server(enabled=true,absolute=START+12*60*MINUTE){
 let now=START,last=START,signedOut=false;
 const attempts:number[]=[];
 function state(){return {user:signedOut?null:{id:1,email:'synthetic@example.test',display_name:'Review'},csrf_token:'synthetic-fixture-token',expires_at:new Date(absolute).toISOString(),...(enabled?{server_time:new Date(now).toISOString(),last_activity_at_ms:last,idle_expires_at:new Date(Math.min(last+30*MINUTE,absolute)).toISOString()}: {})}}
 return {attempts,state,setNow:(value:number)=>{now=value},install:async(page:Page,baseURL:string,failure?:number|'network')=>{
  await page.clock.install({time:new Date(START)});await installManualAccessibilityFixture(page,{baseURL});
  await page.route('**/api/auth/session',route=>route.fulfill({json:state()}));
  await page.route('**/api/auth/logout',route=>{signedOut=true;return route.fulfill({status:204})});
  await page.route('**/api/auth/activity',async route=>{
   expect(route.request().headers()['x-csrf-token']).toBe('synthetic-fixture-token');
   const expected=route.request().postDataJSON().expected_last_activity_at_ms;attempts.push(expected);
   if(failure==='network'){await route.abort();return}
   if(failure){await route.fulfill({status:failure,json:{detail:'Synthetic failure'}});return}
   if(expected!==last){await route.fulfill({status:409,json:{detail:'State changed'}});return}
   last=now;await route.fulfill({json:state()});
  });
 }};
}

test('disabled fixture never shows warnings or sends activity',async({page,baseURL})=>{
 const api=server(false);await api.install(page,baseURL!);await open(page);
 await expect(page.getByRole('heading',{name:'A gentler day, Review.'})).toBeVisible();await page.clock.fastForward(31*MINUTE);
 await expect(page.getByRole('button',{name:'Stay signed in'})).toHaveCount(0);expect(api.attempts).toHaveLength(0);
});

test('keyboard warning inside diary dialog preserves unsaved notes and restores focus on confirmed extension',async({page,baseURL})=>{
 const api=server();await api.install(page,baseURL!);await open(page);
 await page.getByRole('button',{name:'Log an episode',exact:true}).click();await page.getByRole('dialog').getByText(/Optional details/).click();const draft=page.locator('textarea[name="notes"]');await draft.fill('Synthetic unsaved diary');
 api.setNow(START+25*MINUTE);await page.clock.fastForward(25*MINUTE);
 const warning=page.getByRole('dialog').getByRole('region',{name:'Your session will end soon'});
 await expect(warning).toBeVisible();await expect(draft).toBeFocused();
 // The warning lives inside the existing modal trap, with native keyboard controls.
 await warning.getByRole('button',{name:'Stay signed in'}).focus();await page.keyboard.press('Enter');
 await expect(page.getByRole('button',{name:'Stay signed in'})).toHaveCount(0);await expect(draft).toHaveValue('Synthetic unsaved diary');await expect(draft).toBeFocused();
 expect(api.attempts).toEqual([START]);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 expect(await page.evaluate(()=>Object.values(localStorage).join('').includes('Synthetic unsaved diary'))).toBe(false);
});

test('idle expiry removes unsaved check-in content and latches sign-in through bootstrap',async({page,baseURL})=>{
 const api=server();await api.install(page,baseURL!);await open(page);
 await navigate(page,'Daily status');
 await page.getByText('Timing and optional observations',{exact:true}).click();const draft=page.getByLabel('Routine changes (optional)',{exact:true});await draft.fill('Synthetic unsaved check-in');
 await page.clock.fastForward(30*MINUTE);await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeVisible();
 await expect(draft).toHaveCount(0);await expect(page.getByRole('alert')).toContainText('Unsaved entries were discarded');await expect(page.getByRole('heading',{name:'Welcome back.'})).toBeFocused();
 await page.getByRole('button',{name:'Retry connection'}).click();await expect(page.getByRole('navigation')).toHaveCount(0);expect(api.attempts).toHaveLength(0);
});

for(const failure of [403,409,401,500,'network'] as const){
 test(`extension failure ${failure} is never reported as a successful renewal`,async({page,baseURL})=>{
  const api=server();await api.install(page,baseURL!,failure);await open(page);
  api.setNow(START+25*MINUTE);await page.clock.fastForward(25*MINUTE);await page.getByRole('button',{name:'Stay signed in'}).click();
  if(failure===401)await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeVisible();
  else{await expect(page.getByRole('alert')).toContainText('Your session was not extended');await expect(page.getByRole('button',{name:'Stay signed in'})).toBeVisible();await page.clock.fastForward(5*MINUTE);await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeVisible()}
  expect(api.attempts).toHaveLength(1);
 });
}

test('two tabs share only server-confirmed state; stale refresh is rejected then explicitly checked',async({page,context,baseURL})=>{
 const api=server();const other=await context.newPage();await api.install(page,baseURL!);await api.install(other,baseURL!);await open(page);await open(other);
 await expect(page.getByRole('heading',{name:'A gentler day, Review.'})).toBeVisible();await expect(other.getByRole('heading',{name:'A gentler day, Review.'})).toBeVisible();
 // Playwright's installed clock is shared by pages in this browser context.
 api.setNow(START+25*MINUTE);await page.clock.fastForward(25*MINUTE);
 await page.getByRole('button',{name:'Stay signed in'}).click();await expect(page.getByRole('button',{name:'Stay signed in'})).toHaveCount(0);
 await other.getByRole('button',{name:'Stay signed in'}).click();await expect(other.getByRole('alert')).toContainText('not extended');
 await other.getByRole('button',{name:'Check session status'}).click();await expect(other.getByRole('button',{name:'Stay signed in'})).toHaveCount(0);expect(api.attempts).toEqual([START,START]);
});

test('warning sign out uses the existing endpoint and does not save drafts',async({page,baseURL})=>{
 const api=server();await api.install(page,baseURL!);await open(page);await page.clock.fastForward(25*MINUTE);
 await page.getByRole('region',{name:'Your session will end soon'}).getByRole('button',{name:'Sign out',exact:true}).click();await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeVisible();expect(api.attempts).toHaveLength(0);
});

test('absolute deadline survives successful activity and reduced motion is respected',async({page,baseURL})=>{
 const api=server(true,START+30*MINUTE);await page.emulateMedia({reducedMotion:'reduce'});await api.install(page,baseURL!);await open(page);
 api.setNow(START+25*MINUTE);await page.clock.fastForward(25*MINUTE);await page.getByRole('button',{name:'Stay signed in'}).click();
 await expect(page.getByText('The fixed sign-in limit cannot be extended.')).toBeVisible();await expect(page.getByRole('button',{name:'Stay signed in'})).toBeVisible();
 expect(await page.getByRole('region',{name:'Your session will end soon'}).evaluate(node=>getComputedStyle(node).animationName)).toBe('none');
 await page.clock.fastForward(5*MINUTE);await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeVisible();
});
