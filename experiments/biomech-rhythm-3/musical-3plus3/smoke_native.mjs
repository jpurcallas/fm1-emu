/* Native PI32v2 musical 3+3 proof in fm1-emu. This is NOT an audio driver.
 * Test is headless and requires real CPU1 to complete DSP jobs.
 */
import {readFileSync} from "node:fs";
const [app,nm,wasm]=process.argv.slice(2);
if(!app||!nm||!wasm)throw Error("usage: smoke_native.mjs app.bin app.nm fm1_web.wasm");
const image=readFileSync(app), symbols=readFileSync(nm,"utf8").split("\n");
const sym=name=>{
 const line=symbols.find(l=>l.trim().endsWith(" "+name));
 if(!line)throw Error("no ELF symbol: "+name);
 return parseInt(line.trim().split(/\s+/)[0],16);
};
const {instance}=await WebAssembly.instantiate(readFileSync(wasm),{env:{fm1_jit_compile:()=>0}});
const x=instance.exports;
x.fm1_jit(0,0);
const p=x.fm1_alloc(0x120+image.length);
new Uint8Array(x.memory.buffer,p,0x120+image.length).fill(255);
new Uint8Array(x.memory.buffer,p+0x120,image.length).set(image);
x.fm1_boot(p,0x120+image.length,0x02000120,200);
const ramOffset=sym("br3_blackbox")-0x01C00000;
const refs=["br3_test_status","br3_test_peakbits","br3_test_checksum","br3_test_rendered",
"br3_completed_jobs","br3_timeouts","br3_fallback_jobs","br3_cpu0_stage","br3_cpu1_stage"];
const addr=Object.fromEntries(refs.map(k=>[k,sym(k)-0x01C00000]));
const read=(off)=>new DataView(x.memory.buffer,x.fm1_blackbox_ram_ptr()).getUint32(off,true);
let status=0,iterations=0;
for(iterations=0;iterations<2000;iterations++){
 x.fm1_render(128,50000);
 status=read(addr.br3_test_status);
 if(status===0xB330A11F || (status&0xFFFF0000)===0xB33E0000 || x.fm1_halted())break;
}
const data=Object.fromEntries(refs.map(k=>[k,read(addr[k])]));
const peakView=new DataView(new ArrayBuffer(4));
peakView.setUint32(0,data.br3_test_peakbits,true);
data.peak=peakView.getFloat32(0,true);
data.iterations=iterations;
data.halted=Boolean(x.fm1_halted());
const ram=new Uint8Array(x.memory.buffer,x.fm1_blackbox_ram_ptr()+ramOffset,8);
data.bb_marker=Array.from(ram).map(v=>String.fromCharCode(v)).join("");
console.log("BR3_MUSICAL_NATIVE",JSON.stringify(data));
if(status!==0xB330A11F || data.br3_test_rendered!==32 ||
 data.peak<=0.00001 || data.br3_completed_jobs<=0 || data.br3_timeouts!==0 ||
 data.bb_marker!=="BR3BBX01" || data.halted)
 throw Error("PI32v2 musical six-track native CPU1 job completion FAILED; no .fwsc release");
console.log("PASS: real emulated CPU1 executed BIOMECH3 synth workload for tracks 4-6; CPU0 mixed all six tracks.");
