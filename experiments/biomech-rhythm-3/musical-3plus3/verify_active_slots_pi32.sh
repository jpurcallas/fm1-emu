#!/bin/bash
# 64-slot pool remains intact: skip ONLY repeated per-sample visits to idle slots.
# Preserve six TRACKS, polyphony, voice-stealing and original summation order.
set -euo pipefail
S=experiments/biomech-rhythm-3/musical-3plus3
O=/tmp/biomech3-music
T=/tmp/jieli/pi32v2/bin
L=/tmp/jieli/pi32v2/lib/r3
"$T/clang" -target pi32v2 -I/tmp/jieli/pi32v2/include -mcpu=r3 -mfprev1 -ffp-contract=off -O2 -ffreestanding -fno-builtin -ffunction-sections -fdata-sections -DBR3_DUAL_CORE -DBR3_PI32V2 -DBR3_ACTIVE_SLOTS_LAB -I"$S" -c "$S/biomech.c" -o "$O/engine_live.o"
"$T/ld" --gc-sections -T "$S/linkcheck.ld" -e _start "$O/cpu0_entry.o" "$O/cpu1_entry.o" "$O/engine_live.o" "$O/br3_cpu1_runtime.o" "$O/br3_blackbox.o" "$O/linkcheck_main.o" --start-group "$L/libm.a" "$L/libc.a" "$L/libcompiler_rt.a" --end-group -o "$O/music_live.elf"
/tmp/jieli/common/bin/objcopy -O binary -j .text "$O/music_live.elf" "$O/live.text"
/tmp/jieli/common/bin/objcopy -O binary -j .data "$O/music_live.elf" "$O/live.data"
"$T/nm" "$O/music_live.elf" > "$O/music_live.nm"
python3 - "$O" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1])
lines=p.joinpath('music_live.nm').read_text().splitlines()
def symbol(name):
 for line in lines:
  fields=line.split()
  if len(fields)==3 and fields[2]==name:return int(fields[0],16)
 raise RuntimeError(name)
a=p.joinpath('live.text').read_bytes()
b=p.joinpath('live.data').read_bytes()
off=symbol('_data_load')-0x02000120
assert off>=len(a) and symbol('_bss_end')<0x01C74000
image=a+bytes([255])*(off-len(a))+b
assert len(image)<=0x8DFBC and image[:4]==bytes.fromhex('04818000')
p.joinpath('music_live.bin').write_bytes(image)
print('BR3_ACTIVE_SLOTS_IMAGE',len(image),'BSS_END',hex(symbol('_bss_end')))
PY
node "$S/smoke_native.mjs" "$O/music_live.bin" "$O/music_live.nm" "$O/fm1_web.wasm"
node "$S/compare_native.mjs" "$O/serial_music.bin" "$O/serial_music.nm" "$O/music_live.bin" "$O/music_live.nm" "$O/fm1_web.wasm"
echo 'PASS: six-track 3+3 active-slot native DSP parity with serial (same order, full pool)'
