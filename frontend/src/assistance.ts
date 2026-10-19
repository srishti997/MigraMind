export type TrustedContact={id:number,name:string,relationship:string,phone:string};
export type SupportProfile={name:string,support:string,avoid:string,communication:string,environment?:string};
export type AttackSession={id:number,started_at:string,ended_at:string|null};
export const supportMessage='I am having a migraine attack and would appreciate support. Please check in by text when you can.';
export const phoneNumber=(phone:string)=>phone.replace(/[^+0-9]/g,'');
export function smsLink(phone:string,userAgent=navigator.userAgent,touchPoints=navigator.maxTouchPoints,message=supportMessage){
 const ios=/iPhone|iPad|iPod/.test(userAgent)||(/Macintosh/.test(userAgent)&&touchPoints>1);
 return `sms:${phoneNumber(phone)}${ios?'&':'?'}body=${encodeURIComponent(message)}`;
}
