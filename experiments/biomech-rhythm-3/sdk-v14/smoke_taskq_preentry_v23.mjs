// BIOMECH3 v17: same SDK, real MIDI UART/keyboard route, one verified ELF
// call + RAM pointer A/B. Read-only guest mailbox, no synthesized auto-notes.
import {readFileSync,writeFileSync,mkdirSync} from "node:fs";
import {createHash} from "node:crypto";
const [wasmPath,untouchedPath,hookedPath,nmPath,outDir]=process.argv.slice(2);
if(!outDir) throw Error("usage smoke_coop_v17.mjs wasm unhooked.fwsc hooked.fwsc sdk.nm output-dir");
mkdirSync(outDir,{recursive:true});
const wasm=readFileSync(wasmPath);
const names={};
for(const l of readFileSync(nmPath,"utf8").split("\n")){
 const m=l.trim().match(/^([0-9a-fA-F]+)\s+\w\s+(\S+)$/);
 if(m && /^(br3_coop_mailbox|br3_coop_ready_seen|br3_coop_original_sdk_worker|br3_coop_worker_anchor|br3_blackbox|br3_input_(?:screen_callbacks|midi_callbacks|midi_last_source|midi_last_length|audio_callbacks|audio_frames)|br3_phase_ticks|br3_phase_segments|br3_v19_(?:render_calls|render_total_ticks|render_max_ticks|render_last_ticks)|head\.792)$/.test(m[2])){
  names[m[2]]=parseInt(m[1],16);
 }
}
for(const k of ["br3_coop_mailbox","br3_coop_ready_seen","br3_coop_original_sdk_worker","br3_input_screen_callbacks","br3_input_midi_callbacks","br3_input_midi_last_source","br3_input_midi_last_length","br3_input_audio_callbacks","br3_input_audio_frames","br3_phase_ticks","br3_phase_segments","br3_v19_render_calls","br3_v19_render_total_ticks","br3_v19_render_max_ticks","br3_v19_render_last_ticks"]){
 if(!names[k])throw Error("required ABI symbol missing: "+k);
}
async function boot(label,path,quanta,intervene=false){
 const {instance}=await WebAssembly.instantiate(wasm,{env:{fm1_jit_compile:()=>0}});
 const x=instance.exports;
 x.fm1_jit(0,0);
 const fw=readFileSync(path), ptr=x.fm1_alloc(fw.length);
 new Uint8Array(x.memory.buffer,ptr,fw.length).set(fw);
 const rc=x.fm1_boot_fwsc(ptr,fw.length,0,0,200);
 if(rc!==0)throw Error("FWSC refused: "+label+" code "+rc);
 let rendered=0,nonzero=0,haltAt=-1;
 const pcSamples=[],pcHistogram=new Map(),regionHistogram=new Map();
 const taskqEvidence=[];
 const taskqHead=names["head.792"];
 if(!taskqHead || taskqHead!==0x01c6d21c)
   throw Error("Task-queue head does not match audited ELF: "+taskqHead);
 function captureTaskq(i){
  const ptr=x.fm1_blackbox_json(),bytes=new Uint8Array(x.memory.buffer);
  let end=ptr;while(end<bytes.length&&bytes[end])end++;
  const bb=JSON.parse(new TextDecoder().decode(bytes.subarray(ptr,end)));
  const base=0x01c00000,len=x.fm1_blackbox_ram_len();
  const dv=new DataView(x.memory.buffer,x.fm1_blackbox_ram_ptr(),len);
  const valid=a=>Number.isInteger(a)&&a>=base&&a+4<=base+len&&(a&3)===0;
  const get=a=>valid(a)?dv.getUint32(a-base,true):null;
  const first=get(taskqHead);
  let next=first,status="",cycleAt=null;
  const visited=new Map(),nodes=[];
  for(let n=0;n<128;n++){
    if(next===taskqHead){status="returns_to_head";break;}
    if(!valid(next)){status="invalid_address";break;}
    if(visited.has(next)){status="cycle_excludes_head";cycleAt=visited.get(next);break;}
    visited.set(next,n);
    nodes.push({address:"0x"+next.toString(16),
      next:"0x"+get(next).toString(16),
      owner_or_name:get(next+8),queue_or_payload:get(next+12)});
    next=get(next);
  }
  if(!status)status="chain_over_128_nodes";
  taskqEvidence.push({quantum:i,ms:bb.ms,
    cpu0_pc:"0x"+(bb.cpu0?.pc??0).toString(16),
    cpu0_user:bb.cpu0?.user,registers:(bb.cpu0?.regs||[]).slice(0,16),
    list_head:"0x"+taskqHead.toString(16),
    head_next:first===null?null:"0x"+first.toString(16),
    list_status:status,cycle_start:cycleAt,visited_nodes:visited.size,nodes:nodes.slice(0,40)});
 }
 function sampleCpu0(i){
   const ptr=x.fm1_blackbox_json(),m=new Uint8Array(x.memory.buffer);
   let end=ptr;while(end<m.length&&m[end])end++;
   const b=JSON.parse(new TextDecoder().decode(m.subarray(ptr,end)));
   const pc=b.cpu0?.pc??0;
   const region="0x"+(pc&0xffffff00).toString(16);
   pcHistogram.set(pc,(pcHistogram.get(pc)||0)+1);
   regionHistogram.set(region,(regionHistogram.get(region)||0)+1);
   pcSamples.push({quantum:i,ms:b.ms,pc,hex:"0x"+pc.toString(16),
      user:b.cpu0?.user,sp:b.cpu0?.sp,ssp:b.cpu0?.ssp,usp:b.cpu0?.usp,
      insn_count:b.cpu0?.insn_count,stuck_on:b.cpu0?.stuck_on,cpu1PC:b.cpu1?.pc});
 }
 for(let i=0;i<quanta;i++){
  // Genuine FM1 UART path, NOT direct br_trigger from audio callback.
  if(i===120||i===370||i===620||i===1000){
   for(const byte of [0x99,36,110])x.fm1_midi(byte);
  }
  if(i===200||i===450||i===700||i===1080){
   for(const byte of [0x89,36,0])x.fm1_midi(byte);
  }
  if(i===800)x.fm1_key(39,1);
  if(i===805)x.fm1_key(39,0);
  if(i===84 && intervene){
    // THIS IS A HOST-ONLY EMULATOR COUNTERFACTUAL, NOT A FIRMWARE PATCH.
    // One 32-bit write to the exact ELF-derived taskq list head.
    const len=x.fm1_blackbox_ram_len(),p=x.fm1_blackbox_ram_ptr();
    if(len!==1048576)throw Error("counterfactual RAM window unexpected");
    const head=names["head.792"],offset=head-0x01c00000;
    const dv=new DataView(x.memory.buffer,p,len);
    if(head!==0x01c6d21c||dv.getUint32(offset,true)!==0)
       throw Error("counterfactual invalid: list head was not zero");
    dv.setUint32(offset,head,true);
    if(dv.getUint32(offset,true)!==head)throw Error("counterfactual write failed");
    console.log("BR3_V23_HOST_RAM_COUNTERFACTUAL_SINGLE_WRITE",
      JSON.stringify({quantum:i,head:"0x"+head.toString(16),from:0,to:"0x"+head.toString(16)}));
  }
  let have=x.fm1_render(128,4000000);
  rendered+=have;
  if(have>0){
   const dv=new DataView(x.memory.buffer),l=x.fm1_out_l(),r=x.fm1_out_r();
   for(let j=0;j<have;j++){
    if(Math.abs(dv.getFloat32(l+j*4,true))>1e-8||Math.abs(dv.getFloat32(r+j*4,true))>1e-8)nonzero++;
   }
  }
  if(i%4===0)sampleCpu0(i);
  if([64,76,82,83,84,85,86,87,88,89,90,100,140,180].includes(i))captureTaskq(i);
  if(x.fm1_halted()){haltAt=i;break;}
 }
 const p=x.fm1_blackbox_ram_ptr(),len=x.fm1_blackbox_ram_len();
 if(len!==1048576)throw Error("invalid SoC RAM window");
 const dv=new DataView(x.memory.buffer,p,len);
 function word(name,offset=0){
  const at=names[name]-0x01c00000+offset;
  if(at<0||at+4>len)throw Error("RAM symbol out of bounds "+name);
  return dv.getUint32(at,true);
 }
 const c=names.br3_coop_mailbox;
 const stats={magic:word("br3_coop_mailbox"),seq:word("br3_coop_mailbox",4),
   done:word("br3_coop_mailbox",8),alive:word("br3_coop_mailbox",12),
   accepted:word("br3_coop_mailbox",24),completed:word("br3_coop_mailbox",28),
   fault:word("br3_coop_mailbox",32),timeouts:word("br3_coop_mailbox",36),
   ready_seen:word("br3_coop_ready_seen"),
   original_sdk_worker:word("br3_coop_original_sdk_worker"),
   input:{screen_callbacks:word("br3_input_screen_callbacks"),
     midi_callbacks:word("br3_input_midi_callbacks"),
     midi_last_source:word("br3_input_midi_last_source"),
     midi_last_length:word("br3_input_midi_last_length"),
     audio_callbacks:word("br3_input_audio_callbacks"),
     audio_frames:word("br3_input_audio_frames")},
   profile:{phase_ticks:[0,1,2,3,4,5].map(i=>word("br3_phase_ticks",4*i)),
     segments:word("br3_phase_segments"),
     calls:word("br3_v19_render_calls"),
     render_ticks_total:word("br3_v19_render_total_ticks"),
     render_ticks_max:word("br3_v19_render_max_ticks"),
     render_ticks_last:word("br3_v19_render_last_ticks")}};
 const bp=x.fm1_blackbox_json(),mem=new Uint8Array(x.memory.buffer);let end=bp;
 while(end<mem.length&&mem[end])end++;
 const bb=JSON.parse(new TextDecoder().decode(mem.subarray(bp,end)));
 const out={label,fwsc_sha256:createHash("sha256").update(fw).digest("hex"),
  quanta,rendered,nonzero,haltAt,emulated_ms:bb.ms,reason:bb.reason,hostCounterfactual:intervene,
  cpu0PC:bb.cpu0?.pc,cpu1PC:bb.cpu1?.pc,cpu0Instructions:bb.cpu0?.insn_count,
  cpu1Instructions:bb.cpu1?.insn_count,guest:stats,
  sampledCpu0:{count:pcSamples.length,every_quanta:4,
   topPCs:[...pcHistogram].sort((a,b)=>b[1]-a[1]).slice(0,20).map(([pc,count])=>({pc:"0x"+pc.toString(16),count})),
   topRegions:[...regionHistogram].sort((a,b)=>b[1]-a[1]).slice(0,20).map(([region,count])=>({region,count})),
   samples:pcSamples},taskqEvidence};
 writeFileSync(outDir+"/"+label+".json",JSON.stringify(out,null,2));
 console.log("BR3_V23_TASKQ_EVIDENCE",JSON.stringify({sha:out.fwsc_sha256,
   points:out.taskqEvidence.map(q=>({quantum:q.quantum,ms:q.ms,cpu0pc:q.cpu0_pc,
     status:q.list_status,nodes:q.visited_nodes,cycle_start:q.cycle_start,
     head_next:q.head_next,chain:q.nodes.slice(0,10)})),
   topPCs:out.sampledCpu0.topPCs.slice(0,3),audio_callbacks:out.guest.input.audio_callbacks,
   midi_callbacks:out.guest.input.midi_callbacks,cpu1_jobs:out.guest.completed}));
 return out;
}
const count=Number(process.env.BR3_V17_QUANTA||"1540");
if(!Number.isInteger(count)||count<500||count>2500)throw Error("invalid quantum count");
const original=await boot("BIOMECH3_v22_original_memory",hookedPath,count,false);
const intervention=await boot("BIOMECH3_v22_host_RAM_counterfactual",hookedPath,count,true);
const reduce=x=>({
  sha:x.fwsc_sha256,halt:x.haltAt,haltReason:x.reason,
  guest_ms:x.emulated_ms,cpu0pc:"0x"+x.cpu0PC.toString(16),
  CPU0insn:x.cpu0Instructions,
  ui:x.guest.input.screen_callbacks,midi:x.guest.input.midi_callbacks,
  audio:x.guest.input.audio_callbacks,frames:x.guest.input.audio_frames,
  jobs:x.guest.completed,failedJobs:x.guest.fault,PCM:x.nonzero,
  samples:x.sampledCpu0.count,
  taskq:x.taskqEvidence.map(y=>({ms:y.ms,pc:y.cpu0_pc,head:y.head_next,
     status:y.list_status,links:y.visited_nodes,cycle:y.cycle_start}))
});
console.log("BR3_V23_CAUSAL_AB",JSON.stringify({original:reduce(original),intervention:reduce(intervention)}));
for(const [name,result] of [["control",original],["one_write_before_get_taskq",intervention]]){
 console.log("BR3_V23_TASKQ_LIVE_REGS",JSON.stringify({
  scenario:name,
  snapshots:result.taskqEvidence.filter(z=>[82,83,84,85,86,87,88,89,90].includes(z.quantum))
   .map(z=>({quantum:z.quantum,ms:z.ms,pc:z.cpu0_pc,head:z.head_next,
             r0:z.registers[0],r1:z.registers[1],r2:z.registers[2],r3:z.registers[3],
             user:z.cpu0_user,chain:z.list_status}))
 }));
}

if(original.fwsc_sha256!==intervention.fwsc_sha256)throw Error("FWSC mismatch");
if(original.fwsc_sha256!=="e00e45f875fbefa24984c0e4aae15e9ecf6b612b3801d2fbdf72c98446357442")
  throw Error("Not the protected v19 FWSC");
console.log("BR3_V23_EXPERIMENT_COMPLETED one host-only RAM word changed, no guest firmware code edited, no physical install");
