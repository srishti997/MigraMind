import {test,expect} from '@playwright/test';

test('built demo refuses a backend that does not attest synthetic mode',async({page})=>{
 await page.route('**/api/auth/session',route=>route.fulfill({json:{user:{id:1,email:'synthetic@example.test',display_name:'Synthetic mismatch'},csrf_token:'synthetic-token',demo_mode:false}}));
 await page.goto('/');
 await expect(page.getByRole('note')).toContainText('Do not enter real health information');
 await expect(page.getByRole('alert')).toContainText('Could not connect');
 await expect(page.getByRole('heading',{name:/A gentler day/})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Create a new account'})).toHaveCount(0);
});

test('read-only screens, keyboard destinations and recoverable failures stay usable',async({page})=>{
 let failSummary=true,failPatterns=true;
 await page.route('**/api/insights?**',route=>failSummary?route.fulfill({status:503,json:{detail:'Synthetic summary outage'}}):route.continue());
 await page.route('**/api/pattern-insights?**',route=>failPatterns?route.fulfill({status:503,json:{detail:'Synthetic pattern outage'}}):route.continue());
 await page.goto('/');
 await page.getByLabel('Password',{exact:true}).fill(process.env.MIGRAMIND_DEMO_PASSWORD!);
 await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await expect(page.getByRole('button',{name:'Retry insights',exact:true})).toBeVisible();
 const writes:string[]=[];
 page.on('request',r=>{if(['POST','PUT','PATCH','DELETE'].includes(r.method()))writes.push(new URL(r.url()).pathname)});
 await page.getByRole('button',{name:'Enter Attack Mode',exact:true}).click();
 await expect(page.getByRole('link',{name:/Emergency call/})).toHaveAttribute('href','tel:112');
 await expect(page.getByRole('button',{name:'Start attack session',exact:true})).toBeDisabled();
 await page.getByText('My support card',{exact:true}).click();
 await expect(page.getByText('Please keep the room quiet and dim. Ask before calling or visiting.',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Exit Attack Mode',exact:true}).click();
 failSummary=false;await page.getByRole('button',{name:'Retry insights',exact:true}).click();
 await expect(page.getByRole('button',{name:'Retry insights',exact:true})).toHaveCount(0);
 await expect(page.getByText('Loading your space…',{exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:'Explore descriptive insights',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Insights',exact:true})).toBeFocused();
 await expect(page.getByRole('button',{name:'Retry pattern insights',exact:true})).toBeVisible();
 failPatterns=false;await page.getByRole('button',{name:'Retry pattern insights',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Not enough information yet',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Review research features',exact:true}).click();
 await expect(page.getByRole('heading',{name:'AI Insights — In Development',exact:true})).toBeFocused();
 for(const key of ['Enter','Space']){
  await page.getByRole('button',{name:'Explore descriptive insights',exact:true}).focus();
  await page.keyboard.press(key);
  await expect(page.getByRole('heading',{name:'Insights',exact:true})).toBeFocused();
  await page.getByRole('button',{name:'Review research features',exact:true}).focus();
  await page.keyboard.press(key);
  const researchHeading=page.getByRole('heading',{name:'AI Insights — In Development',exact:true});
  await expect(researchHeading).toBeFocused();
  await expect(researchHeading).toBeInViewport();
 }
 await page.getByRole('button',{name:'Review research features',exact:true}).focus();
 await page.keyboard.press('Enter'); // Revisit while already on Overview.
 await expect(page.getByRole('heading',{name:'AI Insights — In Development',exact:true})).toBeFocused();
 await page.getByRole('navigation').getByRole('button',{name:'Caregiver profile',exact:true}).click();
 await expect(page.getByLabel('What helps me feel supported')).toBeDisabled();
 await expect(page.getByRole('button',{name:'Save my preferences',exact:true})).toBeDisabled();
 await expect(page.getByRole('button',{name:'Save support choices',exact:true})).toBeDisabled();
 await expect(page.getByRole('button',{name:'Reset action and accessibility choices',exact:true})).toBeDisabled();
 for(const name of ['Save my preferences','Save support choices','Reset action and accessibility choices']){
  await page.getByRole('button',{name,exact:true}).evaluate(element=>(element as HTMLButtonElement).click());
 }
 const screens=['Overview','Daily status','Migraine diary','Calendar','Insights','Wellness','Early symptoms','Trusted contacts','Caregiver profile','Support feedback','Settings','Account'];
 for(const width of [320,768,1280]){
  await page.setViewportSize({width,height:850});
  for(const screen of screens){
   await page.getByRole('navigation').getByRole('button',{name:screen,exact:true}).click();
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${screen} at ${width}px`).toBe(true);
  }
 }
 await expect(page.getByRole('button',{name:'Save account',exact:true})).toHaveCount(0);
 await expect(page.getByLabel('Current password',{exact:true})).toHaveCount(0);
 expect(writes).toEqual([]);
 await page.getByRole('button',{name:'Sign out',exact:true}).click();
 await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeVisible();
});

test('built synthetic demonstration is clearly labelled and rejects health ingestion',async({page,context,baseURL})=>{
 await page.goto('/');
 await expect(page.getByRole('note')).toContainText('Synthetic demonstration');
 await expect(page.getByRole('button',{name:'Create a new account'})).toHaveCount(0);
 await expect(page.getByLabel('Email',{exact:true})).toHaveValue('demo@synthetic.example.test');
 await page.getByLabel('Password',{exact:true}).fill(process.env.MIGRAMIND_DEMO_PASSWORD!);
 await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await expect(page.getByRole('heading',{name:/A gentler day/})).toBeVisible();
 await expect(page.getByRole('note')).toContainText('read-only');
 await expect(page.getByRole('heading',{name:'Explore the synthetic demonstration'})).toBeVisible();
 await page.getByRole('button',{name:'Show example calendar'}).click();
 await expect(page.getByRole('heading',{name:'January 2026',exact:true})).toBeVisible();
 await expect(page.getByText('SYNTHETIC demonstration fixture; not a clinical observation.',{exact:true})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 expect((await context.request.get('/api/ready')).status()).toBe(200);
 const state=await (await context.request.get('/api/auth/session')).json();
 const headers={Origin:new URL(baseURL!).origin,'X-CSRF-Token':state.csrf_token};
 const before=await (await context.request.get('/api/daily-checkins',{headers})).json();
 expect(before).toHaveLength(3);
 expect((await context.request.post('/api/episodes',{headers,data:{notes:'Synthetic blocked test input'}})).status()).toBe(403);
 expect((await context.request.post('/api/auth/register',{headers,data:{}})).status()).toBe(403);
 await page.getByRole('navigation').getByRole('button',{name:'Daily status',exact:true}).click();
 const writes:string[]=[];page.on('request',r=>{if(r.method()==='POST'&&r.url().includes('daily-checkins'))writes.push(r.url())});
 await expect(page.getByText('Read-only demonstration: explore the three January examples and their history below. Creating, correcting and deleting reports is unavailable.')).toBeVisible();
 await expect(page.getByRole('button',{name:'Save daily check-in'})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Edit 2026-01-03',exact:true})).toHaveCount(0);
 await expect(page.getByLabel('Report date')).toHaveCount(0);
 expect(writes).toEqual([]);
 await page.getByRole('button',{name:'History 2026-01-03',exact:true}).click();
 await expect(page.getByRole('region',{name:'History 2026-01-03',exact:true})).toContainText('Private revision history');
 await page.getByRole('button',{name:'Review research features',exact:true}).click();
 await expect(page.getByRole('heading',{name:'AI Insights — In Development',exact:true})).toBeFocused();
 await expect(page.getByText('Insufficient verified data for forecasting.',{exact:true})).toBeVisible();
 await page.getByText('Research data quality',{exact:true}).click();
 await page.getByRole('button',{name:'Review research quality',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Not ready for forecasting research',exact:true})).toBeVisible();
 const download=page.getByRole('button',{name:'Download research-preparation JSON',exact:true});
 await expect(download).toBeDisabled();
 await page.getByRole('checkbox',{name:'I consent to this local download of my numeric observations and correction history.'}).check();
 const [file]=await Promise.all([page.waitForEvent('download'),download.click()]);
 expect(file.suggestedFilename()).toBe('migramind-research-preparation.json');
 await expect(page.getByText('Downloaded to this device. Store the private file securely.',{exact:true})).toBeVisible();
 const request={scope:'local_research_preparation',confirmed:false,timezone_name:'UTC',days:30};
 expect((await context.request.post('/api/v1/research-export',{headers,data:request})).status()).toBe(422);
 const exported=await context.request.post('/api/v1/research-export',{headers,data:{...request,confirmed:true}});
 expect(exported.status()).toBe(200);expect((await exported.json()).synthetic_demo).toBe(true);
 const after=await (await context.request.get('/api/daily-checkins',{headers})).json();expect(after).toEqual(before);
 await page.getByRole('navigation').getByRole('button',{name:'Account',exact:true}).click();
 await expect(page.getByRole('button',{name:'Save account',exact:true})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Permanently delete my account',exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:'Sign out',exact:true}).click();
 await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeVisible();
 await expect(page.getByRole('navigation')).toHaveCount(0);
 expect((await context.request.get('/api/export',{headers})).status()).toBe(401);
});
