// Real guest CPU0 PC sampling; no firmware edits, no synthesized audio.
// Maps emulator BLACK BOX PCs to native ELF symbol table to locate boot stall.
import {readFileSync} from "node:fs";
const [wasmPath,fwscPath,nmPath]=process.argv.slice(2);
if(!nmPath)throw Error("wasm FWSC native-symbol-map required");
const wasm=readFileSync(wasmPath);
const {instance}=await WebAssembly.instantiate(wasm,{env:{fm1_jit_compile:()=>0}});
const x=instance.exports;
x.fm1_jit(0,0);
const bytes=readFileSync(fwscPath),ptr=x.fm1_alloc(bytes.length);
new Uint8Array(x.memory.buffer,ptr,bytes.length).set(bytes);
const rc=x.fm1_boot_fwsc(ptr,bytes.length,0,0,200);
if(rc!==0)throw Error("invalid real FWSC "+rc);
const syms=[];
for(const line of readFileSync(nmPath,"utf8").split("\n")){
 const m=line.trim().match(/^([0-9a-fA-F]+)\s+([a-zA-Z])\s+(\S+)$/);
 if(m)syms.push({address:parseInt(m[1],16),name:m[3],type:m[2]});
}
syms.sort((a,b)=>a.address-b.address);
function nearest(pc){
 let l=0,r=syms.length;
 while(l<r){const mid=(l+r)>>1;if(syms[mid].address<=pc)l=mid+1;else r=mid;}
 if(l===0)return null;
 const sym=syms[l-1];return {name:sym.name,address:"0x"+sym.address.toString(16),offset:pc-sym.address,type:sym.type};
}
function bb(){
 const p=x.fm1_blackbox_json(),v=new Uint8Array(x.memory.buffer);
 let end=p;while(end<v.length&&v[end])end++;
 return JSON.parse(new TextDecoder().decode(v.subarray(p,end)));
}
for(let q=0;q<150;q++){
 const returned=x.fm1_render(128,4000000);
 if([0,4,20,50,100,149].includes(q)){
   const v=bb();const pc=v.cpu0?.pc??0,pc1=v.cpu1?.pc??0;
   console.log("BR3_BOOT_PC",JSON.stringify({quantum:q,returned_frames:returned,ms:v.ms,halted:x.fm1_halted()!==0,pc:"0x"+pc.toString(16),near:nearest(pc),cpu0_insn:v.cpu0?.insn_count,
    cpu1_pc:"0x"+pc1.toString(16),cpu1_near:nearest(pc1),lcd:x.fm1_lcd_revision()}));
 }
 if(x.fm1_halted())throw Error("guest halted at quantum "+q);
}
console.log("PASS: observed real firmware PC path without changing guest firmware");
