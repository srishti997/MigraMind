import {test as base,type BrowserContext} from '@playwright/test';
import {cleanSyntheticAccount,type SyntheticAccount} from './syntheticCleanupCore';

type Cleanup={track:(context:BrowserContext,email:string,password:string)=>SyntheticAccount};

// Fixture teardown has its own Playwright teardown phase, so a test timeout
// does not consume the time allocated for cleanup or replace its first error.
export const test=base.extend<{syntheticCleanup:Cleanup}>({
 syntheticCleanup:[async({browser,baseURL},use)=>{
  void browser;
  const target=baseURL?new URL(baseURL):null;
  if(!target||target.protocol!=='http:'||target.hostname!=='127.0.0.1'||!target.port||target.username||target.password||target.pathname!=='/'||target.search||target.hash)throw new Error('Explicit loopback synthetic test origin required');
  const origin=target.origin,accounts:SyntheticAccount[]=[];
  await use({track:(context,email,password)=>{
   if(!/^synthetic-[a-z0-9-]+@example\.test$/.test(email))throw new Error('Synthetic account identity required');
   const item={context,email,password,attempted:false,deleted:false};accounts.push(item);return item;
  }});
  const failures:string[]=[];
  for(const item of accounts){
   try{
    await cleanSyntheticAccount(item,origin);
   }catch{failures.push('Synthetic account deletion failed or identity was uncertain')}
  }
  for(const context of new Set(accounts.map(item=>item.context))){
   try{await context.close()}catch{failures.push('Synthetic browser context cleanup failed')}
  }
  if(failures.length)throw new Error('Synthetic cleanup failed: '+failures.join('; '));
 },{auto:true}]
});
