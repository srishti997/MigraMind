import type {BrowserContext} from '@playwright/test';

export type SyntheticAccount={context:BrowserContext,email:string,password:string,attempted:boolean,deleted:boolean};

export async function cleanSyntheticAccount(item:SyntheticAccount,origin:string){
 if(!item.attempted)return;
 const session=await item.context.request.get('/api/auth/session');
 if(session.status()!==200)throw new Error('Session lookup failed');
 let state=await session.json();
 if(!state.user){
  const login=await item.context.request.post('/api/auth/login',{headers:{Origin:origin,'X-CSRF-Token':state.csrf_token},data:{email:item.email,password:item.password}});
  if(login.status()===401&&item.deleted)return;
  if(login.status()!==200)throw new Error('Synthetic account cleanup identity is uncertain');
  state=await login.json();
 }
 if(state.user?.email!==item.email)throw new Error('Synthetic account cleanup identity mismatch');
 if(item.deleted)throw new Error('Deleted synthetic account unexpectedly remains active');
 const removed=await item.context.request.delete('/api/account',{headers:{Origin:origin,'X-CSRF-Token':state.csrf_token},data:{password:item.password,confirmation:'DELETE'}});
 if(removed.status()!==204)throw new Error(`Synthetic account deletion failed (${removed.status()})`);
}
