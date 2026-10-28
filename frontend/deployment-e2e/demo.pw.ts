import {test,expect} from '@playwright/test';

test('built demo refuses a backend that does not attest synthetic mode',async({page})=>{
 await page.route('**/api/auth/session',route=>route.fulfill({json:{user:{id:1,email:'synthetic@example.test',display_name:'Synthetic mismatch'},csrf_token:'synthetic-token',demo_mode:false}}));
 await page.goto('/');
 await expect(page.getByRole('note')).toContainText('Do not enter real health information');
 await expect(page.getByRole('alert')).toContainText('Could not connect');
 await expect(page.getByRole('heading',{name:/A gentler day/})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Create a new account'})).toHaveCount(0);
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
 await page.getByRole('button',{name:'Save daily check-in'}).click();
 await expect(page.getByRole('alert')).toContainText('read-only');
 expect(writes).toEqual([]);
 const request={scope:'local_research_preparation',confirmed:false,timezone_name:'UTC',days:30};
 expect((await context.request.post('/api/v1/research-export',{headers,data:request})).status()).toBe(422);
 const exported=await context.request.post('/api/v1/research-export',{headers,data:{...request,confirmed:true}});
 expect(exported.status()).toBe(200);expect((await exported.json()).synthetic_demo).toBe(true);
 const after=await (await context.request.get('/api/daily-checkins',{headers})).json();expect(after).toEqual(before);
 expect((await context.request.post('/api/auth/logout',{headers})).status()).toBe(204);
 expect((await context.request.get('/api/export',{headers})).status()).toBe(401);
});
