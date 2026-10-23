// The emulator in the audio thread: each 128-frame quantum runs the machine until its I2S
// DMA has produced 128 frames, so the audio device paces the emulation. The page gets the
// LCD and the LEDs about 30 times a second; keys, knobs and the pot come back as messages.
// The WebAssembly JIT's host side, as web/jit.js (a copy: an AudioWorklet does not import
// modules everywhere): compile a hot block's module, install its `run` in the function table.
function jitImports(exports, stats) {
  return {
    fm1_jit_compile(ptr, len) {
      const start = now();
      try {
        const x = exports();
        const bytes = new Uint8Array(x.memory.buffer, ptr, len).slice();
        const table = x.__indirect_function_table;
        const run = new WebAssembly.Instance(new WebAssembly.Module(bytes), { env: { memory: x.memory, table } }).exports.run;
        const slot = table.grow(1);
        table.set(slot, run);
        stats.regions++;
        stats.bytes += len;
        stats.tableSlots = table.length;
        return slot;
      } catch (e) {
        stats.failed++;
        stats.error = String(e);
        return 0;
      } finally {
        const elapsed = now() - start;
        stats.compileMs += elapsed;
        stats.compileMaxMs = Math.max(stats.compileMaxMs, elapsed);
      }
    },
  };
}

// the wall clock, for how long each quantum's emulation takes (where an AudioWorklet has no
// performance.now(), Date.now(): whole milliseconds, which still average out over a second)
const now = globalThis.performance?.now ? () => performance.now() : () => Date.now();

class Fm1 extends AudioWorkletProcessor {
  constructor() {
    super();
    this.x = null;
    this.calls = 0;
    this.bootToken = 0;
    this.snapshots = [];
    this.port.onmessageerror = () => this.port.postMessage({ type: "error", message: "a message could not be read" });
    this.port.onmessage = async (e) => {
      const m = e.data;
      if (m.type === "boot") {
        const token = ++this.bootToken;
        // Keep the previous (paused) instance until the replacement boots successfully.
        try {
          await this.boot(m, token);
        } catch (err) {
          if (token !== this.bootToken) return;
          this.paused = false;
          this.port.postMessage({ type: "error", seq: m.seq, message: `boot: ${err}` });
        }
      } else if (m.type === "cancel-boot") {
        ++this.bootToken;
        this.x = null;
        this.snapshots = [];
      } else if (m.type === "snapshot" && !this.x) {
        this.port.postMessage({ type: "snapshot", seq: m.seq, request: m.request, unavailable: true });
      } else if (this.x) {
        if (m.type === "blackbox-request") this.captureBlackbox("manual export");
        else if (m.type === "wav-request") this.captureWav();
        else if (m.type === "record8-request") this.startRecord8();
        else if (m.type === "snapshot") {
          if (m.seq !== this.seq) return;
          this.snapshots.push({ ...m, started: now() });
          this.flushSnapshots();
        } else if (m.type === "cancel-snapshot") this.snapshots = this.snapshots.filter(r => r.request !== m.request);
        else if (m.type === "resume") this.paused = false;
        else if (m.type === "key") this.x.fm1_key(m.id, m.down ? 1 : 0);
        else if (m.type === "enc") this.x.fm1_enc(m.enc, m.clicks);
        else if (m.type === "pot") this.x.fm1_pot(m.value);
        else if (m.type === "midi") for (const b of m.bytes) this.x.fm1_midi(b);
        else if (m.type === "analog") this.x.fm1_analog(m.idx, m.value);   // SMK-37: pads, faders, wheels
        else if (m.type === "vel") this.x.fm1_velocity(m.us);             // SMK-37: the next keys' velocity
      }
    };
  }

