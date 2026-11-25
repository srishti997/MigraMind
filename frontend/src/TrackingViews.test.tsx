// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import {afterEach,expect,test,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,within} from '@testing-library/react';
import {InsightsPanel,WellnessEntries} from './TrackingViews';
import type {Episode,Insights,Wellness} from './tracking';

afterEach(cleanup);

test('dashboard distinguishes unavailable, unknown and recorded synthetic counts',()=>{
 const {rerender}=render(<InsightsPanel insights={null}/>);
 expect(screen.getByText(/unavailable until your records load/)).toBeVisible();
 const insights:Insights={data_status:'recorded_episodes',headache_days:1,episode_count:2,
  average_severity:0,average_duration_minutes:null,severity_count:2,duration_count:0,wellness_days:0,
  daily:[{date:'2025-01-02',episodes:2,headache_reported:true}],limitations:'Synthetic observations only'};
 rerender(<InsightsPanel insights={insights}/>);
 expect(screen.getByRole('img',{name:/2025-01-02: 2/})).toBeInTheDocument();
 fireEvent.click(screen.getByText('View chart data as a table'));
 expect(within(screen.getByRole('table')).getByText('2')).toBeInTheDocument();
 expect(screen.getByText('Not enough data')).toBeVisible();
 expect(screen.getByText('Synthetic observations only')).toBeVisible();
});

test('recorded summaries distinguish distinct headache days, episode onsets and missing values',()=>{
 const data:Insights={data_status:'recorded_episodes',headache_days:1,episode_count:2,
  average_severity:0,average_duration_minutes:null,severity_count:1,duration_count:0,wellness_days:0,
  window_start:'2025-01-01',window_end:'2025-01-30',timezone_name:'UTC',
  daily:[{date:'2025-01-02',episodes:2,headache_reported:true}],limitations:'Synthetic only'};
 const episodes:Episode[]=[{id:1,date:'2025-01-02',severity:0,duration:null,trigger:'Stress, Poor sleep',notes:'',symptoms:['Nausea','nausea']},
  {id:2,date:'2025-01-02',severity:null,duration:null,trigger:'stress',notes:'',symptoms:['Nausea']}];
 const {rerender}=render(<InsightsPanel insights={data} episodes={episodes}/>);
 expect(screen.getByText('Reported headache days').closest('article')).toHaveTextContent('1');
 expect(screen.getByText('Episodes recorded').closest('article')).toHaveTextContent('2');
 expect(screen.getByText('Average reported severity').closest('article')).toHaveTextContent(/0\s*\/\s*10/);
 expect(screen.getByText('Average known duration').closest('article')).toHaveTextContent('Not enough data');
 expect(screen.getByText('Average known duration').closest('article')).toHaveTextContent('0 entries with duration');
 const frequency=screen.getByRole('region',{name:'Symptoms and associated factors in recorded episodes'});
 expect(within(frequency).getByText('Nausea').parentElement).toHaveTextContent('2 of 2');
 expect(within(frequency).getByText('Stress').parentElement).toHaveTextContent('2 of 2');
 expect(within(frequency).getByText('Poor sleep').parentElement).toHaveTextContent('1 of 2');
 expect(within(frequency).getByText(/not confirmed causes/)).toBeVisible();
 fireEvent.click(screen.getByText('View chart data as a table'));
 expect(screen.getByRole('table',{name:'Recorded episode onsets in the reporting window'})).toHaveTextContent('2025-01-02');
 rerender(<InsightsPanel insights={{...data,average_duration_minutes:0,duration_count:1}} episodes={episodes}/>);
 expect(screen.getByText('Average known duration').closest('article')).toHaveTextContent(/0\s*minutes/);
});

test('loading, failure, empty and inconsistent histories do not manufacture frequencies',()=>{
 const data:Insights={data_status:'insufficient_data',headache_days:null,episode_count:null,average_severity:null,average_duration_minutes:null,severity_count:0,duration_count:0,wellness_days:0,window_start:'2025-01-01',window_end:'2025-01-30',timezone_name:'UTC',daily:[],limitations:''};
 const {rerender}=render(<InsightsPanel insights={null} insightsLoading/>);
 expect(screen.getByRole('status')).toHaveTextContent('Loading recorded summaries');
 rerender(<InsightsPanel insights={null} insightsError/>);
 expect(screen.getByText(/summaries could not be loaded/)).toBeVisible();
 rerender(<InsightsPanel insights={data} episodes={[]} episodesLoading/>);
 expect(screen.getByRole('status')).toHaveTextContent('Loading episode details');
 rerender(<InsightsPanel insights={data} episodes={[]} episodesError/>);
 expect(screen.getByText(/Episode details could not be loaded/)).toBeVisible();
 rerender(<InsightsPanel insights={data} episodes={[]}/>);
 expect(screen.getByText(/No episode onsets were recorded/)).toBeVisible();
 const retry=vi.fn();rerender(<InsightsPanel insights={{...data,episode_count:2}} episodes={[]} onRetry={retry}/>);
 expect(screen.getByRole('status')).toHaveTextContent('counts differ');
 fireEvent.click(screen.getByRole('button',{name:'Refresh summaries'}));expect(retry).toHaveBeenCalledOnce();
});

test('wellness history exposes record-specific edit and delete actions',()=>{
 const edit=vi.fn(),remove=vi.fn();
 const entry:Wellness={id:17,date:'2025-01-02',timezone_name:'UTC',recorded_at:'2025-01-02T10:00:00Z',
  sleep_hours:null,sleep_quality:null,stress:0,hydration_ml:null,missed_meals:null,screen_hours:null,menstrual_notes:null};
 render(<WellnessEntries entries={[entry]} onEdit={edit} onDelete={remove}/>);
 expect(screen.getByRole('heading',{name:'Wellness · 2025-01-02'})).toBeVisible();
 expect(screen.getByText('0/10')).toBeVisible();
 fireEvent.click(screen.getByRole('button',{name:'Edit check-in'}));
 fireEvent.click(screen.getByRole('button',{name:'Delete check-in'}));
 expect(edit).toHaveBeenCalledWith(17);expect(remove).toHaveBeenCalledWith(17);
});
