export function DemoGuide({onNavigate}:{onNavigate:(page:string)=>void}){
 return <section className="demo-guide" aria-labelledby="demo-guide-title">
  <h2 id="demo-guide-title">Explore the synthetic demonstration</h2>
  <p>Read-only fictional examples from January 2026. Do not enter real health information. Current-month summaries may be empty.</p>
  <details><summary>Quick tour and research limits</summary>
   <ol><li>Daily status keeps migraine, explicit no migraine and unknown separate. Open record history to see when it was recorded.</li><li>The example calendar shows a fictional episode recorded on 2 January 2026 UTC, displayed in your device timezone.</li><li>Insights describe observations. They do not predict migraine or establish causal triggers.</li><li>In AI Insights on Overview, open Research data quality. Review requires an explicit action; export requires separate consent and downloads only to this device.</li></ol>
   <p>No independently verified outcomes or clinical validation are established. These fixtures cannot demonstrate predictive effectiveness. No caregiver alerts are sent automatically; avoid live call or SMS links during the tour.</p>
  </details>
  <div className="demo-guide-actions"><button className="secondary" onClick={()=>onNavigate('Daily status')}>Explore daily status</button><button className="secondary" onClick={()=>onNavigate('Calendar')}>Show example calendar</button><button className="secondary" onClick={()=>onNavigate('Overview')}>Review research features</button></div>
 </section>;
}
