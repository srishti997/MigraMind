// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import {afterEach,beforeEach,expect,test,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,within} from '@testing-library/react';
import {App} from './main';
import {AttackMode} from './AttackMode';
import {api} from './api';
import {callLink,phoneNumber,smsLink} from './assistance';
import {episodePayload} from './tracking';
import type {Episode} from './tracking';
import {DEFAULT_PREFERENCES} from './support';

vi.mock('./api',()=>({api:vi.fn()}));
const contacts=[{id:1,name:'Synthetic friend',relationship:'Test',phone:'+1 (202) 555-0100'}];
const profile={name:'Synthetic',support:'Quiet synthetic preference',avoid:'Noise',communication:'Text'};
function defaults(path:string){
 if(path==='contacts')return contacts;
 if(path==='profile')return profile;
 if(path==='support/preferences')return DEFAULT_PREFERENCES;
 if(path.startsWith('insights?'))return null;
 if(path==='attack-sessions/current')return null;
 if(path==='v1/forecast')return {status:'insufficient_data',probability:null,clinically_validated:false};
 return [];
}
beforeEach(()=>{localStorage.clear();vi.mocked(api).mockImplementation(async path=>defaults(path))});
afterEach(()=>{cleanup();vi.resetAllMocks()});

test('unrelated insights failure keeps contacts and saved support usable; retry recovers',async()=>{
 let fail=true;
 vi.mocked(api).mockImplementation(async path=>{if(path.startsWith('insights?')&&fail)throw new Error('Synthetic insights outage');return defaults(path)});
 render(<App/>);
 expect(await screen.findByRole('alert')).toHaveTextContent('insights could not be loaded');
 expect(screen.getByRole('heading',{name:'A gentler day, Synthetic.'})).toBeVisible();
 fail=false;fireEvent.click(screen.getByRole('button',{name:'Retry insights'}));
 await vi.waitFor(()=>expect(screen.queryByRole('alert')).not.toBeInTheDocument());
 fireEvent.click(screen.getByRole('button',{name:'Enter Attack Mode'}));
 expect(await screen.findByRole('link',{name:'Call contact'})).toHaveAttribute('href','tel:+12025550100');
 expect(screen.getByText('Quiet synthetic preference')).toBeInTheDocument();
});

test('support resolves while an unrelated read remains pending',async()=>{
 let finish!:(value:unknown)=>void;
 vi.mocked(api).mockImplementation(async path=>path.startsWith('insights?')?new Promise(resolve=>{finish=resolve}):defaults(path));
 render(<App/>);
 await screen.findByRole('heading',{name:'A gentler day, Synthetic.'});
 fireEvent.click(screen.getByRole('button',{name:'Enter Attack Mode'}));
 expect(await screen.findByRole('link',{name:'Call contact'})).toBeVisible();
 finish(null);
});

test('failed profile disables blind writes; healthy contacts render and retry restores saved values',async()=>{
 let fail=true;
 vi.mocked(api).mockImplementation(async path=>{if(path==='profile'&&fail)throw new Error('Synthetic profile outage');return defaults(path)});
 render(<App/>);
 await screen.findByRole('alert');
 fireEvent.click(within(screen.getByRole('navigation')).getByRole('button',{name:'Trusted contacts'}));
 expect(screen.getByRole('link',{name:'Call'})).toHaveAttribute('href','tel:+12025550100');
 fireEvent.click(within(screen.getByRole('navigation')).getByRole('button',{name:'Caregiver profile'}));
 expect(screen.getByRole('button',{name:'Save my preferences'})).toBeDisabled();
 fail=false;fireEvent.click(screen.getByRole('button',{name:'Retry profile'}));
 await vi.waitFor(()=>expect(screen.getByRole('button',{name:'Save my preferences'})).toBeEnabled());
 expect(screen.getByLabelText('What helps me feel supported')).toHaveValue(profile.support);
 expect(vi.mocked(api).mock.calls.every(([,method])=>!method||method==='GET')).toBe(true);
});

