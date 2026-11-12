// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import {afterEach,beforeEach,expect,test,vi} from 'vitest';
import {act,cleanup,fireEvent,render,screen} from '@testing-library/react';
import {Authentication} from './Authentication';
import {clearAuthentication} from './api';
import {readIdleSession} from './IdleSession';

vi.mock('./main',()=>({App:({onLogout}:{onLogout:(password?:string)=>Promise<void>})=><main id="page-content" tabIndex={-1}><h1>Private workspace</h1><label>Unsaved diary<textarea/></label><label>Unsaved check-in<input/></label><button onClick={()=>{void onLogout().catch(()=>{})}}>Workspace sign out</button><button onClick={()=>{void onLogout('Synthetic-password-123').catch(()=>{})}}>Workspace sign out all</button></main>}));
const START=Date.parse('2026-01-01T12:00:00Z'),MINUTE=60000;
const account={id:1,email:'synthetic@example.test',display_name:'Synthetic'};
function state(activity=START,server=START,absolute=START+12*60*MINUTE){return {user:account,csrf_token:'synthetic-csrf',server_time:new Date(server).toISOString(),last_activity_at_ms:activity,idle_expires_at:new Date(Math.min(activity+30*MINUTE,absolute)).toISOString(),expires_at:new Date(absolute).toISOString()}}
function json(value:unknown,status=200){return new Response(JSON.stringify(value),{status})}
async function flush(){await act(async()=>{await Promise.resolve()})}
async function advance(ms:number){await act(async()=>{vi.advanceTimersByTime(ms)})}
beforeEach(()=>{vi.useFakeTimers({toFake:['Date','performance','setTimeout','clearTimeout']});vi.setSystemTime(START)});
afterEach(()=>{cleanup();clearAuthentication();vi.restoreAllMocks();vi.useRealTimers()});

test('disabled mode shows no warning or activity requests even during passive events',async()=>{
 const fetcher=vi.spyOn(globalThis,'fetch').mockResolvedValue(json({user:account,csrf_token:'synthetic-csrf',expires_at:new Date(START+12*60*MINUTE).toISOString()}));
 render(<Authentication/>);await flush();await advance(31*MINUTE);
 fireEvent(document,new Event('visibilitychange'));
 expect(screen.queryByRole('heading',{name:'Your session will end soon'})).toBeNull();
 expect(screen.getByText('Private workspace')).toBeVisible();
 expect(fetcher.mock.calls.every(([path])=>!String(path).endsWith('auth/activity'))).toBe(true);
});

test('warning appears at 25 minutes without taking focus or treating typing as activity',async()=>{
 const fetcher=vi.spyOn(globalThis,'fetch').mockResolvedValue(json(state()));
 render(<Authentication/>);await flush();const input=screen.getByLabelText('Unsaved diary');input.focus();fireEvent.change(input,{target:{value:'Synthetic private draft'}});
 await advance(25*MINUTE-1);expect(screen.queryByRole('button',{name:'Stay signed in'})).toBeNull();
 await advance(1);expect(screen.getByRole('region',{name:'Your session will end soon'})).toBeVisible();
 expect(input).toHaveFocus();expect(input).toHaveValue('Synthetic private draft');
 expect(fetcher).toHaveBeenCalledTimes(1);
 expect(screen.getByText(/Nothing is saved automatically/)).toBeVisible();
});

test('explicit acknowledged extension preserves drafts, sends exact precondition and restores focus',async()=>{
 let finish!:(response:Response)=>void;
 const fetcher=vi.spyOn(globalThis,'fetch').mockImplementation(async input=>String(input).endsWith('auth/activity')?new Promise<Response>(resolve=>{finish=resolve}):json(state()));
 render(<Authentication/>);await flush();const input=screen.getByLabelText('Unsaved diary');input.focus();fireEvent.change(input,{target:{value:'Synthetic retained draft'}});
 await advance(25*MINUTE);fireEvent.click(screen.getByRole('button',{name:'Stay signed in'}));await flush();
 expect(screen.getByRole('button',{name:'Stay signed in'})).toBeDisabled();expect(screen.getByRole('region',{name:'Your session will end soon'})).toBeVisible();
 const request=fetcher.mock.calls.at(-1)![1]!;expect(JSON.parse(String(request.body))).toEqual({expected_last_activity_at_ms:START});expect(request.headers).toMatchObject({'X-CSRF-Token':'synthetic-csrf'});expect(request.credentials).toBe('include');
 await act(async()=>{finish(json(state(START+25*MINUTE,START+25*MINUTE)))});
 expect(screen.queryByRole('button',{name:'Stay signed in'})).toBeNull();expect(input).toHaveValue('Synthetic retained draft');expect(input).toHaveFocus();
 await advance(5*MINUTE);expect(screen.getByText('Private workspace')).toBeVisible();
});

