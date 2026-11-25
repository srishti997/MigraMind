// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import {afterEach,beforeEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,within} from '@testing-library/react';
import {App} from './main';
import {api} from './api';
import {DEFAULT_PREFERENCES} from './support';
import type {Episode} from './tracking';

vi.mock('./api',()=>({api:vi.fn()}));
const episodes:Episode[]=[
 {id:1,date:'2025-01-01',started_at:new Date(2025,0,1,23).toISOString(),ended_at:new Date(2025,0,2,1).toISOString(),severity:0,duration:120,trigger:'Stress',notes:'Synthetic first',symptoms:['Nausea'],medications:[{name:'Synthetic medication',taken_at:new Date(2025,0,1,23,30).toISOString()}]},
 {id:2,date:'2025-01-02',severity:null,duration:null,trigger:'Custom observation',notes:'Synthetic second',symptoms:['Aura'],medications:[]}
];
beforeEach(()=>{vi.useFakeTimers({toFake:['Date']});vi.setSystemTime(new Date(2025,0,2,12));localStorage.clear();vi.mocked(api).mockImplementation(async path=>{
 if(path==='profile')return {name:'Synthetic',support:'',avoid:'',communication:''};
 if(path==='support/preferences')return DEFAULT_PREFERENCES;
 if(path==='episodes')return episodes;
 if(path.startsWith('insights?'))return null;
 return [];
})});
afterEach(()=>{cleanup();vi.useRealTimers();vi.resetAllMocks();vi.restoreAllMocks()});

it('navigates months across years and marks selected dates with count and intensity',async()=>{
 render(<App/>);
 await screen.findByRole('heading',{name:'A gentler day, Synthetic.'});
 fireEvent.click(within(screen.getByRole('navigation')).getByRole('button',{name:'Calendar'}));
 expect(await screen.findByRole('heading',{name:'January 2025'})).toBeVisible();
 expect(screen.getByText('Select a date',{selector:'h2'})).toBeVisible();
 expect(screen.queryByText(/No episodes recorded here/)).not.toBeInTheDocument();
 const day=screen.getByRole('button',{name:'2025-01-02: 2 episodes, 0 wellness check-ins'});
 expect(day).toHaveAccessibleDescription(/Highest recorded pain 0 of 10.*1 without recorded intensity/);
 expect(day).toHaveAttribute('aria-pressed','false');fireEvent.click(day);
 expect(day).toHaveAttribute('aria-pressed','true');
 expect(screen.getAllByRole('button',{name:'Edit episode'})).toHaveLength(2);
 const first=screen.getByText('Synthetic first').closest('article')!;
 fireEvent.click(within(first).getByText('View entry details'));
 expect(within(first).getByText('Nausea')).toBeVisible();
 expect(within(first).getByText('Synthetic medication', {exact:false})).toBeVisible();
 expect(within(first).getByText('Possible associated factors')).toBeVisible();
 const second=screen.getByText('Synthetic second').closest('article')!;
 fireEvent.click(within(second).getByText('View entry details'));
 expect(within(second).getByText(/2025-01-02 · exact time unknown/)).toBeVisible();
 expect(within(second).getByText('Severity not recorded',{exact:false})).toBeVisible();
 fireEvent.click(screen.getByRole('button',{name:'Previous month'}));
 expect(screen.getByRole('heading',{name:'December 2024'})).toBeVisible();
 fireEvent.click(screen.getByRole('button',{name:'Next month'}));
 expect(screen.getByRole('heading',{name:'January 2025'})).toBeVisible();
 fireEvent.click(screen.getByRole('button',{name:'Next month'}));
 fireEvent.click(screen.getByRole('button',{name:'This month'}));
 expect(screen.getByRole('heading',{name:'January 2025'})).toBeVisible();
});

it('retains edit and confirmed delete actions on filtered records',async()=>{
 const confirm=vi.spyOn(window,'confirm').mockReturnValue(true);
 render(<App/>);await screen.findByRole('heading',{name:'A gentler day, Synthetic.'});
 fireEvent.click(within(screen.getByRole('navigation')).getByRole('button',{name:'Migraine diary'}));
 fireEvent.click(await screen.findByText('Filter and sort history'));
 fireEvent.change(screen.getByLabelText('Symptom contains'),{target:{value:'aura'}});
 fireEvent.click(screen.getByRole('button',{name:'Edit episode'}));
 expect(screen.getByRole('dialog')).toBeVisible();
 expect(screen.getByLabelText('Legacy date · exact time unknown')).toHaveValue('2025-01-02');
 fireEvent.click(screen.getByRole('button',{name:'Close dialog'}));
 fireEvent.click(screen.getByRole('button',{name:'Delete episode'}));
 expect(await screen.findByText('Record deleted.')).toBeVisible();
 expect(confirm).toHaveBeenCalledOnce();
 expect(vi.mocked(api).mock.calls.filter(([path,method])=>path==='episodes/2'&&method==='DELETE')).toHaveLength(1);
});

it('filters, sorts, clears and distinguishes no matches from an empty diary',async()=>{
 render(<App/>);await screen.findByRole('heading',{name:'A gentler day, Synthetic.'});
 fireEvent.click(within(screen.getByRole('navigation')).getByRole('button',{name:'Migraine diary'}));
 fireEvent.click(await screen.findByText('Filter and sort history'));
 fireEvent.change(screen.getByLabelText('Pain intensity'),{target:{value:'0'}});
 expect(screen.getByText('Synthetic first')).toBeVisible();expect(screen.queryByText('Synthetic second')).not.toBeInTheDocument();
 fireEvent.change(screen.getByLabelText('Pain intensity'),{target:{value:'unknown'}});
 expect(screen.getByText('Synthetic second')).toBeVisible();expect(screen.queryByText('Synthetic first')).not.toBeInTheDocument();
 fireEvent.change(screen.getByLabelText('Symptom contains'),{target:{value:'missing'}});
 expect(screen.getByText('No episodes match these filters.')).toBeVisible();
 fireEvent.click(screen.getByRole('button',{name:'Clear all filters'}));
 fireEvent.change(screen.getByLabelText('Order'),{target:{value:'oldest'}});
 expect(screen.getAllByText(/Synthetic (first|second)/).map(node=>node.textContent)).toEqual(['Synthetic first','Synthetic second']);
 fireEvent.change(screen.getByLabelText('From date'),{target:{value:'2025-01-03'}});
 fireEvent.change(screen.getByLabelText('Through date'),{target:{value:'2025-01-01'}});
 expect(screen.getByRole('alert')).toHaveTextContent('start date');
});
