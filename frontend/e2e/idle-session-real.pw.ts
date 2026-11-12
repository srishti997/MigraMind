import {test,expect} from '@playwright/test';

// Only a dedicated temporary backend started by the isolated runner is supported.
test.skip(!process.env.MIGRAMIND_IDLE_TEST_BACKEND||!process.env.MIGRAMIND_IDLE_TEST_TOKEN,'Requires the explicit synthetic idle backend fixture');
const password='Synthetic-idle-password-123';
async function control(request:any,path:string,minutes?:number){
 const backend=process.env.MIGRAMIND_IDLE_TEST_BACKEND!;
 if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(backend))throw new Error('Loopback fixture required');
 const options={headers:{'X-Idle-Test-Token':process.env.MIGRAMIND_IDLE_TEST_TOKEN!},...(minutes===undefined?{}:{data:{minutes}})};
 const response=path==='info'?await request.get(backend+'/__idle_test__/info',options):await request.post(backend+'/__idle_test__/'+path,options);
 expect(response.ok()).toBe(true);return response.json();
}
async function register(page:any,request:any){
 if(process.env.MIGRAMIND_IDLE_DIAGNOSTIC==='1')page.on('response',(response:any)=>{const path=new URL(response.url()).pathname;if(path.startsWith('/api/'))console.log('Synthetic HTTP',response.status(),path)});
 const info=await control(request,'info');expect(info.fixture).toBe('synthetic-idle-v1');
 await page.clock.install({time:new Date(info.server_time)});
 await page.addInitScript(()=>document.addEventListener('click',event=>{const link=event.target instanceof Element?event.target.closest<HTMLAnchorElement>('a[href]'):null;if(link&&/^(tel:|sms:)/.test(link.href))event.preventDefault()},true));
 const frontend=process.env.MIGRAMIND_E2E_BASE_URL!;
 if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(frontend))throw new Error('Explicit loopback frontend required');
 await page.route('**/*',route=>new URL(route.request().url()).origin===frontend?route.continue():route.abort());
 await page.goto('/');await page.getByRole('button',{name:'Create a new account'}).click();
 const email=`synthetic-idle-${crypto.randomUUID()}@example.test`;
 await page.getByLabel('Display name',{exact:true}).fill('Synthetic Idle');await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Password',{exact:true}).fill(password);
 await page.getByRole('button',{name:'Create account',exact:true}).click();await expect(page.getByRole('heading',{name:'A gentler day, Synthetic Idle.'})).toBeVisible();return email;
}

test('real temporary API: deliberate extension then remote global revocation removes private UI',async({page,request,browser,baseURL})=>{
 const email=await register(page,request);
 await page.getByRole('navigation').getByRole('button',{name:'Daily status',exact:true}).click();
 await page.getByText('Timing and optional observations',{exact:true}).click();
 const draft=page.getByLabel('Routine changes (optional)',{exact:true});await draft.fill('Synthetic unsaved real-API check-in');
 await control(request,'advance',25);await page.clock.fastForward(25*60000);
 await expect(page.getByRole('button',{name:'Stay signed in'})).toBeVisible();
 const response=page.waitForResponse(response=>response.url().endsWith('/api/auth/activity'));
 await page.getByRole('button',{name:'Stay signed in'}).click();expect((await response).status()).toBe(200);
 await expect(page.getByRole('button',{name:'Stay signed in'})).toHaveCount(0);await expect(draft).toHaveValue('Synthetic unsaved real-API check-in');
 const other=await browser.newContext();
 try{
  const anonymous=await(await other.request.get(baseURL+'/api/auth/session')).json();
  const login=await other.request.post(baseURL+'/api/auth/login',{headers:{Origin:baseURL!,'X-CSRF-Token':anonymous.csrf_token},data:{email,password}});expect(login.status()).toBe(200);
  const auth=await login.json();expect((await other.request.post(baseURL+'/api/auth/logout-all',{headers:{Origin:baseURL!,'X-CSRF-Token':auth.csrf_token},data:{password}})).status()).toBe(204);
  await page.getByRole('navigation').getByRole('button',{name:'Account',exact:true}).click();
  await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeVisible();await expect(draft).toHaveCount(0);
 }finally{await other.close()}
});

test('real temporary API: expiry discards an unsaved diary and stale credentials cannot refresh',async({page,request})=>{
 await register(page,request);
 await page.getByRole('button',{name:'Log an episode',exact:true}).click();
 await page.getByRole('dialog').getByText(/Optional details/).click();
 const draft=page.locator('textarea[name="notes"]');await draft.fill('Synthetic unsaved real-API diary');
 const session=await(await page.request.get('/api/auth/session')).json();
 await control(request,'advance',25);await page.clock.fastForward(25*60000);
 await expect(page.getByRole('dialog').getByRole('button',{name:'Stay signed in'})).toBeVisible();
 await control(request,'advance',6);await page.clock.fastForward(6*60000);
 await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeVisible();await expect(draft).toHaveCount(0);
 const response=await page.request.post('/api/auth/activity',{headers:{Origin:new URL(page.url()).origin,'X-CSRF-Token':session.csrf_token},data:{expected_last_activity_at_ms:session.last_activity_at_ms}});
 expect(response.status()).toBe(401);
 await page.getByRole('button',{name:'Retry connection'}).click();await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeVisible();
});
