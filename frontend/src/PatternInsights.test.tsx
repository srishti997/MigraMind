// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import {afterEach,expect,test,vi} from 'vitest';
import {cleanup,render,screen,fireEvent} from '@testing-library/react';
import {PatternInsights} from './PatternInsights';
import {patternFixture} from '../test-fixtures/patterns';
afterEach(()=>{cleanup();vi.restoreAllMocks()});
const response=(data:unknown)=>new Response(JSON.stringify(data));
test('sparse observations show insufficiency without inventing episode-free comparisons',async()=>{
 vi.spyOn(globalThis,'fetch').mockImplementation(async()=>response(patternFixture()));render(<PatternInsights/>);
 expect(await screen.findByRole('heading',{name:'Not enough information yet'})).toBeVisible();
 expect(screen.getByText(/0 onset days and 0 explicitly episode-free days/)).toBeVisible();
 expect(screen.queryByRole('img',{name:/Sleep duration:/})).toBeNull();
 fireEvent.click(screen.getByText('Missing data and exclusions'));
 expect(screen.getByText(/27.*Days have unknown episode status/)).toBeVisible();
});
test('supported comparisons include denominators and distinguish timestamped records',async()=>{
 vi.spyOn(globalThis,'fetch').mockImplementation(async()=>response(patternFixture(true)));render(<PatternInsights/>);
 await screen.findByRole('heading',{name:'Descriptive records available'});
 expect(screen.getByText('Recorded onset days (n=3)')).toBeVisible();
 expect(screen.getByText('Explicit episode-free observations (n=3)')).toBeVisible();
 fireEvent.click(screen.getByText('View timed symptoms and attacks'));
 expect(screen.getByRole('table',{name:'Symptoms and attacks remain distinct by onset timestamp'})).toBeVisible();
 expect(screen.getByText(/not a confirmed prodrome \(1 hours\)/)).toBeVisible();
 expect(screen.getByText(/Their recording timestamp does not establish/)).toBeVisible();
});
test('timezone and window selection reloads user-scoped results and clears stale content',async()=>{
 const fetcher=vi.spyOn(globalThis,'fetch').mockImplementation(async()=>response(patternFixture(true)));render(<PatternInsights/>);
 await screen.findByRole('heading',{name:'Descriptive records available'});
 let done!:(r:Response)=>void;fetcher.mockImplementationOnce(()=>new Promise(resolve=>{done=resolve}));
 fireEvent.change(screen.getByLabelText('Reporting timezone'),{target:{value:'America/New_York'}});
 expect(screen.queryByRole('heading',{name:'Descriptive records available'})).toBeNull();
 done(response(patternFixture(false,'America/New_York')));
 await screen.findByRole('heading',{name:'Not enough information yet'});
 expect(fetcher.mock.calls.at(-1)![0]).toContain('America%2FNew_York');
 fireEvent.change(screen.getByLabelText('Reporting window'),{target:{value:'90'}});
 await screen.findByRole('heading',{name:'Descriptive records available'});
 expect(fetcher.mock.calls.at(-1)![0]).toContain('days=90');
 fireEvent.change(screen.getByLabelText('Reporting window'),{target:{value:'7'}});
 await screen.findByRole('heading',{name:'Descriptive records available'});
 expect(fetcher.mock.calls.at(-1)![0]).toContain('days=7');
});
test('failed requests provide retry without invented insight values',async()=>{
 const fetcher=vi.spyOn(globalThis,'fetch').mockResolvedValueOnce(new Response('{}',{status:503}));render(<PatternInsights/>);
 await screen.findByRole('alert');expect(screen.queryByText('Recorded onset days (n=3)')).toBeNull();
 fetcher.mockImplementation(async()=>response(patternFixture()));fireEvent.click(screen.getByRole('button',{name:'Retry pattern insights'}));
 await screen.findByRole('heading',{name:'Not enough information yet'});
});


test('unknown severity renders as not recorded while a reported zero remains zero',async()=>{
 const data=patternFixture();
 const fetcher=vi.spyOn(globalThis,'fetch').mockImplementation(async()=>response(data));
 render(<PatternInsights/>);
 await screen.findByRole('heading',{name:'Not enough information yet'});
 const severity=screen.getByText('Average reported severity').parentElement!;
 expect(severity).toHaveTextContent('Not recorded');
 expect(severity).toHaveTextContent('0 rated entries');
 const zero=patternFixture();zero.summary.average_severity=0;zero.summary.severity_count=1;
 fetcher.mockImplementation(async()=>response(zero));
 fireEvent.change(screen.getByLabelText('Reporting window'),{target:{value:'90'}});
 await screen.findByText(/0.*1 rated entries/);
 expect(screen.getByText('Average reported severity').parentElement!).not.toHaveTextContent('Not recorded');
});
