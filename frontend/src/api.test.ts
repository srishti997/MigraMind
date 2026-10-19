// @vitest-environment jsdom
import {afterEach,expect,test,vi} from 'vitest';
import {api,clearAuthentication} from './api';
afterEach(()=>{clearAuthentication();vi.restoreAllMocks()});
test('discard in-flight health responses after session changes',async()=>{
 let resolve!:(response:Response)=>void;
 vi.spyOn(globalThis,'fetch').mockImplementation(()=>new Promise<Response>(done=>{resolve=done}));
 const request=api('episodes');clearAuthentication();
 resolve(new Response(JSON.stringify([{notes:'Synthetic old session'}])));
 await expect(request).rejects.toThrow('Session changed');
});
test('discard stale bootstrap tokens after a new session starts',async()=>{
 let resolve!:(response:Response)=>void;
 const fetcher=vi.spyOn(globalThis,'fetch').mockImplementationOnce(()=>new Promise<Response>(done=>{resolve=done}));
 const stale=api('auth/session');
 fetcher.mockResolvedValueOnce(new Response(JSON.stringify({user:{id:2},csrf_token:'new-token'})));
 await api('auth/login','POST',{email:'synthetic@example.test',password:'Synthetic-password-123'});
 resolve(new Response(JSON.stringify({user:{id:1},csrf_token:'old-token'})));
 await expect(stale).rejects.toThrow('Session changed');
 fetcher.mockResolvedValueOnce(new Response('[]'));await api('episodes');
 expect(fetcher.mock.calls.at(-1)![1]!.headers).toMatchObject({'X-CSRF-Token':'new-token'});
});
