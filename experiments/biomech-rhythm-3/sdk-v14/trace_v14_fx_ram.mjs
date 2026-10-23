// Observe runtime writes (not reads) in the actual V14 SDK FX BSS region.
// JIT OFF, exact linked ELF symbol location; no changes to firmware/DSP.
// A negative result CANNOT prove that SDK never reads this region.
import {readFileSync,writeFileSync} from "node:fs";
const [wasmPath,fwscPath,nmPath,outPath] = process.argv.slice(2);
if(!outPath)throw Error("Usage: node trace_v14_fx_ram.mjs fm1_web.wasm firmware.fwsc sdk.nm report.json");
const sym=readFileSync(nmPath,"utf8").split("\n").map(x=>x.trim().match(/^([0-9a-fA-F]+)\s+[bBdD]\s+fm1_fx_states$/)).filter(Boolean);
if(sym.length!==1)throw Error("Expected one SDK FX symbol in this native linker map");
const guestAddress=parseInt(sym[0][1],16),ramOffset=guestAddress-0x01c00000,fxBytes=48832;
const wasm=readFileSync(wasmPath);
const {instance}=await WebAssembly.instantiate(wasm,{env:{fm1_jit_compile:()=>0}});
const x=instance.exports;x.fm1_jit(0,0);
const file=readFileSync(fwscPath),p=x.fm1_alloc(file.length);
new Uint8Array(x.memory.buffer,p,file.length).set(file);
let rc=x.fm1_boot_fwsc(p,file.length,0,0,200);if(rc)throw Error("FWSC boot rejected: "+rc);
const guestBytes=x.fm1_blackbox_ram_len(),guestPtr=x.fm1_blackbox_ram_ptr();
if(ramOffset<0||ramOffset+fxBytes>guestBytes)throw Error("Legacy FX buffer not wholly contained in guest RAM");
const sample=()=>new Uint8Array(x.memory.buffer,guestPtr+ramOffset,fxBytes).slice();
function fnv32(buf){let h=2166136261;for(let i=0;i<buf.length;i++)h=Math.imul(h^buf[i],16777619);return (h>>>0).toString(16).padStart(8,"0");}
const initial=sample();let previous=initial;const checkpoints=[{q:-1,ms:x.fm1_ms(),hash:fnv32(initial),nonzero:initial.filter(v=>v!==0).length}];
let totalChanges=0,blocks=0,halted=false;let input=0;
for(let q=0;q<800;q++){
 if(q===120){for(const b of [0x90,60,110])x.fm1_midi(b);input+=3;}
 if(q===210){x.fm1_key(0,1);input++;}
 if(q===310){x.fm1_key(0,0);input++;}
 if(q===400){x.fm1_key(39,1);input++;}
 if(q===407){x.fm1_key(39,0);input++;}
 const n=x.fm1_render(128,4000000);if(n>0)blocks++;
 const now=sample();let changed=0;for(let k=0;k<fxBytes;k++)if(now[k]!==previous[k])changed++;
 totalChanges+=changed;
 if(q===0||q%40===0||q===799)checkpoints.push({q,ms:x.fm1_ms(),hash:fnv32(now),changed_since_prev:changed,changed_from_boot:now.reduce((v,b,k)=>v+(b!==initial[k]),0)});
 previous=now;
 if(x.fm1_halted()){halted=true;break;}
}
const report={source:fwscPath,emulator:"WASM real V14",jit:false,guestAddress:"0x"+guestAddress.toString(16),fxBytes,quanta:800,
 blocks,halted,hostInputBytesOrKeys:input,changed_byte_observations:totalChanges,
 ever_changed_after_boot:totalChanges>0,checkpoints,
 limitation:"Only byte modifications at render boundaries are observed; reads and transient rewrites cannot be excluded. Cannot certify FX memory safe to overlap or free."};
writeFileSync(outPath,JSON.stringify(report,null,2));
console.log("BR3_FX_RAM_TRACE "+JSON.stringify({address:report.guestAddress,bytes:fxBytes,blocks,halted,changed_observations:totalChanges,initial:checkpoints[0],last:checkpoints.at(-1),limitation:report.limitation}));
if(halted)throw Error("Guest firmware halted");
