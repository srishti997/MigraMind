// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {cleanup,render,screen,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {AttackMode} from './AttackMode';
import {App} from './main';
import {smsLink,supportMessage} from './assistance';
const contacts=[{id:1,name:'Jamie Demo',relationship:'Partner',phone:'+91 99999 00001'},{id:2,name:'Sam Demo',relationship:'Friend',phone:'+91 99999 00002'}];
const profile={name:'Alex',support:'A quiet room',avoid:'Strong scents',communication:'Text me first'};
let session:{id:number,started_at:string,ended_at:string|null}|null;
let fail=false;
let fixtureContacts=contacts;
beforeEach(()=>{session=null;fail=false;fixtureContacts=contacts;localStorage.clear();vi.stubGlobal('fetch',vi.fn(async(url:string,opts?:RequestInit)=>{
 const path=url.replace('/api/','');
 if(fail&&path.startsWith('attack-sessions'))return {ok:false};
 let data:unknown=null;
 if(path==='contacts')data=fixtureContacts;
 if(path==='profile')data=profile;
 if(path==='episodes')data=[];
 if(path==='attack-sessions/current')data=session;
 if(path==='attack-sessions/start'){session=session&&!session.ended_at?session:{id:1,started_at:'2026-10-19T12:00:00+00:00',ended_at:null};data=session;}
 if(path==='attack-sessions/1/end'){session={...session!,ended_at:'2026-10-19T13:00:00+00:00'};data=session;}
 return {ok:true,status:200,json:async()=>data};
 }));});
