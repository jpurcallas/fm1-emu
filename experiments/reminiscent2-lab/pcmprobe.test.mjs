// Controlled AudioWorklet test: host PCM must reflect the output buffer exactly.
// This is independent of the REminiSCENT DSP or of the physical loudspeakers.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

function harness(have=128, enabled=true) {
  let Processor, ms=500;
  const received=[];
  const memory=new WebAssembly.Memory({initial:4});
  const context=vm.createContext({
    WebAssembly, Float32Array, Uint32Array, Uint16Array, Uint8Array,
    sampleRate:44100, performance:{now:()=>0},
    AudioWorkletProcessor:class {constructor(){this.port={postMessage:m=>received.push(m)};}},
    registerProcessor(_name,p){Processor=p;},
  });
  vm.runInContext(fs.readFileSync(new URL('../web/worklet.js', import.meta.url),'utf8'),context);
  const p=new Processor();
  p.x={
    memory, fm1_render:()=>have, fm1_out_l:()=>0, fm1_out_r:()=>4096,
    fm1_ms:()=>ms, fm1_halted:()=>false
  };
  Object.assign(p,{seq:1,budget:100000,short:0,reportFrames:0,
    reportCalls:0,busy:0,worst:0,paused:false});
  p.pcmStats={
    schema:'REM2-AUDIOWORKLET-PCM-1',enabled,
    sampleRate:44100,quanta:0,requestedFrames:0,renderedFrames:0,
    shortQuanta:0,nonzeroFrames:0,nonzeroQuanta:0,silentQuanta:0,
    outputPeak:0,firstNonzeroGuestMs:null,lastNonzeroGuestMs:null,
    wallLateQuanta:0,worstWorkletMs:0,recent:[],threshold:1/32768
  };
  const output=[[new Float32Array(128),new Float32Array(128)]];
  return {p,memory,output,received,run:()=>p.process([],output)};
}

test('host PCM probe sees nonzero output copied to both browser channels',()=>{
  const h=harness();
  new Float32Array(h.memory.buffer)[0]=0.125;
  new Float32Array(h.memory.buffer)[1024]=-0.25;
  h.run();
  assert.equal(h.output[0][0][0],0.125);
  assert.equal(h.output[0][1][0],-0.25);
  assert.equal(h.p.pcmStats.nonzeroFrames,1);
  assert.equal(h.p.pcmStats.outputPeak,0.25);
  assert.equal(h.p.pcmStats.nonzeroQuanta,1);
  assert.equal(h.p.pcmStats.firstNonzeroGuestMs,500);
  assert.equal(h.p.pcmStats.lastNonzeroGuestMs,500);
  assert.equal(h.p.pcmStats.requestedFrames,128);
  assert.equal(h.p.pcmStats.renderedFrames,128);
  assert.equal(h.p.pcmStats.recent.length,1);
});
test('probe distinguishes silent quantum and emulation underrun',()=>{
  const h=harness(64);
  h.run();
  assert.equal(h.p.pcmStats.shortQuanta,1);
  assert.equal(h.p.pcmStats.silentQuanta,1);
  assert.equal(h.p.pcmStats.nonzeroFrames,0);
  assert.equal(h.p.pcmStats.renderedFrames,64);
});
test('measurement disabled for on/off cost comparison, PCM still copied',()=>{
  const h=harness(128,false);
  new Float32Array(h.memory.buffer)[0]=0.5;
  h.run();
  assert.equal(h.output[0][0][0],0.5);
  assert.equal(h.p.pcmStats.quanta,0);
});
