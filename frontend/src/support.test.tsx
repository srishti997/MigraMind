// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import {afterEach,describe,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {AttackMode} from './AttackMode';
import {SupportCard,cardText} from './SupportCard';
import {SupportPreferencesForm} from './SupportPreferencesForm';
import {SupportFeedbackPanel} from './SupportFeedbackPanel';
import {ACTIONS,DEFAULT_PREFERENCES,fallbackRecommendations} from './support';
const contacts=[{id:1,name:'First demo',relationship:'Friend',phone:'+12025550101'},{id:2,name:'Preferred demo',relationship:'Partner',phone:'+12025550102'}];
const profile={name:'Alex',support:'Quiet room',avoid:'Fragrance',communication:'Text before visiting'};
const props=()=>({contacts,profile,loading:false,dataError:'',onRetry:vi.fn(),onExit:vi.fn(),onSetup:vi.fn(),onEdit:vi.fn(),onLog:vi.fn()});
const result=(data:unknown,status=200)=>({ok:status<400,status,json:async()=>data});
afterEach(()=>{cleanup();vi.unstubAllGlobals();vi.restoreAllMocks()});
describe('personalized support',()=>{
 it('honors preferred contact and SMS using explicit fallback without auto dispatch',async()=>{
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>url.endsWith('/current')?result(null):Promise.reject(new Error('Ranking offline'))));
  const prefs={...DEFAULT_PREFERENCES,preferred_contact_id:2,communication_method:'sms' as const};
  render(<AttackMode {...props()} preferences={prefs}/>);
  expect(screen.getByLabelText('Trusted contact')).toHaveValue('2');
  expect(document.querySelector('.recommended-action a')).toHaveAttribute('href',expect.stringContaining('sms:+12025550102'));
  expect(screen.getByRole('link',{name:'Call contact'})).toHaveAttribute('href','tel:+12025550102');
  expect(screen.getByRole('link',{name:/Emergency call/})).toHaveAttribute('href','tel:112');
  await waitFor(()=>expect(vi.mocked(fetch)).toHaveBeenCalled());
  expect(vi.mocked(fetch).mock.calls.every(([url,opts])=>String(url).startsWith('/api/')&&(!opts||opts.method==='GET'))).toBe(true);
 });
 it('renders backend explanations and keeps every action available',async()=>{
  const actions=fallbackRecommendations({...DEFAULT_PREFERENCES,preferred_actions:['support_card']},contacts);
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>result(url.endsWith('recommendations')?{actions,recommended_action:'support_card',algorithm_version:'explicit-feedback-v1'}:null)));
  render(<AttackMode {...props()}/>);await waitFor(()=>expect(document.querySelector('.recommended-action button')).toHaveTextContent('Open my support card'));
  await userEvent.click(screen.getByText('Why this order?'));expect(screen.getByText('Your explicitly prioritized support action.')).toBeVisible();
  expect(screen.getByRole('link',{name:'Call contact'})).toBeVisible();expect(screen.getByRole('link',{name:'Prepare SMS'})).toBeVisible();
 });
 it('offers the support card without contacts and never hides emergency access',()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>result(null)));render(<AttackMode {...props()} contacts={[]}/>);
  expect(screen.getByRole('button',{name:'Open my support card'})).toBeVisible();expect(screen.getByRole('button',{name:'Set up a trusted contact'})).toBeVisible();
  expect(screen.getByRole('link',{name:/Emergency call/})).toHaveAttribute('href','tel:112');
 });
 it('requires review and explicit action to copy or share editable card text',async()=>{
  const copy=vi.fn(async()=>{}),share=vi.fn(async()=>{});vi.stubGlobal('navigator',{clipboard:{writeText:copy},share});
  render(<SupportCard profile={profile} preferences={{...DEFAULT_PREFERENCES,communication_method:'sms'}}/>);
  expect(copy).not.toHaveBeenCalled();expect(share).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button',{name:'Review card for sharing'}));
  expect(screen.getByLabelText('Card text to share')).toHaveValue(cardText(profile,{...DEFAULT_PREFERENCES,communication_method:'sms'}));
  expect(copy).not.toHaveBeenCalled();expect(share).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText('Card text to share'),{target:{value:'Only the text I chose'}});
  fireEvent.click(screen.getByRole('button',{name:'Copy card text'}));await waitFor(()=>expect(copy).toHaveBeenCalledWith('Only the text I chose'));expect(share).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button',{name:'Open device share…'}));await waitFor(()=>expect(share).toHaveBeenCalledWith({title:'My support card',text:'Only the text I chose'}));
  await screen.findByText('Share sheet closed. MigraMind cannot confirm delivery.');
 });
 it('saves support choices and explicitly resets them without sending profile details',async()=>{
  const user=userEvent.setup(),onSaved=vi.fn();vi.stubGlobal('confirm',()=>true);
  vi.stubGlobal('fetch',vi.fn(async(url:string,opts?:RequestInit)=>result(String(url).endsWith('/reset')?DEFAULT_PREFERENCES:{...JSON.parse(String(opts?.body)),id:1})));
  render(<SupportPreferencesForm preferences={DEFAULT_PREFERENCES} contacts={contacts} onSaved={onSaved}/>);
  await user.selectOptions(screen.getByLabelText('Preferred trusted contact'),'2');await user.selectOptions(screen.getByLabelText('Preferred contact method'),'sms');
  await user.click(screen.getByLabelText('Larger text'));await user.click(screen.getByRole('button',{name:'Save support choices'}));
  await waitFor(()=>expect(onSaved).toHaveBeenCalledWith(expect.objectContaining({preferred_contact_id:2,communication_method:'sms',large_text:true,use_feedback:false})));
  const payload=JSON.parse(String(vi.mocked(fetch).mock.calls[0][1]?.body));expect(payload).not.toHaveProperty('support');expect(payload).not.toHaveProperty('id');
  await user.click(screen.getByRole('button',{name:'Reset action and accessibility choices'}));await waitFor(()=>expect(onSaved).toHaveBeenLastCalledWith(DEFAULT_PREFERENCES));
 });
 it('does not ask for feedback during an active session and asks only after an explicit end',async()=>{
  const user=userEvent.setup(),onFeedback=vi.fn();let ended=false;
  vi.stubGlobal('fetch',vi.fn(async(url:string,opts?:RequestInit)=>{if(url.endsWith('/end'))ended=true;return result(url.endsWith('/current')||url.endsWith('/end')?{id:4,started_at:'2026-10-19T10:00:00Z',ended_at:ended?'2026-10-19T11:00:00Z':null}:null)}));
  render(<AttackMode {...props()} onFeedback={onFeedback}/>);await screen.findByText(/Session active/);
  expect(screen.queryByRole('button',{name:'Review support feedback'})).not.toBeInTheDocument();
  await user.click(screen.getByRole('button',{name:'End attack session'}));await screen.findByText(/Session ended/);
  await user.click(screen.getByRole('button',{name:'Skip feedback'}));expect(screen.queryByRole('button',{name:'Review support feedback'})).not.toBeInTheDocument();expect(onFeedback).not.toHaveBeenCalled();
  expect(vi.mocked(fetch).mock.calls.every(([url])=>!String(url).includes('/support/feedback'))).toBe(true);
 });
 it('allows optional feedback saving, reviewing and deletion for an ended session',async()=>{
  const user=userEvent.setup(),ended={id:7,started_at:'2026-10-19T10:00:00Z',ended_at:'2026-10-19T11:00:00Z'};let saved:any[]=[];vi.stubGlobal('confirm',()=>true);
  vi.stubGlobal('fetch',vi.fn(async(url:string,opts?:RequestInit)=>{if(url.endsWith('/attack-sessions'))return result([ended]);if(opts?.method==='POST'){saved=[{id:1,...JSON.parse(String(opts.body)),created_at:'2026-10-19T12:00:00Z'}];return result(saved[0],201)}if(opts?.method==='DELETE'){saved=[];return result(null,204)}return result(saved)}));
  render(<SupportFeedbackPanel sessions={[ended]} initialSessionId={7} initialAction="support_card"/>);await screen.findByLabelText('Was this support action helpful?');
  await user.selectOptions(screen.getByLabelText('Was this support action helpful?'),'yes');await user.click(screen.getByRole('button',{name:'Save optional feedback'}));await screen.findByText('Feedback saved. You can delete it at any time.');
  expect(saved[0]).toMatchObject({session_id:7,action_id:'support_card',helpful:true});
  await user.click(screen.getByRole('button',{name:'Delete feedback 1'}));await screen.findByText('No feedback saved.');expect(saved).toEqual([]);
 });
 it('feedback page suppresses the form while a session is active',async()=>{
  const active={id:1,started_at:'2026-10-19T10:00:00Z',ended_at:null};vi.stubGlobal('fetch',vi.fn(async(url:string)=>result(url.endsWith('/attack-sessions')?[active]:[])));
  render(<SupportFeedbackPanel sessions={[active]}/>);await screen.findByText('Feedback can wait until your active attack session has ended.');
  expect(screen.queryByLabelText('Was this support action helpful?')).not.toBeInTheDocument();
 });
});

