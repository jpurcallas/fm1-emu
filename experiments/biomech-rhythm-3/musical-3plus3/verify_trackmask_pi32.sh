#!/bin/bash
# Experimental alternative 3+3 track assignments. Do NOT modify production
# default 0x38 (CPU0 tracks 1..3, CPU1 4..6) without author approval.
set -euo pipefail
S=experiments/biomech-rhythm-3/musical-3plus3
T=/tmp/jieli/pi32v2/bin
L=/tmp/jieli/pi32v2/lib/r3
O=/tmp/biomech3-music
for MASK in 0x2A 0x15; do
  TAG="${MASK#0x}"
  "$T/clang" -target pi32v2 -I/tmp/jieli/pi32v2/include -mcpu=r3 -mfprev1 -ffp-contract=off -O2 -ffreestanding -fno-builtin -ffunction-sections -fdata-sections -DBR3_DUAL_CORE -DBR3_PI32V2 -DBR3_CPU1_TRACK_MASK="$MASK" -I"$S" -c "$S/biomech.c" -o "$O/engine_mask_$TAG.o"
  "$T/ld" --gc-sections -T "$S/linkcheck.ld" -e _start "$O/cpu0_entry.o" "$O/cpu1_entry.o" "$O/engine_mask_$TAG.o" "$O/br3_cpu1_runtime.o" "$O/br3_blackbox.o" "$O/linkcheck_main.o" --start-group "$L/libm.a" "$L/libc.a" "$L/libcompiler_rt.a" --end-group -o "$O/music_mask_$TAG.elf"
  /tmp/jieli/common/bin/objcopy -O binary -j .text "$O/music_mask_$TAG.elf" "$O/mask_$TAG.text"
  /tmp/jieli/common/bin/objcopy -O binary -j .data "$O/music_mask_$TAG.elf" "$O/mask_$TAG.data"
  "$T/nm" "$O/music_mask_$TAG.elf" > "$O/music_mask_$TAG.nm"
  python3 - "$O" "$TAG" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1]);tag=sys.argv[2]
sym=p.joinpath(f'music_mask_{tag}.nm').read_text().splitlines()
def symbol(name):
 for l in sym:
  f=l.split()
  if len(f)==3 and f[2]==name:return int(f[0],16)
 raise RuntimeError(name)
a=p.joinpath(f'mask_{tag}.text').read_bytes()
b=p.joinpath(f'mask_{tag}.data').read_bytes()
off=symbol('_data_load')-0x02000120
assert off>=len(a) and symbol('_bss_end')<0x01c74000
image=a+bytes([255])*(off-len(a))+b
assert len(image)<=0x8dfbc and image[:4]==bytes.fromhex('04818000')
p.joinpath(f'music_mask_{tag}.bin').write_bytes(image)
print('BR3_TRACKMASK_IMAGE',tag,len(image))
PY
  echo "=== CPU1 MASK $MASK ==="
  node "$S/smoke_native.mjs" "$O/music_mask_$TAG.bin" "$O/music_mask_$TAG.nm" "$O/fm1_web.wasm"
  node "$S/compare_native.mjs" "$O/serial_music.bin" "$O/serial_music.nm" "$O/music_mask_$TAG.bin" "$O/music_mask_$TAG.nm" "$O/fm1_web.wasm"
done
echo "PASS: both alternate 3+3 assignments preserve reference PCM in guest PI32"
