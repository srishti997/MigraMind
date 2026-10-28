import {useEffect,useState,useRef} from 'react';
import {App} from './main';
import {api,clearAuthentication} from './api';
import {announceSessionChange,observeSessionChange} from './sessionEvents';
export type Account={id:number,email:string,display_name:string,created_at:string};

export function Authentication(){
 const [user,setUser]=useState<Account|null>(null),[ready,setReady]=useState(false),[error,setError]=useState(''),[register,setRegister]=useState(false),[busy,setBusy]=useState(false);
 const revision=useRef(0);
 const [expiresAt,setExpiresAt]=useState<string|null>(null);
 const [demoMode,setDemoMode]=useState(import.meta.env.VITE_DATA_MODE==='synthetic');
 const demoNotice=<p role="note" className="settings-note">Synthetic demonstration: read-only. Use only the provided demo account and password. Do not enter real health information. No clinical predictions are available.</p>;
 const bootstrap=async()=>{const current=++revision.current;try{const result=await api('auth/session');if(current!==revision.current)return;setExpiresAt(result.expires_at||null);setDemoMode(result.demo_mode===true);setUser(result.user);setReady(true)}catch{if(current!==revision.current)return;setError('Could not connect. Check that the local backend is running.');setReady(true)}};
 useEffect(()=>{bootstrap();const changed=()=>{clearAuthentication();setUser(null);setReady(false);setRegister(false);setError('Your session changed.');bootstrap()};const restored=(event:PageTransitionEvent)=>{if(event.persisted)changed()};const stop=observeSessionChange(changed);window.addEventListener('migramind-session-ended',changed);window.addEventListener('pageshow',restored);return()=>{revision.current++;stop();window.removeEventListener('migramind-session-ended',changed);window.removeEventListener('pageshow',restored)}},[]);
 useEffect(()=>{if(!user||!expiresAt)return;const remaining=new Date(expiresAt).getTime()-Date.now();const timer=setTimeout(()=>window.dispatchEvent(new Event('migramind-session-ended')),Math.max(0,remaining));return()=>clearTimeout(timer)},[user,expiresAt]);
 useEffect(()=>{if(!user){try{document.documentElement.dataset.theme=localStorage.getItem('migramind-theme')==='dark'?'dark':'warm'}catch{document.documentElement.dataset.theme='warm'}}},[user]);
 const logout=async()=>{await api('auth/logout','POST');clearAuthentication();announceSessionChange();setUser(null);setReady(false);setRegister(false);await bootstrap()};
 if(user)return <>{demoMode&&demoNotice}<App key={user.id} account={user} onAccountChange={setUser} onLogout={logout} onDeleted={()=>{clearAuthentication();announceSessionChange();setUser(null);setReady(false);setRegister(false);bootstrap()}}/></>;
 return <main className="auth-shell"><section className="panel auth-panel"><p className="eyebrow">MIGRAMIND · YOUR PERSONAL SPACE</p><h1>{register?'A space for you.':'Welcome back.'}</h1>{demoMode&&demoNotice}<p>Account-isolated local prototype. Not a medical device or monitored emergency service.</p>{!ready?<p role="status">Connecting…</p>:<form onSubmit={async e=>{e.preventDefault();setBusy(true);setError('');const data=Object.fromEntries(new FormData(e.currentTarget));try{const result=await api(register?'auth/register':'auth/login','POST',data);revision.current++;announceSessionChange();setExpiresAt(result.expires_at||null);setUser(result.user)}catch(e){setError((e as Error).message)}finally{setBusy(false)}}}>
 {register&&<label>Display name<input name="display_name" autoComplete="nickname" required maxLength={100}/></label>}
 <label>Email<input key={String(demoMode)} defaultValue={demoMode?'demo@synthetic.example.test':''} readOnly={demoMode} name="email" type="email" autoComplete="username" required maxLength={254}/></label>
 <label>Password<input name="password" type="password" autoComplete={register?'new-password':'current-password'} required minLength={register?12:1} maxLength={128}/></label>
 {register&&<p className="helper">Use at least 12 characters. Keep this password safe: email verification and password recovery are not available in this prototype. Old local records remain unassigned.</p>}
 <button className="primary full" disabled={busy}>{busy?'Please wait…':register?'Create account':'Sign in'}</button>
 {!demoMode&&<button type="button" className="secondary full" onClick={()=>{setRegister(!register);setError('')}}>{register?'Use an existing account':'Create a new account'}</button>}
 </form>}{error&&<p role="alert" className="error">{error}</p>}<button className="secondary" onClick={bootstrap}>Retry connection</button><div className="settings-note"><div><p>For urgent symptoms or an emergency in India:</p><a className="emergency-action" href="tel:112">Emergency call · 112 (India)</a><p className="helper">You initiate the call. Nothing is dispatched automatically.</p></div></div></section></main>
}
