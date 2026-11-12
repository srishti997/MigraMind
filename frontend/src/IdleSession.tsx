import {useEffect,useLayoutEffect,useRef,useState} from 'react';
import {createPortal} from 'react-dom';
import {api,ApiError} from './api';

const WARNING_MS=5*60*1000;
const IDLE_MS=30*60*1000;
export type IdleSession={activity:number,absolute:number,absoluteDeadline:number,deadline:number,binding:string,sampledAt:number,sampledWall:number};

// Only a complete, explicit backend-enabled contract activates this UI. Times are
// anchored before the request to subtract latency conservatively, never optimistically.
export function readIdleSession(result:any,started:number,previous?:IdleSession):IdleSession|null{
 const fields=['server_time','last_activity_at_ms','idle_expires_at'];
 if(!fields.some(field=>field in result)){if(previous)throw new Error('Idle session information is unavailable.');return null}
 if(result.demo_mode===true)throw new Error('Idle testing is unavailable in the shared demonstration.');
 const server=Date.parse(result.server_time),absolute=Date.parse(result.expires_at),idle=Date.parse(result.idle_expires_at),activity=result.last_activity_at_ms;
 if(!Number.isFinite(server)||!Number.isFinite(absolute)||!Number.isFinite(idle)||!Number.isSafeInteger(activity)||activity<0||activity>server||idle!==Math.min(absolute,activity+IDLE_MS)||previous&&absolute!==previous.absolute)throw new Error('Idle session information is invalid.');
 const binding=result.csrf_token??previous?.binding;
 if(typeof binding!=='string'||!binding)throw new Error('Idle session information is invalid.');
 const absoluteDeadline=Math.min(started+absolute-server,previous?.absoluteDeadline??Infinity);
 return {activity,absolute,absoluteDeadline,deadline:Math.min(started+idle-server,absoluteDeadline),binding,sampledAt:performance.now(),sampledWall:Date.now()};
}

