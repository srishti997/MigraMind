// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import {afterEach,expect,test,vi} from 'vitest';
import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {DataReadiness} from './DataReadiness';
afterEach(()=>{cleanup();vi.restoreAllMocks()});
test('readiness is an explicit read-only request, with missingness and no invented labels',async()=>{
 const fetcher=vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(JSON.stringify({
  version:'account-preparation/v1',window_start:'2026-10-01',window_end:'2026-10-30',days:30,completed_days:29,
  coverage:{episode_recorded:0,no_episode_reported:0,unknown:30,conflict:0,episode_reported_without_onset:0},
  wellness_checkins:1,early_observations:0,missingness:{severity:{available:0,missing:1},stress:{available:1,missing:0}},
  labeled_outcomes:{positive:0,negative:0},training_justified:false,evaluation_justified:false,
  preparation:{prediction_cutoff:'2026-10-30T12:00:00Z',horizon_end:'2026-10-31T12:00:00Z',eligibility:'eligible_for_preparation_only'},
  limitations:['Missing diary dates are unknown, not migraine-free.']
 })));
 render(<DataReadiness/>);expect(fetcher).not.toHaveBeenCalled();
 fireEvent.click(screen.getByText('Your data readiness'));fireEvent.click(screen.getByRole('button',{name:'Review data readiness'}));
 expect(await screen.findByRole('heading',{name:'Not ready for forecasting research'})).toBeVisible();
 expect(screen.getByText('0 positive; 0 negative')).toBeVisible();
 expect(screen.getByText('Missing diary dates are unknown, not migraine-free.')).toBeVisible();
 expect(screen.getByRole('table',{name:'Recorded values and missing fields'})).toBeVisible();
 expect(fetcher.mock.calls[0][1]?.method).toBe('GET');
});
test('failed readiness requests show retry without fabricated data',async()=>{
 vi.spyOn(globalThis,'fetch').mockRejectedValue(new Error('Offline'));
 render(<DataReadiness/>);fireEvent.click(screen.getByText('Your data readiness'));
 fireEvent.click(screen.getByRole('button',{name:'Review data readiness'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('could not be loaded');
 expect(screen.queryByRole('table')).toBeNull();
 expect(screen.getByRole('button',{name:'Review data readiness'})).toBeEnabled();
});
