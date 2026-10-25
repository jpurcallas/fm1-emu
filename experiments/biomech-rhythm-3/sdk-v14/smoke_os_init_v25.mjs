// BIOMECH3 v25: observe os_init_flag and taskq head in the SAME protected guest.
// No edits to firmware, emulation memory, SDK, scheduler, DSP, MIDI or master.
import {readFileSync,writeFileSync,mkdirSync} from "node:fs";
import {createHash} from "node:crypto";
const [wasmPath,fwscPath,nmPath,outputDir]=process.argv.slice(2);
if(!outputDir)throw Error("usage: node smoke_os_init_v25.mjs wasm fwsc nm outdir");
mkdirSync(outputDir,{recursive:true});
const nm=readFileSync(nmPath,"utf8").split("\n");
function sym(s) {
 const a=nm.map(l=>l.match(/^([a-fA-F0-9]+)\s+\w\s+(\S+)$/)).filter(m=>m&&m[2]===s);
 if(a.length!==1)throw Error("symbol missing/ambiguous "+s);
 return parseInt(a[0][1],16);
}
const flag=sym("os_init_flag"),head=sym("head.792");
if(flag!==0x01c17a8c||head!==0x01c6d21c)throw Error("unexpected SDK ELF symbol layout");
const fw=readFileSync(fwscPath),sha=createHash("sha256").update(fw).digest("hex");
if(sha!=="e00e45f875fbefa24984c0e4aae15e9ecf6b612b3801d2fbdf72c98446357442")
  throw Error("FWSC SHA changed");
const {instance}=await WebAssembly.instantiate(readFileSync(wasmPath),{env:{fm1_jit_compile:()=>0}});
const x=instance.exports;x.fm1_jit(0,0);
const p=x.fm1_alloc(fw.length);
new Uint8Array(x.memory.buffer,p,fw.length).set(fw);
const boot=x.fm1_boot_fwsc(p,fw.length,0,0,200);
if(boot)throw Error("guest refused real protected firmware "+boot);
let logs=[],nonzero=0,frames=0;
const indices=new Set([0,1,2,3,4,6,8,12,16,20,24,32,48,60,64,72,76,80,82,83,84,85,86,87,88,89,90,100,120,140,200,300,400,800,1200,1539]);
function readState(i) {
 const base=x.fm1_blackbox_ram_ptr(),len=x.fm1_blackbox_ram_len();
 if(len!==1048576)throw Error("RAM mapping unexpectedly changed");
 const dv=new DataView(x.memory.buffer,base,len);
 const rd32=a=>dv.getUint32(a-0x01c00000,true);
 const rd8=a=>dv.getUint8(a-0x01c00000);
 const ptr=x.fm1_blackbox_json(),view=new Uint8Array(x.memory.buffer);
 let end=ptr;while(end<view.length&&view[end])end++;
 const bb=JSON.parse(new TextDecoder().decode(view.subarray(ptr,end)));
 return {quantum:i,guest_ms:bb.ms,cpu0pc:"0x"+bb.cpu0.pc.toString(16),user:bb.cpu0.user,
  os_init_flag_byte:rd8(flag),os_init_flag_word:rd32(flag),
  head_next:"0x"+rd32(head).toString(16),
  head_prev:"0x"+rd32(head+4).toString(16),
  r0:bb.cpu0.regs?.[0],r3:bb.cpu0.regs?.[3],
  guest_cpu0_insns:bb.cpu0.insn_count,cpu1insns:bb.cpu1?.insn_count,
  halted:bb.halted};
}
for(let i=0;i<1540;i++) {
 if([120,370,620,1000].includes(i))for(const b of [0x99,36,110])x.fm1_midi(b);
 if([200,450,700,1080].includes(i))for(const b of [0x89,36,0])x.fm1_midi(b);
 if(i===800)x.fm1_key(39,1);
 if(i===805)x.fm1_key(39,0);
 const have=x.fm1_render(128,4000000);
 frames+=have;
 if(have>0){
  const dv=new DataView(x.memory.buffer),l=x.fm1_out_l(),r=x.fm1_out_r();
  for(let j=0;j<have;j++)
   if(Math.abs(dv.getFloat32(l+j*4,true))>1e-8 || Math.abs(dv.getFloat32(r+j*4,true))>1e-8)nonzero++;
 }
 if(indices.has(i))logs.push(readState(i));
 if(x.fm1_halted())throw Error("Guest HALT before complete v25 read only trace at quantum "+i);
}
const out={firmware_sha256:sha,os_init_flag_address:"0x"+flag.toString(16),
  taskq_head_address:"0x"+head.toString(16),sample_count:logs.length,output_frames:frames,nonzero_frames:nonzero,snapshots:logs};
writeFileSync(outputDir+"/biomech_v25_os_init_flag.json",JSON.stringify(out,null,2));
console.log("BR3_V25_OS_INIT_TRACE",JSON.stringify(out));
const flags=[...new Set(logs.map(z=>z.os_init_flag_byte))];
const nexts=[...new Set(logs.map(z=>z.head_next))];
console.log("BR3_V25_INIT_SUMMARY",JSON.stringify({sha,flags,nexts,first:logs[0],last:logs.at(-1),screen_midi_audio_not_revalidated:true}));
if(!logs.some(z=>z.cpu0pc==="0x202b378"))throw Error("expected causal baseline CPU0 loop absent");