export function IdleSessionWarning({session,accountId,onUpdate,onExpired,onSignOut}:{session:IdleSession,accountId:number,onUpdate:(value:IdleSession)=>void,onExpired:()=>void,onSignOut:()=>Promise<void>}){
 const [tick,setTick]=useState(0),[busy,setBusy]=useState(false),[error,setError]=useState(''),[canCheck,setCanCheck]=useState(false);
 const [dialogSlot,setDialogSlot]=useState<HTMLElement|null>(null);
 const panel=useRef<HTMLElement>(null),stay=useRef<HTMLButtonElement>(null),opener=useRef<HTMLElement|null>(null),wasWarning=useRef(false),restore=useRef(false),mounted=useRef(true);
 const expired=useRef(onExpired);expired.current=onExpired;
 const remaining=session.deadline-performance.now();
 const warning=remaining<=WARNING_MS;
 useEffect(()=>{mounted.current=true;return()=>{mounted.current=false}},[]);
 useEffect(()=>{const focused=(event:FocusEvent)=>{const target=event.target;if(target instanceof HTMLElement&&!target.closest('.idle-warning')&&target.closest('.app,main'))opener.current=target};document.addEventListener('focusin',focused);return()=>document.removeEventListener('focusin',focused)},[]);
 useLayoutEffect(()=>{const update=()=>{const target=document.getElementById('idle-warning-slot');setDialogSlot(previous=>previous===target?previous:target)};update();const observer=new MutationObserver(update);observer.observe(document.body,{childList:true,subtree:true});return()=>observer.disconnect()},[]);
 useLayoutEffect(()=>{
  if(warning&&!wasWarning.current)opener.current=document.activeElement instanceof HTMLElement&&document.activeElement!==document.body?document.activeElement:null;
  if(!warning&&wasWarning.current&&restore.current){
   const target=opener.current?.isConnected?opener.current:document.getElementById('page-content');target?.focus();restore.current=false;
  }
  wasWarning.current=warning;
 },[warning]);
 useEffect(()=>{
  const update=()=>{
   const mono=performance.now(),wall=Date.now(),elapsed=wall-session.sampledWall;
   const lost=Math.max(0,elapsed-(mono-session.sampledAt));
   if(elapsed<0||mono>=session.deadline-lost)expired.current();
   else if(lost>0)onUpdate({...session,deadline:session.deadline-lost,absoluteDeadline:session.absoluteDeadline-lost,sampledAt:mono,sampledWall:wall});
   else setTick(value=>value+1);
  };
  const warn=setTimeout(update,Math.max(0,Math.ceil(session.deadline-performance.now()-WARNING_MS)));
  const end=setTimeout(update,Math.max(0,Math.ceil(session.deadline-performance.now())));
  const visible=()=>{if(document.visibilityState==='visible')update()};
  document.addEventListener('visibilitychange',visible);
  window.addEventListener('focus',visible);
  return()=>{clearTimeout(warn);clearTimeout(end);document.removeEventListener('visibilitychange',visible);window.removeEventListener('focus',visible)};
 },[session]);
 useEffect(()=>{if(!busy&&error&&warning&&(document.activeElement===document.body||panel.current?.contains(document.activeElement)))stay.current?.focus()},[busy,error,warning]);
 // Read the tick so warning timers render without an interval or activity heartbeat.
 void tick;
 async function perform(check=false){
  if(busy)return;
  if(performance.now()>=session.deadline){onExpired();return}
  restore.current=true;setBusy(true);setError('');
  const started=performance.now();
  try{
   const result=check?await api('auth/session'):await api('auth/activity','POST',{expected_last_activity_at_ms:session.activity});
   if(!mounted.current)return;
   if(performance.now()>=session.deadline){onExpired();return}
   if(check&&(!result.user||result.user.id!==accountId||result.csrf_token!==session.binding)){onExpired();return}
   const updated=readIdleSession(result,started,session);
   if(!updated||updated.deadline<=performance.now()){onExpired();return}
   if(!check&&updated.activity<=session.activity)throw new Error('Activity was not confirmed.');
   onUpdate(updated);setCanCheck(false);
  }catch(cause){
   if(!mounted.current)return;
   if(cause instanceof ApiError&&cause.status===401){onExpired();return}
   setCanCheck(cause instanceof ApiError&&cause.status===409);
   setError('Your session was not extended. '+(cause instanceof ApiError&&cause.status===409?'Check session status before a new attempt.':'Check your connection or sign out.'));
  }finally{if(mounted.current)setBusy(false)}
 }
 if(!warning)return null;
 const content=<section ref={panel} className="idle-warning" aria-labelledby="idle-warning-heading">
  <div role="status" aria-live="polite" aria-atomic="true"><h2 id="idle-warning-heading">Your session will end soon</h2><p>Stay signed in before the deadline to continue. Unsaved diary and check-in entries will be discarded when the workspace closes. Nothing is saved automatically.</p></div>
  {session.absoluteDeadline-session.deadline<1&&<p>The fixed sign-in limit cannot be extended.</p>}
  <div className="idle-warning-actions"><button type="button" ref={stay} className="primary" disabled={busy} onClick={()=>{void perform()}}>Stay signed in</button><button type="button" className="secondary" disabled={busy} onClick={async()=>{setBusy(true);setError('');try{await onSignOut()}catch{if(mounted.current)setError('Sign out was not confirmed. Check your connection and try again.')}finally{if(mounted.current)setBusy(false)}}}>Sign out</button>
  {canCheck&&<button type="button" className="secondary" disabled={busy} onClick={()=>{void perform(true)}}>Check session status</button>}</div>
  {busy&&<p role="status">Checking session…</p>}{error&&<p role="alert">{error}</p>}
 </section>;
 return dialogSlot?createPortal(content,dialogSlot):content;
}
