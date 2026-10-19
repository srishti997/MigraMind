import {test,expect} from '@playwright/test';
const contacts=[{id:1,name:'Jamie Demo',relationship:'Partner',phone:'+919999900001'},{id:2,name:'Sam Demo',relationship:'Friend',phone:'+919999900002'}];
const profile={name:'Alex',support:'Quiet space. '+ 'Synthetic support preference. '.repeat(20),avoid:'Bright light',communication:'Please text first.'};
test.beforeEach(async({page})=>{
 await page.route('**/api/**',route=>{
  const path=new URL(route.request().url()).pathname;
  let data=path.endsWith('/contacts')?contacts:path.endsWith('/profile')?profile:path.endsWith('/episodes')?[]:path.endsWith('/v1/forecast')?{status:'insufficient_data',probability:null,clinically_validated:false}:null;
  if(path==='/api/auth/session')data={user:{id:1,email:'synthetic@example.test',display_name:'Alex'},csrf_token:'synthetic-test-csrf'};
  return route.fulfill({json:data});
 });
});
test('responsive pages and attack assistance avoid horizontal overflow',async({page})=>{
 for(const width of [320,390,768,1280]){
  await page.setViewportSize({width,height:850});await page.goto('/');await expect(page.getByRole('heading',{name:'A gentler day, Alex.'})).toBeVisible();await expect(page.getByRole('heading',{name:/AI Insights/})).toBeVisible();await expect(page.getByText('Insufficient verified data for forecasting.')).toBeVisible();
  for(const name of ['Overview','Migraine diary','Calendar','Wellness','Early symptoms','Trusted contacts','Caregiver profile','Support feedback','Settings']){
   await page.getByRole('navigation').getByRole('button',{name,exact:true}).click();
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${name} at ${width}px`).toBe(true);
  }
  await page.getByRole('button',{name:'Enter Attack Mode'}).click();
  await expect(page.getByRole('link',{name:/Emergency call/})).toBeInViewport();
  await expect(page.getByRole('button',{name:'Exit Attack Mode'})).toBeInViewport();
  await page.getByText('My support card',{exact:true}).click();
  await expect(page.getByText('Please text first.',{exact:true})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`Attack Mode at ${width}px`).toBe(true);
  for(const name of ['Exit Attack Mode','Call contact','Prepare SMS','Emergency call · 112 (India)']){
   const control=page.getByRole(name.includes('Mode')?'button':'link',{name,exact:true});
   const box=await control.boundingBox();expect(box!.height).toBeGreaterThanOrEqual(60);
  }
  if(width===390)await page.screenshot({path:'test-results/attack-mobile.png',fullPage:true});
 }
});
test('keyboard focus, reduced motion and safe device links',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});await page.goto('/');
 await page.getByLabel('Color theme').selectOption('dark');
 const enter=page.getByRole('button',{name:'Enter Attack Mode'});await enter.focus();await page.keyboard.press('Enter');
 await expect(page.getByRole('heading',{name:'One thing at a time.'})).toBeFocused();
 await page.keyboard.press('Tab');await expect(page.getByRole('button',{name:'Exit Attack Mode'})).toBeFocused();
 await page.getByLabel('Trusted contact').selectOption('2');
 await expect(page.getByRole('link',{name:'Call contact',exact:true})).toHaveAttribute('href','tel:+919999900002');
 await expect(page.getByRole('link',{name:'Prepare SMS'})).toHaveAttribute('href',/^sms:\+919999900002[?&]body=/);
 await expect(page.getByRole('link',{name:/Emergency call/})).toHaveAttribute('href','tel:112');
 expect(await page.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches)).toBe(true);
 const motion=await page.getByRole('button',{name:'Exit Attack Mode'}).evaluate(el=>({animation:getComputedStyle(el).animationName,transition:getComputedStyle(el).transitionDuration}));
 expect(motion).toEqual({animation:'none',transition:'0s'});
 await page.getByRole('button',{name:'Log an episode'}).click();
 await expect(page.getByRole('dialog')).toBeVisible();await expect(page.locator('html')).toHaveAttribute('data-theme','attack');
 await page.getByRole('button',{name:'Save episode'}).focus();await page.keyboard.press('Tab');await expect(page.getByRole('button',{name:'Close dialog'})).toBeFocused();
 await page.keyboard.press('Escape');await expect(page.getByRole('button',{name:'Log an episode'})).toBeFocused();
 await page.getByRole('button',{name:'Exit Attack Mode'}).click();await expect(enter).toBeFocused();await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
});
