// @vitest-environment jsdom
import {afterEach,expect,test,vi} from 'vitest';
import {api,clearAuthentication} from './api';
import {validateProductionApiOrigin} from './securityConfig';
afterEach(()=>{clearAuthentication();vi.restoreAllMocks()});

test('synthetic mode blocks health writes before any request body is uploaded',async()=>{
 const fetcher=vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(JSON.stringify({demo_mode:true,csrf_token:'synthetic-token'})));
 await api('auth/session');fetcher.mockClear();
 await expect(api('episodes','POST',{notes:'Synthetic blocked text'})).rejects.toThrow('read-only');
 expect(fetcher).not.toHaveBeenCalled();
 fetcher.mockResolvedValue(new Response(JSON.stringify({synthetic_demo:true})));
 await api('v1/research-export','POST',{confirmed:true});expect(fetcher).toHaveBeenCalledTimes(1);
});

test('health requests disable browser caching and referrer disclosure',async()=>{
 const fetcher=vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response('[]'));
 await api('episodes');
 expect(fetcher.mock.calls[0][1]).toMatchObject({credentials:'include',cache:'no-store',referrerPolicy:'no-referrer'});
});

test('unexpected server error bodies are not displayed',async()=>{
 vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(JSON.stringify({detail:'Synthetic private database value'}),{status:500}));
 await expect(api('episodes')).rejects.toThrow('Could not save or load your data');
});

test('production API configuration rejects insecure and credential-bearing URLs',()=>{
 for(const value of ['http://example.test','https://user:secret@example.test','https://example.test/path','https://example.test?key=secret','//example.test']){
  expect(()=>validateProductionApiOrigin(value)).toThrow('exact HTTPS origin');
 }
 expect(()=>validateProductionApiOrigin('')).not.toThrow();
 expect(()=>validateProductionApiOrigin('https://api.example.test')).not.toThrow();
});
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
