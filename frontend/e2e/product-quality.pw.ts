import {test,expect} from '@playwright/test';
test.beforeEach(async({page})=>{
 await page.route('**/api/**',route=>{
  const path=new URL(route.request().url()).pathname;
  let value:unknown=path==='/api/insights'||path==='/api/pattern-insights'?null:[];
  if(path==='/api/auth/session')value={user:{id:1,email:'demo@synthetic.example.test',display_name:'Synthetic demonstration'},csrf_token:'synthetic-token',demo_mode:true};
  if(path==='/api/profile')value={name:'Synthetic demonstration',support:'',avoid:'',communication:''};
  if(path==='/api/support/preferences')value={};
  if(path==='/api/v1/forecast')value={status:'insufficient_data',probability:null,clinically_validated:false};
  return route.fulfill({json:value});
 });
});
test('guided demo stays readable at mobile, tablet and desktop widths',async({page})=>{
 const writes:string[]=[];page.on('request',request=>{if(['POST','PUT','PATCH','DELETE'].includes(request.method()))writes.push(request.url())});
 for(const width of [320,768,1280]){
  await page.setViewportSize({width,height:850});await page.goto('/');
  await expect(page.getByRole('heading',{name:'Explore the synthetic demonstration'})).toBeVisible();
  await page.getByRole('button',{name:'Show example calendar'}).click();
  await expect(page.getByRole('heading',{name:'January 2026',exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'Calendar',exact:true})).toBeFocused();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.getByRole('button',{name:'Add episode',exact:true}).click();
  await expect(page.getByRole('status')).toContainText('read-only');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByText('No episodes recorded here. Missing entries do not confirm a migraine-free day.',{exact:true})).toBeVisible();
  expect(writes).toEqual([]);
  if(width===320||width===1280)await page.screenshot({path:'.research/sprint16-demo-'+width+'.png',fullPage:true});
 }
});
test('skip link and semantic controls support keyboard navigation without uploads',async({page})=>{
 await page.goto('/');await expect(page.getByRole('heading',{name:'Explore the synthetic demonstration'})).toBeVisible();
 await page.keyboard.press('Tab');await expect(page.getByRole('link',{name:'Skip to page content'})).toBeFocused();
 await page.keyboard.press('Enter');await expect(page.locator('#page-content')).toBeFocused();
 const missing=await page.locator('button,input:not([type=hidden]),select,textarea').evaluateAll(nodes=>nodes.filter(node=>{
  const el=node as HTMLElement;
  return !el.textContent?.trim()&&!el.getAttribute('aria-label')&&!el.getAttribute('aria-labelledby')&&!(el as HTMLInputElement).labels?.length;
 }).map(node=>node.outerHTML));
 expect(missing).toEqual([]);
 await page.getByRole('navigation').getByRole('button',{name:'Insights',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Insights',exact:true})).toBeFocused();
 for(const theme of ['dark','warm']){
  await page.getByLabel('Color theme').selectOption(theme);
  const ratios=await page.evaluate(()=>{
   const css=getComputedStyle(document.documentElement);
   const luminance=(key:string)=>{
    const hex=css.getPropertyValue(key).trim().replace('#','');
    const c=[0,2,4].map(offset=>parseInt(hex.slice(offset,offset+2),16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);
    return c[0]*.2126+c[1]*.7152+c[2]*.0722;
   };
   return [['--text','--surface'],['--muted-readable','--surface'],['--on-primary','--primary']].map(([a,b])=>{
    const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);
   });
  });
  for(const ratio of ratios)expect(ratio).toBeGreaterThanOrEqual(4.5);
 }
});

for(const [zone,date,label] of [['Etc/GMT+12','2026-01-01','January 1, 2026'],['UTC','2026-01-02','January 2, 2026'],['Pacific/Kiritimati','2026-01-03','January 3, 2026']]){
 test.describe('fixture calendar in '+zone,()=>{
  test.use({timezoneId:zone});
  test('selects the displayed local episode day across UTC boundaries',async({page})=>{
   await page.route('**/api/episodes',route=>route.fulfill({json:[{id:1,date:'2026-01-02',started_at:'2026-01-02T10:00:00Z',ended_at:'2026-01-02T11:00:00Z',timezone_name:'UTC',severity:3,duration:60,trigger:'Unknown',notes:'Synthetic timezone boundary fixture'}]}));
   await page.goto('/');
   await page.getByRole('button',{name:'Show example calendar'}).click();
   await expect(page.getByRole('heading',{name:label,exact:true})).toBeVisible();
   await expect(page.getByRole('button',{name:date+': 1 episodes, 0 wellness check-ins',exact:true})).toHaveClass(/selected/);
   await expect(page.getByText('Synthetic timezone boundary fixture',{exact:true})).toBeVisible();
  });
 });
}
