// Broadcast only a change signal, never account identity, health data or tokens.
const channelName='migramind-session-change';
// Ephemeral notification deduplication only; never an account/session identifier.
const source=globalThis.crypto?.randomUUID?.()??String(Math.random());
export function announceSessionChange(){
 // Some privacy policies expose BroadcastChannel but reject its constructor.
 try{
  if(typeof BroadcastChannel!=='undefined'){
   const channel=new BroadcastChannel(channelName);
   try{channel.postMessage({type:'changed',source})}finally{channel.close()}
   return;
  }
 }catch{/* Fall back to the storage change signal. */}
 try{localStorage.setItem(channelName,crypto.randomUUID())}catch{/* Stale API reads remain blocked server-side. */}
}
export function observeSessionChange(callback:()=>void){
 try{
  if(typeof BroadcastChannel!=='undefined'){
   const channel=new BroadcastChannel(channelName);channel.onmessage=event=>{if(event.data==='changed'||event.data?.type==='changed'&&event.data.source!==source)callback()};
   return()=>{try{channel.close()}catch{/* Cleanup must not interrupt unmounting. */}};
  }
 }catch{/* Cross-tab messaging is optional; authentication must still render. */}
 const listener=(event:StorageEvent)=>{if(event.key===channelName)callback()};
 window.addEventListener('storage',listener);return()=>window.removeEventListener('storage',listener);
}
