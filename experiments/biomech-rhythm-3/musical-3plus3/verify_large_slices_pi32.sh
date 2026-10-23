#!/bin/bash
# Measure LARGE 64/128 slice overhead and memory in emulated PI32v2; NO SDK firmware.
# Validate against unmodified serial native reference, DO NOT publish if any fails.
set -euo pipefail
S=experiments/biomech-rhythm-3/musical-3plus3
T=/tmp/jieli/pi32v2/bin
L=/tmp/jieli/pi32v2/lib/r3
O=/tmp/biomech3-music
for FRAMES in 64 128; do
  echo "=== BR3 GUEST PI32v2 3+3 frame slice $FRAMES ==="
  "$T/clang" -target pi32v2 -I/tmp/jieli/pi32v2/include -mcpu=r3 -mfprev1 -ffp-contract=off -O2 -ffreestanding -fno-builtin -ffunction-sections -fdata-sections -DBR3_DUAL_CORE -DBR3_PI32V2 -DBR3_SLICE_FRAMES="$FRAMES" -DBR3_LARGE_SLICE_LAB -I"$S" -c "$S/biomech.c" -o "$O/biomech_$FRAMES.o"
  "$T/clang" -target pi32v2 -I/tmp/jieli/pi32v2/include -mcpu=r3 -mfprev1 -ffp-contract=off -O2 -ffreestanding -fno-builtin -ffunction-sections -fdata-sections -DBR3_DUAL_CORE -DBR3_PI32V2 -DBR3_SLICE_FRAMES="$FRAMES" -DBR3_LARGE_SLICE_LAB -I"$S" -c "$S/br3_cpu1_runtime.c" -o "$O/br3_cpu1_runtime_$FRAMES.o"
  "$T/ld" --gc-sections -T "$S/linkcheck.ld" -e _start "$O/cpu0_entry.o" "$O/cpu1_entry.o" "$O/biomech_$FRAMES.o" "$O/br3_cpu1_runtime_$FRAMES.o" "$O/br3_blackbox.o" "$O/linkcheck_main.o" --start-group "$L/libm.a" "$L/libc.a" "$L/libcompiler_rt.a" --end-group -o "$O/br3_music_$FRAMES.elf"
  /tmp/jieli/common/bin/objcopy -O binary -j .text "$O/br3_music_$FRAMES.elf" "$O/text_$FRAMES.bin"
  /tmp/jieli/common/bin/objcopy -O binary -j .data "$O/br3_music_$FRAMES.elf" "$O/data_$FRAMES.bin"
  "$T/nm" "$O/br3_music_$FRAMES.elf" > "$O/br3_music_$FRAMES.nm"
  python3 - "$O" "$FRAMES" <<'PY'
import pathlib,sys
root=pathlib.Path(sys.argv[1]);frames=sys.argv[2]
syms=root.joinpath('br3_music_'+frames+'.nm').read_text().splitlines()
def symbol(name):
 for line in syms:
  fields=line.split()
  if len(fields)==3 and fields[2]==name:return int(fields[0],16)
 raise ValueError('missing '+name)
a=root.joinpath('text_'+frames+'.bin').read_bytes()
b=root.joinpath('data_'+frames+'.bin').read_bytes()
off=symbol('_data_load')-0x02000120
assert off>=len(a) and symbol('_bss_end')<0x01c74000
data=a+bytes([255])*(off-len(a))+b
assert len(data)<=0x8dfbc and data[:4]==bytes.fromhex('04818000')
root.joinpath('br3_music_'+frames+'.bin').write_bytes(data)
print('BR3_SLICE_MEMORY',frames,'engine_bytes',len(data),'BSS_END',hex(symbol('_bss_end')))
PY
  node "$S/smoke_native.mjs" "$O/br3_music_$FRAMES.bin" "$O/br3_music_$FRAMES.nm" "$O/fm1_web.wasm"
  node "$S/compare_native.mjs" "$O/serial_music.bin" "$O/serial_music.nm" "$O/br3_music_$FRAMES.bin" "$O/br3_music_$FRAMES.nm" "$O/fm1_web.wasm"
done
echo 'PASS: diagnostic 64/128 guest PI32v2 slices match original serial PCM; inspect CPU effort and BSS before any adoption'
