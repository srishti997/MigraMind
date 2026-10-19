import {useEffect,useRef,useState} from 'react';
import {phoneNumber,smsLink} from './assistance';
import type {TrustedContact} from './assistance';

export type OneTimeLocation={latitude:number,longitude:number,accuracy:number};
export function helpRequest(text:string,location:OneTimeLocation|null){
 return text.trim()+(location?`\nLocation: ${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)} (accuracy about ${Math.ceil(location.accuracy)} m).`:'');
}
export function SOSMessage({contacts,contact,onSelect,initialMessage,onClose,onSetup,onGuide,unavailable=false,loading=false,onAction}:{contacts:TrustedContact[],contact?:TrustedContact,onSelect:(id:string)=>void,initialMessage:string,onClose:()=>void,onSetup:()=>void,onGuide?:()=>void,unavailable?:boolean,loading?:boolean,onAction?:(action:'call_contact'|'prepare_sms')=>void}){
 const [draft,setDraft]=useState(initialMessage),[consent,setConsent]=useState(false),[position,setPosition]=useState<(OneTimeLocation&{recipientId:number|null})|null>(null),[locating,setLocating]=useState(false),[status,setStatus]=useState('');
 const request=useRef(0),heading=useRef<HTMLHeadingElement>(null),preview=useRef<HTMLTextAreaElement>(null);
 useEffect(()=>{heading.current?.focus();heading.current?.scrollIntoView?.({block:'nearest',behavior:'auto'});return()=>{request.current++}},[]);
 useEffect(()=>{request.current++;setConsent(false);setPosition(null);setLocating(false);setStatus('')},[contact?.id]);
 const includedPosition=consent&&position?.recipientId===(contact?.id??null)?position:null;
 const message=helpRequest(draft,includedPosition);
 function removeLocation(){request.current++;setConsent(false);setPosition(null);setLocating(false);setStatus('Location removed from this preview. Previously copied text is not changed.')}
 function locate(){
  if(!consent||locating)return;
  if(!navigator.geolocation){setStatus('Location is unavailable. You can still call, copy or prepare your message.');return}
  const current=++request.current;setPosition(null);setLocating(true);setStatus('');
  navigator.geolocation.getCurrentPosition(result=>{
   if(current!==request.current)return;
   const {latitude,longitude,accuracy}=result.coords;
   setLocating(false);
   if(!Number.isFinite(latitude)||!Number.isFinite(longitude)||!Number.isFinite(accuracy)||Math.abs(latitude)>90||Math.abs(longitude)>180||accuracy<0){setStatus('Location could not be read. Continue without it.');return}
   setPosition({latitude,longitude,accuracy,recipientId:contact?.id??null});setStatus('Location added to this preview only. Review it before copying or opening SMS.');
  },()=>{if(current===request.current){setLocating(false);setStatus('Location unavailable or permission declined. Continue without it.')}},
  {enableHighAccuracy:false,timeout:10000,maximumAge:0});
 }
 async function copy(){
  try{if(!navigator.clipboard?.writeText)throw new Error('Unavailable');await navigator.clipboard.writeText(message);setStatus('Copied to your clipboard. Nothing was sent. Clear your clipboard when finished.')}
  catch{preview.current?.focus();preview.current?.select();setStatus('Clipboard unavailable. Select and copy the prepared message manually. Nothing was sent.')}
 }
 return <section id="help-request" className="assistance-card sos-message" aria-labelledby="sos-heading">
 <div className="panel-heading"><h2 id="sos-heading" tabIndex={-1} ref={heading}>Get help from someone you trust</h2><button className="secondary" onClick={onClose}>Close help request</button></div>
 {loading?<p role="status">Loading contacts…</p>:unavailable?<p role="alert">Contacts are unavailable. Retry contacts below. Emergency calling remains available.</p>:contacts.length?<label>Trusted contact<select value={contact?.id||''} onChange={e=>onSelect(e.target.value)}>{contacts.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label>:<><p>No trusted contact saved yet. You can still copy a message or use emergency calling above.</p><button className="secondary" onClick={onSetup}>Set up a trusted contact</button></>}
 {contact&&!unavailable&&!loading&&<a className="attack-button" href={'tel:'+phoneNumber(contact.phone)} onClick={()=>onAction?.('call_contact')}>Call {contact.name}</a>}
 <label>Help-request message<textarea maxLength={400} rows={3} value={draft} onChange={e=>setDraft(e.target.value)}/></label>
 <details><summary>Optional one-time location · off by default</summary><p className="small">Your device may ask for location permission. Nothing is saved to MigraMind or shared until you choose to copy or open SMS. No background tracking.</p><label className="check-option"><input type="checkbox" checked={consent} onChange={e=>{if(e.target.checked){request.current++;setConsent(true);setPosition(null);setStatus('')}else removeLocation()}}/>I consent to attaching my location to this help request.</label><button className="secondary" disabled={!consent||locating} onClick={locate}>{locating?'Getting location…':'Get my location once'}</button></details>
 {includedPosition&&<div className="location-preview"><p>Location is included below. Accuracy is approximate.</p><button className="secondary" onClick={removeLocation}>Remove location</button></div>}
 <label>Prepared message to copy or send<textarea ref={preview} readOnly rows={4} value={message}/></label>
 <div className="sos-actions">
 {contact&&!unavailable&&!loading&&message&&<a className="attack-button" href={smsLink(contact.phone,undefined,undefined,message)} onClick={()=>{onAction?.('prepare_sms');setStatus('SMS composer requested. You must choose to send; delivery is not confirmed.')}}>Open SMS composer</a>}
 <button className="attack-button" disabled={!message} onClick={copy}>Copy help message</button></div>
 <p className="small">Calling opens your dialer. SMS opens a composer where supported; check the recipient and text before sending. If text is missing, paste the copied message. MigraMind cannot confirm calls or message delivery.</p>
 {onGuide&&<button className="secondary" onClick={onGuide}>View caregiver guide</button>}
 {status&&<p role="status">{status}</p>}
 </section>
}
