// @vitest-environment jsdom
import {afterEach,expect,test,vi} from 'vitest';

class Channel{
 static instances=new Set<Channel>();
 static messages:unknown[]=[];
 onmessage:((event:{data:unknown})=>void)|null=null;
 constructor(){Channel.instances.add(this)}
 postMessage(data:unknown){Channel.messages.push(data);for(const receiver of Channel.instances)if(receiver!==this)queueMicrotask(()=>receiver.onmessage?.({data}))}
 close(){Channel.instances.delete(this)}
}
afterEach(()=>{Channel.instances.clear();Channel.messages=[];vi.unstubAllGlobals();vi.resetModules()});
async function tab(){vi.stubGlobal('BroadcastChannel',Channel);vi.resetModules();return import('./sessionEvents')}

test('a page never consumes its own sign-in or logout notification',async()=>{
 const a=await tab(),changed=vi.fn(),stop=a.observeSessionChange(changed);
 a.announceSessionChange();await Promise.resolve();expect(changed).not.toHaveBeenCalled();stop();
 expect(Object.keys(Channel.messages[0] as object).sort()).toEqual(['source','type']);
});

test('another tab still receives identity changes in both directions',async()=>{
 const a=await tab(),b=await tab(),changedA=vi.fn(),changedB=vi.fn();
 const stopA=a.observeSessionChange(changedA),stopB=b.observeSessionChange(changedB);
 a.announceSessionChange();await Promise.resolve();expect(changedA).not.toHaveBeenCalled();expect(changedB).toHaveBeenCalledTimes(1);
 b.announceSessionChange();await Promise.resolve();expect(changedA).toHaveBeenCalledTimes(1);expect(changedB).toHaveBeenCalledTimes(1);stopA();stopB();
});

test('legacy notifications are accepted without adding identity or health payloads',async()=>{
 const a=await tab(),changed=vi.fn(),stop=a.observeSessionChange(changed),legacy=new Channel();
 legacy.postMessage('changed');await Promise.resolve();expect(changed).toHaveBeenCalledTimes(1);stop();legacy.close();
});
