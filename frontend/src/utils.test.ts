import {describe,it,expect} from 'vitest';
import {localDate,monthCells} from './utils';
describe('calendar',()=>{it('keeps dates in local timezone',()=>{expect(localDate(new Date(2026,9,19))).toBe('2026-10-19')});it('aligns Monday-first and includes leap day',()=>{const cells=monthCells(new Date(2024,1,1));expect(cells.slice(0,3)).toEqual([null,null,null]);expect(cells.at(-1)).toBe(29);expect(cells.length).toBe(32)})});
