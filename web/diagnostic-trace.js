// Optional eight-second emulator timing trace, collected from status messages.
// Never runs on the audio thread and never changes the simulated device/audio samples.
const COLUMNS = [
  'firmware', 'package_sha256', 'clock_mhz', 'latency', 'emulated_elapsed_ms',
  'wall_elapsed_ms', 'emulator_instructions', 'short_quanta_total',
  'short_quanta_delta', 'worklet_busy_ms', 'worklet_worst_quantum_ms',
  'worklet_quanta', 'worklet_frames_per_quantum', 'jit_regions', 'jit_failed'
];
const csvCell = v => {
  const s = String(v ?? '');
  return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
};

export class DiagnosticTrace {
  constructor({ seq, firmware, packageHash, clockMHz, latency, durationMs = 8000 }) {
    this.seq = seq;
    this.firmware = firmware;
    this.packageHash = packageHash;
    this.clockMHz = clockMHz;
    this.latency = latency;
    this.durationMs = durationMs;
    this.started = null;
    this.wallStarted = null;
    this.prevShort = null;
    this.rows = [];
    this.done = false;
  }
  add(frame, wallTimeMs) {
    if (this.done || frame?.type !== 'frame' || frame.seq !== this.seq) return false;
    if (this.started === null) {
      this.started = frame.ms;
      this.wallStarted = wallTimeMs;
    }
    const elapsed = frame.ms - this.started;
    if (!Number.isFinite(elapsed) || elapsed < 0) return false;
    const shortTotal = Number(frame.short) || 0;
    const shortDelta = this.prevShort === null ? 0 : Math.max(0, shortTotal - this.prevShort);
    this.prevShort = shortTotal;
    this.rows.push([
      this.firmware, this.packageHash, this.clockMHz, this.latency,
      elapsed, wallTimeMs - this.wallStarted, frame.minsns,
      shortTotal, shortDelta, frame.busy, frame.worst,
      frame.quanta, frame.frames, frame.jit?.regions, frame.jit?.failed,
    ]);
    this.done = elapsed >= this.durationMs;
    return this.done;
  }
  toCSV() {
    return [COLUMNS.join(','), ...this.rows.map(row => row.map(csvCell).join(','))].join('\n') + '\n';
  }
}
