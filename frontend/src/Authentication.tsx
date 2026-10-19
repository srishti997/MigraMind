import {useEffect,useState} from 'react';
import {App} from './main';
import {api,clearAuthentication} from './api';
export type Account={id:number,email:string,display_name:string,created_at:string};

export function Authentication(){
 const [user,setUser]=useState<Account|null>(null),[ready,setReady]=useState(false),[error,setError]=useState(''),[register,setRegister]=useState(false),[busy,setBusy]=useState(false);
 const bootstrap=async()=>{try{const result=await api('auth/session');setUser(result.user);setReady(true)}catch{setError('Could not connect. Check that the local backend is running.');setReady(true)}};
 useEffect(()=>{bootstrap();const expired=()=>{clearAuthentication();setUser(null);setRegister(false);setError('Your session ended. Sign in to continue.');bootstrap()};window.addEventListener('migramind-session-ended',expired);return()=>window.removeEventListener('migramind-session-ended',expired)},[]);
 useEffect(()=>{if(!user){try{document.documentElement.dataset.theme=localStorage.getItem('migramind-theme')==='dark'?'dark':'warm'}catch{document.documentElement.dataset.theme='warm'}}},[user]);
 const logout=async()=>{await api('auth/logout','POST');clearAuthentication();setUser(null);setRegister(false);await bootstrap()};
 if(user)return <App key={user.id} account={user} onAccountChange={setUser} onLogout={logout} onDeleted={()=>{clearAuthentication();setUser(null);setRegister(false);bootstrap()}}/>;
 return <main className="auth-shell"><section className="panel auth-panel"><p className="eyebrow">MIGRAMIND · YOUR PERSONAL SPACE</p><h1>{register?'A space for you.':'Welcome back.'}</h1><p>Account-isolated local prototype. Not a medical device or monitored emergency service.</p>{!ready?<p role="status">Connecting…</p>:<form onSubmit={async e=>{e.preventDefault();setBusy(true);setError('');const data=Object.fromEntries(new FormData(e.currentTarget));try{const result=await api(register?'auth/register':'auth/login','POST',data);setUser(result.user)}catch(e){setError((e as Error).message)}finally{setBusy(false)}}}>
 {register&&<label>Display name<input name="display_name" autoComplete="nickname" required maxLength={100}/></label>}
 <label>Email<input name="email" type="email" autoComplete="username" required maxLength={254}/></label>
 <label>Password<input name="password" type="password" autoComplete={register?'new-password':'current-password'} required minLength={register?12:1} maxLength={128}/></label>
 {register&&<p className="helper">Use at least 12 characters. Keep this password safe: email verification and password recovery are not available in this prototype. Old local records remain unassigned.</p>}
 <button className="primary full" disabled={busy}>{busy?'Please wait…':register?'Create account':'Sign in'}</button>
 <button type="button" className="secondary full" onClick={()=>{setRegister(!register);setError('')}}>{register?'Use an existing account':'Create a new account'}</button>
 </form>}{error&&<p role="alert" className="error">{error}</p>}<button className="secondary" onClick={bootstrap}>Retry connection</button><div className="settings-note"><div><p>For urgent symptoms or an emergency in India:</p><a className="emergency-action" href="tel:112">Emergency call · 112 (India)</a><p className="helper">You initiate the call. Nothing is dispatched automatically.</p></div></div></section></main>
}
