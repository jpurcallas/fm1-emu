// Original upstream FM1 V14 stock guest vs experimental v29 input diagnosis.
// No BR3 symbols, no musical substitutions, no hardware install.
import {readFileSync} from "node:fs";
import {createHash} from "node:crypto";
const [wasmPath,fwscPath]=process.argv.slice(2);
const pkg=readFileSync(fwscPath),sha=createHash("sha256").update(pkg).digest("hex");
const {instance}=await WebAssembly.instantiate(readFileSync(wasmPath),{env:{fm1_jit_compile:()=>0}});
const x=instance.exports;x.fm1_jit(0,0);
const ptr=x.fm1_alloc(pkg.length);new Uint8Array(x.memory.buffer,ptr,pkg.length).set(pkg);
const status=x.fm1_boot_fwsc(ptr,pkg.length,0,0,200);
if(status)throw Error("stock V14 FWSC boot rejected "+status);
const samples=[];
function readJson(exportName) {
 const p=x[exportName](),m=new Uint8Array(x.memory.buffer);let e=p;
 while(e<m.length&&m[e])e++;
 return JSON.parse(new TextDecoder().decode(m.subarray(p,e)));
}
for(let k=0;k<800;k++){
 if([100,200,400,600].includes(k))for(const v of [0x90,60,100])x.fm1_midi(v);
 if(k===350)x.fm1_key(39,1);
 if(k===370)x.fm1_key(39,0);
 x.fm1_render(128,4000000);
 if([0,5,8,20,50,100,110,200,210,350,370,400,410,600,610,799].includes(k)){
  const b=readJson("fm1_blackbox_json"),u=readJson("fm1_br3_v33_uart_json");
  samples.push({k,ms:b.ms,pc:"0x"+b.cpu0.pc.toString(16),user:b.cpu0.user,uart:u,
   irq20:b.br3_v32_irq_delivered?.[20],irq63:b.br3_v32_irq_delivered?.[63],tick:b.br3_v32_irq_delivered?.[3],
   audio:b.br3_v32_irq_delivered?.[11],halt:b.halted,reason:b.reason});
 }
 if(x.fm1_halted())break;
}
console.log("BR3_V34_STOCK_SDK_UART_BASELINE",JSON.stringify({sha,pkgBytes:pkg.length,samples}));
const f=samples.at(-1);
if(!f)throw Error("No stock guest time");
console.log("BR3_V34_STOCK_GATE",JSON.stringify({sha,ms:f.ms,uart_con0:f.uart.registers[0],
 rx_base:f.uart.registers[2],rx_end:f.uart.registers[3],irq20:f.irq20,
 midi_dropped:f.uart.dropped,os_ticks:f.tick,panel_irq:f.irq63,audio_irq:f.audio,halt:f.halt}));
