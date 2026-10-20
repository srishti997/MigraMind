import {test,expect} from '@playwright/test';

test('real local API: two accounts stay isolated; logout, consent and deletion work',async({browser})=>{
 const a=await browser.newContext({viewport:{width:320,height:850}}),b=await browser.newContext({viewport:{width:390,height:850}});
 const password='Synthetic-test-password-123';const suffix=Date.now();
 const records=[{context:a,email:`synthetic-a-${suffix}@example.test`,name:'Synthetic Alpha'},{context:b,email:`synthetic-b-${suffix}@example.test`,name:'Synthetic Beta'}];
 try{
  for(const {context,email,name} of records){
   const page=await context.newPage();await page.goto('/');await page.getByRole('button',{name:'Create a new account'}).click();
   await page.getByLabel('Display name',{exact:true}).fill(name);await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Password',{exact:true}).fill(password);
   await page.getByRole('button',{name:'Create account',exact:true}).click();
   await expect(page.getByRole('heading',{name:`A gentler day, ${name}.`})).toBeVisible();
   const cookies=await context.cookies();expect(cookies.find(c=>c.name==='migramind_session')?.httpOnly).toBe(true);
  }
  let pa=a.pages()[0];const pb=b.pages()[0];
  // Regression: a restored session must render even when privacy policy blocks messaging.
  const renderErrors:string[]=[];
  pa.on('pageerror',error=>renderErrors.push(error.message));
  await pa.addInitScript(()=>{
   Object.defineProperty(window,'BroadcastChannel',{configurable:true,value:class {
    constructor(){throw new DOMException('Blocked by browser policy','SecurityError')}
   }});
  });
  await pa.reload();
  await expect(pa.getByRole('heading',{name:'A gentler day, Synthetic Alpha.'})).toBeVisible();
  for(const name of ['Migraine diary','Calendar','Insights','Overview']){
   await pa.getByRole('navigation').getByRole('button',{name,exact:true}).click();
   await expect(pa.locator('main h1')).toBeVisible();
   expect(await pa.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  }
  await pa.getByRole('button',{name:'Enter Attack Mode'}).click();
  await expect(pa.getByRole('button',{name:'Exit Attack Mode'})).toBeVisible();
  await expect(pa.getByRole('link',{name:/Emergency call/})).toHaveAttribute('href','tel:112');
  await pa.getByRole('button',{name:'Exit Attack Mode'}).click();
  expect(renderErrors).toEqual([]);
  await pa.close();
  pa=await a.newPage();await pa.goto('/');
  await expect(pa.getByRole('heading',{name:'A gentler day, Synthetic Alpha.'})).toBeVisible();
  await pa.getByRole('navigation').getByRole('button',{name:'Trusted contacts',exact:true}).click();
  await pa.getByRole('button',{name:'Add contact',exact:true}).click();
  await pa.getByLabel('Name',{exact:true}).fill('Synthetic Alpha contact');await pa.getByLabel('Relationship',{exact:true}).fill('Friend');await pa.getByLabel('Phone number',{exact:true}).fill('+12025550100');await pa.getByRole('button',{name:'Save contact',exact:true}).click();
  await expect(pa.getByText('Synthetic Alpha contact',{exact:true})).toBeVisible();
  const stale=await a.newPage();await stale.goto('/');
  await expect(stale.getByRole('heading',{name:'A gentler day, Synthetic Alpha.'})).toBeVisible();
  await stale.getByRole('navigation').getByRole('button',{name:'Trusted contacts',exact:true}).click();
  await expect(stale.getByText('Synthetic Alpha contact',{exact:true})).toBeVisible();
  await pb.getByRole('navigation').getByRole('button',{name:'Trusted contacts',exact:true}).click();await expect(pb.getByText('Synthetic Alpha contact',{exact:true})).toHaveCount(0);
  const auth=await (await a.request.get('/api/auth/session')).json();
  const onset=new Date(Date.now()-86400000).toISOString(),end=new Date(Date.now()-82800000).toISOString();
  const headers={Origin:'http://127.0.0.1:5173','X-CSRF-Token':auth.csrf_token};
  expect((await a.request.post('/api/episodes',{headers,data:{started_at:onset,ended_at:end,timezone_name:'UTC',severity:4}})).status()).toBe(201);
  expect((await a.request.post('/api/early-symptoms',{headers,data:{symptom:'Synthetic private pattern symptom',onset_at:new Date(Date.now()-90000000).toISOString(),timezone_name:'UTC'}})).status()).toBe(201);
  for(const [page,count] of [[pa,'1'],[pb,'0']] as const){
   await page.getByRole('navigation').getByRole('button',{name:'Insights',exact:true}).click();
   await expect(page.getByText('Timed episode onsets',{exact:true}).locator('..').locator('dd')).toHaveText(count);
  }
  await expect(pa.getByText('Synthetic private pattern symptom: 1 recorded observations',{exact:true})).toBeVisible();
  await expect(pb.getByText(/Synthetic private pattern symptom/)).toHaveCount(0);
  for(const page of [pa,pb]){
   await page.getByRole('navigation').getByRole('button',{name:'Account',exact:true}).click();
   await expect(page.getByRole('heading',{name:'Your account & privacy'})).toBeVisible();
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  }
  await pa.getByRole('checkbox').check();await pa.getByRole('button',{name:'Record consent (sharing disabled)'}).click();
  await expect(pa.getByText('Consent recorded. No information was shared.')).toBeVisible();await pa.getByRole('button',{name:'Revoke consent'}).click();await expect(pa.getByText(/Support card · Revoked/)).toBeVisible();
  await pa.getByRole('button',{name:'Sign out',exact:true}).click();
  await expect(stale.getByRole('button',{name:'Sign in',exact:true})).toBeVisible();
  await expect(stale.getByText('Synthetic Alpha contact',{exact:true})).toHaveCount(0);
  await pb.getByRole('button',{name:'Sign out',exact:true}).click();await expect(pb.getByRole('button',{name:'Sign in',exact:true})).toBeVisible();expect(await pb.getByRole('navigation').count()).toBe(0);
  await pb.getByLabel('Email',{exact:true}).fill(records[1].email);await pb.getByLabel('Password',{exact:true}).fill(password);await pb.getByRole('button',{name:'Sign in',exact:true}).click();await expect(pb.getByRole('heading',{name:'A gentler day, Synthetic Beta.'})).toBeVisible();
  await pb.getByRole('button',{name:'Enter Attack Mode'}).click();await expect(pb.getByRole('link',{name:/Emergency call/})).toHaveAttribute('href','tel:112');await pb.getByRole('button',{name:'Exit Attack Mode'}).click();
  await pb.getByRole('navigation').getByRole('button',{name:'Account',exact:true}).click();await pb.getByLabel('Current password',{exact:true}).fill(password);await pb.getByLabel('Type DELETE to confirm').fill('DELETE');await pb.getByRole('button',{name:'Permanently delete my account'}).click();await expect(pb.getByRole('button',{name:'Sign in',exact:true})).toBeVisible();
 }finally{
  for(const {context,email} of records){
   const session=await context.request.get('/api/auth/session');let state=await session.json();
   // A failure after sign-out must not leave the test-created account behind.
   if(!state.user){
    const login=await context.request.post('/api/auth/login',{headers:{Origin:'http://127.0.0.1:5173','X-CSRF-Token':state.csrf_token},data:{email,password}});
    if(login.status()===200)state=await login.json();else expect(login.status()).toBe(401);
   }
   if(state.user){const result=await context.request.delete('/api/account',{headers:{Origin:'http://127.0.0.1:5173','X-CSRF-Token':state.csrf_token},data:{password,confirmation:'DELETE'}});expect(result.status()).toBe(204)}
   await context.close();
  }
 }
});
