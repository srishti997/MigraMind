// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import {afterEach,expect,test,vi} from 'vitest';
import {render,screen,fireEvent,cleanup,waitFor} from '@testing-library/react';
import {ResearchQuality} from './ResearchQuality';
import {api} from './api';
vi.mock('./api',()=>({api:vi.fn()}));
afterEach(()=>{cleanup();vi.restoreAllMocks();vi.resetAllMocks()});
const quality={research_ready:false,window_start:'2025-10-04',window_end:'2025-11-02',timezone_name:'America/New_York',days:30,observed_days:1,missing_days:29,confirmed_episode_days:0,explicit_no_episode_days:0,unknown_days:30,incomplete_records:1,other_timezone_reports:0,verified_outcomes:0,eligible_observations:1,issues:[{code:'conflicting_daily_observation',date:'2025-11-02'}],blockers:['Independent outcome coverage is unavailable.']};

test('quality distinguishes missing and unknown days, conflicts and verification blockers',async()=>{
 vi.mocked(api).mockResolvedValue(quality);render(<ResearchQuality/>);
 expect(api).not.toHaveBeenCalled();fireEvent.click(screen.getByRole('button',{name:'Review research quality'}));
 expect(await screen.findByText('Missing days')).toBeInTheDocument();
 expect(screen.getByText('Unknown or unconfirmed days')).toBeInTheDocument();
 expect(screen.getByText('2025-11-02: Daily report disagrees with another record')).toBeInTheDocument();
 expect(screen.getByText(/America\/New_York/)).toBeInTheDocument();
 expect(screen.getByRole('button',{name:'Download research-preparation JSON'})).toBeDisabled();
 expect(screen.getByText(/not independently verified outcome labels/)).toBeInTheDocument();
});

test('explicit local scope required for each export; download never happens automatically',async()=>{
 vi.mocked(api).mockResolvedValueOnce(quality).mockResolvedValueOnce({export_schema:'migramind-research-preparation/1'});
 const create=vi.fn(()=> 'blob:synthetic');Object.defineProperty(URL,'createObjectURL',{value:create,configurable:true});Object.defineProperty(URL,'revokeObjectURL',{value:vi.fn(),configurable:true});
 const click=vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(()=>{});
 render(<ResearchQuality/>);fireEvent.click(screen.getByRole('button',{name:'Review research quality'}));
 const checkbox=await screen.findByRole('checkbox');fireEvent.click(checkbox);
 fireEvent.click(screen.getByRole('button',{name:'Download research-preparation JSON'}));
 await waitFor(()=>expect(api).toHaveBeenCalledWith('v1/research-export','POST',{confirmed:true,scope:'local_research_preparation',timezone_name:'America/New_York',days:30}));
 await screen.findByText(/Downloaded to this device/);expect(click).toHaveBeenCalledTimes(1);expect(create).toHaveBeenCalledTimes(1);
 expect(checkbox).not.toBeChecked();expect(screen.getByRole('button',{name:'Download research-preparation JSON'})).toBeDisabled();
});

test('load failure exposes retry without export controls',async()=>{
 vi.mocked(api).mockRejectedValue(new Error('Synthetic failure'));render(<ResearchQuality/>);
 fireEvent.click(screen.getByRole('button',{name:'Review research quality'}));expect(await screen.findByRole('alert')).toHaveTextContent('Please retry');
 expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
});

test('empty reports explain missingness without claiming clinical readiness',async()=>{
 vi.mocked(api).mockResolvedValue({...quality,issues:[],eligible_observations:0,observed_days:0,missing_days:30});render(<ResearchQuality/>);
 fireEvent.click(screen.getByRole('button',{name:'Review research quality'}));
 expect(await screen.findByText(/No record issues found/)).toBeInTheDocument();expect(screen.getByText(/not clinically validated requirements/)).toBeInTheDocument();
});


test('failed export shows a clear error without downloading or claiming success',async()=>{
 vi.mocked(api).mockResolvedValueOnce(quality).mockRejectedValueOnce(new Error('Synthetic export failure'));
 render(<ResearchQuality/>);fireEvent.click(screen.getByRole('button',{name:'Review research quality'}));
 fireEvent.click(await screen.findByRole('checkbox'));
 fireEvent.click(screen.getByRole('button',{name:'Download research-preparation JSON'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('Export could not be downloaded');
 expect(screen.queryByText(/Downloaded to this device/)).not.toBeInTheDocument();
});
