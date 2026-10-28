import {test,expect} from '@playwright/test';

test('real synthetic API enforces export CSRF, literal consent and private response headers',async({browser})=>{
 const a=await browser.newContext(),anonymous=await browser.newContext();
 const password='Synthetic-security-password-123';let token='';
 const origin='http://127.0.0.1:5173';
 const payload={confirmed:true,scope:'local_research_preparation',timezone_name:'UTC',days:30};
 try{
  const state=await (await a.request.get('/api/auth/session')).json();
  const result=await a.request.post('/api/auth/register',{headers:{Origin:origin,'X-CSRF-Token':state.csrf_token},data:{email:`synthetic-security-${Date.now()}@example.test`,display_name:'Synthetic security',password}});
  expect(result.status()).toBe(201);token=(await result.json()).csrf_token;
  const headers={Origin:origin,'X-CSRF-Token':token};
  expect((await anonymous.request.post('/api/v1/research-export',{headers,data:payload})).status()).toBe(401);
  expect((await a.request.post('/api/v1/research-export',{headers:{...headers,Origin:'https://attacker.example.test'},data:payload})).status()).toBe(403);
  expect((await a.request.post('/api/v1/research-export',{headers:{Origin:origin},data:payload})).status()).toBe(403);
  expect((await a.request.post('/api/v1/research-export',{headers,data:{...payload,confirmed:'true'}})).status()).toBe(422);
  const exported=await a.request.post('/api/v1/research-export',{headers,data:payload});
  expect(exported.status()).toBe(200);expect(exported.headers()['cache-control']).toBe('no-store');expect(exported.headers()['x-content-type-options']).toBe('nosniff');
  expect(exported.headers()['referrer-policy']).toBe('no-referrer');
  expect((await exported.json()).consent.research_enrollment).toBe(false);
 }finally{
  if(token){
   const oldCookies=await a.cookies();
   const result=await a.request.delete('/api/account',{headers:{Origin:origin,'X-CSRF-Token':token},data:{password,confirmation:'DELETE'}});
   expect(result.status()).toBe(204);await a.addCookies(oldCookies);
   expect((await a.request.get('/api/export',{headers:{'X-CSRF-Token':token}})).status()).toBe(401);
  }
  await a.close();await anonymous.close();
 }
});
