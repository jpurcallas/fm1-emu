#!/bin/bash
# 64-slot polyphony stress in actual PI32 guest, native CPU1 work at 200MHz.
# Golden serial and CPU1 3+3 receive identical note/voice-stealing patterns.
set -euo pipefail
S=experiments/biomech-rhythm-3/musical-3plus3
O=/tmp/biomech3-music
T=/tmp/jieli/pi32v2/bin
L=/tmp/jieli/pi32v2/lib/r3
COMMON='-target pi32v2 -I/tmp/jieli/pi32v2/include -mcpu=r3 -mfprev1 -ffp-contract=off -O2 -ffreestanding -fno-builtin -ffunction-sections -fdata-sections -DBR3_NATIVE_STRESS'
"$T/clang" $COMMON -DBR3_SERIAL_REFERENCE -I"$S" -c "$S/linkcheck_main.c" -o "$O/stress_serial_main.o"
"$T/clang" $COMMON -DBR3_DUAL_CORE -DBR3_PI32V2 -I"$S" -c "$S/linkcheck_main.c" -o "$O/stress_dual_main.o"
"$T/ld" --gc-sections -T "$S/linkcheck.ld" -e _start "$O/cpu0_entry.o" "$O/serial_engine.o" "$O/stress_serial_main.o" --start-group "$L/libm.a" "$L/libc.a" "$L/libcompiler_rt.a" --end-group -o "$O/stress_serial.elf"
"$T/ld" --gc-sections -T "$S/linkcheck.ld" -e _start "$O/cpu0_entry.o" "$O/cpu1_entry.o" "$O/engine_live.o" "$O/br3_cpu1_runtime.o" "$O/br3_blackbox.o" "$O/stress_dual_main.o" --start-group "$L/libm.a" "$L/libc.a" "$L/libcompiler_rt.a" --end-group -o "$O/stress_3plus3.elf"
for kind in serial 3plus3; do
  /tmp/jieli/common/bin/objcopy -O binary -j .text "$O/stress_$kind.elf" "$O/stress_$kind.text"
  /tmp/jieli/common/bin/objcopy -O binary -j .data "$O/stress_$kind.elf" "$O/stress_$kind.data"
  "$T/nm" "$O/stress_$kind.elf" > "$O/stress_$kind.nm"
done
python3 - "$O" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1])
for kind in ('serial','3plus3'):
 lines=p.joinpath('stress_'+kind+'.nm').read_text().splitlines()
 def symbol(name):
  for line in lines:
   x=line.split()
   if len(x)==3 and x[2]==name:return int(x[0],16)
  raise RuntimeError(name)
 a=p.joinpath('stress_'+kind+'.text').read_bytes()
 b=p.joinpath('stress_'+kind+'.data').read_bytes()
 off=symbol('_data_load')-0x02000120
 assert off>=len(a) and symbol('_bss_end')<0x01C74000
 img=a+bytes([255])*(off-len(a))+b
 assert len(img)<=0x8DFBC and img[:4]==bytes.fromhex('04818000')
 p.joinpath('stress_'+kind+'.bin').write_bytes(img)
 print('BR3_STRESS_NATIVE_IMAGE',kind,len(img),'BSS_END',hex(symbol('_bss_end')))
PY
node "$S/smoke_native.mjs" "$O/stress_3plus3.bin" "$O/stress_3plus3.nm" "$O/fm1_web.wasm"
node "$S/compare_native.mjs" "$O/stress_serial.bin" "$O/stress_serial.nm" "$O/stress_3plus3.bin" "$O/stress_3plus3.nm" "$O/fm1_web.wasm"
echo "PASS: native PI32 voice-stealing stress serial=CPU1 3+3 exact PCM"
