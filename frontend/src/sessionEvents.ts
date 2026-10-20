// Broadcast only a change signal, never account identity, health data or tokens.
const channelName='migramind-session-change';
export function announceSessionChange(){
 // Some privacy policies expose BroadcastChannel but reject its constructor.
 try{
  if(typeof BroadcastChannel!=='undefined'){
   const channel=new BroadcastChannel(channelName);
   try{channel.postMessage('changed')}finally{channel.close()}
   return;
  }
 }catch{/* Fall back to the storage change signal. */}
 try{localStorage.setItem(channelName,crypto.randomUUID())}catch{/* Stale API reads remain blocked server-side. */}
}
export function observeSessionChange(callback:()=>void){
 try{
  if(typeof BroadcastChannel!=='undefined'){
   const channel=new BroadcastChannel(channelName);channel.onmessage=()=>callback();
   return()=>{try{channel.close()}catch{/* Cleanup must not interrupt unmounting. */}};
  }
 }catch{/* Cross-tab messaging is optional; authentication must still render. */}
 const listener=(event:StorageEvent)=>{if(event.key===channelName)callback()};
 window.addEventListener('storage',listener);return()=>window.removeEventListener('storage',listener);
}
