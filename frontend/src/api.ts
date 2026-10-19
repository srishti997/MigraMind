let csrfToken='';
export function clearAuthentication(){csrfToken=''}
export async function api(path:string,method='GET',data?:unknown){
 const r=await fetch(`${import.meta.env.VITE_API_URL||''}/api/${path}`,{method,credentials:'include',headers:{'Content-Type':'application/json',...(csrfToken?{'X-CSRF-Token':csrfToken}:{})},body:data?JSON.stringify(data):undefined});
 if(r.status===401&&!path.startsWith('auth/'))window.dispatchEvent(new Event('migramind-session-ended'));
 if(!r.ok){let message='Could not save or load your data. Check your connection and try again.';try{const error=await r.json();if(typeof error.detail==='string')message=error.detail;else if(Array.isArray(error.detail))message=error.detail.map((d:{loc:string[],msg:string})=>`${d.loc.slice(1).join(' ')}: ${d.msg}`).join('; ')}catch{/* Preserve a generic error without logging records. */}throw new Error(message)}
 const result=r.status===204?null:await r.json();
 if(path.startsWith('auth/')&&result?.csrf_token)csrfToken=result.csrf_token;
 return result;
}