afterEach(()=>{cleanup();vi.unstubAllGlobals()});
const props=()=>({contacts,profile,loading:false,dataError:'',onRetry:vi.fn(),onExit:vi.fn(),onSetup:vi.fn(),onEdit:vi.fn(),onLog:vi.fn()});
describe('attack assistance',()=>{
 it('selects a saved contact and prepares safe call/SMS links without activating them',async()=>{
  const user=userEvent.setup();render(<AttackMode {...props()}/>);
  await user.selectOptions(screen.getByLabelText('Trusted contact'),'2');
  expect(screen.getByRole('link',{name:'Call contact'})).toHaveAttribute('href','tel:+919999900002');
  expect(screen.getByRole('link',{name:'Prepare SMS'}).getAttribute('href')).toContain('sms:+919999900002');
  expect(decodeURIComponent(screen.getByRole('link',{name:'Prepare SMS'}).getAttribute('href')!)).toContain(supportMessage);
  expect(screen.getByRole('link',{name:/Emergency call/})).toHaveAttribute('href','tel:112');
  expect(vi.mocked(fetch).mock.calls.every(([u])=>String(u).startsWith('/api/'))).toBe(true);
 });
 it('offers contact setup when none exist',async()=>{
  const p=props();render(<AttackMode {...p} contacts={[]}/>);
  expect(screen.getByText('No trusted contact saved yet.')).toBeInTheDocument();
  expect(screen.queryByRole('link',{name:'Call contact'})).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole('button',{name:'Set up a trusted contact'}));expect(p.onSetup).toHaveBeenCalledOnce();
 });
 it('renders saved support preferences and allows review outside attack mode',async()=>{
  const p=props();render(<AttackMode {...p}/>);
  await userEvent.click(screen.getByText('My support card'));
  for(const value of [profile.support,profile.avoid,profile.communication])expect(screen.getByText(value)).toBeVisible();
  await userEvent.click(screen.getByRole('button',{name:'Review or edit outside Attack Mode'}));expect(p.onEdit).toHaveBeenCalledOnce();
 });
 it('starts and ends only through explicit action and reloads session status',async()=>{
  const p=props(),user=userEvent.setup();const view=render(<AttackMode {...p}/>);
  await screen.findByText('No active session');
  await user.click(screen.getByRole('button',{name:'Start attack session'}));await screen.findByText(/Session active/);
  await user.click(screen.getByRole('button',{name:'Exit Attack Mode'}));expect(p.onExit).toHaveBeenCalledOnce();
  expect(session?.ended_at).toBeNull();view.unmount();render(<AttackMode {...p}/>);
  await screen.findByText(/Session active/);
  await user.click(screen.getByRole('button',{name:'End attack session'}));await screen.findByText(/Session ended/);
 });
 it('keeps emergency access available during session API failure',async()=>{
  fail=true;render(<AttackMode {...props()}/>);
  await screen.findByRole('alert');expect(screen.getByRole('link',{name:/Emergency call/})).toHaveAttribute('href','tel:112');
  expect(screen.getByRole('button',{name:'Retry session status'})).toBeEnabled();
 });
 it('does not misrepresent loading or failed contacts as missing contacts',()=>{
  const view=render(<AttackMode {...props()} contacts={[]} loading/>);
  expect(screen.getByText('Loading contacts…')).toBeInTheDocument();
  expect(screen.queryByText('No trusted contact saved yet.')).not.toBeInTheDocument();
  view.rerender(<AttackMode {...props()} contacts={[]} dataError="Unavailable"/>);
  expect(screen.getByText('Contacts and preferences could not be loaded.')).toBeInTheDocument();
 });
 it('supports iOS and Android SMS URI formats with encoded text',()=>{
  expect(smsLink('+91 123','iPhone',0)).toBe('sms:+91123&body='+encodeURIComponent(supportMessage));
  expect(smsLink('+91 123','Android',0)).toBe('sms:+91123?body='+encodeURIComponent(supportMessage));
  expect(smsLink('+91 123','Macintosh',5)).toContain('&body=');
 });
 it('navigates by keyboard, restores focus and preserves the chosen theme',async()=>{
  const user=userEvent.setup();render(<App/>);
  await screen.findByRole('heading',{name:'A gentler day, Alex.'});
  await user.selectOptions(screen.getByLabelText('Color theme'),'dark');
  const enter=screen.getByRole('button',{name:'Enter Attack Mode'});enter.focus();await user.keyboard('{Enter}');
  await waitFor(()=>expect(screen.getByRole('heading',{name:'One thing at a time.'})).toHaveFocus());
  expect(document.documentElement.dataset.theme).toBe('attack');
  await user.tab();expect(screen.getByRole('button',{name:'Exit Attack Mode'})).toHaveFocus();
  await user.keyboard('{Enter}');expect(screen.getByRole('button',{name:'Enter Attack Mode'})).toHaveFocus();
  expect(document.documentElement.dataset.theme).toBe('dark');
 });
 it('keeps diary logging dark and traps keyboard focus inside its dialog',async()=>{
  const user=userEvent.setup();render(<App/>);await screen.findByRole('heading',{name:'A gentler day, Alex.'});
  await user.click(screen.getByRole('button',{name:'Enter Attack Mode'}));await user.click(screen.getByRole('button',{name:'Log an episode'}));
  expect(document.documentElement.dataset.theme).toBe('attack');
  expect(screen.getByRole('dialog')).toBeInTheDocument();
  const save=screen.getByRole('button',{name:'Save episode'});save.focus();await user.tab();expect(screen.getByRole('button',{name:'Close dialog'})).toHaveFocus();
  await user.keyboard('{Escape}');expect(screen.queryByRole('dialog')).not.toBeInTheDocument();expect(screen.getByRole('button',{name:'Log an episode'})).toHaveFocus();
 });
 it.each([
  ['Trusted contacts','Set up a trusted contact'],
  ['Caregiver profile','Review or edit outside Attack Mode'],
 ])('focuses %s on navigation, including same-page handoffs, without changing ordinary exit focus',async(destination,action)=>{
  fixtureContacts=[];
  const user=userEvent.setup();render(<App/>);
  await screen.findByRole('heading',{name:'A gentler day, Alex.'});
  for(let visit=0;visit<2;visit++){
   screen.getByRole('button',{name:'Enter Attack Mode'}).focus();await user.keyboard('{Enter}');
   await waitFor(()=>expect(screen.getByRole('heading',{name:'One thing at a time.'})).toHaveFocus());
   if(destination==='Caregiver profile')await user.click(screen.getByText('My support card',{exact:true}));
   const navigate=await screen.findByRole('button',{name:action});navigate.focus();await user.keyboard('{Enter}');
   const title=screen.getByRole('heading',{name:destination});
   await waitFor(()=>expect(title).toHaveFocus());
   await user.tab();expect(title).not.toHaveFocus();
  }
  const enter=screen.getByRole('button',{name:'Enter Attack Mode'});enter.focus();await user.keyboard('{Enter}');
  screen.getByRole('button',{name:'Exit Attack Mode'}).focus();await user.keyboard('{Enter}');
  expect(screen.getByRole('button',{name:'Enter Attack Mode'})).toHaveFocus();
  if(destination==='Trusted contacts'){
   const add=screen.getByRole('button',{name:'Add contact'});await user.click(add);
   await screen.findByRole('dialog');await user.keyboard('{Escape}');expect(add).toHaveFocus();
  }
 });
 it('makes a newly started session available to the diary without reloading',async()=>{
  const user=userEvent.setup();render(<App/>);await screen.findByRole('heading',{name:'A gentler day, Alex.'});
  await user.click(screen.getByRole('button',{name:'Enter Attack Mode'}));await screen.findByText('No active session');
  await user.click(screen.getByRole('button',{name:'Start attack session'}));await screen.findByText(/Session active/);
  await user.click(screen.getByRole('button',{name:'Log an episode'}));await user.click(screen.getByText(/Optional details/));
  expect(screen.getByRole('option',{name:/Session 1/})).toBeInTheDocument();
 });

});
