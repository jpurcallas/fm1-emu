import { test } from 'node:test';
import assert from 'node:assert/strict';
import { encodeStereoWav, synchronizedCSV } from './synchronized-capture.js';
test('stereo WAV is valid 16-bit 44.1k and preserves stereo sample alignment', () => {
  const bytes = encodeStereoWav(new Float32Array([0,1,-1,.5]), new Float32Array([0,-1,1,-.5]));
  const v = new DataView(bytes);
  assert.equal(bytes.byteLength, 60);
  assert.equal(v.getUint32(4,true), 52);
  assert.equal(v.getUint16(22,true), 2);
  assert.equal(v.getUint32(24,true), 44100);
  assert.equal(v.getUint32(40,true), 16);
  assert.deepEqual([v.getInt16(44,true), v.getInt16(46,true), v.getInt16(48,true), v.getInt16(50,true)], [0,0,32767,-32768]);
});
test('each CSV record aligns its frame offset and short count to the same captured WAV', () => {
  const csv = synchronizedCSV({ packageHash:'abc', firmware:'A, B', mhz:200, latency:'interactive', sampleRate:44100 }, [
    [0,128,128,1.2,2500], [128,128,64,4.1,1900], [256,32,32,.2,500],
  ]);
  const lines = csv.trim().split('\n');
  assert.equal(lines.length,4);
  assert.ok(lines[1].includes('"A, B"'));
  assert.equal(lines[2].split(',').slice(-5).join(','), '4.100,1900,1,0,0');
  assert.equal(lines[3].split(',').slice(-5).join(','), '0.200,500,1,0,0');
});
test('post-capture comparison recognizes 256-sample repeated nonzero data but excludes silence', () => {
  const left = new Float32Array(768), right = new Float32Array(768);
  left.set([.25, .5, .75], 0); right.set([.4, .5, .6], 0);
  left.set([.25, .5, .75], 256); right.set([.4, .5, .6], 256);
  const csv = synchronizedCSV({ packageHash:'h', firmware:'n', mhz:200, latency:'x', sampleRate:44100, left, right },
    [[256,128,128,2,12]]).trim().split('\n')[1];
  assert.equal(csv.split(',').at(-2), '128');
  assert.equal(csv.split(',').at(-1), '3');
});