it('does not let failed preference loading overwrite saved choices with defaults',()=>{
 const retry=vi.fn();render(<SupportPreferencesForm preferences={DEFAULT_PREFERENCES} contacts={contacts} onSaved={vi.fn()} loadError="Saved choices unavailable" onRetry={retry}/>);
 expect(screen.queryByRole('button',{name:'Save support choices'})).not.toBeInTheDocument();
 fireEvent.click(screen.getByRole('button',{name:'Retry saved choices'}));expect(retry).toHaveBeenCalledOnce();
});

it('does not request feedback when current session status cannot be verified',async()=>{
 vi.stubGlobal('fetch',vi.fn(async()=>{throw new Error('Offline')}));
 render(<SupportFeedbackPanel sessions={[{id:1,started_at:'2026-10-19T10:00Z',ended_at:'2026-10-19T11:00Z'}]}/>);
 await screen.findByRole('alert');expect(screen.queryByLabelText('Was this support action helpful?')).not.toBeInTheDocument();
});

it('does not present unavailable communication choices as a known sharing preference',()=>{
 render(<SupportCard profile={profile} preferences={DEFAULT_PREFERENCES} preferencesKnown={false}/>);
 expect(screen.getByText('Preferred method: Saved method unavailable')).toBeVisible();
 expect(screen.getByRole('button',{name:'Review card for sharing'})).toBeDisabled();
 expect(screen.getByText('Quiet room')).toBeVisible();
});
