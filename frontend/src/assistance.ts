export type TrustedContact={id:number,name:string,relationship:string,phone:string};
export type SupportProfile={name:string,support:string,avoid:string,communication:string,environment?:string};
export type AttackSession={id:number,started_at:string,ended_at:string|null};
export const supportMessage='I am having a migraine attack and would appreciate support. Please check in by text when you can.';
// Syntax validation only. Do not infer a country, number length or reachability.
export function phoneNumber(phone:string){
 const text=phone.trim();
 if(text.length>32||!/^\+?[0-9 ()-]+$/.test(text)||!/[0-9]/.test(text))return '';
 let opened=false,digits=0;
 for(const char of text){
  if(char==='('){if(opened)return '';opened=true;digits=0}
  else if(char===')'){if(!opened||!digits)return '';opened=false}
  else if(opened&&/[0-9]/.test(char))digits++;
 }
 return opened?'':text.replace(/[ ()-]/g,'');
}
export const callLink=(phone:string)=>{const number=phoneNumber(phone);return number?'tel:'+number:undefined};
export function smsLink(phone:string,userAgent=navigator.userAgent,touchPoints=navigator.maxTouchPoints,message=supportMessage){
 const number=phoneNumber(phone);if(!number)return undefined;
 const ios=/iPhone|iPad|iPod/.test(userAgent)||(/Macintosh/.test(userAgent)&&touchPoints>1);
 return `sms:${number}${ios?'&':'?'}body=${encodeURIComponent(message)}`;
}
