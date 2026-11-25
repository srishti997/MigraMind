import {expect,it,vi} from 'vitest';
import type {BrowserContext} from '@playwright/test';
import {cleanSyntheticAccount,type SyntheticAccount} from '../e2e/syntheticCleanupCore';

const reply=(status:number,data:unknown={})=>({status:()=>status,json:async()=>data});
function fixture(state:unknown){
 const request={get:vi.fn().mockResolvedValue(reply(200,state)),post:vi.fn(),delete:vi.fn().mockResolvedValue(reply(204))};
 const item:SyntheticAccount={context:{request} as unknown as BrowserContext,email:'synthetic-a@example.test',password:'synthetic-only',attempted:true,deleted:false};
 return {request,item};
}
const origin='http://127.0.0.1:5173';

it('deletes only the exact synthetic account with the current CSRF token',async()=>{
 const {request,item}=fixture({user:{email:'synthetic-a@example.test'},csrf_token:'synthetic-csrf'});
 await cleanSyntheticAccount(item,origin);
 expect(request.delete).toHaveBeenCalledWith('/api/account',{headers:{Origin:origin,'X-CSRF-Token':'synthetic-csrf'},data:{password:'synthetic-only',confirmation:'DELETE'}});
});
it('refuses mismatched identities and surfaces deletion failures',async()=>{
 const {request,item}=fixture({user:{email:'synthetic-b@example.test'},csrf_token:'synthetic-csrf'});
 await expect(cleanSyntheticAccount(item,origin)).rejects.toThrow('identity mismatch');expect(request.delete).not.toHaveBeenCalled();
 request.get.mockResolvedValue(reply(200,{user:{email:item.email},csrf_token:'synthetic-csrf'}));request.delete.mockResolvedValue(reply(503));
 await expect(cleanSyntheticAccount(item,origin)).rejects.toThrow('deletion failed');
});
it('refuses uncertain login failures, permitting only a confirmed prior deletion',async()=>{
 const {request,item}=fixture({user:null,csrf_token:'synthetic-csrf'});request.post.mockResolvedValue(reply(401));
 await expect(cleanSyntheticAccount(item,origin)).rejects.toThrow('uncertain');
 item.deleted=true;await expect(cleanSyntheticAccount(item,origin)).resolves.toBeUndefined();expect(request.delete).not.toHaveBeenCalled();
});
it('does not access the account when registration was never attempted',async()=>{
 const {request,item}=fixture({});item.attempted=false;
 await cleanSyntheticAccount(item,origin);expect(request.get).not.toHaveBeenCalled();
});