test('a saved episode stays saved when analytics refresh fails and retry never repeats the write',async()=>{
 let episodes:unknown[]=[];let fail=false;
 vi.mocked(api).mockImplementation(async(path,method)=>{
  if(path==='episodes'&&method==='POST'){
   episodes=[{id:1,date:'2024-01-02',started_at:'2024-01-02T10:00:00Z',ended_at:null,
    timezone_name:'UTC',severity:null,duration:null,trigger:'Unknown',notes:'Synthetic saved despite analytics outage',symptoms:[],medications:[]}];
   fail=true;return episodes[0];
  }
  if(path==='episodes')return episodes;
  if(path.startsWith('insights?')&&fail)throw new Error('Synthetic analytics outage');
  return defaults(path);
 });
 render(<App/>);
 await screen.findByRole('heading',{name:'A gentler day, Synthetic.'});
 fireEvent.click(within(screen.getByRole('navigation')).getByRole('button',{name:'Migraine diary'}));
 fireEvent.click(screen.getByRole('button',{name:'Log an episode'}));
 fireEvent.change(screen.getByLabelText('Attack started'),{target:{value:'2024-01-02T10:00:00'}});
 fireEvent.submit(screen.getByRole('dialog').querySelector('form')!);
 expect(await screen.findByText('Synthetic saved despite analytics outage')).toBeVisible();
 expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
 expect(screen.getByRole('alert')).toHaveTextContent('insights could not be loaded');
 fail=false;fireEvent.click(screen.getByRole('button',{name:'Retry insights'}));
 await vi.waitFor(()=>expect(screen.queryByRole('alert')).not.toBeInTheDocument());
 expect(vi.mocked(api).mock.calls.filter(([path,method])=>path==='episodes'&&method==='POST')).toHaveLength(1);
});

test('malformed historic contacts cannot produce dial or SMS links and emergency fallback remains valid',async()=>{
 for(const value of ['---','()','++12','12+3','tel:112','*123#','12;34','(123','123)','((12))','()12','123\n456','１２３']){
  expect(phoneNumber(value)).toBe('');expect(callLink(value)).toBeUndefined();expect(smsLink(value,'Android',0)).toBeUndefined();
 }
 for(const value of ['1','112','020 1234-5678','+91 (20) 1234-5678'])expect(phoneNumber(value)).not.toBe('');
 render(<AttackMode contacts={[{...contacts[0],phone:'---'}]} profile={profile} loading={false} dataError="" onRetry={vi.fn()} onExit={vi.fn()} onSetup={vi.fn()} onEdit={vi.fn()} onLog={vi.fn()} preferences={{...DEFAULT_PREFERENCES,emergency_number:'tel:123'}}/>);
 expect(screen.getByRole('link',{name:/Emergency call/})).toHaveAttribute('href','tel:112');
 expect(screen.queryByRole('link',{name:'Call contact'})).not.toBeInTheDocument();
 expect(screen.queryByRole('link',{name:'Prepare SMS'})).not.toBeInTheDocument();
});

test('episode serialization rejects invalid intervals and future observations before upload',()=>{
 function form(fields:Record<string,string>){const f=document.createElement('form');for(const [name,value] of Object.entries(fields)){const i=document.createElement('input');i.name=name;i.value=value;f.append(i)}return f}
 const start='2024-01-02T10:00:00';
 for(const ended_at of [start,'2024-01-02T09:59:59'])expect(()=>episodePayload(form({started_at:start,ended_at}))).toThrow('after start');
 expect(()=>episodePayload(form({started_at:'2099-01-01T10:00:00'}))).toThrow('future');
 expect(()=>episodePayload(form({started_at:start,ended_at:'2099-01-01T10:00:00'}))).toThrow('future');
 const value=episodePayload(form({date:'2024-01-01',started_at:start,ended_at:'2024-01-02T11:00:00',duration:'999'}));
 expect(value.date).toBeNull();expect(value.duration).toBeNull(); // Server derives both from exact times.
});

test('date-only edits preserve the recorded zone and validate its local date without inventing one',()=>{
 vi.spyOn(Date,'now').mockReturnValue(new Date('2026-01-02T01:00:00Z').getTime());
 try{
  const form=document.createElement('form');const input=document.createElement('input');
  input.name='date';input.value='2026-01-01';form.append(input);
  const original:Episode={id:1,date:input.value,timezone_name:'America/Los_Angeles',severity:null,duration:null,trigger:'Unknown',notes:''};
  expect(episodePayload(form,original).timezone_name).toBe('America/Los_Angeles');
  input.value='2026-01-02';
  expect(()=>episodePayload(form,original)).toThrow('future');
  expect(episodePayload(form,{...original,timezone_name:null}).timezone_name).toBeNull();
  vi.mocked(Date.now).mockReturnValue(new Date('2026-01-02T12:00:00Z').getTime());
  input.value='2026-01-03';
  expect(episodePayload(form,{...original,timezone_name:'Pacific/Kiritimati'}).timezone_name).toBe('Pacific/Kiritimati');
 }finally{vi.restoreAllMocks()}
});
