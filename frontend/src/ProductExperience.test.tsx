// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import {afterEach,beforeEach,expect,test,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor,within} from '@testing-library/react';
import {App} from './main';
import {api} from './api';
import {DEFAULT_PREFERENCES} from './support';

vi.mock('./api',()=>({api:vi.fn()}));
function defaults(path:string){
 if(path==='profile')return {name:'Synthetic',support:'',avoid:'',communication:''};
 if(path==='support/preferences')return DEFAULT_PREFERENCES;
 if(path.startsWith('insights?'))return null;
 return [];
}
beforeEach(()=>{localStorage.clear();vi.mocked(api).mockImplementation(async path=>defaults(path))});
afterEach(()=>{cleanup();vi.resetAllMocks();vi.restoreAllMocks()});

test('mobile menu exposes its state and closes after navigating',async()=>{
 const {container}=render(<App/>);
 await screen.findByRole('heading',{name:'A gentler day, Synthetic.'});
 const toggle=container.querySelector<HTMLButtonElement>('.mobile-menu-toggle')!;
 const nav=screen.getByRole('navigation',{name:'Main navigation'});
 expect(toggle).toHaveAttribute('aria-expanded','false');
 expect(nav).toHaveAttribute('data-open','false');
 fireEvent.click(toggle);
 expect(toggle).toHaveAttribute('aria-expanded','true');
 fireEvent.click(within(nav).getByRole('button',{name:'Migraine diary'}));
 expect(toggle).toHaveAttribute('aria-expanded','false');
 expect(screen.getByRole('heading',{name:'Migraine diary'})).toHaveFocus();
 expect(screen.getByRole('button',{name:'Log an episode'})).toBeVisible();
 fireEvent.click(toggle);
 fireEvent.click(within(nav).getByRole('button',{name:'Migraine diary'}));
 expect(screen.getByRole('heading',{name:'Migraine diary'})).toHaveFocus();
});

test('workspace labels reflect local and synthetic-demo modes',async()=>{
 const {rerender}=render(<App/>);
 await screen.findByText('Local workspace');
 expect(screen.queryByText('Synthetic demonstration')).not.toBeInTheDocument();
 rerender(<App demoMode/>);
 expect(screen.getByText('Synthetic demonstration')).toBeInTheDocument();
 expect(screen.queryByText('Local workspace')).not.toBeInTheDocument();
});

test('failed wellness, symptom and contact reads do not display empty-state claims',async()=>{
 vi.mocked(api).mockImplementation(async path=>{
  if(['wellness','early-symptoms','contacts'].includes(path))throw new Error('Synthetic read failed');
  return defaults(path);
 });
 render(<App/>);
 await screen.findByRole('button',{name:'Retry wellness'});
 const nav=screen.getByRole('navigation',{name:'Main navigation'});
 fireEvent.click(within(nav).getByRole('button',{name:'Wellness'}));
 expect(screen.queryByText('No wellness check-ins for these dates.')).not.toBeInTheDocument();
 fireEvent.click(within(nav).getByRole('button',{name:'Early symptoms'}));
 expect(screen.queryByText('No early symptom observations yet.')).not.toBeInTheDocument();
 fireEvent.click(within(nav).getByRole('button',{name:'Trusted contacts'}));
 expect(screen.queryByText('Add someone you trust to get started.')).not.toBeInTheDocument();
});

test('history does not claim no episodes while loading or after a failed read',async()=>{
 let rejectRead!:(reason:Error)=>void;
 vi.mocked(api).mockImplementation(async path=>path==='episodes'?new Promise((_,reject)=>{rejectRead=reject}):defaults(path));
 render(<App/>);
 fireEvent.click(within(screen.getByRole('navigation')).getByRole('button',{name:'Migraine diary'}));
 expect(screen.getByRole('status')).toHaveTextContent('Loading your space');
 expect(screen.queryByText(/No episodes recorded here/)).not.toBeInTheDocument();
 rejectRead(new Error('Synthetic read failed'));
 expect(await screen.findByRole('alert')).toHaveTextContent('episodes could not be loaded');
 expect(screen.queryByText(/No episodes recorded here/)).not.toBeInTheDocument();
 vi.mocked(api).mockImplementation(async path=>defaults(path));
 fireEvent.click(screen.getByRole('button',{name:'Retry episodes'}));
 expect(await screen.findByText(/No episodes recorded here/)).toBeVisible();
});

test('episode save failure stays in the dialog and a later success is confirmed',async()=>{
 let attempts=0;
 vi.mocked(api).mockImplementation(async(path,method)=>{
  if(path==='episodes'&&method==='POST'&&++attempts===1)throw new Error('Synthetic save failed');
  return defaults(path);
 });
 render(<App/>);
 await screen.findByRole('heading',{name:'A gentler day, Synthetic.'});
 fireEvent.click(screen.getByRole('button',{name:'Log an episode'}));
 const dialog=screen.getByRole('dialog');
 fireEvent.change(within(dialog).getByLabelText('Attack started'),{target:{value:'2024-01-02T10:00:00'}});
 fireEvent.submit(dialog.querySelector('form')!);
 expect(await within(dialog).findByRole('alert')).toHaveTextContent('Synthetic save failed');
 fireEvent.submit(dialog.querySelector('form')!);
 await waitFor(()=>expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
 expect(await screen.findByText('Record saved.')).toHaveAttribute('role','status');
 expect(screen.queryByText('Synthetic save failed')).not.toBeInTheDocument();
 expect(attempts).toBe(2);
});

test('deletion confirmation appears only after the delete succeeds',async()=>{
 vi.spyOn(window,'confirm').mockReturnValue(true);
 const episode={id:5,date:'2024-01-02',severity:null,duration:null,trigger:'Unknown',notes:'Synthetic'};
 vi.mocked(api).mockImplementation(async(path,method)=>path==='episodes'&&method==='DELETE'?null:path==='episodes'?[episode]:defaults(path));
 render(<App/>);
 await screen.findByText('Synthetic',{selector:'.notes'});
 fireEvent.click(screen.getByRole('button',{name:'Delete episode'}));
 expect(await screen.findByText('Record deleted.')).toHaveAttribute('role','status');
 expect(vi.mocked(api).mock.calls.filter(([path,method])=>path==='episodes/5'&&method==='DELETE')).toHaveLength(1);
});
