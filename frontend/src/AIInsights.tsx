import {useEffect,useState} from 'react';
import {Leaf} from 'lucide-react';
import {api} from './api';
import {DataReadiness} from './DataReadiness';
type ForecastStatus={status:'insufficient_data'|'model_unavailable',probability:null,clinically_validated:false};
export function AIInsights(){
 const [status,setStatus]=useState<ForecastStatus|null>(null);
 useEffect(()=>{let live=true;api('v1/forecast').then(result=>{if(live)setStatus(result)}).catch(()=>{if(live)setStatus(null)});return()=>{live=false}},[]);
 return <section className="panel ai-research" aria-labelledby="ai-research-title"><div className="ai-research-heading"><Leaf size={21}/><h2 id="ai-research-title">AI Insights — In Development</h2></div><p>Future personalized insights may explore patterns in your recorded history. Migraine forecasting is still research; no validated risk score is available.</p><p className="ai-status">{status?.status==='insufficient_data'?'Insufficient verified data for forecasting.':status?.status==='model_unavailable'?'No validated forecasting model is available.':'Forecasting is unavailable. Your diary and support tools remain available.'}</p><details><summary>What’s needed before forecasting?</summary><p>Consistent observations, confirmed observation periods, reliable timestamps, and careful prospective evaluation. Missing diary entries do not mean attack-free days. Research results will not activate emergency actions.</p></details><DataReadiness/></section>
}
