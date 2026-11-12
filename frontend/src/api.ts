let csrfToken='';
let sessionGeneration=0;
const buildDemo=import.meta.env.VITE_DATA_MODE==='synthetic';
let demoMode=buildDemo;
export class ApiError extends Error{constructor(message:string,public status:number){super(message)}}
export function clearAuthentication(){csrfToken='';demoMode=buildDemo;sessionGeneration++}
export async function api(path:string,method='GET',data?:unknown){
 if(demoMode&&!['GET','HEAD','OPTIONS'].includes(method)&&!['auth/login','auth/logout','v1/research-export'].includes(path))throw new Error('Synthetic demonstration is read-only. Do not enter real health information.');
 const generation=sessionGeneration;
 const r=await fetch(`${import.meta.env.VITE_API_URL||''}/api/${path}`,{method,credentials:'include',cache:'no-store',referrerPolicy:'no-referrer',headers:{'Content-Type':'application/json',...(csrfToken?{'X-CSRF-Token':csrfToken}:{})},body:data?JSON.stringify(data):undefined});
 if(generation!==sessionGeneration)throw new Error('Session changed. Please try again.');
 if(r.status===401&&(!path.startsWith('auth/')||path==='auth/activity'))window.dispatchEvent(new Event('migramind-session-ended'));
 if(!r.ok){let message='Could not save or load your data. Check your connection and try again.';try{if(r.status<500){const error=await r.json();if(typeof error.detail==='string')message=error.detail;else if(Array.isArray(error.detail))message=error.detail.map((d:{loc:string[],msg:string})=>`${d.loc.slice(1).join(' ')}: ${d.msg}`).join('; ')}}catch{/* Preserve a generic error without logging records. */}throw new ApiError(message,r.status)}
 const result=r.status===204?null:await r.json();
 if(generation!==sessionGeneration)throw new Error('Session changed. Please try again.');
 if(buildDemo&&path.startsWith('auth/')&&result?.csrf_token&&result.demo_mode!==true)throw new Error('Synthetic demonstration requires a synthetic backend.');
 if((path==='auth/login'||path==='auth/register')&&result?.user)sessionGeneration++;
 if(path.startsWith('auth/')&&result?.csrf_token)csrfToken=result.csrf_token;
 if(path.startsWith('auth/')&&result?.csrf_token)demoMode=buildDemo||result.demo_mode===true;
 return result;
}
