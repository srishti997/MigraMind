import {navigate} from './navigation';
import {test,expect} from '@playwright/test';
import {installManualAccessibilityFixture} from '../test-fixtures/manual-accessibility';

// UI-only: intercept every API request; never use a real backend or browser profile.
for(const outcome of ['cancel','success','failure'] as const){
 test(`synthetic global sign-out: keyboard ${outcome}`,async({page,baseURL})=>{
  if(!baseURL)throw new Error('An explicit loopback fixture URL is required');
  await installManualAccessibilityFixture(page,{baseURL});
  let signedOut=false,attempts=0;
  await page.route('**/api/auth/session',route=>route.fulfill({json:{user:signedOut?null:{id:1,email:'synthetic@example.test',display_name:'Review'},csrf_token:'synthetic-fixture-token'}}));
  await page.route('**/api/auth/logout-all',async route=>{
   attempts++;
   expect(route.request().method()).toBe('POST');
   expect(route.request().headers()['x-csrf-token']).toBe('synthetic-fixture-token');
   expect(route.request().postDataJSON()).toEqual({password:'Synthetic-password-123'});
   if(outcome==='success'){signedOut=true;await route.fulfill({status:204})}
   else await route.fulfill({status:400,json:{detail:'Password confirmation failed'}});
  });
  await page.goto('/');
  await navigate(page,'Account');
  const trigger=page.getByRole('button',{name:'Sign out all sessions',exact:true});
  await trigger.focus();await page.keyboard.press('Enter');
  const password=page.getByLabel('Confirm current password',{exact:true});
  await expect(password).toBeFocused();await password.fill('Synthetic-password-123');
  if(outcome==='cancel'){
   await page.keyboard.press('Tab');await expect(page.getByRole('button',{name:'Confirm sign out all sessions'})).toBeFocused();
   await page.keyboard.press('Tab');await expect(page.getByRole('button',{name:'Cancel sign out all sessions'})).toBeFocused();
   await page.keyboard.press('Enter');await expect(trigger).toBeFocused();expect(attempts).toBe(0);
  }else{
   await page.keyboard.press('Enter');
   if(outcome==='success'){
    await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeVisible();
    await expect(page.getByRole('heading',{name:'Your account & privacy'})).toHaveCount(0);
   }else{
    await expect(page.getByRole('alert')).toHaveText('Password confirmation failed');
    await expect(password).toHaveValue('');await expect(password).toBeFocused();
    await expect(page.getByRole('heading',{name:'Your account & privacy'})).toBeVisible();
   }
   expect(attempts).toBe(1);
  }
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 });
}
