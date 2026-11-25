import {expect,type Locator,type Page} from '@playwright/test';

export async function focusWithKeyboard(page:Page,target:Locator,direction:'Tab'|'Shift+Tab'){
 for(let step=0;step<200;step++){
  if(await target.evaluate(element=>element===document.activeElement))return;
  await page.keyboard.press(direction);
 }
 throw new Error('Could not reach the navigation control with the keyboard');
}

/** Follow the visible navigation, including the collapsed mobile menu. */
export async function openNavigation(page:Page,keyboard=false){
 await expect(page.locator('#page-content h1')).toBeVisible();
 const navigation=page.getByRole('navigation',{name:'Main navigation'});
 const menu=page.getByRole('button',{name:'Menu',exact:true});
 if(await menu.isVisible()){
  await expect(menu).toHaveAttribute('aria-expanded','false');
  if(keyboard){
   const start=await page.evaluate(()=>document.activeElement===document.body);
   await focusWithKeyboard(page,menu,start?'Tab':'Shift+Tab');await page.keyboard.press('Enter');
  }else await menu.click();
 }
 await expect(navigation).toBeVisible();
 return navigation;
}

export async function navigate(page:Page,name:string,keyboard=false){
 const navigation=await openNavigation(page,keyboard);
 const destination=navigation.getByRole('button',{name,exact:true});
 if(keyboard){
  const mobile=await page.locator('.mobile-menu-toggle').isVisible();
  const start=await page.evaluate(()=>document.activeElement===document.body);
  await focusWithKeyboard(page,destination,mobile||start?'Tab':'Shift+Tab');
  await page.keyboard.press('Enter');
 }else await destination.click();
}
