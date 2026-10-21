import { test } from 'node:test';
import assert from 'node:assert/strict';
import { DiagnosticTrace } from './diagnostic-trace.js';
const make = () => new DiagnosticTrace({ seq: 2, firmware: 'BIOMECH, v0.31',
  packageHash: 'abcdef', clockMHz: 200, latency: 'interactive' });
const frame = (ms, short = 0, seq = 2) => ({ type: 'frame', seq, ms, minsns: ms * 200,
  short, busy: 1.4, worst: 2.1, quanta: 12, frames: 128,
  jit: { regions: 4, failed: 0 } });
test('captures exactly one firmware, eight seconds of emulated time', () => {
  const d = make();
  assert.equal(d.add(frame(1200, 10), 100), false);
  assert.equal(d.add(frame(3000, 11, 3), 200), false);
  assert.equal(d.rows.length, 1);
  assert.equal(d.add(frame(5200, 15), 300), false);
  assert.equal(d.add(frame(9200, 16), 600), true);
  assert.equal(d.add(frame(9300, 17), 700), false);
  assert.equal(d.rows.length, 3);
  assert.deepEqual(d.rows.map(x => x[8]), [0, 5, 1]);
  assert.deepEqual(d.rows.map(x => x[4]), [0, 4000, 8000]);
});
test('CSV quotes unusual firmware names and preserves the immutable identity', () => {
  const d = make();
  d.add(frame(1000), 50);
  const lines = d.toCSV().trim().split('\n');
  assert.equal(lines.length, 2);
  assert.ok(lines[0].includes('short_quanta_delta'));
  assert.ok(lines[1].startsWith('"BIOMECH, v0.31",abcdef,200,interactive,0,0'));
});
test('refuses a rebooted emulated timestamp rather than joining runs', () => {
  const d = make();
  d.add(frame(8000, 42), 100);
  assert.equal(d.add(frame(0, 0), 250), false);
  assert.equal(d.rows.length, 1);
});
