import {test,expect} from '@playwright/test';
import {patternFixture} from '../test-fixtures/patterns';
test.beforeEach(async({page})=>{
 await page.route('**/api/**',route=>{
  const url=new URL(route.request().url()),path=url.pathname;let data:unknown=[];
  if(path==='/api/auth/session')data={user:{id:1,email:'synthetic@example.test',display_name:'Synthetic'},csrf_token:'synthetic-csrf'};
  if(path==='/api/profile')data={name:'Synthetic',support:'',avoid:'',communication:''};
  if(path==='/api/insights'||path==='/api/attack-sessions/current')data=null;
  if(path==='/api/pattern-insights')data=patternFixture(url.searchParams.get('days')==='90',url.searchParams.get('timezone_name')||'UTC');
  return route.fulfill({json:data});
 });
});
test('sparse and supported descriptive insights are readable on mobile and keyboard accessible',async({page})=>{
 await page.setViewportSize({width:320,height:800});await page.emulateMedia({reducedMotion:'reduce'});await page.goto('/');
 await page.getByRole('navigation').getByRole('button',{name:'Insights',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Not enough information yet'})).toBeVisible();
 await expect(page.getByText(/0 onset days and 0 explicitly episode-free days/)).toBeVisible();
 await page.getByLabel('Reporting timezone').selectOption('UTC');await page.getByLabel('Reporting window').selectOption('90');
 await expect(page.getByRole('heading',{name:'Descriptive records available'})).toBeVisible();
 await expect(page.getByRole('img',{name:/Sleep duration:/})).toBeVisible();
 const summary=page.getByText('View daily chart data',{exact:true});await summary.focus();await page.keyboard.press('Enter');
 await expect(page.getByRole('table',{name:'Recorded onsets and explicit observation status'})).toBeVisible();
 await page.getByText('View timed symptoms and attacks',{exact:true}).click();
 await expect(page.getByText(/not a confirmed prodrome \(1 hours\)/)).toBeVisible();
 for(const width of [320,390,768,1280]){await page.setViewportSize({width,height:850});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)}
 await page.getByLabel('Color theme').selectOption('dark');await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
 await page.getByRole('button',{name:'Enter Attack Mode'}).click();await expect(page.getByRole('link',{name:/Emergency call/})).toBeInViewport();
 await page.getByRole('button',{name:'Exit Attack Mode'}).click();await expect(page.getByRole('heading',{name:'Insights',exact:true})).toBeVisible();
});
test('timezone display preserves offsets during the repeated DST hour',async({page})=>{
 await page.route('**/api/pattern-insights?**',route=>{
  const data=patternFixture(true,'America/New_York');data.timeline[0].at='2026-11-01T05:30:00Z';data.timeline[1].at='2026-11-01T06:15:00Z';data.timeline[0].hours_before=0.75;
  return route.fulfill({json:data});
 });
 await page.goto('/');await page.getByRole('navigation').getByRole('button',{name:'Insights',exact:true}).click();
 await page.getByLabel('Reporting timezone').selectOption('America/New_York');await page.getByText('View timed symptoms and attacks',{exact:true}).click();
 await expect(page.getByRole('cell',{name:/01:30 AM EDT/})).toBeVisible();await expect(page.getByRole('cell',{name:/01:15 AM EST/})).toBeVisible();
});

test('wellness editing preserves the recorded timezone and requires an explicit whole-day observation',async({page})=>{
 const entry={id:7,date:'2026-10-14',timezone_name:'America/New_York',recorded_at:'2026-10-15T12:00:00Z',sleep_hours:7,sleep_quality:null,stress:null,hydration_ml:null,screen_hours:null,missed_meals:null,menstrual_notes:null,episode_observation:null};
 let saved:any=null;
 await page.route('**/api/wellness',route=>route.fulfill({json:[entry]}));
 await page.route('**/api/wellness/7',route=>{saved=route.request().postDataJSON();return route.fulfill({json:{...entry,...saved}})});
 await page.goto('/');await page.getByRole('navigation').getByRole('button',{name:'Wellness',exact:true}).click();
 await page.getByRole('button',{name:'Edit check-in'}).click();
 const observation=page.getByRole('combobox',{name:/Whole-day episode observation/});
 await expect(observation).toHaveValue('');
 await observation.selectOption('no_episode');await page.getByRole('button',{name:'Save check-in',exact:true}).click();
 await expect(page.getByRole('dialog')).toHaveCount(0);
 expect(saved.timezone_name).toBe('America/New_York');expect(saved.episode_observation).toBe('no_episode');
 expect(saved).not.toHaveProperty('observation_recorded_at');
});
