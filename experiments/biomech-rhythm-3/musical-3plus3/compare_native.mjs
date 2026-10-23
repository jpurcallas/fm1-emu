/* Compare actual PI32v2 serial and CPU1 3+3 native binary outputs.
 * Distinct WebAssembly instances so RAM/peripherals/CPU state cannot leak.
 * No DSP replacement; both versions use their real compiled C99 engines.
 */
import { readFileSync } from "node:fs";
const [serialBin, serialSymbols, parallelBin, parallelSymbols, wasmPath] = process.argv.slice(2);
if (!wasmPath) throw Error("usage: compare_native.mjs serial.bin serial.nm parallel.bin parallel.nm fm1_web.wasm");
const wasm = readFileSync(wasmPath);
async function run(binPath, symbolPath, label) {
  const image = readFileSync(binPath);
  const lines = readFileSync(symbolPath,"utf8").split("\n");
  const symbol = (name) => {
    const line=lines.find(l=>l.trim().endsWith(" "+name));
    if(!line) throw Error(label+": missing ELF symbol "+name);
    return parseInt(line.trim().split(/\s+/)[0],16);
  };
  const {instance}=await WebAssembly.instantiate(wasm,{env:{fm1_jit_compile:()=>0}});
  const x=instance.exports;
  x.fm1_jit(0,0);
  const n=0x120+image.length,ptr=x.fm1_alloc(n);
  new Uint8Array(x.memory.buffer,ptr,n).fill(0xff);
  new Uint8Array(x.memory.buffer,ptr+0x120,image.length).set(image);
  x.fm1_boot(ptr,n,0x02000120,200);
  const keys=["br3_test_status","br3_test_checksum","br3_test_peakbits","br3_test_rendered"];
  const addresses=Object.fromEntries(keys.map(k=>[k,symbol(k)-0x01C00000]));
  const read=k=>new DataView(x.memory.buffer,x.fm1_blackbox_ram_ptr()).getUint32(addresses[k],true);
  let status=0,rounds=0;
  for(;rounds<1500;rounds++){
    x.fm1_render(128,50000);
    status=read("br3_test_status");
    if(status===0xB330A11F || (status&0xFFFF0000)===0xB33E0000 || x.fm1_halted())break;
  }
  const data={label,rounds,halted:Boolean(x.fm1_halted())};
  for(const k of keys) data[k]=read(k);
  console.log("BR3_PI32_COMPARISON",JSON.stringify(data));
  if(data.halted || status!==0xB330A11F || data.br3_test_rendered!==32)
    throw Error(label+" native musical test did not complete");
  return data;
}
const a=await run(serialBin,serialSymbols,"serial");
const b=await run(parallelBin,parallelSymbols,"3plus3");
if(a.br3_test_checksum!==b.br3_test_checksum ||
   a.br3_test_peakbits!==b.br3_test_peakbits)
  throw Error("Native PI32v2 musical PCM DIFFERENCE: serial/CPU1 3+3 checksum or peak changed. Do not call it sonically identical.");
console.log("PASS: native PI32v2 serial and CPU1 3+3 engines reproduce exactly identical 4096-frame PCM checksums and peaks.");
