// Broadcast only a change signal, never account identity, health data or tokens.
const channelName='migramind-session-change';
export function announceSessionChange(){
 if(typeof BroadcastChannel!=='undefined'){
  const channel=new BroadcastChannel(channelName);channel.postMessage('changed');channel.close();return;
 }
 try{localStorage.setItem(channelName,crypto.randomUUID())}catch{/* Stale API reads remain blocked server-side. */}
}
export function observeSessionChange(callback:()=>void){
 if(typeof BroadcastChannel!=='undefined'){
  const channel=new BroadcastChannel(channelName);channel.onmessage=()=>callback();return()=>channel.close();
 }
 const listener=(event:StorageEvent)=>{if(event.key===channelName)callback()};
 window.addEventListener('storage',listener);return()=>window.removeEventListener('storage',listener);
}
