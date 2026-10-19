// @vitest-environment jsdom
import {describe,it,expect} from 'vitest';
import {episodePayload,localInput,deviceZone,timestamp} from './tracking';
describe('tracking entry serialization',()=>{
 it('preserves zero severity and leaves optional values unknown',()=>{
  const form=document.createElement('form');form.innerHTML='<input name="date" value="2026-10-19"><input name="severity" value="0"><input name="started_at" value="2026-10-19T10:30:00"><input name="duration" value="">';
  const data=episodePayload(form);expect(data.severity).toBe(0);expect(data.duration).toBeNull();expect(data.started_at).toBe(new Date('2026-10-19T10:30:00').toISOString());expect(data.timezone_name).toBe(deviceZone());
 });
 it('does not invent a precise timestamp or timezone for legacy records',()=>{
  const form=document.createElement('form');form.innerHTML='<input name="date" value="2026-10-19">';const data=episodePayload(form);expect(data.started_at).toBeNull();expect(data.timezone_name).toBeNull();
 });
 it('requires both medication name and time and serializes separate observations',()=>{
  const form=document.createElement('form');form.innerHTML='<input name="symptoms" value="Nausea, Fatigue"><input name="medication_name" value="Synthetic"><input name="medication_time" value="">';
  expect(()=>episodePayload(form)).toThrow('both a name and time');
  (form.elements.namedItem('medication_time') as HTMLInputElement).value='2026-10-19T10:30:00';
  const data=episodePayload(form);expect(data.symptoms).toEqual(['Nausea','Fatigue']);expect(data.medications).toHaveLength(1);
 });
 it('roundtrips a precise local timestamp and rejects invalid input',()=>{
  const value='2026-10-19T10:30:15';expect(localInput(timestamp(value))).toBe(value);expect(()=>timestamp('not-a-time')).toThrow();
 });
});
