// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import {afterEach,expect,test,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,within} from '@testing-library/react';
import {InsightsPanel,WellnessEntries} from './TrackingViews';
import type {Insights,Wellness} from './tracking';

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
