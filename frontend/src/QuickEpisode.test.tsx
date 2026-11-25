// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import {afterEach,expect,test} from 'vitest';
import {cleanup,fireEvent,render,screen,within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {EpisodeFields} from './TrackingForms';
import {episodePayload} from './tracking';
import type {Episode} from './tracking';

afterEach(cleanup);
function form(entry?:Episode){
 const view=render(<form aria-label="Synthetic episode"><EpisodeFields entry={entry} date="2024-01-02" sessions={[]}/></form>);
 const element=screen.getByRole('form',{name:'Synthetic episode'}) as HTMLFormElement;
 fireEvent.change(screen.getByLabelText('Attack started'),{target:{value:'2024-01-02T10:00:00'}});
 if(!entry)fireEvent.click(screen.getByText('Optional details · now or later'));
 return {...view,element};
}

test('suggestions toggle multiple selections with announced states and keyboard activation',async()=>{
 const user=userEvent.setup();const {element}=form();
 const symptoms=screen.getByRole('group',{name:'Symptoms · optional'});
 const nausea=within(symptoms).getByRole('button',{name:'Nausea'});
 nausea.focus();await user.keyboard('{Enter}');
 expect(nausea).toHaveAttribute('aria-pressed','true');
 await user.click(within(symptoms).getByRole('button',{name:'Light sensitivity'}));
 await user.click(screen.getByRole('button',{name:'Stress'}));
 await user.click(screen.getByRole('button',{name:'Poor sleep'}));
 expect(episodePayload(element)).toMatchObject({symptoms:['Nausea','Light sensitivity'],trigger:'Stress, Poor sleep',severity:null});
 await user.click(nausea);
 expect(nausea).toHaveAttribute('aria-pressed','false');
 const stress=screen.getByRole('button',{name:'Stress'});stress.focus();await user.keyboard(' ');
 expect(stress).toHaveAttribute('aria-pressed','false');
 expect(episodePayload(element).symptoms).toEqual(['Light sensitivity']);
 expect(episodePayload(element).trigger).toBe('Poor sleep');
 expect(screen.getByText(/not medically confirmed causes/)).toBeVisible();
});

test('custom entries and suggestions are deduplicated without changing the API shape',async()=>{
 const user=userEvent.setup();const {element}=form();
 const symptoms=screen.getByLabelText('Symptoms · separate with commas');
 await user.type(symptoms,'nausea, Custom symptom, NAUSEA');
 expect(screen.getByRole('button',{name:'Nausea'})).toHaveAttribute('aria-pressed','true');
 await user.click(screen.getByRole('button',{name:'Fatigue'}));
 const factors=screen.getByLabelText('Possible associated factor · not a proven trigger');
 await user.type(factors,'stress, Custom factor, STRESS');
 expect(screen.getByRole('button',{name:'Stress'})).toHaveAttribute('aria-pressed','true');
 await user.click(screen.getByRole('button',{name:'Caffeine'}));
 const data=episodePayload(element);
 expect(data.symptoms).toEqual(['nausea','Custom symptom','Fatigue']);
 expect(data.trigger).toBe('stress, Custom factor, Caffeine');
 expect(typeof data.trigger).toBe('string');
 expect(data.severity).toBeNull();
});

test('historical custom values survive editing and adding a suggestion, including embedded commas',async()=>{
 const entry:Episode={id:2,date:'2024-01-02',started_at:'2024-01-02T10:00:00Z',severity:0,duration:null,
  trigger:'Custom factor,  second observation',notes:'Synthetic note',symptoms:['Custom, embedded comma','nausea','Nausea'],medications:[]};
 const {element}=form(entry);
 const data=episodePayload(element,entry);
 expect(data.symptoms).toEqual(entry.symptoms);
 expect(data.trigger).toBe(entry.trigger);
 expect(data.notes).toBe(entry.notes);
 expect(data.severity).toBe(0);
 expect(screen.getByRole('button',{name:'Nausea'})).toHaveAttribute('aria-pressed','true');
 await userEvent.click(screen.getByRole('button',{name:'Fatigue'}));
 expect(episodePayload(element,entry).symptoms).toEqual([...entry.symptoms!,'Fatigue']);
 fireEvent.change(screen.getByLabelText('Symptoms · separate with commas'),{target:{value:'Custom, embedded comma, nausea, Nausea, Fatigue, Another custom symptom'}});
 expect(episodePayload(element,entry).symptoms).toEqual([...entry.symptoms!,'Fatigue','Another custom symptom']);
});

test('factor length and symptom limits are explicit and prevent invalid payloads',()=>{
 const {element}=form();
 const factor=screen.getByLabelText('Possible associated factor · not a proven trigger');
 fireEvent.change(factor,{target:{value:'x'.repeat(99)}});
 expect(screen.getByRole('button',{name:'Stress'})).toBeDisabled();
 expect(screen.getByText(/99\/100/)).toBeVisible();
 fireEvent.change(screen.getByLabelText('Symptoms · separate with commas'),{target:{value:'x'.repeat(101)}});
 expect(()=>episodePayload(element)).toThrow('at most 100 characters');
 fireEvent.change(screen.getByLabelText('Symptoms · separate with commas'),{target:{value:Array.from({length:31},(_,i)=>`Symptom ${i}`).join(', ')}});
 expect(()=>episodePayload(element)).toThrow('up to 30 symptoms');
});
