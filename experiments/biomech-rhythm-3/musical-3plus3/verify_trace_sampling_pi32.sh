#!/bin/bash
# Performance control: with the SAME full DSP/CPU1 jobs compare BLACK BOX
# per-job event frequency 1 (default) versus 16 (laboratory only).
# Never change audio, CPU routing, fault logs or DMA behavior.
set -euo pipefail
S=experiments/biomech-rhythm-3/musical-3plus3
T=/tmp/jieli/pi32v2/bin
L=/tmp/jieli/pi32v2/lib/r3
O=/tmp/biomech3-music
"$T/clang" -target pi32v2 -I/tmp/jieli/pi32v2/include -mcpu=r3 -mfprev1 -ffp-contract=off -O2 -ffreestanding -fno-builtin -ffunction-sections -fdata-sections -DBR3_DUAL_CORE -DBR3_PI32V2 -DBR3_BB_SAMPLE_RATE=16 -I"$S" -c "$S/br3_cpu1_runtime.c" -o "$O/br3_cpu1_runtime_sample16.o"
"$T/ld" --gc-sections -T "$S/linkcheck.ld" -e _start "$O/cpu0_entry.o" "$O/cpu1_entry.o" "$O/biomech.o" "$O/br3_cpu1_runtime_sample16.o" "$O/br3_blackbox.o" "$O/linkcheck_main.o" --start-group "$L/libm.a" "$L/libc.a" "$L/libcompiler_rt.a" --end-group -o "$O/br3_music_sample16.elf"
/tmp/jieli/common/bin/objcopy -O binary -j .text "$O/br3_music_sample16.elf" "$O/sample16_text.bin"
/tmp/jieli/common/bin/objcopy -O binary -j .data "$O/br3_music_sample16.elf" "$O/sample16_data.bin"
"$T/nm" "$O/br3_music_sample16.elf" > "$O/br3_music_sample16.nm"
python3 - "$O" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1])
sym=p.joinpath('br3_music_sample16.nm').read_text().splitlines()
def symbol(name):
    for line in sym:
        a=line.split()
        if len(a)==3 and a[2]==name:return int(a[0],16)
    raise ValueError(name)
a=p.joinpath('sample16_text.bin').read_bytes()
b=p.joinpath('sample16_data.bin').read_bytes()
offset=symbol('_data_load')-0x02000120
assert offset>=len(a) and symbol('_bss_end')<0x01c74000
image=a+bytes([255])*(offset-len(a))+b
assert len(image)<=0x8dfbc
p.joinpath('br3_music_sample16.bin').write_bytes(image)
print('BR3_SAMPLE16_IMAGE_BYTES',len(image))
PY
node "$S/compare_native.mjs" "$O/serial_music.bin" "$O/serial_music.nm" "$O/br3_music_sample16.bin" "$O/br3_music_sample16.nm" "$O/fm1_web.wasm"
echo 'PASS: sampled BLACK BOX mode preserved reference PCM and executed CPU1; compare BR3_CPU_EFFORT to full trace'
