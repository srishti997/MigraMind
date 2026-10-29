// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import {cleanup,render,screen,fireEvent} from '@testing-library/react';
import {afterEach,expect,test,vi} from 'vitest';
import {DemoGuide} from './DemoGuide';
afterEach(cleanup);
test('tour is explicit, fictional, read-only and never navigates automatically',()=>{
 const navigate=vi.fn();render(<DemoGuide onNavigate={navigate}/>);
 expect(screen.getByText(/Read-only fictional examples/)).toHaveTextContent('January 2026');
 expect(screen.getByText(/No independently verified outcomes/)).toHaveTextContent('cannot demonstrate predictive effectiveness');
 expect(navigate).not.toHaveBeenCalled();
 fireEvent.click(screen.getByRole('button',{name:'Show example calendar'}));expect(navigate).toHaveBeenCalledWith('Calendar');
});
test('research and daily status remain separate explicit tour actions',()=>{
 const navigate=vi.fn();render(<DemoGuide onNavigate={navigate}/>);
 fireEvent.click(screen.getByRole('button',{name:'Explore daily status'}));
 fireEvent.click(screen.getByRole('button',{name:'Review research features'}));
 expect(navigate.mock.calls).toEqual([['Daily status'],['Overview']]);
});
