// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import {afterEach,expect,test,vi} from 'vitest';
import {render,screen,fireEvent,cleanup,within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {DailyCheckin} from './DailyCheckin';
import {CollectionQuality} from './CollectionQuality';
import {api} from './api';
vi.mock('./api',()=>({api:vi.fn()}));
afterEach(()=>{cleanup();vi.resetAllMocks()});
const values={date:'2025-11-02',timezone_name:'America/New_York',status:'no_migraine',event_at:'2025-11-02T06:30:00Z',observed_at:'2025-11-02T06:30:00Z',sleep_hours:null,sleep_quality:null,stress:0,hydration_ml:null,routine_changes:null,early_symptoms:null};
const row={id:1,date:values.date,timezone_name:values.timezone_name,values,created_at:'2025-11-03T12:00:00Z',revision:1,deleted_at:null,retrospective:true,day_complete:true,episode_discrepancy:'no_migraine_with_diary_episode',wellness_discrepancy:false};

test('quick check-in leaves optional values unknown and defaults to explicitly unsure',async()=>{
 vi.mocked(api).mockResolvedValue([]);render(<DailyCheckin/>);
 const save=await screen.findByRole('button',{name:'Save daily check-in'});
 await vi.waitFor(()=>expect(save).toBeEnabled());
 expect(screen.getByLabelText('Migraine status')).toHaveValue('unknown');
 fireEvent.submit(screen.getByRole('form',{name:'Daily migraine check-in'}));
 await vi.waitFor(()=>expect(api).toHaveBeenCalledWith('daily-checkins','POST',expect.objectContaining({status:'unknown',sleep_hours:null,stress:null,early_symptoms:null})));
 expect(await screen.findByText('Daily check-in saved.')).toBeVisible();
});

test('editing preserves exact repeated-hour timestamps, zero and revision; history is explicit',async()=>{
 vi.mocked(api).mockImplementation(async(path)=>path.endsWith('/history')?[{id:1,revision:1,action:'creation',recorded_at:row.created_at,values}]:[row]);
 render(<DailyCheckin/>);
 expect(await screen.findByText(/Discrepancy:/)).toBeVisible();
 expect(screen.getByText(/Retrospective entry/)).toBeVisible();
 fireEvent.click(screen.getByRole('button',{name:'History 2025-11-02'}));
 expect(await screen.findByRole('region',{name:'History 2025-11-02'})).toBeInTheDocument();
 fireEvent.click(screen.getByRole('button',{name:'Edit 2025-11-02'}));
 expect(screen.getByLabelText('Report date')).toHaveAttribute('readonly');
 fireEvent.submit(screen.getByRole('form',{name:'Daily migraine check-in'}));
 await vi.waitFor(()=>expect(api).toHaveBeenCalledWith('daily-checkins/1','PUT',expect.objectContaining({expected_revision:1,stress:0,event_at:'2025-11-02T06:30:00.000Z',timezone_name:'America/New_York'})));
});

test('cancel returns to the initiating Edit control without saving or changing the report',async()=>{
 const saved=structuredClone(row);vi.mocked(api).mockResolvedValue([row]);
 render(<><button>Outside the check-in</button><DailyCheckin/></>);
 const outside=screen.getByRole('button',{name:'Outside the check-in'});outside.focus();
 const edit=await screen.findByRole('button',{name:'Edit 2025-11-02'});expect(outside).toHaveFocus();
 const user=userEvent.setup();
 for(let visit=0;visit<2;visit++){
  edit.focus();await user.keyboard('{Enter}');expect(screen.getByLabelText('Migraine status')).toHaveFocus();
  expect(screen.getByLabelText('Migraine status')).toHaveValue('no_migraine');
  await user.selectOptions(screen.getByLabelText('Migraine status'),'migraine');
  screen.getByRole('button',{name:'Cancel correction'}).focus();await user.keyboard('{Enter}');
  await vi.waitFor(()=>expect(edit).toHaveFocus());
  expect(screen.queryByRole('button',{name:'Cancel correction'})).toBeNull();
  expect(screen.getByLabelText('Migraine status')).toHaveValue('unknown');
  await user.tab();expect(screen.getByRole('button',{name:'Delete 2025-11-02'})).toHaveFocus();
 }
 expect(row).toEqual(saved);expect(vi.mocked(api).mock.calls.every(([,method])=>!method||method==='GET')).toBe(true);
});

test('cancel focuses the new status control if a refresh removes its Edit opener',async()=>{
 let reports=[row];
 vi.mocked(api).mockImplementation(async path=>{if(path.endsWith('/history'))throw new Error('Synthetic history failure');return reports});
 render(<DailyCheckin/>);const user=userEvent.setup();
 await user.click(await screen.findByRole('button',{name:'Edit 2025-11-02'}));
 await user.click(screen.getByRole('button',{name:'History 2025-11-02'}));await screen.findByRole('alert');
 reports=[];await user.click(screen.getByRole('button',{name:'Reload check-ins'}));
 await vi.waitFor(()=>expect(screen.queryByRole('button',{name:'Edit 2025-11-02'})).toBeNull());
 screen.getByRole('button',{name:'Cancel correction'}).focus();await user.keyboard('{Enter}');
 await vi.waitFor(()=>expect(screen.getByLabelText('Migraine status')).toHaveFocus());
 expect(vi.mocked(api).mock.calls.every(([,method])=>!method||method==='GET')).toBe(true);
});

test('cancelling a correction opened by Review yesterday restores that initiating control',async()=>{
 const day=new Date();day.setDate(day.getDate()-1);
 const date=`${day.getFullYear()}-${String(day.getMonth()+1).padStart(2,'0')}-${String(day.getDate()).padStart(2,'0')}`;
 const yesterday={...row,date,timezone_name:'UTC',values:{...values,date,timezone_name:'UTC',event_at:date+'T12:00:00Z',observed_at:date+'T12:00:00Z'}};
 vi.mocked(api).mockResolvedValue([yesterday]);render(<DailyCheckin/>);const user=userEvent.setup();
 const review=await screen.findByRole('button',{name:'Review yesterday'});await vi.waitFor(()=>expect(review).toBeEnabled());
 review.focus();await user.keyboard('{Enter}');expect(screen.getByLabelText('Migraine status')).toHaveFocus();
 screen.getByRole('button',{name:'Cancel correction'}).focus();await user.keyboard('{Enter}');
 await vi.waitFor(()=>expect(review).toHaveFocus());
 expect(vi.mocked(api).mock.calls.every(([,method])=>!method||method==='GET')).toBe(true);
});

test('deletion uses current revision and explains retention',async()=>{
 vi.mocked(api).mockResolvedValue([row]);const confirm=vi.spyOn(window,'confirm').mockReturnValue(true);
 render(<DailyCheckin/>);fireEvent.click(await screen.findByRole('button',{name:'Delete 2025-11-02'}));
 await vi.waitFor(()=>expect(api).toHaveBeenCalledWith('daily-checkins/1?expected_revision=1','DELETE'));
 expect(confirm).toHaveBeenCalledWith(expect.stringContaining('private history'));confirm.mockRestore();
});

test('failed load disables saving until a successful reload',async()=>{
 vi.mocked(api).mockRejectedValue(new Error('Offline'));render(<DailyCheckin/>);
 expect(await screen.findByRole('alert')).toHaveTextContent('could not be loaded');
 // Failure must not allow a blind create over an unknown existing date.
 expect(screen.getByRole('button',{name:'Save daily check-in'})).toBeDisabled();
});

test('quality requests are explicit and never imply clinical readiness',async()=>{
 vi.mocked(api).mockResolvedValue({status:'insufficient_evidence_for_forecasting',window_start:'2025-01-01',window_end:'2025-01-30',observed_days:1,explicit_no_episode_days:0,unknown_days:30,explicit_unknown_days:1,same_day_observations:0,retrospective_observations:1,other_timezone_reports:0,discrepancies:0,correction_count:2,deleted_reports:0,missing_fields:{stress:1}});
 render(<CollectionQuality/>);expect(api).not.toHaveBeenCalled();
 fireEvent.click(screen.getByText('Daily collection quality'));fireEvent.click(screen.getByRole('button',{name:'Review collection quality'}));
 expect(await screen.findByRole('heading',{name:'Insufficient evidence for forecasting'})).toBeVisible();
 expect(within(screen.getByRole('table')).getByText('stress')).toBeVisible();
});


test('review yesterday keeps status unknown until explicit confirmation and uses the completed local date',async()=>{
 vi.mocked(api).mockResolvedValue([]);render(<DailyCheckin/>);
 const button=await screen.findByRole('button',{name:'Review yesterday'});
 await vi.waitFor(()=>expect(button).toBeEnabled());fireEvent.click(button);
 const day=new Date();day.setDate(day.getDate()-1);
 const expected=`${day.getFullYear()}-${String(day.getMonth()+1).padStart(2,'0')}-${String(day.getDate()).padStart(2,'0')}`;
 expect(screen.getByLabelText('Report date')).toHaveValue(expected);
 expect(screen.getByLabelText('Migraine status')).toHaveValue('unknown');
 expect(String((screen.getByLabelText('Event time') as HTMLInputElement).value)).toMatch(new RegExp('^'+expected));
 expect(vi.mocked(api).mock.calls.every(call=>call[1]!=='POST')).toBe(true);
});
