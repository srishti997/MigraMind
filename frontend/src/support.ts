import type {TrustedContact} from './assistance';
export const ACTIONS=['call_contact','prepare_sms','support_card'] as const;
export type SupportAction=typeof ACTIONS[number];
export const ACTION_LABELS:Record<SupportAction,string>={call_contact:'Call contact',prepare_sms:'Prepare SMS',support_card:'Open my support card'};
export type SupportPreferences={preferred_contact_id:number|null,communication_method:'none'|'call'|'sms',preferred_actions:SupportAction[],large_text:boolean,reduce_motion:boolean,simplified_view:boolean,use_feedback:boolean,ranking_mode:'adaptive'|'fixed'};
export const DEFAULT_PREFERENCES:SupportPreferences={preferred_contact_id:null,communication_method:'none',preferred_actions:[],large_text:false,reduce_motion:false,simplified_view:false,use_feedback:false,ranking_mode:'adaptive'};
export function normalizePreferences(raw?:Partial<SupportPreferences>|null):SupportPreferences{return Object.fromEntries(Object.keys(DEFAULT_PREFERENCES).map(key=>[key,raw?.[key as keyof SupportPreferences]??DEFAULT_PREFERENCES[key as keyof SupportPreferences]])) as SupportPreferences}
export type Recommendation={id:SupportAction,label:string,available:boolean,explanation:string,feedback_count:number};
export type RecommendationResponse={algorithm_version:string,contact_id?:number|null,actions:Recommendation[],recommended_action:SupportAction|null};
export function fallbackRecommendations(p:SupportPreferences,contacts:TrustedContact[]):Recommendation[]{
 const method=p.communication_method==='call'?'call_contact':p.communication_method==='sms'?'prepare_sms':null;
 const pins=[...p.preferred_actions,...(method?[method]:[])];const ordered=Array.from(new Set([...pins,...ACTIONS])) as SupportAction[];
 return ordered.map(id=>({id,label:ACTION_LABELS[id],available:id==='support_card'||contacts.length>0,explanation:p.preferred_actions.includes(id)?'Your explicitly prioritized support action.':id===method?'Matches your saved communication method.':'Saved preferences and stable defaults; feedback ranking is unavailable.',feedback_count:0})).sort((a,b)=>Number(b.available)-Number(a.available));
}
export type SupportFeedback={id:number,session_id:number,action_id:SupportAction,helpful:boolean,created_at:string};
