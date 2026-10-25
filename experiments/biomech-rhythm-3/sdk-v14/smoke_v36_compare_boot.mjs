// Read-only guest symbol-entry comparison: true pinned V14 vs BR3 v29.
import {readFileSync} from "node:fs";
import {createHash} from "node:crypto";
const [wasm,stockFw,stockNm,br3Fw,br3Nm]=process.argv.slice(2);
const names=[
  "fm1_app_init","fm1_device_start","fm1_controls_init","groove_screen_init",
  "fm1_io_trs_midi_enabled","fm1_midi_input_ports","fm1_app_midi_received",
  "fm1_control_request","os_task_create","fm1_r_f03cc16d330d",
  "biomech_sdk_init","biomech_sdk_control","groove_screen_control",
  "fm1_audio_start","fm1_route_short","fm1_midi_ready_ports"
];
const wasmBytes=readFileSync(wasm);
function getSymbols(path) {
 const lines=readFileSync(path,"utf8").split("\n");
 const m=new Map();
 for(const l of lines){const x=l.match(/^([0-9a-fA-F]+)\s+[a-zA-Z]\s+(\S+)$/);if(x)m.set(x[2],parseInt(x[1],16));}
 return m;
}
async function test(label,fp,np){
 const fw=readFileSync(fp),sha=createHash("sha256").update(fw).digest("hex");
 const nm=getSymbols(np);
 const {instance}=await WebAssembly.instantiate(wasmBytes,{env:{fm1_jit_compile:()=>0}});
 const x=instance.exports;x.fm1_jit(0,0);
 const ptr=x.fm1_alloc(fw.length);
 new Uint8Array(x.memory.buffer,ptr,fw.length).set(fw);
 const rc=x.fm1_boot_fwsc(ptr,fw.length,0,0,200);
 if(rc)throw Error("boot "+label+" "+rc);
 const targets=names.map((n,i)=>({name:n,addr:nm.get(n)||0,i}));
 for(const t of targets)if(t.addr)x.fm1_br3_v36_add_probe(t.i,t.addr);
 function decode(n){
  const p=x[n](),m=new Uint8Array(x.memory.buffer);let e=p;
  while(e<m.length&&m[e])e++;
  return JSON.parse(new TextDecoder().decode(m.subarray(p,e)));
 }
 let snapshots=[];
 for(let k=0;k<520;k++){
  if([110,230,400].includes(k))for(const b of [0x90,60,110])x.fm1_midi(b);
  if(k===170)x.fm1_key(39,1);
  if(k===180)x.fm1_key(39,0);
  x.fm1_render(128,4000000);
  if([0,5,10,25,50,80,110,135,170,230,300,400,519].includes(k)){
   const boot=decode("fm1_br3_v36_boot_json");
   const uart=decode("fm1_br3_v33_uart_json");
   const bb=decode("fm1_blackbox_json");
   snapshots.push({k,ms:boot.ms,boot,uart,irq20:bb.br3_v32_irq_delivered?.[20],
    irq63:bb.br3_v32_irq_delivered?.[63],irq3:bb.br3_v32_irq_delivered?.[3],
    irq11:bb.br3_v32_irq_delivered?.[11],cpu0:bb.cpu0.pc,halt:bb.halted,reason:bb.reason});
  }
  if(x.fm1_halted())break;
 }
 const end=snapshots.at(-1);
 const present=targets.filter(z=>z.addr).map(z=>({symbol:z.name,addr:"0x"+z.addr.toString(16),
   hits:end.boot.counts[z.i]}));
 console.log("BR3_V36_BOOT_"+label,JSON.stringify({label,sha,firmware_length:fw.length,
   symbols:present,missing:targets.filter(t=>!t.addr).map(t=>t.name),
   uart_end:end.uart,irq_end:{uart:end.irq20,panel:end.irq63,tick:end.irq3,audio:end.irq11},
   events:end.boot.events,checkpoints:snapshots.map(z=>({k:z.k,ms:z.ms,
   uartCon:z.uart.registers[0],rxAddr:z.uart.registers[2],drops:z.uart.dropped,
   counts:z.boot.counts,pc:z.cpu0,halt:z.halt}))}));
 return {label,sha,present,uart:end.uart,irq20:end.irq20,events:end.boot.events};
}
const stock=await test("STOCK",stockFw,stockNm);
const br3=await test("BR3",br3Fw,br3Nm);
console.log("BR3_V36_GATE",JSON.stringify({
 stock_uart:stock.uart.registers[0],br3_uart:br3.uart.registers[0],
 stock_drop:stock.uart.dropped,br3_drop:br3.uart.dropped,
 stock_20:stock.irq20,br3_20:br3.irq20,
 stock_symbols:stock.present,br3_symbols:br3.present}));
