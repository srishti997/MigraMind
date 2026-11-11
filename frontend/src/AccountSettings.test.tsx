// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import {afterEach,beforeEach,expect,test,vi} from 'vitest';
import {cleanup,render,screen,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {AccountSettings} from './AccountSettings';
import {api} from './api';

vi.mock('./api',()=>({api:vi.fn()}));
beforeEach(()=>{vi.mocked(api).mockResolvedValue([])});
afterEach(()=>{cleanup();vi.resetAllMocks()});
const account={id:1,email:'synthetic@example.test',display_name:'Synthetic',created_at:'2026-11-11T00:00:00Z'};
function setup(onLogout=vi.fn().mockResolvedValue(undefined),demoMode=false){
 render(<AccountSettings account={account} onChange={vi.fn()} onLogout={onLogout} onDeleted={vi.fn()} demoMode={demoMode}/>);
 return {user:userEvent.setup(),onLogout};
}

test('keyboard opens confirmation, cancellation restores focus and sends nothing',async()=>{
 const {user,onLogout}=setup();
 const trigger=screen.getByRole('button',{name:'Sign out all sessions'});
 trigger.focus();await user.keyboard('{Enter}');
 const password=screen.getByLabelText('Confirm current password');expect(password).toHaveFocus();
 expect(password).toHaveAttribute('type','password');expect(password).toHaveAttribute('autocomplete','current-password');expect(password).toBeRequired();
 await user.type(password,'Synthetic-not-submitted');
 await user.tab();expect(screen.getByRole('button',{name:'Confirm sign out all sessions'})).toHaveFocus();
 await user.tab();expect(screen.getByRole('button',{name:'Cancel sign out all sessions'})).toHaveFocus();
 await user.keyboard('{Enter}');
 expect(screen.queryByLabelText('Confirm current password')).toBeNull();
 expect(screen.getByRole('button',{name:'Sign out all sessions'})).toHaveFocus();
 expect(onLogout).not.toHaveBeenCalled();
 expect(vi.mocked(api).mock.calls.every(([,method])=>!method||method==='GET')).toBe(true);
 await user.keyboard('{Enter}');expect(screen.getByLabelText('Confirm current password')).toHaveValue('');
});

test('confirmation requires a password and Enter submits once; pending action cannot be repeated',async()=>{
 let complete!:()=>void;
 const onLogout=vi.fn(()=>new Promise<void>(resolve=>{complete=resolve}));
 const {user}=setup(onLogout);
 await user.click(screen.getByRole('button',{name:'Sign out all sessions'}));
 await user.keyboard('{Enter}');expect(onLogout).not.toHaveBeenCalled();
 await user.type(screen.getByLabelText('Confirm current password'),'Synthetic-password-123');await user.keyboard('{Enter}');
 expect(onLogout).toHaveBeenCalledExactlyOnceWith('Synthetic-password-123');
 expect(screen.getByLabelText('Confirm current password')).toHaveValue('');
 expect(screen.getByRole('button',{name:'Signing out…'})).toBeDisabled();
 expect(screen.getByRole('button',{name:'Cancel sign out all sessions'})).toBeDisabled();
 complete();await waitFor(()=>expect(screen.getByLabelText('Confirm current password')).toBeEnabled());
});

test('failed confirmation reports failure, clears password and permits a focused retry',async()=>{
 const onLogout=vi.fn().mockRejectedValue(new Error('Password confirmation failed'));
 const {user}=setup(onLogout);
 await user.click(screen.getByRole('button',{name:'Sign out all sessions'}));
 await user.type(screen.getByLabelText('Confirm current password'),'Synthetic-wrong');await user.keyboard('{Enter}');
 expect(await screen.findByRole('alert')).toHaveTextContent('Password confirmation failed');
 expect(screen.getByLabelText('Confirm current password')).toHaveValue('');
 await waitFor(()=>expect(screen.getByLabelText('Confirm current password')).toHaveFocus());
 expect(screen.getByRole('heading',{name:'Your account & privacy'})).toBeVisible();
 expect(screen.queryByRole('status')).toBeNull();
});

test('shared read-only demo keeps ordinary logout but offers no global revocation',async()=>{
 const {user,onLogout}=setup(undefined,true);
 expect(screen.queryByRole('button',{name:'Sign out all sessions'})).toBeNull();
 expect(screen.getByText(/Sign out all sessions is unavailable/)).toBeVisible();
 await user.click(screen.getByRole('button',{name:'Sign out'}));
 expect(onLogout).toHaveBeenCalledExactlyOnceWith();
});
