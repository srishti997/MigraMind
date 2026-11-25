import {navigate} from './navigation';
import {test,expect} from '@playwright/test';
import {installManualAccessibilityFixture} from '../test-fixtures/manual-accessibility';

test('manual fixture is isolated, navigable and rejects persistence',async({page,baseURL})=>{
 await installManualAccessibilityFixture(page,{baseURL:baseURL!});
 await page.goto('/');await expect(page.getByRole('heading',{name:'A gentler day, Review.'})).toBeVisible();
 for(const name of ['Daily status','Migraine diary','Calendar','Insights','Wellness','Early symptoms','Trusted contacts','Caregiver profile','Support feedback','Settings','Account']){
  await navigate(page,name);
  await expect(page.getByRole('heading',{name,exact:true})).toBeFocused();
 }
 const result=await page.evaluate(async()=>({
  write:(await fetch('/api/profile',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'Synthetic blocked'})})).status,
  unknown:(await fetch('/api/unimplemented-manual-fixture')).status,
  contacts:await(await fetch('/api/contacts')).json(),
 }));
 expect(result.write).toBe(422);expect(result.unknown).toBe(404);expect(result.contacts[0].name).toBe('Synthetic contact');
 await page.getByRole('button',{name:'Enter Attack Mode',exact:true}).click();
 // Independent final guard: even a broken fixture must never activate a real handler.
 await page.evaluate(()=>document.addEventListener('click',event=>{
  (window as any).__fixturePreventedDefault=event.defaultPrevented;event.preventDefault();
 },{once:true}));
 const url=page.url(),link=page.getByRole('link',{name:/Emergency call/});await link.focus();await page.keyboard.press('Enter');
 expect(await page.evaluate(()=>(window as any).__fixturePreventedDefault)).toBe(true);expect(page.url()).toBe(url);
});

test('anonymous manual fixture gives controlled errors without real credentials',async({page,baseURL})=>{
 await installManualAccessibilityFixture(page,{baseURL:baseURL!,anonymous:true});await page.goto('/');
 await page.getByLabel('Email',{exact:true}).fill('synthetic@example.test');await page.getByLabel('Password',{exact:true}).fill('Synthetic-only-123');
 await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await expect(page.getByRole('alert')).toContainText('Synthetic manual fixture error');
});

test('manual fixture refuses a non-loopback origin before navigation',async({page})=>{
 await expect(installManualAccessibilityFixture(page,{baseURL:'https://example.test'})).rejects.toThrow('explicit loopback');
 expect(page.url()).toBe('about:blank');
});

test('Daily Status cancellation restores the correct Edit control and leaves saved reports unchanged',async({page,baseURL})=>{
 await page.setViewportSize({width:320,height:850});
 await installManualAccessibilityFixture(page,{baseURL:baseURL!});
 const writes:string[]=[];page.on('request',request=>{if(!['GET','HEAD'].includes(request.method()))writes.push(request.url())});
 await page.goto('/');await navigate(page,'Daily status');
 const before=await page.evaluate(async()=>await(await fetch('/api/daily-checkins?include_deleted=true')).json());
 for(const date of ['2026-01-03','2026-01-01','2026-01-03']){
  const edit=page.getByRole('button',{name:'Edit '+date,exact:true});await edit.focus();await page.keyboard.press('Enter');
  await expect(page.getByLabel('Migraine status')).toBeFocused();
  await page.getByLabel('Migraine status').selectOption('migraine');
  await page.getByRole('button',{name:'Cancel correction',exact:true}).focus();await page.keyboard.press('Enter');
  await expect(edit).toBeFocused();await expect(page.getByRole('button',{name:'Cancel correction',exact:true})).toHaveCount(0);
  await expect(page.getByLabel('Migraine status')).toHaveValue('unknown');
  await page.keyboard.press('Tab');await expect(page.getByRole('button',{name:'Delete '+date,exact:true})).toBeFocused();
 }
 const after=await page.evaluate(async()=>await(await fetch('/api/daily-checkins?include_deleted=true')).json());
 expect(after).toEqual(before);expect(writes).toEqual([]);
});

test('Daily Status cancellation has a stable focus fallback when its Edit control disappears',async({page,baseURL})=>{
 await page.setViewportSize({width:1280,height:850});
 await installManualAccessibilityFixture(page,{baseURL:baseURL!,failPaths:['/api/daily-checkins/3/history']});
 const writes:string[]=[];page.on('request',request=>{if(!['GET','HEAD'].includes(request.method()))writes.push(request.url())});
 await page.goto('/');await navigate(page,'Daily status');
 await page.getByRole('button',{name:'Edit 2026-01-03',exact:true}).click();await expect(page.getByLabel('Migraine status')).toBeFocused();
 await page.getByRole('button',{name:'History 2026-01-03',exact:true}).click();await expect(page.getByRole('alert')).toBeVisible();
 // A masked GET snapshot simulates an unavailable opener; no record is deleted.
 await page.route('**/api/daily-checkins?*',route=>route.fulfill({json:[]}));
 await page.getByRole('button',{name:'Reload check-ins',exact:true}).click();
 await expect(page.getByRole('button',{name:'Edit 2026-01-03',exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:'Cancel correction',exact:true}).focus();await page.keyboard.press('Enter');
 await expect(page.getByLabel('Migraine status')).toBeFocused();expect(writes).toEqual([]);
});
