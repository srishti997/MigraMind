import {test,expect} from '@playwright/test';

test.beforeEach(async({page})=>{
 await page.route('**/api/**',route=>{
  const path=new URL(route.request().url()).pathname;
  let data:unknown=[];
  if(path==='/api/auth/session')data={user:{id:1,email:'synthetic@example.test',display_name:'Review'},csrf_token:'synthetic-csrf'};
  if(path==='/api/profile')data={name:'Review',support:'Synthetic quiet preference',avoid:'Noise',communication:'Text'};
  if(path==='/api/support/preferences')data={};
  if(['/api/insights','/api/pattern-insights','/api/support/recommendations','/api/attack-sessions/current'].includes(path))data=null;
  return route.fulfill({json:data});
 });
});

for(const width of [320,390,1280]){
 test(`login emergency link retains a large, keyboard-accessible target at ${width}px`,async({page})=>{
  await page.setViewportSize({width,height:850});
  let demoMode=false;
  await page.route('**/api/auth/session',route=>route.fulfill({json:{user:null,csrf_token:'synthetic-csrf',demo_mode:demoMode}}));
  // Observe keyboard activation without requesting a real telephone handler.
  await page.addInitScript(()=>{
   (window as any).__emergencyActivations=0;
   document.addEventListener('click',event=>{
    if(event.target instanceof Element&&event.target.closest('a[href="tel:112"]')){
     event.preventDefault();(window as any).__emergencyActivations++;
    }
   },true);
  });
  for(const demo of [false,true])for(const theme of ['warm','dark']){
   demoMode=demo;
   await page.goto('/');
   await page.evaluate(value=>localStorage.setItem('migramind-theme',value),theme);
   await page.reload();
   await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeVisible();
   const link=page.getByRole('link',{name:'Emergency call · 112 (India)',exact:true});
   await expect(link).toHaveAttribute('href','tel:112');
   expect(await link.evaluate(element=>element.tagName)).toBe('A');
   expect((await link.boundingBox())!.height).toBeGreaterThanOrEqual(48);
   for(let step=0;step<12&&!await link.evaluate(element=>element===document.activeElement);step++)await page.keyboard.press('Tab');
   await expect(link).toBeFocused();await expect(link).toBeInViewport();
   await expect(link).toHaveCSS('outline-style','solid');await expect(link).toHaveCSS('outline-width','3px');
   const url=page.url();await page.keyboard.press('Enter');
   expect(await page.evaluate(()=>(window as any).__emergencyActivations)).toBe(1);
   expect(page.url()).toBe(url);
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  }
 });
}

for(const [destination,action] of [
 ['Trusted contacts','Set up a trusted contact'],
 ['Caregiver profile','Review or edit outside Attack Mode'],
]){
 test(`Attack Mode hands focus to ${destination}, including repeated navigation`,async({page})=>{
  const writes:string[]=[];
  page.on('request',request=>{if(['POST','PUT','PATCH','DELETE'].includes(request.method()))writes.push(request.url())});
  await page.goto('/');await expect(page.getByRole('heading',{name:'A gentler day, Review.'})).toBeVisible();
  for(let visit=0;visit<2;visit++){
   await page.getByRole('button',{name:'Enter Attack Mode',exact:true}).focus();await page.keyboard.press('Enter');
   await expect(page.getByRole('heading',{name:'One thing at a time.'})).toBeFocused();
   if(destination==='Caregiver profile'){
    await page.getByText('My support card',{exact:true}).focus();await page.keyboard.press('Enter');
   }
   const navigate=page.getByRole('button',{name:action,exact:true});await navigate.focus();await page.keyboard.press('Enter');
   const heading=page.getByRole('heading',{name:destination,exact:true});await expect(heading).toBeFocused();
   await page.keyboard.press('Tab');await expect(heading).not.toBeFocused();
  }
  await page.getByRole('button',{name:'Enter Attack Mode',exact:true}).focus();await page.keyboard.press('Enter');
  await page.getByRole('button',{name:'Exit Attack Mode',exact:true}).focus();await page.keyboard.press('Enter');
  await expect(page.getByRole('button',{name:'Enter Attack Mode',exact:true})).toBeFocused();
  if(destination==='Trusted contacts'){
   const add=page.getByRole('button',{name:'Add contact',exact:true});await add.click();await expect(page.getByRole('dialog')).toBeVisible();
   await page.keyboard.press('Escape');await expect(add).toBeFocused();
  }
  expect(writes).toEqual([]);
 });
}
