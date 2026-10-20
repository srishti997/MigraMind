import {test,expect} from '@playwright/test';

test('readiness is user initiated, read only, accessible and usable at mobile width',async({page})=>{
 const requests:string[]=[];const errors:string[]=[];
 page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/api/**',route=>{
  const path=new URL(route.request().url()).pathname;let data:unknown=[];
  if(path==='/api/auth/session')data={user:{id:1,email:'synthetic@example.test',display_name:'Synthetic'},csrf_token:'synthetic-csrf'};
  if(path==='/api/profile')data={name:'Synthetic',support:'',avoid:'',communication:''};
  if(path==='/api/insights'||path==='/api/attack-sessions/current')data=null;
  if(path==='/api/v1/forecast')data={status:'insufficient_data',probability:null};
  if(path==='/api/v1/data-readiness'){
   requests.push(route.request().method());
   data={version:'account-preparation/v1',window_start:'2026-10-01',window_end:'2026-10-30',days:30,completed_days:29,
    coverage:{episode_recorded:1,no_episode_reported:0,unknown:29,conflict:0,episode_reported_without_onset:0},
    wellness_checkins:1,early_observations:0,missingness:{severity:{available:0,missing:1},stress:{available:1,missing:0}},
    labeled_outcomes:{positive:0,negative:0},training_justified:false,evaluation_justified:false,
    preparation:{prediction_cutoff:'2026-10-30T12:00:00Z',horizon_end:'2026-10-31T12:00:00Z',eligibility:'eligible_for_preparation_only'},
    limitations:['Missing diary dates are unknown, not migraine-free.']};
  }
  return route.fulfill({json:data});
 });
 await page.setViewportSize({width:320,height:850});await page.goto('/');
 const disclosure=page.getByText('Your data readiness',{exact:true});await disclosure.focus();await page.keyboard.press('Enter');
 expect(requests).toEqual([]);
 await page.getByRole('button',{name:'Review data readiness'}).click();
 await expect(page.getByRole('heading',{name:'Not ready for forecasting research'})).toBeVisible();
 await expect(page.getByRole('table',{name:'Recorded values and missing fields'})).toBeVisible();
 await expect(page.getByText('0 positive; 0 negative')).toBeVisible();
 expect(requests).toEqual(['GET']);expect(errors).toEqual([]);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.getByLabel('Color theme').selectOption('dark');await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
