import {navigate} from './navigation';
import {expect} from '@playwright/test';
import {test} from './syntheticCleanup';

test('synthetic daily reports: keyboard check-in, corrections, private history, tombstones and quality',async({browser,syntheticCleanup})=>{
 const a=await browser.newContext({viewport:{width:320,height:850},timezoneId:'UTC'});
 const b=await browser.newContext({viewport:{width:390,height:850},timezoneId:'UTC'});
 const password='Synthetic-sprint9-password-123';const suffix=Date.now();
 const accounts:{context:typeof a,token:string}[]=[];
 const tracked=[a,b].map((context,index)=>syntheticCleanup.track(context,`synthetic-s9-${suffix}-${index}@example.test`,password));
  for(const [index,context] of [a,b].entries()){
   const bootstrap=await (await context.request.get('/api/auth/session')).json();
   tracked[index].attempted=true;
   const response=await context.request.post('/api/auth/register',{headers:{Origin:'http://127.0.0.1:5173','X-CSRF-Token':bootstrap.csrf_token},data:{email:`synthetic-s9-${suffix}-${index}@example.test`,display_name:`Synthetic S9 ${index}`,password}});
   expect(response.status()).toBe(201);accounts.push({context,token:(await response.json()).csrf_token});
  }
  const page=await a.newPage();const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('/');
  await navigate(page,'Daily status');
  await expect(page.getByText('No daily reports yet.',{exact:false})).toBeVisible();
  await page.getByLabel('Migraine status').selectOption('no_migraine');
  const save=page.getByRole('button',{name:'Save daily check-in'});await save.focus();await page.keyboard.press('Enter');
  await expect(page.getByText('Daily check-in saved.',{exact:true})).toBeVisible();
  await expect(page.getByText(/Day still in progress/)).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  const headers={Origin:'http://127.0.0.1:5173','X-CSRF-Token':accounts[0].token};
  const rows=await (await a.request.get('/api/daily-checkins',{headers})).json();const row=rows[0];
  await page.getByRole('button',{name:`Edit ${row.date}`,exact:true}).click();
  await page.getByText('Timing and optional observations',{exact:true}).click();
  await page.getByLabel('Stress (0–10)',{exact:true}).fill('0');
  await page.getByRole('button',{name:'Save correction'}).click();
  await page.getByRole('button',{name:`History ${row.date}`,exact:true}).click();
  await expect(page.getByText(/Revision 2: correction/)).toBeVisible();
  const privateHeaders={'X-CSRF-Token':accounts[1].token};
  expect((await b.request.get('/api/daily-checkins',{headers:privateHeaders})).status()).toBe(200);
  expect(await (await b.request.get('/api/daily-checkins',{headers:privateHeaders})).json()).toEqual([]);
  expect((await b.request.get(`/api/daily-checkins/${row.id}/history`,{headers:privateHeaders})).status()).toBe(404);
  await page.getByLabel('Color theme').selectOption('dark');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.getByRole('button',{name:'Enter Attack Mode'}).click();await expect(page.getByRole('button',{name:'Exit Attack Mode'})).toBeVisible();await page.getByRole('button',{name:'Exit Attack Mode'}).click();
  page.once('dialog',dialog=>dialog.accept());await page.getByRole('button',{name:`Delete ${row.date}`,exact:true}).click();
  await expect(page.getByRole('heading',{name:`${row.date} — Deleted check-in`})).toBeVisible();
  await page.getByRole('button',{name:`History ${row.date}`,exact:true}).click();await expect(page.getByText(/Revision 3: deletion/)).toBeVisible();
  await navigate(page,'Overview');
  await page.getByText('Daily collection quality',{exact:true}).click();await page.getByRole('button',{name:'Review collection quality'}).click();
  await expect(page.getByRole('heading',{name:'Insufficient evidence for forecasting'})).toBeVisible();
  expect(errors).toEqual([]);
});
