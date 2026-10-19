import {test,expect} from '@playwright/test';
import {DEFAULT_PREFERENCES} from '../src/support';
test.beforeEach(async({page})=>{
 await page.addInitScript(()=>{
  (window as any).__locationCalls=0;(window as any).__messageCopies=[];
  Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async(text:string)=>{(window as any).__messageCopies.push(text)}}});
  Object.defineProperty(navigator,'geolocation',{configurable:true,value:{getCurrentPosition:(success:any)=>{(window as any).__locationCalls++;success({coords:{latitude:12.34,longitude:56.78,accuracy:75}})}}});
 });
 await page.route('**/api/**',route=>{
  const path=new URL(route.request().url()).pathname;
  let data:unknown=[];
  if(path==='/api/auth/session')data={user:{id:1,email:'synthetic@example.test',display_name:'Synthetic'},csrf_token:'synthetic-token'};
  if(path==='/api/contacts')data=[{id:1,name:'Synthetic Jamie',phone:'+12025550100',relationship:'Friend'},{id:2,name:'Synthetic Sam',phone:'+12025550101',relationship:'Friend'}];
  if(path==='/api/profile')data={name:'Synthetic',environment:'Synthetic preferred environment',support:'Ask before visiting',avoid:'Strong scents',communication:'Text first'};
  if(path==='/api/support/preferences')data={...DEFAULT_PREFERENCES,large_text:true,reduce_motion:true,help_message:'Please text before visiting.',emergency_number:'999'};
  if(path==='/api/attack-sessions/current'||path==='/api/support/recommendations'||path==='/api/insights')data=null;
  return route.fulfill({json:data});
 });
});

test('mobile SOS stays accessible; message/location require explicit actions and are never posted',async({page})=>{
 await page.setViewportSize({width:320,height:740});await page.emulateMedia({reducedMotion:'reduce'});
 const mutations:string[]=[];page.on('request',r=>{if(r.url().includes('/api/')&&r.method()!=='GET')mutations.push(r.url())});
 await page.goto('/');await page.getByLabel('Color theme').selectOption('dark');await page.getByRole('button',{name:'Enter Attack Mode'}).click();
 const sos=page.getByRole('button',{name:'SOS / Get help'}),emergency=page.getByRole('link',{name:/Emergency call/});
 await expect(sos).toBeInViewport();await expect(emergency).toBeInViewport();await expect(emergency).toHaveAttribute('href','tel:999');
 await sos.focus();await page.keyboard.press('Enter');await expect(page.getByRole('heading',{name:'Get help from someone you trust'})).toBeFocused();
 await page.getByLabel('Trusted contact').selectOption('2');await expect(page.getByRole('link',{name:'Call Synthetic Sam'})).toHaveAttribute('href','tel:+12025550101');
 expect(await page.evaluate(()=>(window as any).__locationCalls)).toBe(0);
 await page.getByRole('textbox',{name:'Help-request message',exact:true}).fill('Only my chosen message.');
 await page.getByText('Optional one-time location',{exact:false}).click();await expect(page.getByRole('button',{name:'Get my location once'})).toBeDisabled();
 await page.getByRole('checkbox').check();expect(await page.evaluate(()=>(window as any).__locationCalls)).toBe(0);
 await page.getByRole('button',{name:'Get my location once'}).click();await expect(page.getByLabel('Prepared message to copy or send')).toHaveValue(/Location: 12\.3400, 56\.7800/);
 await expect(page.getByRole('link',{name:'Open SMS composer'})).toHaveAttribute('href',/sms:\+12025550101[?&]body=/);
 await page.getByRole('button',{name:'Copy help message'}).click();expect(await page.evaluate(()=>(window as any).__messageCopies[0])).toContain('Only my chosen message.\nLocation:');
 await expect(sos).toBeInViewport();await expect(emergency).toBeInViewport();
 await page.getByRole('button',{name:'Remove location'}).click();await expect(page.getByRole('checkbox')).not.toBeChecked();
 await expect(page.getByLabel('Prepared message to copy or send')).toHaveValue('Only my chosen message.');
 expect(mutations).toEqual([]);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 for(const control of [sos,emergency,page.getByRole('button',{name:'Copy help message'})]){const box=await control.boundingBox();expect(box!.height).toBeGreaterThanOrEqual(60)}
 await page.screenshot({path:'test-results/sos-mobile.png',fullPage:true});
 await page.getByRole('button',{name:'View caregiver guide'}).click();await expect(page.getByText('Synthetic preferred environment',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Exit Attack Mode'}).click();await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
});

test('manual clipboard fallback and emergency access survive unavailable device APIs',async({page})=>{
 await page.addInitScript(()=>{Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new Error('denied')}}});Object.defineProperty(navigator,'geolocation',{configurable:true,value:undefined})});
 await page.goto('/');await page.getByRole('button',{name:'Enter Attack Mode'}).click();await page.getByRole('button',{name:'SOS / Get help'}).click();
 await page.getByRole('button',{name:'Copy help message'}).click();await expect(page.getByText(/Clipboard unavailable/)).toBeVisible();await expect(page.getByLabel('Prepared message to copy or send')).toBeFocused();
 await page.getByText('Optional one-time location',{exact:false}).click();await page.getByRole('checkbox').check();await page.getByRole('button',{name:'Get my location once'}).click();
 await expect(page.getByText('Location is unavailable. You can still call, copy or prepare your message.')).toBeVisible();
 await expect(page.getByRole('link',{name:/Emergency call/})).toHaveAttribute('href','tel:999');
});
