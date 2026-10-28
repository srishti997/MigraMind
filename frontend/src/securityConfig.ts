// Build-time guard only. Browser environment variables are public configuration.
export function validateProductionApiOrigin(value:string){
 if(!value)return;
 try{
  const url=new URL(value);
  if(url.protocol==='https:'&&!url.username&&!url.password&&url.origin===value)return;
 }catch{/* Do not echo configuration values into build logs. */}
 throw new Error('Production VITE_API_URL must be empty or an exact HTTPS origin');
}
