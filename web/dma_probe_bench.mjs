// Isolated diagnostic; not part of production firmware or default emulator.
// FM1_FWSC=/path/to/REMINISCENT_v323.fwsc node web/dma_probe_bench.mjs 200 2000
import {readFileSync} from "node:fs";
import {performance} from "node:perf_hooks";
import {jitImports} from "./jit.js";

const mhz = +(process.argv[2] || 200);
const limitMs = +(process.argv[3] || 2000);
if (![120,200].includes(mhz) || limitMs < 300 || limitMs > 20000)
  throw Error("Usage: FM1_FWSC=... node web/dma_probe_bench.mjs 120|200 duration_ms");
if (!process.env.FM1_FWSC) throw Error("FM1_FWSC must point to the original .fwsc");
const fw = readFileSync(process.env.FM1_FWSC);
const wasm = readFileSync(process.env.FM1_WASM || new URL("../target/wasm/wasm32-unknown-unknown/release/fm1_web.wasm",import.meta.url));
let x;
const jit={regions:0,failed:0,bytes:0,compileMs:0,compileMaxMs:0};
x=(await WebAssembly.instantiate(wasm,{env:jitImports(()=>x,jit)})).instance.exports;
for(const fn of ["fm1_dma_probe","fm1_dma_report","fm1_bench_script"]) if(typeof x[fn]!=="function") throw Error("Missing export "+fn);
x.fm1_jit(1,16);
const p=x.fm1_alloc(fw.length);
new Uint8Array(x.memory.buffer,p,fw.length).set(fw);
if(x.fm1_boot_fwsc(p,fw.length,0,0,mhz))throw Error("Boot failed");
const script=new TextEncoder().encode("150:m903c64,1400:m803c00,1650:m904064,2700:m804000");
const q=x.fm1_alloc(script.length);
new Uint8Array(x.memory.buffer,q,script.length).set(script);
if(x.fm1_bench_script(q,script.length))throw Error("Input script failed");
x.fm1_dma_probe(1);
const readReport=()=>{
 const ptr=x.fm1_dma_report(),view=new Uint8Array(x.memory.buffer),end=view.indexOf(0,ptr);
 if(end<ptr) throw Error("Invalid DMA report");
 return JSON.parse(new TextDecoder().decode(view.subarray(ptr,end)));
};
let calls=0,short=0,produced=0,late=0,maxMs=0,firstAudible=null;
let prev=performance.now(), wallStart=prev;
const events=[];
let lastSeen=0,retained=0,discarded=0,same=0,silent=0;
while(x.fm1_ms()<limitMs){
 const start=performance.now();
 const have=x.fm1_render(128,Math.round(mhz*1e6*0.02));
 const elapsed=performance.now()-start;
 calls++;short+=(have<128);produced+=have;late+=(elapsed>128/44100*1000);
 maxMs=Math.max(maxMs,elapsed);
 if(firstAudible===null&&have){
   const l=new Float32Array(x.memory.buffer,x.fm1_out_l(),have);
   const r=new Float32Array(x.memory.buffer,x.fm1_out_r(),have);
   if(l.some(v=>v!==0)||r.some(v=>v!==0))firstAudible=x.fm1_ms();
 }
 if(calls%64===0){
  const d=readReport();lastSeen=d.seen;discarded=d.discarded;same=d.sameAsPrior;silent=d.silent;
  events.push(...d.events);retained+=d.events.length;
 }
 if(x.fm1_halted())throw Error("Halted at "+x.fm1_ms());
 if(performance.now()-wallStart>90000)throw Error("Timed out");
}
const d=readReport();
events.push(...d.events);retained+=d.events.length;
const result={mhz,emulatedMs:x.fm1_ms(),wallMs:performance.now()-wallStart,calls,shortQuanta:short,
  renderExceedingDeadline:late,slowestRenderMs:maxMs,producedFrames:produced,firstAudibleMs:firstAudible,jit,
  dma:{consumedHalves:d.seen,repeatVsPreviousSameHalf:d.sameAsPrior,silentHalves:d.silent,
    traceDrops:d.discarded,capturedEvents:retained,
    disclaimer:"ALNK RAM samples observed at consumption. Does NOT prove firmware render/copy or physical DAC playback."},
  firstEvents:events.slice(0,8),lastEvents:events.slice(-8)};
console.log(JSON.stringify(result,null,2));