  async boot(m, token) {
    // the module arrives as bytes: a compiled WebAssembly.Module does not cross into the
    // AudioWorklet's scope (Chrome delivers it as a messageerror). Compiled once, here: on a
    // phone compiling it again on every firmware change takes a noticeable while
    if (!this.module) this.module = await WebAssembly.compile(m.wasm);
    let x;
    this.jit = { regions: 0, failed: 0, error: "", bytes: 0, tableSlots: 0, compileMs: 0, compileMaxMs: 0 };
    x = (await WebAssembly.instantiate(this.module, { env: jitImports(() => x, this.jit) })).exports;
    if (token !== this.bootToken) return;
    // hot code compiled to WebAssembly, a few blocks per quantum at most (?jit=0: interpreter only)
    x.fm1_jit(m.jit === false ? 0 : 1, 16);
    // the whole update package (.fwsc): the machine unpacks it, gets the flash chip and the
    // boot parameters from it (what M-VAVE's own firmware needs; the others boot the same)
    const copy = (buf) => {
      const p = x.fm1_alloc(buf.byteLength);
      new Uint8Array(x.memory.buffer, p, buf.byteLength).set(new Uint8Array(buf));
      return p;
    };
    const pkg = copy(m.package);
    if (x.fm1_boot_fwsc(pkg, m.package.byteLength, 0, 0, m.mhz) !== 0) {
      throw new Error("not an FM-1 update package (or a DX7 bank it cannot use)");
    }
    if (m.sectors?.byteLength && x.fm1_flash_restore(copy(m.sectors), m.sectors.byteLength) !== 0) {
      throw new Error("invalid saved flash sectors");
    }
    if (m.syx && x.fm1_load_syx(copy(m.syx), m.syx.byteLength) === 1) {
      throw new Error("this firmware cannot load that DX7 bank");
    }
    this.x = x;                         // (a reboot replaces the whole instance)
    this.budget = m.mhz * 1e6 * 0.02;   // at most 20 ms of emulated time per quantum
    this.lastTiming = null;
    this.views = null;
    this.lcdRevision = null;
    this.reportFrames = 0;
    this.reportCalls = 0;
    this.haltReported = false;
    this.short = 0;
    // Emulator PCM evidence, separate from host hardware playback / microphone capture.
    // Keep the last six seconds of both channels and a bounded per-quantum history.
    this.pcmCapacity = Math.max(128, Math.floor(sampleRate * 6));
    this.pcmL = new Float32Array(this.pcmCapacity);
    this.pcmR = new Float32Array(this.pcmCapacity);
    this.pcmWrite = 0;
    this.pcmFilled = 0;
    this.record8 = null;                 // from-button eight-second recording (separate from rolling WAV)
    this.audioStats = {
      source: "emulator PCM after DMA before browser output",
      sampleRate, quantumFrames: 128, requestedFrames: 0, deliveredFrames: 0,
      shortQuanta: 0, missingFrames: 0, quanta: 0,
      nonzeroStereoFrames: 0, nearClipSamples: 0, peak: 0, sumSquares: 0,
      sampleCount: 0, quantumTrace: []
    };
    this.calls = 0;
    this.busy = 0;                      // ms spent emulating since the last frame message
    this.worst = 0;                     // the longest quantum among them
    this.board = x.fm1_board();         // 0 the FM-1, 1 the SMK-37 (the package says which)
    this.seq = m.seq;
    this.paused = false;
    this.snapshots = [];
    this.flashRevision = x.fm1_flash_revision();
    this.observedRevision = this.flashRevision;
    this.flashChangedAt = this.lastSnapshot = now();
    const base = new Uint8Array(x.memory.buffer, x.fm1_flash_base(), x.fm1_flash_len()).slice();
    const flash = new Uint8Array(x.memory.buffer, x.fm1_flash(), x.fm1_flash_len()).slice();
    this.port.postMessage({ type: "booted", seq: m.seq, board: this.board, revision: this.flashRevision, base, flash }, [base.buffer, flash.buffer]);
  }

  observeFlash() {
    const revision = this.x.fm1_flash_revision();
    if (revision !== this.observedRevision) {
      this.observedRevision = revision;
      this.flashChangedAt = now();
      this.port.postMessage({ type: "flash-changed", seq: this.seq, revision });
    }
    return revision;
  }

