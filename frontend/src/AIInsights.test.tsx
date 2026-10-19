// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import {afterEach,describe,expect,it,vi} from 'vitest';
import {render,screen,cleanup} from '@testing-library/react';
import {AIInsights} from './AIInsights';
afterEach(()=>{cleanup();vi.unstubAllGlobals()});
describe('research status',()=>{
 it('shows insufficient data without a risk score or emergency action',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,status:200,json:async()=>({status:'insufficient_data',probability:null,clinically_validated:false})})));
  const {container}=render(<AIInsights/>);
  expect(screen.getByRole('heading',{name:'AI Insights — In Development'})).toBeInTheDocument();
  await screen.findByText('Insufficient verified data for forecasting.');
  expect(container.textContent).not.toMatch(/\d+\s*%/);
  expect(container.querySelector('a[href^="tel:"],a[href^="sms:"]')).toBeNull();
 });
 it('handles model unavailability and network failure quietly',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,status:200,json:async()=>({status:'model_unavailable',probability:null,clinically_validated:false})})));
  const view=render(<AIInsights/>);await screen.findByText('No validated forecasting model is available.');view.unmount();
  vi.stubGlobal('fetch',vi.fn(async()=>{throw new Error('Offline')}));render(<AIInsights/>);
  await screen.findByText('Forecasting is unavailable. Your diary and support tools remain available.');
 });
});
