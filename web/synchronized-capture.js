// Read-only capture exports. Samples are copied from the audio worklet output.
export function encodeStereoWav(left, right, sampleRate = 44100) {
  if (!(left instanceof Float32Array) || !(right instanceof Float32Array) || left.length !== right.length)
    throw new TypeError('Stereo Float32Array channels of equal length required');
  const size = left.length;
  const buf = new ArrayBuffer(44 + size * 4);
  const v = new DataView(buf);
  const str = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
  str(0, 'RIFF'); v.setUint32(4, 36 + size * 4, true); str(8, 'WAVE');
  str(12, 'fmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true);
  v.setUint16(22, 2, true); v.setUint32(24, sampleRate, true);
  v.setUint32(28, sampleRate * 4, true); v.setUint16(32, 4, true);
  v.setUint16(34, 16, true); str(36, 'data'); v.setUint32(40, size * 4, true);
  for (let i = 0, o = 44; i < size; i++, o += 4) {
    const pcm = x => Number.isFinite(x) ? Math.round(Math.max(-1, Math.min(1, x)) * (x < 0 ? 32768 : 32767)) : 0;
    v.setInt16(o, pcm(left[i]), true);
    v.setInt16(o + 2, pcm(right[i]), true);
  }
  return buf;
}
const HEADER = ['package_sha256','firmware','clock_mhz','latency','sample_rate','audio_frame_offset',
  'elapsed_audio_ms','frames_rendered','frames_received_from_dma','missing_frames','render_wall_ms',
  'emulated_instructions','short_quanta_since_start','repeat256_frames','repeat256_nonzero_frames'];
const quote = x => { const s = String(x ?? ''); return /[",\r\n]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s; };
export function synchronizedCSV(meta, records) {
  const left = meta.left, right = meta.right;
  const rows = [HEADER.join(',')];
  let shorts = 0;
  for (const [offset, frames, have, renderWallMs, instructions] of records) {
    if (have < frames) shorts++;
    let repeat256 = 0, repeat256Nonzero = 0;
    if (left && right) for (let k = offset; k < offset + frames; k++) {
      if (k >= 256 && left[k] === left[k - 256] && right[k] === right[k - 256]) {
        repeat256++;
        if (left[k] !== 0 || right[k] !== 0) repeat256Nonzero++;
      }
    }
    rows.push([meta.packageHash, meta.firmware, meta.mhz, meta.latency, meta.sampleRate,
      offset, (offset * 1000 / meta.sampleRate).toFixed(3), frames, have, frames - have,
      Number(renderWallMs).toFixed(3), instructions, shorts, repeat256, repeat256Nonzero,
    ].map(quote).join(','));
  }
  return rows.join('\n') + '\n';
}