  flushSnapshots() {
    const x = this.x;
    if (!x) return;
    this.observeFlash();
    const quiet = now() - this.flashChangedAt >= 250 || x.fm1_halted();
    const busy = x.fm1_flash_busy();
    for (const request of this.snapshots.splice(0)) {
      if (busy || !quiet) {
        if (request.request !== undefined && now() - request.started >= 1500) {
          // A constantly writing firmware must not prevent switching away. Keep its
          // last stable save instead of persisting a possibly half-written sector.
          if (request.pause) this.paused = true;
          this.port.postMessage({ type: "snapshot", seq: this.seq, request: request.request,
            unavailable: true, error: request.pause ? null : "flash did not become quiet; try saving again" });
        } else this.snapshots.push(request);
        continue;
      }
      const flash = new Uint8Array(x.memory.buffer, x.fm1_flash(), x.fm1_flash_len()).slice();
      this.flashRevision = x.fm1_flash_revision();
      this.observedRevision = this.flashRevision;
      this.lastSnapshot = now();
      if (request.pause) this.paused = true;
      this.port.postMessage({ type: "snapshot", seq: this.seq, request: request.request,
        revision: this.flashRevision, flash }, [flash.buffer]);
    }
  }

  captureWav() {
    const count = this.pcmFilled || 0;
    if (!count) {
      this.port.postMessage({type:"wav", seq:this.seq, error:"No emulator PCM captured yet; play the sequence first."});
      return;
    }
    // Little-endian PCM16 stereo WAV. This is exactly the PCM emitted by the
    // emulator before Chrome's AudioContext mixes / resamples it.
    const bytes = new ArrayBuffer(44 + count * 4), view = new DataView(bytes);
    const tag = (off, value) => { for(let k=0;k<4;k++) view.setUint8(off+k, value.charCodeAt(k)); };
    tag(0,"RIFF"); view.setUint32(4,36+count*4,true); tag(8,"WAVE");
    tag(12,"fmt "); view.setUint32(16,16,true); view.setUint16(20,1,true);
    view.setUint16(22,2,true); view.setUint32(24,sampleRate,true);
    view.setUint32(28,sampleRate*4,true); view.setUint16(32,4,true);
    view.setUint16(34,16,true); tag(36,"data"); view.setUint32(40,count*4,true);
    let idx = (this.pcmWrite - count + this.pcmCapacity) % this.pcmCapacity;
    for(let i=0;i<count;i++) {
      const clip = v => Math.max(-32768, Math.min(32767, Math.round(v*32768)));
      view.setInt16(44+i*4,clip(this.pcmL[idx]),true);
      view.setInt16(46+i*4,clip(this.pcmR[idx]),true);
      idx = (idx+1)%this.pcmCapacity;
    }
    this.port.postMessage({type:"wav",seq:this.seq,buffer:bytes,frames:count,sampleRate},[bytes]);
  }

  startRecord8() {
    if (this.record8) {
      this.port.postMessage({type:"record8-status", seq:this.seq, status:"already-recording"});
      return;
    }
    const target=Math.round(sampleRate*8);
    this.record8={
      left:new Float32Array(target),
      right:new Float32Array(target),
      frames:0, target
    };
    this.port.postMessage({type:"record8-status",seq:this.seq,status:"recording",seconds:8});
  }

  finishRecord8() {
    const rec=this.record8;
    if (!rec || rec.frames!==rec.target) return;
    this.record8=null;
    const count=rec.target;
    const bytes=new ArrayBuffer(44+count*4), view=new DataView(bytes);
    const tag=(off,value)=>{for(let k=0;k<4;k++)view.setUint8(off+k,value.charCodeAt(k));};
    tag(0,"RIFF");view.setUint32(4,36+count*4,true);tag(8,"WAVE");
    tag(12,"fmt ");view.setUint32(16,16,true);view.setUint16(20,1,true);
    view.setUint16(22,2,true);view.setUint32(24,sampleRate,true);
    view.setUint32(28,sampleRate*4,true);view.setUint16(32,4,true);
    view.setUint16(34,16,true);tag(36,"data");view.setUint32(40,count*4,true);
    for(let i=0;i<count;i++) {
      const clip=v=>Math.max(-32768,Math.min(32767,Math.round(v*32768)));
      view.setInt16(44+4*i,clip(rec.left[i]),true);
      view.setInt16(46+4*i,clip(rec.right[i]),true);
    }
    this.port.postMessage({type:"record8-wav",seq:this.seq,buffer:bytes,frames:count,sampleRate},[bytes]);
  }

