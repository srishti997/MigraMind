// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import {afterEach,beforeEach,expect,test,vi} from 'vitest';
import {cleanup,render,screen,fireEvent,waitFor,act} from '@testing-library/react';
import {AttackMode} from './AttackMode';
import {SOSMessage,helpRequest} from './SOSMessage';
import {SupportCard,cardText} from './SupportCard';
import {DEFAULT_PREFERENCES} from './support';
import {smsLink} from './assistance';
const contacts=[{id:1,name:'Synthetic Jamie',phone:'+12025550100',relationship:'Friend'},{id:2,name:'Synthetic Sam',phone:'+12025550101',relationship:'Friend'}];
const profile={name:'Synthetic',environment:'My chosen quiet space',support:'Ask before visiting',avoid:'Strong scents',communication:'Text softly'};
const props=()=>({contacts,profile,loading:false,dataError:'',onRetry:vi.fn(),onExit:vi.fn(),onSetup:vi.fn(),onEdit:vi.fn(),onLog:vi.fn()});
const messageProps=()=>({contacts,contact:contacts[0],onSelect:vi.fn(),initialMessage:'Please check in by text.',onClose:vi.fn(),onSetup:vi.fn()});
beforeEach(()=>{vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,status:200,json:async()=>null})))});
afterEach(()=>{cleanup();vi.unstubAllGlobals();vi.restoreAllMocks()});
test('SOS navigation preserves emergency access and selected contact without dispatch',async()=>{
 const locate=vi.fn(),copy=vi.fn();vi.stubGlobal('navigator',{userAgent:'Android',maxTouchPoints:0,geolocation:{getCurrentPosition:locate},clipboard:{writeText:copy}});
 render(<AttackMode {...props()} preferences={{...DEFAULT_PREFERENCES,emergency_number:'999',help_message:'My saved request'}}/>);
 expect(screen.getByRole('link',{name:/Emergency call/})).toHaveAttribute('href','tel:999');
 const sos=screen.getByRole('button',{name:'SOS / Get help'});fireEvent.click(sos);
 expect(screen.getByRole('heading',{name:'Get help from someone you trust'})).toHaveFocus();
 fireEvent.change(screen.getByLabelText('Trusted contact'),{target:{value:'2'}});
 expect(screen.getByRole('link',{name:'Call Synthetic Sam'})).toHaveAttribute('href','tel:+12025550101');
 expect(screen.getByRole('link',{name:'Open SMS composer'})).toHaveAttribute('href',expect.stringContaining(encodeURIComponent('My saved request')));
 expect(locate).not.toHaveBeenCalled();expect(copy).not.toHaveBeenCalled();
 fireEvent.click(screen.getByRole('button',{name:'Close help request'}));expect(sos).toHaveFocus();
 await waitFor(()=>expect(vi.mocked(fetch)).toHaveBeenCalled());
 expect(vi.mocked(fetch).mock.calls.every(([,options])=>!options||options.method==='GET')).toBe(true);
});
test('missing contacts still allow copying a request and emergency calling',async()=>{
 render(<AttackMode {...props()} contacts={[]}/>);fireEvent.click(screen.getByRole('button',{name:'SOS / Get help'}));
 expect(screen.queryByRole('link',{name:'Open SMS composer'})).toBeNull();
 expect(screen.getByRole('button',{name:'Copy help message'})).toBeEnabled();
 expect(screen.getByRole('link',{name:/Emergency call/})).toHaveAttribute('href','tel:112');
 expect(screen.getByRole('button',{name:'Set up a trusted contact'})).toBeVisible();
});
test('edited request generates encoded SMS text; copying does not send it',async()=>{
 const copy=vi.fn(async()=>{});vi.stubGlobal('navigator',{userAgent:'Android',maxTouchPoints:0,clipboard:{writeText:copy}});
 render(<SOSMessage {...messageProps()}/>);fireEvent.change(screen.getByLabelText('Help-request message'),{target:{value:'Please help & text first?'}});
 expect(screen.getByRole('link',{name:'Open SMS composer'})).toHaveAttribute('href',smsLink(contacts[0].phone,'Android',0,'Please help & text first?'));
 fireEvent.click(screen.getByRole('button',{name:'Copy help message'}));
 await waitFor(()=>expect(copy).toHaveBeenCalledWith('Please help & text first?'));
 expect(screen.getByText(/Nothing was sent/)).toBeVisible();
 expect(smsLink('+12025550100','iPhone',0,'A & B')).toBe('sms:+12025550100&body=A%20%26%20B');
});
test('copy failure selects the manual preview fallback',async()=>{
 vi.stubGlobal('navigator',{userAgent:'Android',maxTouchPoints:0,clipboard:{writeText:vi.fn(async()=>{throw new Error('denied')})}});
 render(<SOSMessage {...messageProps()}/>);fireEvent.click(screen.getByRole('button',{name:'Copy help message'}));
 await screen.findByText(/Clipboard unavailable/);const preview=screen.getByLabelText('Prepared message to copy or send') as HTMLTextAreaElement;
 expect(preview).toHaveFocus();expect(preview.selectionStart).toBe(0);expect(preview.selectionEnd).toBe(preview.value.length);
});
test('location requires checkbox consent AND a one-time request; removed on recipient changes',async()=>{
 let success!:(result:GeolocationPosition)=>void;const locate=vi.fn((callback)=>{success=callback});const copy=vi.fn(async()=>{});
 vi.stubGlobal('navigator',{userAgent:'Android',maxTouchPoints:0,geolocation:{getCurrentPosition:locate},clipboard:{writeText:copy}});
 const p=messageProps(),view=render(<SOSMessage {...p}/>);fireEvent.click(screen.getByText(/Optional one-time location/));
 expect(screen.getByRole('button',{name:'Get my location once'})).toBeDisabled();
 fireEvent.click(screen.getByRole('checkbox'));expect(locate).not.toHaveBeenCalled();
 fireEvent.click(screen.getByRole('button',{name:'Get my location once'}));
 expect(locate).toHaveBeenCalledWith(expect.any(Function),expect.any(Function),{enableHighAccuracy:false,timeout:10000,maximumAge:0});
 act(()=>success({coords:{latitude:12.34,longitude:56.78,accuracy:75}} as GeolocationPosition));
 expect((screen.getByLabelText('Prepared message to copy or send') as HTMLTextAreaElement).value).toContain('Location: 12.3400, 56.7800');
 expect(copy).not.toHaveBeenCalled();expect(vi.mocked(fetch)).not.toHaveBeenCalled();
 view.rerender(<SOSMessage {...p} contact={contacts[1]}/>);
 expect(screen.getByRole('checkbox')).not.toBeChecked();
 expect((screen.getByLabelText('Prepared message to copy or send') as HTMLTextAreaElement).value).not.toContain('Location:');
});
test('revoked consent discards pending location results; permission denial stays usable',async()=>{
 let success!:(result:GeolocationPosition)=>void,fail!:()=>void;
 const locate=vi.fn((ok,error)=>{success=ok;fail=error});
 vi.stubGlobal('navigator',{userAgent:'Android',maxTouchPoints:0,geolocation:{getCurrentPosition:locate}});
 render(<SOSMessage {...messageProps()}/>);fireEvent.click(screen.getByText(/Optional one-time location/));
 fireEvent.click(screen.getByRole('checkbox'));fireEvent.click(screen.getByRole('button',{name:'Get my location once'}));
 fireEvent.click(screen.getByRole('checkbox'));
 act(()=>success({coords:{latitude:12.34,longitude:56.78,accuracy:75}} as GeolocationPosition));
 expect(screen.getByLabelText('Prepared message to copy or send')).toHaveValue('Please check in by text.');
 fireEvent.click(screen.getByRole('checkbox'));fireEvent.click(screen.getByRole('button',{name:'Get my location once'}));act(()=>fail());
 expect(screen.getByText(/permission declined/)).toBeVisible();expect(screen.getByRole('link',{name:'Open SMS composer'})).toBeVisible();
});
test('guide includes only saved preferences and requires explicit review before sharing',()=>{
 const copy=vi.fn();vi.stubGlobal('navigator',{clipboard:{writeText:copy}});
 render(<SupportCard profile={profile} preferences={DEFAULT_PREFERENCES}/>);
 for(const text of [profile.environment,profile.support,profile.avoid,profile.communication])expect(screen.getByText(text)).toBeVisible();
 expect(screen.queryByLabelText('Card text to share')).toBeNull();expect(copy).not.toHaveBeenCalled();
 fireEvent.click(screen.getByRole('button',{name:'Review card for sharing'}));
 expect(screen.getByLabelText('Card text to share')).toHaveValue(cardText(profile,DEFAULT_PREFERENCES));expect(copy).not.toHaveBeenCalled();
 expect(helpRequest('Help',null)).toBe('Help');
});
