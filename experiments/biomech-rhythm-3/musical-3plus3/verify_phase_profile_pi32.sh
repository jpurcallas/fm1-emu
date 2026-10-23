#!/bin/bash
# BIOMECH 3 native CPU1 pipeline phase audit; no SDK, firmware or DSP changes.
set -euo pipefail
S=experiments/biomech-rhythm-3/musical-3plus3
O=/tmp/biomech3-music
T=/tmp/jieli/pi32v2/bin
L=/tmp/jieli/pi32v2/lib/r3
"$T/clang" -target pi32v2 -I/tmp/jieli/pi32v2/include -mcpu=r3 -mfprev1 -ffp-contract=off -O2 -ffreestanding -fno-builtin -ffunction-sections -fdata-sections -DBR3_DUAL_CORE -DBR3_PI32V2 -DBR3_PROFILE_PHASES -I"$S" -c "$S/biomech.c" -o "$O/engine_profile.o"
"$T/ld" --gc-sections -T "$S/linkcheck.ld" -e _start "$O/cpu0_entry.o" "$O/cpu1_entry.o" "$O/engine_profile.o" "$O/br3_cpu1_runtime.o" "$O/br3_blackbox.o" "$O/linkcheck_main.o" --start-group "$L/libm.a" "$L/libc.a" "$L/libcompiler_rt.a" --end-group -o "$O/music_profile.elf"
/tmp/jieli/common/bin/objcopy -O binary -j .text "$O/music_profile.elf" "$O/profile.text"
/tmp/jieli/common/bin/objcopy -O binary -j .data "$O/music_profile.elf" "$O/profile.data"
"$T/nm" "$O/music_profile.elf" > "$O/music_profile.nm"
python3 - "$O" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1])
lines=p.joinpath('music_profile.nm').read_text().splitlines()
def symbol(name):
 for line in lines:
  fields=line.split()
  if len(fields)==3 and fields[2]==name:return int(fields[0],16)
 raise RuntimeError('missing '+name)
a=p.joinpath('profile.text').read_bytes()
b=p.joinpath('profile.data').read_bytes()
off=symbol('_data_load')-0x02000120
assert off>=len(a) and symbol('_bss_end')<0x01C74000
image=a+bytes([255])*(off-len(a))+b
assert len(image)<=0x8DFBC and image[:4]==bytes.fromhex('04818000')
p.joinpath('music_profile.bin').write_bytes(image)
print('BR3_PHASE_IMAGE',len(image),'BSS_END',hex(symbol('_bss_end')))
PY
node "$S/compare_native.mjs" "$O/serial_music.bin" "$O/serial_music.nm" "$O/music_profile.bin" "$O/music_profile.nm" "$O/fm1_web.wasm"
echo "PASS: 3+3 phase profiling preserved original PCM in native emulator"
