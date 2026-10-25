// BIOMECH3 v29 real V14 .fwsc recovery test, no synthetic br_trigger.
// All SDK names resolved from THIS ELF, never reusing old RAM addresses.
import {readFileSync,writeFileSync,mkdirSync} from "node:fs";
import {createHash} from "node:crypto";
const [wasmPath,fwscPath,nmPath,outDir]=process.argv.slice(2);
if(!outDir)throw Error("usage: smoke_v29_recovery.mjs emulator.wasm fwsc nm outdir");
mkdirSync(outDir,{recursive:true});
const nm=readFileSync(nmPath,"utf8").split("\n");
function symbol(name){
 const m=nm.map(z=>z.match(/^([0-9A-Fa-f]+)\s+\w\s+(\S+)$/)).filter(z=>z&&z[2]===name);
 if(m.length!==1)throw Error("symbol missing or ambiguous "+name);
 return parseInt(m[0][1],16);
}
const names=["head.792","os_init_flag","br3_coop_mailbox","br3_coop_ready_seen",
 "br3_input_audio_callbacks","br3_input_audio_frames","br3_input_midi_callbacks",
 "br3_input_screen_callbacks","br3_v19_render_max_ticks","br3_seg","_MALLOC_SIZE"];
const locations=Object.fromEntries(names.map(n=>[n,symbol(n)]));
if(locations["_MALLOC_SIZE"]<49152)throw Error("SDK malloc heap floor below 48KiB");
const fw=readFileSync(fwscPath),sha=createHash("sha256").update(fw).digest("hex");
const {instance}=await WebAssembly.instantiate(readFileSync(wasmPath),{env:{fm1_jit_compile:()=>0}});
const x=instance.exports;
x.fm1_jit(0,0);
const p=x.fm1_alloc(fw.length);new Uint8Array(x.memory.buffer,p,fw.length).set(fw);
const rc=x.fm1_boot_fwsc(p,fw.length,0,0,200);
if(rc)throw Error("v29 firmware refused "+rc);
let nonzero=0,rendered=0,halt=-1,maxPeak=0;
const checkpoints=[];
function snap(quantum){
 const ptr=x.fm1_blackbox_ram_ptr(),len=x.fm1_blackbox_ram_len();
 const dv=new DataView(x.memory.buffer,ptr,len);
 const off=n=>locations[n]-0x01c00000;
 function u32(n,d=0){if(off(n)<0||off(n)+d+4>len)throw Error("RAM address invalid "+n);return dv.getUint32(off(n)+d,true)}
 function u8(n){if(off(n)<0||off(n)>=len)throw Error("RAM address invalid "+n);return dv.getUint8(off(n))}
 const pointer=x.fm1_blackbox_json(),m=new Uint8Array(x.memory.buffer);let end=pointer;
 while(end<m.length&&m[end])end++;
 const bb=JSON.parse(new TextDecoder().decode(m.subarray(pointer,end)));
 return {quantum,ms:bb.ms,pc:"0x"+bb.cpu0.pc.toString(16),user:bb.cpu0.user,dispatch_hits:bb.cpu0.br3_v31_hits,
   head_next:"0x"+u32("head.792").toString(16),head_prev:"0x"+u32("head.792",4).toString(16),
   init:u8("os_init_flag"),screen:u32("br3_input_screen_callbacks"),
   midi:u32("br3_input_midi_callbacks"),audio:u32("br3_input_audio_callbacks"),
   audio_frames:u32("br3_input_audio_frames"),cpu1_alive:u32("br3_coop_mailbox",12),
   cpu1_accepted:u32("br3_coop_mailbox",24),
   cpu1_completed:u32("br3_coop_mailbox",28),
   cpu1_fault:u32("br3_coop_mailbox",32),
   cpu1_timeouts:u32("br3_coop_mailbox",36),
   render_max_ticks:u32("br3_v19_render_max_ticks"),reason:bb.reason};
}
const indices=new Set([0,3,4,5,6,7,8,10,15,20,30,50,85,120,200,400,800,1539]);
for(let k=0;k<1540;k++){
 if([120,370,620,1000].includes(k))for(const v of [0x99,36,110])x.fm1_midi(v);
 if([200,450,700,1080].includes(k))for(const v of [0x89,36,0])x.fm1_midi(v);
 if(k===800)x.fm1_key(39,1);
 if(k===805)x.fm1_key(39,0);
 const have=x.fm1_render(128,4000000);
 rendered+=have;
 if(have>0) {
  const dv=new DataView(x.memory.buffer),lp=x.fm1_out_l(),rp=x.fm1_out_r();
  for(let j=0;j<have;j++){
   const l=dv.getFloat32(lp+j*4,true),r=dv.getFloat32(rp+j*4,true);
   const a=Math.max(Math.abs(l),Math.abs(r));if(a>1e-8)nonzero++;
   maxPeak=Math.max(maxPeak,a);
  }
 }
 if(indices.has(k))checkpoints.push(snap(k));
 if(x.fm1_halted()){halt=k;checkpoints.push(snap(k));break;}
}
const last=checkpoints.at(-1);
const out={sha,size:fw.length,rendered,nonzero,maxPeak,halt,
  symbols:locations,checkpoints,final:last};
writeFileSync(outDir+"/BIOMECH3_v31_dispatch_guest.json",JSON.stringify(out,null,2));
console.log("BR3_V31_RECOVERY",JSON.stringify(out));
if(halt>=0)throw Error("Guest halted at quantum "+halt+" "+last.reason);
const fail=checkpoints.filter(z=>z.ms>=154 && (z.head_next==="0x0"||z.head_prev==="0x0"));
if(fail.length)throw Error("RTOS task-queue head still corrupted after moving preflight off stack");
if(last.cpu1_fault||last.cpu1_timeouts)throw Error("CPU1 bridge failure");
console.log("BR3_V31_GATE",JSON.stringify({head_intact:!fail.length,
  screen:last.screen,midi:last.midi,audio:last.audio,CPU1_jobs:last.cpu1_completed,
  PCM_nonzero:nonzero,render_max_ticks:last.render_max_ticks,not_approved_for_hardware:true}));

const hit=last.dispatch_hits||[];
console.log("BR3_V31_ROUTING_HITS",JSON.stringify({labels:["control_message","screen_control","midi_route_short","midi_received","audio_irq","control_request"],hits:hit,screen:last.screen,midi:last.midi,audio:last.audio,PCM:nonzero,init:last.init,guest_ms:last.ms}));
if(hit.length!==6)throw Error("v31 emulator does not expose expected hit counters");
