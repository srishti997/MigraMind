export async function api(path:string,method='GET',data?:unknown){
 const r=await fetch(`${import.meta.env.VITE_API_URL||''}/api/${path}`,{method,headers:{'Content-Type':'application/json'},body:data?JSON.stringify(data):undefined});
 if(!r.ok){let message='Could not save or load your data. Check your connection and try again.';try{const error=await r.json();if(typeof error.detail==='string')message=error.detail;else if(Array.isArray(error.detail))message=error.detail.map((d:{loc:string[],msg:string})=>`${d.loc.slice(1).join(' ')}: ${d.msg}`).join('; ')}catch{/* Preserve a generic error without logging records. */}throw new Error(message)}
 return r.status===204?null:r.json();
}
