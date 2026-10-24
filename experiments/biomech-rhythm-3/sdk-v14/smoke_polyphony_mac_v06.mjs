// Emulator-only V14 BR3 polyphonic listening candidate smoke.
// Build actual WAV and verify guest active voice counters. No mock DSP.
import {readFileSync,writeFileSync} from "node:fs";
const [wasmPath,fwscPath,nmPath,outPath]=process.argv.slice(2);
if(!outPath)throw Error("usage: node smoke_polyphony_mac_v05.mjs emulator.wasm br3.fwsc sdk.nm output-prefix");
const source=new Uint8Array(readFileSync(wasmPath));
const {instance}=await WebAssembly.instantiate(source,{env:{fm1_jit_compile:()=>0}});
const x=instance.exports;
x.fm1_jit(0,0);
const firmware=readFileSync(fwscPath);
const fp=x.fm1_alloc(firmware.length);
new Uint8Array(x.memory.buffer,fp,firmware.length).set(firmware);
const rc=x.fm1_boot_fwsc(fp,firmware.length,0,0,200);
if(rc)throw Error("BR3 guest boot rejected "+rc);
const wanted=["br3_v06_scenario","br3_v06_notes_sent","br3_v06_active_at_start",
 "br3_v06_audio_calls","br3_v06_guest_frames","br3_v06_render_returned"];
const scenario=process.env.BR3_V06_SCENARIO||"unknown";
const symbols={};
for(const line of readFileSync(nmPath,"utf8").split("\n")){
 const m=line.trim().match(/^([0-9a-fA-F]+)\s+[a-zA-Z]\s+(\S+)$/);
 if(m&&wanted.includes(m[2]))symbols[m[2]]=parseInt(m[1],16)-0x01c00000;
}
for(const key of wanted)if(!(key in symbols))throw Error("missing real C99 LAB symbol "+key);
const L=[],R=[],snapshots=[];
let frames=0,nonzero=0,peak=0,short=0,halted=false,firstAudio=-1;
for(let q=0;q<650;q++){
 const have=x.fm1_render(128,4000000);
 if(have!==128)short++;
 if(have>0){
  if(firstAudio<0)firstAudio=q;
  const data=new DataView(x.memory.buffer);
  const l=x.fm1_out_l(),r=x.fm1_out_r();
  for(let j=0;j<have;j++){
   const a=data.getFloat32(l+j*4,true),b=data.getFloat32(r+j*4,true);
   if(!Number.isFinite(a)||!Number.isFinite(b))throw Error("non-finite PCM");
   L.push(a);R.push(b);
   if(Math.abs(a)>1e-7||Math.abs(b)>1e-7)nonzero++;
   peak=Math.max(peak,Math.abs(a),Math.abs(b));
  }
  frames+=have;
 }
 const p=x.fm1_blackbox_ram_ptr(),len=x.fm1_blackbox_ram_len();
 const ram=new DataView(x.memory.buffer,p,len);
 const get=k=>{let off=symbols[k];if(off<0||off+4>len)throw Error("symbol outside RAM "+k);return ram.getUint32(off,true)};
 if(q%25===0||q===649) snapshots.push({q,host_frames:frames,
   guest_frames:get("br3_v06_guest_frames"),calls:get("br3_v06_audio_calls"),
   returns:get("br3_v06_render_returned"),active:get("br3_v06_active_at_start")});
 if(x.fm1_halted()){halted=true;break}
}
const p=x.fm1_blackbox_ram_ptr(),len=x.fm1_blackbox_ram_len(),ram=new DataView(x.memory.buffer,p,len);
const read=k=>ram.getUint32(symbols[k],true);
const state=Object.fromEntries(wanted.map(k=>[k,read(k)]));
const wav=Buffer.alloc(44+frames*4);
wav.write("RIFF",0);wav.writeUInt32LE(wav.length-8,4);wav.write("WAVEfmt ",8);
wav.writeUInt32LE(16,16);wav.writeUInt16LE(1,20);wav.writeUInt16LE(2,22);
wav.writeUInt32LE(44100,24);wav.writeUInt32LE(44100*4,28);
wav.writeUInt16LE(4,32);wav.writeUInt16LE(16,34);
wav.write("data",36);wav.writeUInt32LE(frames*4,40);
for(let i=0;i<frames;i++){
 for(const [ch,value] of [[0,L[i]],[1,R[i]]]){
  wav.writeInt16LE(Math.max(-32768,Math.min(32767,Math.round(value*32767))),44+4*i+ch*2);
 }
}
writeFileSync(outPath+".wav",wav);
const report={model:"FM1 V14 PI32v2 BR3 unchanged DSP v0.6 A/B",scenario,fwsc:fwscPath,jit:false,mhz:200,
 frames,short,nonzero,peak,firstAudio,halted,state,snapshots,\n expected_notes:scenario==="single"?1:6,guest_progress:state.br3_v06_render_returned>=60,
 warning:"AUTO-generated notes in real C99 audio owner; not external MIDI/keys, not safe CPU1 3+3 or physical FM1 certification."};
writeFileSync(outPath+".json",JSON.stringify(report,null,2));
console.log("BR3_POLYPHONY_V06 "+JSON.stringify(report));
if(halted||state.br3_v06_active_at_start!==(scenario==="single"?1:6)||state.br3_v06_notes_sent!==(scenario==="single"?1:6))
 throw Error("BR3_V06_NOTE_GATE_FAILED");
if(!nonzero)console.log("BR3_V06_SILENT_GUEST warning: note triggers occurred but PCM is silent");
if(state.br3_v06_render_returned<60)
 console.log("BR3_V06_DSP_NOT_ADVANCING warning: guest render calls insufficient even if host PCM nonzero");
console.log("BR3_V06_DONE: see guest frame progress and WAV; do not assume sustained polyphony");