  // Independent emulator snapshot: runs after CPU halt, not from guest interrupt handlers.
  // Capture the whole guest RAM in addition to the emulator's exact CPU/error state.
  captureBlackbox(note, extraError = "") {
    const x = this.x;
    if (!x) {
      this.port.postMessage({ type: "blackbox", seq: this.seq, note, error: "emulator instance unavailable" });
      return;
    }
    try {
      const p = x.fm1_blackbox_json();
      const memory = new Uint8Array(x.memory.buffer);
      let end = p;
      while (end < memory.length && end - p < 100000 && memory[end] !== 0) end++;
      // TextDecoder is not exposed on all AudioWorkletGlobalScope implementations.
      // The snapshot is ASCII JSON, so convert directly without relying on worker APIs.
      let json = "";
      for (let i = p; i < end; i += 8192)
        json += String.fromCharCode(...memory.subarray(i, Math.min(i + 8192, end)));
      const state = JSON.parse(json);
      const at = x.fm1_blackbox_ram_ptr(), len = x.fm1_blackbox_ram_len();
      const ram = new Uint8Array(x.memory.buffer, at, len).slice().buffer;
      this.port.postMessage({ type: "blackbox", seq: this.seq, note, error: extraError,
        machine: state, ram, capturedAt: new Date().toISOString(),
        jit: { ...this.jit },
        audio_metrics: this.audioStats ? {
          ...this.audioStats,
          rms: this.audioStats.sampleCount ? Math.sqrt(this.audioStats.sumSquares / this.audioStats.sampleCount) : 0,
          availableWavFrames: this.pcmFilled,
          latest6sSeconds: this.pcmFilled/sampleRate
        } : null,
        clockHz: this.budget / 0.02 * 1e6 / 1e6 }, [ram]);
    } catch (e) {
      this.port.postMessage({ type: "blackbox", seq: this.seq, note,
        error: "capture failed: " + String(e) + "; original: " + extraError });
    }
  }

