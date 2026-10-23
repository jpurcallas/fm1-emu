// Emulated original SDK-vs-BIOMECH3 FWSC first boot evidence.
// The emulator owns the BLACK BOX even if firmware does not initialize.
import {readFileSync} from "node:fs";
const [wasmPath, stockPath, br3Path]=process.argv.slice(2);
if(!br3Path) throw Error("usage smoke_fwsc_blackbox.mjs emulator.wasm stock.fwsc BR3.fwsc");
const wasm=readFileSync(wasmPath);
async function boot(label,path) {
  const {instance}=await WebAssembly.instantiate(wasm,{env:{fm1_jit_compile:()=>0}});
  const x=instance.exports;
  x.fm1_jit(0,0);
  const bytes=readFileSync(path);
  const ptr=x.fm1_alloc(bytes.length);
  new Uint8Array(x.memory.buffer,ptr,bytes.length).set(bytes);
  const rc=x.fm1_boot_fwsc(ptr,bytes.length,0,0,200);
  if(rc!==0)throw Error(label+": rejected real FWSC package; code="+rc);
  let quanta=0,frames=0,nonzero=0,maxAbs=0,halted=false,screenRevision=0;
  // No unsupported synthetic audio: each call drives the same FWSC V14 +
  // ALNK/DMA as browser's AudioWorklet, including actual guest boot time.
  for(;quanta<390;quanta++){
    const have=x.fm1_render(128,4000000);
    frames+=have;
    if(have){
      const data=new DataView(x.memory.buffer);
      const l=x.fm1_out_l(),r=x.fm1_out_r();
      for(let j=0;j<128;j++){
        const a=Math.abs(data.getFloat32(l+j*4,true));
        const b=Math.abs(data.getFloat32(r+j*4,true));
        if(a>1e-8||b>1e-8)nonzero++;
        maxAbs=Math.max(maxAbs,a,b);
      }
    }
    if(x.fm1_halted()){halted=true;break}
  }
  screenRevision=x.fm1_lcd_revision();
  const p=x.fm1_blackbox_json(),bytesNow=new Uint8Array(x.memory.buffer);
  let n=p;while(n<bytesNow.length && bytesNow[n]!==0)n++;
  if(n===bytesNow.length)throw Error("BLACK BOX string unterminated");
  const bb=JSON.parse(new TextDecoder().decode(bytesNow.subarray(p,n)));
  const result={label,packageBytes:bytes.length,quanta,frames,nonzero,maxAbs,
    halted,emulatedMs:bb.ms,cpu0PC:bb.cpu0?.pc,cpu0Instructions:bb.cpu0?.insn_count,
    cpu1PC:bb.cpu1?.pc,cpu1Instructions:bb.cpu1?.insn_count,
    screenRevision,reason:bb.reason,ramBytes:bb.ram_len,controlEvents:bb.control_events?.length||0};
  console.log("BR3_FWSC_BLACKBOX",JSON.stringify(result));
  if(bb.ram_len!==1048576 || !bb.cpu0)throw Error(label+": BLACK BOX missing valid state");
  if(halted)throw Error(label+": guest halted before completed boot smoke: "+bb.reason);
  return result;
}
const a=await boot("stock-v14-control",stockPath);
const b=await boot("biomech3-v04-16f",br3Path);
if(!a.cpu0Instructions||!b.cpu0Instructions)throw Error("CPU never executed");
console.log("BR3_FWSC_EMULATOR_SMOKE",JSON.stringify({stock_ms:a.emulatedMs,br3_ms:b.emulatedMs,
  stock_frames:a.frames,br3_frames:b.frames,br3_pcm_samples:b.nonzero}));
console.log("PASS: both genuine packaged FWSC accepted; emulated CPU runs and BLACK BOX available. Audio requires nonzero frame evidence separately.");
