// BIOMECH 3: real FM1 V14 FWSC musical stimulation, no mock DSP.
// JIT OFF, direct TRS MIDI UART bytes into the real emulated firmware.
// Do not claim CPU1 ownership, real-time DMA success or physical hardware.
import {readFileSync,writeFileSync} from "node:fs";
const [wasmPath,stockPath,br3Path,outDir,nmPath,bootNotePath,queuedMidiPath]=process.argv.slice(2);
if(!outDir)throw Error("usage: node smoke_fwsc_musical.mjs emulator.wasm stock.fwsc br3.fwsc outDir");
const wasm=readFileSync(wasmPath);
const framesPerBlock=128;
function f32Sample(data,at){const v=data.getFloat32(at,true);return Number.isFinite(v)?v:0;}
function encodeWav(left,right){
 const frames=left.length,buf=Buffer.alloc(44+frames*4);
 buf.write("RIFF",0);buf.writeUInt32LE(buf.length-8,4);buf.write("WAVEfmt ",8);
 buf.writeUInt32LE(16,16);buf.writeUInt16LE(1,20);buf.writeUInt16LE(2,22);
 buf.writeUInt32LE(44100,24);buf.writeUInt32LE(44100*4,28);
 buf.writeUInt16LE(4,32);buf.writeUInt16LE(16,34);
 buf.write("data",36);buf.writeUInt32LE(frames*4,40);
 for(let i=0;i<frames;i++){let a=Math.round(Math.max(-1,Math.min(1,left[i]))*32767),b=Math.round(Math.max(-1,Math.min(1,right[i]))*32767);
 buf.writeInt16LE(a,44+4*i);buf.writeInt16LE(b,46+4*i)}
 return buf;
}
function guestDiagnostic(x){
  const p=x.fm1_blackbox_ram_ptr(),len=x.fm1_blackbox_ram_len();
  const ram=new Uint8Array(x.memory.buffer,p,len),dv=new DataView(x.memory.buffer,p,len);
  const symbols={};
  if(nmPath){
    for(const line of readFileSync(nmPath,"utf8").split("\n")){
      const match=line.trim().match(/^([0-9a-fA-F]+)\s+[a-zA-Z]\s+([^\s]+)$/);
      if(match && /^(runtime|initialized|midi_head|midi_tail|midi_dropped|br3_blackbox|br3_completed_jobs|br3_cpu1_stage|br3_cpu0_stage|biomech_sdk_audio|fm1_audio_start)/.test(match[2])){
        const addr=parseInt(match[1],16),offs=addr-0x01c00000;
        if(offs>=0&&offs+16<=len){
          symbols[match[2]]={address:"0x"+addr.toString(16),u32:[0,4,8,12].map(j=>dv.getUint32(offs+j,true))};
        }else symbols[match[2]]={address:"0x"+addr.toString(16)};
      }
    }
  }
  const magic=Buffer.from("BR3BBX01","ascii");let found=-1;
  search:for(let i=0;i<=len-magic.length;i++){
    for(let j=0;j<magic.length;j++)if(ram[i+j]!==magic[j])continue search;
    found=i;break;
  }
  const marker=found>=0?{offset:found,schema:dv.getUint32(found+8,true),
    build_tag:dv.getUint32(found+12,true),
    events_cpu0:dv.getUint32(found+16,true),
    events_cpu1:dv.getUint32(found+20,true),
    jobs_sent:dv.getUint32(found+32,true),jobs_done:dv.getUint32(found+36,true),
    fallback:dv.getUint32(found+48,true),dma_ok:dv.getUint32(found+52,true),
    dma_missed:dv.getUint32(found+56,true),last_error:dv.getUint32(found+92,true)}:null;
  return {memory_bytes:len,br3_marker:marker,symbols};
}
async function run(label,path,mode='midi'){
 const {instance}=await WebAssembly.instantiate(wasm,{env:{fm1_jit_compile:()=>0}});
 const x=instance.exports;x.fm1_jit(0,0);
 const file=readFileSync(path), p=x.fm1_alloc(file.length);
 new Uint8Array(x.memory.buffer,p,file.length).set(file);
 const rc=x.fm1_boot_fwsc(p,file.length,0,0,200);
 if(rc)throw Error(label+" firmware rejected code "+rc);
 const L=[],R=[],phases=[],events=[];
 let nonzero=0,total=0,maxAbs=0,halted=false;let consecutiveZero=0;
 // Direct TRS MIDI byte stream (FM1's UART emulation), with both channel 1 and
 // GM drum channel 10. Test six known percussion note values individually.
 const midi=(status,note,velocity)=>{for(const b of [status,note,velocity])x.fm1_midi(b);events.push({block:k,status,note,velocity,emulated_ms:x.fm1_ms()})};
 const keys=[36,38,42,46,49,51];
 let k=0;
 for(;k<800;k++){
   if(mode==='keys'){
     // Two physical controls, no synthetic DSP notes: real keyboard matrix id0
     // (key F3) and transport PLAY (FM1 button id 39, verified from UI map).
     if(k===120){x.fm1_key(39,1);events.push({block:k,key:39,down:1})}
     if(k===125){x.fm1_key(39,0);events.push({block:k,key:39,down:0})}
     if(k===200){x.fm1_key(0,1);events.push({block:k,key:0,down:1})}
     if(k===310){x.fm1_key(0,0);events.push({block:k,key:0,down:0})}
     if(k===390){x.fm1_key(3,1);events.push({block:k,key:3,down:1})}
     if(k===500){x.fm1_key(3,0);events.push({block:k,key:3,down:0})}
   }
   if(mode==='midi'&&k>=120&&k<120+6*92&&(k-120)%92===0){
     const note=keys[Math.floor((k-120)/92)];
     midi(0x90,note,110);midi(0x99,note,110);
   }
   if(mode==='midi'&&k>=176&&k<176+6*92&&(k-176)%92===0){
     const note=keys[Math.floor((k-176)/92)];
     midi(0x80,note,0);midi(0x89,note,0);
   }
   const have=x.fm1_render(framesPerBlock,4000000);
   if(have>0){
     const data=new DataView(x.memory.buffer);
     const lp=x.fm1_out_l(),rp=x.fm1_out_r();
     let count=0,peak=0;
     for(let j=0;j<have;j++){
       const a=f32Sample(data,lp+j*4),b=f32Sample(data,rp+j*4);
       L.push(a);R.push(b);
       if(Math.abs(a)>1e-8||Math.abs(b)>1e-8)count++;
       peak=Math.max(peak,Math.abs(a),Math.abs(b));
     }
     nonzero+=count;total+=have;maxAbs=Math.max(maxAbs,peak);
     if(k%50===0)phases.push({block:k,ms:x.fm1_ms(),frames:have,nonzero:count,peak});
     consecutiveZero=count===0?consecutiveZero+1:0;
   }
   if(x.fm1_halted()){halted=true;break}
 }
 const ptr=x.fm1_blackbox_json(),mem=new Uint8Array(x.memory.buffer);
 let end=ptr;while(end<mem.length&&mem[end])end++;
 const bb=JSON.parse(new TextDecoder().decode(mem.subarray(ptr,end)));
 const result={label,firmware_sha_source:path,fwsc_bytes:file.length,quanta:k,frames:total,
   nonzero_stereo_frames:nonzero,peak:maxAbs,halted,reason:bb.reason,
   emulated_ms:bb.ms,cpu0_insn:bb.cpu0?.insn_count,cpu1_insn:bb.cpu1?.insn_count,
   lcd_revision:x.fm1_lcd_revision(),control_events:bb.control_events?.length??0,
   stimulus_mode:mode,events_sent:events.length,input_events:events,phase_samples:phases,
   guest_state:label.startsWith("biomech3-")?guestDiagnostic(x):undefined};
 writeFileSync(outDir+"/"+label+".json",JSON.stringify(result,null,2));
 writeFileSync(outDir+"/"+label+".wav",encodeWav(L,R));
 console.log("BR3_MUSICAL_BLACKBOX "+JSON.stringify(result));
 if(halted)throw Error(label+" firmware halted "+bb.reason);
 return result;
}
const stock=await run("stock-midi",stockPath);
const br3=await run("biomech3-midi",br3Path);
const keys=await run("biomech3-keys",br3Path,"keys");
const tone=bootNotePath?await run("biomech3-direct-note",bootNotePath,"none"):null;
const queued=queuedMidiPath?await run("biomech3-queued-midi",queuedMidiPath,"none"):null;
console.log("BR3_MUSICAL_GUARD "+JSON.stringify({stock_pcm:stock.nonzero_stereo_frames,br3_pcm:br3.nonzero_stereo_frames,stock_peak:stock.peak,br3_peak:br3.peak,br3_keyboard_pcm:keys.nonzero_stereo_frames,br3_keyboard_peak:keys.peak,direct_note_pcm:tone?.nonzero_stereo_frames??null,direct_note_peak:tone?.peak??null,queued_midi_pcm:queued?.nonzero_stereo_frames??null,queued_midi_peak:queued?.peak??null,br3_fwsc_boot:true}));
console.log("STAGE: real firmware booted; MIDI was injected. Nonzero PCM and musical behavior remain separately evidenced.");
