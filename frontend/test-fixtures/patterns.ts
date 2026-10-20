// Synthetic fixtures imported only by automated unit/browser tests.
import type {PatternData} from '../src/PatternInsights';
export function patternFixture(supported=false,timezone='UTC'):PatternData{
 return {version:'descriptive-v1',window_start:'2026-10-01',window_end:'2026-10-30',timezone_name:timezone,data_status:supported?'descriptive_records':'insufficient_data',
  summary:{timed_episodes:supported?3:0,average_severity:supported?5:null,severity_count:supported?3:0,average_duration_minutes:supported?60:null,duration_count:supported?3:0,wellness_checkins:supported?6:1,early_observations:supported?3:0,early_before_onset:supported?2:0,early_timing_uncertain:0,cycle_notes_checkins:0},
  warnings:{days_without_explicit_episode_status:27,missing_episode_ends:1},
  factors:[{key:'sleep_hours',label:'Sleep duration',unit:'hours',count:supported?6:1,missing_count:0,mean:supported?7:8,comparison_status:supported?'available':'insufficient_data',episode_days:supported?3:0,non_episode_days:supported?3:0,episode_mean:supported?6:null,non_episode_mean:supported?8:null}],
  daily:[{date:'2026-10-14',episodes:supported?1:0,status:supported?'episode_recorded':'unknown',completed:true},{date:'2026-10-15',episodes:0,status:'unknown',completed:true},{date:'2026-10-16',episodes:0,status:supported?'no_episode_reported':'unknown',completed:true}],
  symptoms:supported?[{symptom:'Synthetic yawning',count:3}]:[],
  timeline:supported?[{kind:'early_symptom',id:1,label:'Synthetic yawning',at:'2026-10-14T09:00:00Z',ended_at:null,relation:'Before a recorded onset within 24 hours; not a confirmed prodrome',hours_before:1},{kind:'attack',id:1,label:'Recorded migraine episode',at:'2026-10-14T10:00:00Z',ended_at:'2026-10-14T11:00:00Z',relation:'Recorded onset',hours_before:null}]:[],timeline_total:supported?2:0,
  daily_observations:[{id:1,date:'2026-10-14',timezone_name:'UTC',recorded_at:'2026-10-15T12:00:00Z',episode_observation:null}],
  comparison_minimum_per_group:3,comparison_basis:'Completed days with recorded onsets versus explicit episode-free observations. Exposure times are unknown.',
  limitations:['Missing entries remain unknown. Descriptive associations are not causes. No forecasting model is used.']};
}
