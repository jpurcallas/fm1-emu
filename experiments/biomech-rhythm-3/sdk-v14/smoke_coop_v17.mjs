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
 if(m && /^(br3_coop_mailbox|br3_coop_ready_seen|br3_coop_original_sdk_worker|br3_coop_worker_anchor|br3_blackbox)$/.test(m[2])){
  names[m[2]]=parseInt(m[1],16);
 }
}
for(const k of ["br3_coop_mailbox","br3_coop_ready_seen","br3_coop_original_sdk_worker"]){
 if(!names[k])throw Error("required ABI symbol missing: "+k);
}
async function boot(label,path,quanta){
 const {instance}=await WebAssembly.instantiate(wasm,{env:{fm1_jit_compile:()=>0}});
 const x=instance.exports;
 x.fm1_jit(0,0);
 const fw=readFileSync(path), ptr=x.fm1_alloc(fw.length);
 new Uint8Array(x.memory.buffer,ptr,fw.length).set(fw);
 const rc=x.fm1_boot_fwsc(ptr,fw.length,0,0,200);
 if(rc!==0)throw Error("FWSC refused: "+label+" code "+rc);
 let rendered=0,nonzero=0,haltAt=-1;
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
  let have=x.fm1_render(128,4000000);
  rendered+=have;
  if(have>0){
   const dv=new DataView(x.memory.buffer),l=x.fm1_out_l(),r=x.fm1_out_r();
   for(let j=0;j<have;j++){
    if(Math.abs(dv.getFloat32(l+j*4,true))>1e-8||Math.abs(dv.getFloat32(r+j*4,true))>1e-8)nonzero++;
   }
  }
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
   original_sdk_worker:word("br3_coop_original_sdk_worker")};
 const bp=x.fm1_blackbox_json(),mem=new Uint8Array(x.memory.buffer);let end=bp;
 while(end<mem.length&&mem[end])end++;
 const bb=JSON.parse(new TextDecoder().decode(mem.subarray(bp,end)));
 const out={label,fwsc_sha256:createHash("sha256").update(fw).digest("hex"),
  quanta,rendered,nonzero,haltAt,emulated_ms:bb.ms,reason:bb.reason,
  cpu0PC:bb.cpu0?.pc,cpu1PC:bb.cpu1?.pc,cpu0Instructions:bb.cpu0?.insn_count,
  cpu1Instructions:bb.cpu1?.insn_count,guest:stats};
 writeFileSync(outDir+"/"+label+".json",JSON.stringify(out,null,2));
 console.log("BR3_V17_REAL_INPUT",JSON.stringify(out));
 return out;
}
const count=Number(process.env.BR3_V17_QUANTA||"1540");
if(!Number.isInteger(count)||count<500||count>2500)throw Error("invalid quanta");
const a=await boot("sdk_call_original",untouchedPath,count);
const b=await boot("sdk_first_cooperative_hook",hookedPath,count);
const aAlive=a.guest.alive,bAlive=b.guest.alive;
console.log("BR3_V17_AB",{aAlive,bAlive,aReady:a.guest.ready_seen,bReady:b.guest.ready_seen,
  aJobs:a.guest.accepted,bJobs:b.guest.accepted,bCompleted:b.guest.completed,
  aHalt:a.haltAt,bHalt:b.haltAt,originalWorker:b.guest.original_sdk_worker});
if(aAlive!==0)throw Error("CONTROL worker unexpectedly touched cooperative mailbox");
if(bAlive!==0xC103C003)throw Error("CPU1 SDK post-service callback never observed");
if(b.guest.original_sdk_worker===0xB330C017)throw Error("sentinel not patched");
if(b.guest.fault)throw Error("cooperative mailbox fault: "+b.guest.fault);
if(b.haltAt>=0)throw Error("hooked CPU0 halted: "+b.reason);
console.log("BR3_V17_GATE SDK-first trampoline executed on emulated CPU1; musical acceptance requires real CPU1 jobs, MIDI-to-PCM and author listening separately.");