test.each([403,409,500])('rejected extension %s never dismisses or automatically retries',async status=>{
 const fetcher=vi.spyOn(globalThis,'fetch').mockImplementation(async input=>String(input).endsWith('auth/activity')?json({detail:'Synthetic refusal'},status):json(state()));
 render(<Authentication/>);await flush();await advance(25*MINUTE);fireEvent.click(screen.getByRole('button',{name:'Stay signed in'}));await flush();
 expect(screen.getByRole('alert')).toHaveTextContent('Your session was not extended');expect(screen.getByRole('button',{name:'Stay signed in'})).toBeVisible();
 await advance(MINUTE);expect(fetcher.mock.calls.filter(([path])=>String(path).endsWith('auth/activity'))).toHaveLength(1);
 await advance(4*MINUTE);expect(screen.queryByText('Private workspace')).toBeNull();
});

test('network error keeps the last deadline and does not persist or restore unsaved content',async()=>{
 const storage=vi.spyOn(Storage.prototype,'setItem');
 vi.spyOn(globalThis,'fetch').mockImplementation(async input=>{if(String(input).endsWith('auth/activity'))throw new Error('Synthetic offline');return json(state())});
 render(<Authentication/>);await flush();fireEvent.change(screen.getByLabelText('Unsaved check-in'),{target:{value:'Synthetic unsaved check-in'}});
 await advance(25*MINUTE);fireEvent.click(screen.getByRole('button',{name:'Stay signed in'}));await flush();expect(screen.getByRole('alert')).toHaveTextContent('not extended');
 await advance(5*MINUTE);expect(screen.queryByLabelText('Unsaved check-in')).toBeNull();expect(screen.getByRole('button',{name:'Sign in'})).toBeVisible();
 expect(screen.getByRole('heading',{name:'Welcome back.'})).toHaveFocus();expect(screen.getByRole('alert')).toHaveTextContent('Unsaved entries were discarded');
 fireEvent.click(screen.getByRole('button',{name:'Retry connection'}));await flush();expect(screen.queryByText('Private workspace')).toBeNull();
 expect(storage.mock.calls.every(([,value])=>!value.includes('Synthetic unsaved'))).toBe(true);
});

test('401 from activity removes content and a still-valid bootstrap cannot reopen it',async()=>{
 vi.spyOn(globalThis,'fetch').mockImplementation(async input=>String(input).endsWith('auth/activity')?json({detail:'Sign in to continue'},401):json(state(START+25*MINUTE,START+25*MINUTE)));
 render(<Authentication/>);await flush();await advance(25*MINUTE);fireEvent.click(screen.getByRole('button',{name:'Stay signed in'}));await flush();
 expect(screen.queryByText('Private workspace')).toBeNull();expect(screen.getByRole('button',{name:'Sign in'})).toBeVisible();
});

test('late successful response cannot unlock expired private content',async()=>{
 let finish!:(response:Response)=>void;
 vi.spyOn(globalThis,'fetch').mockImplementation(async input=>String(input).endsWith('auth/activity')?new Promise<Response>(resolve=>{finish=resolve}):json(state()));
 render(<Authentication/>);await flush();await advance(25*MINUTE);fireEvent.click(screen.getByRole('button',{name:'Stay signed in'}));await flush();
 await advance(5*MINUTE);expect(screen.queryByText('Private workspace')).toBeNull();
 await act(async()=>{finish(json(state(START+25*MINUTE,START+25*MINUTE)))});
 expect(screen.queryByText('Private workspace')).toBeNull();expect(screen.getByRole('button',{name:'Sign in'})).toBeVisible();
});