  process(_inputs, outputs) {
    const out = outputs[0];
    const x = this.x;
    if (!x || this.paused) return true;
    const n = out[0].length;
    const t0 = now();
    let have;
    try {
      have = x.fm1_render(n, this.budget);
    } catch (err) {                       // a trap in the emulator: stop and say so
      this.captureBlackbox("emulator render exception", String(err));
      this.x = null;
      for (const request of this.snapshots.splice(0)) {
        this.port.postMessage({ type: "snapshot", seq: this.seq, request: request.request, unavailable: true });
      }
      this.port.postMessage({ type: "error", seq: this.seq, fatal: true, message: `render: ${err}` });
      return true;
    }
    if (x.fm1_halted() && !this.haltReported) {
      this.haltReported = true;
      this.captureBlackbox("emulated CPU halted");
    }
    const buffer = x.memory.buffer, lp = x.fm1_out_l(), rp = x.fm1_out_r();
    if (!this.views || this.views.l.buffer !== buffer || this.views.l.length !== n ||
        this.views.l.byteOffset !== lp || this.views.r.byteOffset !== rp) {
      this.views = { l: new Float32Array(buffer, lp, n), r: new Float32Array(buffer, rp, n) };
    }
    const { l, r } = this.views;
    out[0].set(l);
    if (out[1]) out[1].set(r);
    // Exact eight seconds starting at the user's RECORD press; do not
    // replace or shorten the existing independently exported rolling six seconds.
    if (this.record8) {
      const rec=this.record8;
      const take=Math.min(n,rec.target-rec.frames);
      rec.left.set(l.subarray(0,take),rec.frames);
      rec.right.set(r.subarray(0,take),rec.frames);
      rec.frames+=take;
      if (rec.frames===rec.target) this.finishRecord8();
    }
    this.short = (this.short || 0) + (have < n ? 1 : 0);
    // Never infer distortion solely from nonzero/near-clipping values; report
    // underruns separately from signal saturation and browser worklet workload.
    let peak = 0, nearClip = 0, nonzero = 0;
    for(let i=0;i<n;i++) {
      const a=l[i], b=r[i], pa=Math.abs(a), pb=Math.abs(b);
      peak=Math.max(peak,pa,pb);
      nearClip+=(pa>=0.98?1:0)+(pb>=0.98?1:0);
      if(pa>1/32768 || pb>1/32768) nonzero++;
      this.audioStats.sumSquares+=a*a+b*b;
      const k=this.pcmWrite;
      this.pcmL[k]=a; this.pcmR[k]=b;
      this.pcmWrite=(k+1)%this.pcmCapacity;
    }
    this.pcmFilled=Math.min(this.pcmCapacity,this.pcmFilled+n);
    const metrics=this.audioStats;
    metrics.quanta++; metrics.requestedFrames+=n;
    metrics.deliveredFrames+=have;
    metrics.shortQuanta+=(have<n?1:0);
    metrics.missingFrames+=n-have;
    metrics.sampleCount+=2*n; metrics.nonzeroStereoFrames+=nonzero;
    metrics.nearClipSamples+=nearClip; metrics.peak=Math.max(peak,metrics.peak);
    const tookAudio=now()-t0;
    const trace=metrics.quantumTrace;
    if(trace.length===2048) trace.shift();
    trace.push([x.fm1_ms(),have,n,+peak.toFixed(4),nearClip,nonzero,+tookAudio.toFixed(3)]);
    this.reportFrames += n;
    this.reportCalls++;
    if (this.reportFrames >= sampleRate / 30) {
      const flashRevision = this.observeFlash();
      if (flashRevision !== this.flashRevision && now() - this.lastSnapshot >= 1000 &&
          now() - this.flashChangedAt >= 250 && !this.snapshots.length) {
        this.snapshots.push({});
      }
      this.flushSnapshots();
      const revision = x.fm1_lcd_revision();
      const lcd = revision !== this.lcdRevision ? new Uint16Array(x.memory.buffer, x.fm1_lcd(), 240 * 240).slice() : null;
      this.lcdRevision = revision;
      const leds = new Float32Array(x.memory.buffer, x.fm1_leds(), 41).slice();
      const pads = this.board ? new Uint32Array(x.memory.buffer, x.fm1_pads(), 16).slice() : null;
      const transfer = [leds.buffer];
      if (lcd) transfer.push(lcd.buffer);
      if (pads) transfer.push(pads.buffer);
      // Report the preceding interval: its final postMessage is included in its timing.
      this.port.postMessage({ type: "frame", seq: this.seq, lcd, leds, ms: x.fm1_ms(), minsns: x.fm1_minsns(),
        short: this.short, halted: x.fm1_halted(), jit: this.jit, pads,
        busy: this.lastTiming?.busy ?? 0, worst: this.lastTiming?.worst ?? 0,
        quanta: this.lastTiming?.quanta ?? 0, frames: this.lastTiming?.frames ?? n }, transfer);
      const took = now() - t0;
      this.lastTiming = { busy: this.busy + took, worst: Math.max(this.worst, took),
        quanta: this.reportCalls, frames: this.reportFrames / this.reportCalls };
      this.busy = 0;
      this.worst = 0;
      this.reportFrames = 0;
      this.reportCalls = 0;
    } else {
      const took = now() - t0;
      this.busy += took;
      this.worst = Math.max(this.worst, took);
    }
    return true;
  }
}
registerProcessor("fm1", Fm1);
