// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import {afterEach,expect,test,vi} from 'vitest';
import {cleanup,render,screen,fireEvent,waitFor,act} from '@testing-library/react';
import {Authentication} from './Authentication';
import {AccountSettings} from './AccountSettings';
import {clearAuthentication} from './api';
vi.mock('./main',()=>({App:()=> <div>Private workspace</div>}));
afterEach(()=>{cleanup();vi.useRealTimers();vi.restoreAllMocks();clearAuthentication()});
const account={id:1,email:'synthetic@example.test',display_name:'Synthetic',created_at:'2026-10-19T00:00:00Z'};
test('sign-in keeps health screens gated and emergency calling directly accessible',async()=>{
 const fetcher=vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(JSON.stringify({user:null,csrf_token:'test-csrf'})));
 render(<Authentication/>);
 await screen.findByRole('button',{name:'Sign in'});
 expect(screen.queryByRole('navigation')).toBeNull();
 expect(screen.getByRole('link',{name:/Emergency call/}).getAttribute('href')).toBe('tel:112');
 fireEvent.change(screen.getByLabelText('Email'),{target:{value:account.email}});
 fireEvent.change(screen.getByLabelText('Password'),{target:{value:'Synthetic-password-123'}});
 fetcher.mockResolvedValueOnce(new Response(JSON.stringify({detail:'Email or password is incorrect'}),{status:401}));
 fireEvent.click(screen.getByRole('button',{name:'Sign in'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('Email or password is incorrect');
 const options=fetcher.mock.calls.at(-1)![1]!;
 expect(options.credentials).toBe('include');expect(options.headers).toMatchObject({'X-CSRF-Token':'test-csrf'});
});
test('registration uses an explicit detailed entry flow',async()=>{
 vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(JSON.stringify({user:null,csrf_token:'test-csrf'})));
 render(<Authentication/>);await screen.findByRole('button',{name:'Sign in'});
 fireEvent.click(screen.getByRole('button',{name:'Create a new account'}));
 expect(screen.getByLabelText('Display name')).toBeRequired();
 expect(screen.getByLabelText('Password')).toHaveAttribute('minLength','12');
 expect(screen.getByText(/Old local records remain unassigned/)).toBeVisible();
});
test('hide mounted health screens at the server session deadline',async()=>{
 vi.useFakeTimers();vi.setSystemTime(new Date('2026-10-19T00:00:00Z'));
 vi.spyOn(globalThis,'fetch')
  .mockResolvedValueOnce(new Response(JSON.stringify({user:account,csrf_token:'test-csrf',expires_at:'2026-10-19T00:00:01Z'})))
  .mockImplementation(async()=>new Response(JSON.stringify({user:null,csrf_token:'anonymous-csrf'})));
 render(<Authentication/>);await act(async()=>{await Promise.resolve()});
 expect(screen.getByText('Private workspace')).toBeVisible();
 await act(async()=>{vi.advanceTimersByTime(1100);await Promise.resolve()});
 expect(screen.queryByText('Private workspace')).toBeNull();
 expect(screen.getByRole('link',{name:/Emergency call/})).toHaveAttribute('href','tel:112');
});
test('account deletion requires password and typed confirmation; consent requires explicit confirmation',async()=>{
 const fetcher=vi.spyOn(globalThis,'fetch').mockImplementation(async input=>new Response(JSON.stringify(String(input).endsWith('contacts')?[{id:7,name:'Synthetic caregiver'}]:[])));
 const onDeleted=vi.fn();render(<AccountSettings account={account} onChange={vi.fn()} onLogout={vi.fn()} onDeleted={onDeleted}/>);
 const checkbox=await screen.findByRole('checkbox');expect(checkbox).not.toBeChecked();expect(checkbox).toBeRequired();
 expect(screen.getByLabelText('Current password')).toBeRequired();
 expect(screen.getByLabelText('Type DELETE to confirm')).toHaveAttribute('pattern','DELETE');
 expect(onDeleted).not.toHaveBeenCalled();
 expect(fetcher.mock.calls.every(([,options])=>!options?.method||options.method==='GET')).toBe(true);
 fireEvent.click(checkbox);fireEvent.click(screen.getByRole('button',{name:'Record consent (sharing disabled)'}));
 await waitFor(()=>expect(fetcher.mock.calls.some(([path,options])=>String(path).endsWith('account/consents')&&options?.method==='POST')).toBe(true));
 expect(onDeleted).not.toHaveBeenCalled();
});