test('stale tab checks server state explicitly without automatic retry or changing account',async()=>{
 let stale=false;
 const fetcher=vi.spyOn(globalThis,'fetch').mockImplementation(async input=>{
  if(String(input).endsWith('auth/activity')){stale=true;return json({detail:'State changed'},409)}
  return json(stale?state(START+25*MINUTE,START+25*MINUTE):state());
 });
 render(<Authentication/>);await flush();await advance(25*MINUTE);fireEvent.click(screen.getByRole('button',{name:'Stay signed in'}));await flush();
 fireEvent.click(screen.getByRole('button',{name:'Check session status'}));await flush();
 expect(screen.queryByRole('button',{name:'Stay signed in'})).toBeNull();expect(screen.getByText('Private workspace')).toBeVisible();
 expect(fetcher.mock.calls.filter(([path])=>String(path).endsWith('auth/activity'))).toHaveLength(1);
});

test.each(['account','binding'])('status check closes a stale workspace after %s changes',async change=>{
 let checking=false;
 const fetcher=vi.spyOn(globalThis,'fetch').mockImplementation(async input=>{
  if(String(input).endsWith('auth/activity')){checking=true;return json({detail:'State changed'},409)}
  const result=state(START+25*MINUTE,START+25*MINUTE);
  return json(checking?{...result,...(change==='account'?{user:{...account,id:2}}:{csrf_token:'synthetic-other-session'})}:state());
 });
 render(<Authentication/>);await flush();await advance(25*MINUTE);fireEvent.click(screen.getByRole('button',{name:'Stay signed in'}));await flush();
 fireEvent.click(screen.getByRole('button',{name:'Check session status'}));await flush();
 expect(screen.queryByText('Private workspace')).toBeNull();expect(screen.getByRole('button',{name:'Sign in'})).toBeVisible();
 expect(fetcher.mock.calls.filter(([path])=>String(path).endsWith('auth/activity'))).toHaveLength(1);
});

test('fixed absolute expiry is not extended even by successful activity',async()=>{
 const absolute=START+30*MINUTE;
 vi.spyOn(globalThis,'fetch').mockImplementation(async input=>json(String(input).endsWith('auth/activity')?state(START+25*MINUTE,START+25*MINUTE,absolute):state(START,START,absolute)));
 render(<Authentication/>);await flush();await advance(25*MINUTE);fireEvent.click(screen.getByRole('button',{name:'Stay signed in'}));await flush();
 expect(screen.getByText('The fixed sign-in limit cannot be extended.')).toBeVisible();expect(screen.getByRole('button',{name:'Stay signed in'})).toBeVisible();
 await advance(5*MINUTE);expect(screen.queryByText('Private workspace')).toBeNull();
});

test('metadata validation rejects invented extension and subtracts request latency',()=>{
 const initial=readIdleSession(state(),0)!;
 expect(initial.deadline).toBe(30*MINUTE);
 expect(()=>readIdleSession({...state(),idle_expires_at:new Date(START+31*MINUTE).toISOString()},0)).toThrow('invalid');
 expect(()=>readIdleSession(state(START,START,START+13*60*MINUTE),0,initial)).toThrow('invalid');
 expect(readIdleSession(state(START,START+1000),10)!.deadline).toBe(30*MINUTE-990);
});

test('visibility return after a suspended monotonic clock can only shorten or lock',async()=>{
 const fetcher=vi.spyOn(globalThis,'fetch').mockImplementation(async()=>json(state()));
 render(<Authentication/>);await flush();
 // Emulate sleep: wall time advances while performance/timer time is suspended.
 vi.setSystemTime(START+31*MINUTE);fireEvent(document,new Event('visibilitychange'));await flush();
 expect(screen.queryByText('Private workspace')).toBeNull();
 expect(screen.getByRole('button',{name:'Sign in'})).toBeVisible();
 expect(fetcher.mock.calls.every(([path])=>!String(path).endsWith('auth/activity'))).toBe(true);
});
