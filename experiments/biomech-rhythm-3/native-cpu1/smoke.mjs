/* CI: actual emulated guest CPU1 must execute a native PI32v2 mailbox job.
 * Standalone CPU1 test only. Do not call this BIOMECH 3 audio firmware.
 */
import {readFileSync} from "node:fs";
const [binName,nmName,wasmName]=process.argv.slice(2);
if(!binName||!nmName||!wasmName) throw Error("usage: smoke.mjs app.bin app.nm fm1_web.wasm");
const bin=readFileSync(binName), symbols=readFileSync(nmName,"utf8").split("\n");
const addr=name=>{
  const line=symbols.find(l=>l.trim().endsWith(" "+name));
  if(!line)throw Error("missing symbol "+name);
  return parseInt(line.trim().split(/\s+/)[0],16);
};
const {instance}=await WebAssembly.instantiate(readFileSync(wasmName),{env:{fm1_jit_compile:()=>0}});
const x=instance.exports;
x.fm1_jit(0,0);
// fm1_boot maps the supplied bytes from 0x02000000, whereas the JieLi
// application itself begins at XIP + 0x120. The FWSC loader normally pads it.
const imageLength=0x120+bin.length;
const p=x.fm1_alloc(imageLength);
new Uint8Array(x.memory.buffer,p,imageLength).fill(0xFF);
new Uint8Array(x.memory.buffer,p+0x120,bin.length).set(bin);
x.fm1_boot(p,imageLength,0x02000120,200);
const fields=["br3_status","br3_cpu0_trace","br3_cpu1_trace","br3_result_expected","br3_result_observed"];
const locations=Object.fromEntries(fields.map(f=>[f,addr(f)]));
function read(a){
  const ram=x.fm1_blackbox_ram_ptr();
  return new DataView(x.memory.buffer,ram).getUint32(a-0x01C00000,true);
}
let loops=0,status=0;
for(loops=0;loops<400;loops++){
  x.fm1_render(128,50000);
  status=read(locations.br3_status);
  if(status===0xB3300003 || (status & 0xFFFF0000)===0xB33E0000 || x.fm1_halted())break;
}
const value=Object.fromEntries(fields.map(f=>[f,"0x"+read(locations[f]).toString(16)]));
value.emulator_ms=x.fm1_ms();value.cpu_slices=loops;value.halted=!!x.fm1_halted();
console.log("BR3_NATIVE_PI32_CPU1",JSON.stringify(value));
if(status!==0xB3300003 || value.br3_cpu1_trace!=="0xc1000002" ||
   read(locations.br3_result_expected)!==read(locations.br3_result_observed)) {
   throw Error("Guest CPU1 handshake did not complete; do not distribute this candidate as validated");
}
console.log("PASS: real emulated PI32v2 CPU1 executed one checked job and returned the exact result.");
