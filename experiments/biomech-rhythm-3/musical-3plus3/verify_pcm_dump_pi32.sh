#!/bin/bash
# Compare complete raw PCM for serial and real PI32 CPU1 3+3, normal and steal.
# Lab-only 32 KiB buffer, never installed in FM-1 firmware.
set -euo pipefail
S=experiments/biomech-rhythm-3/musical-3plus3
O=/tmp/biomech3-music
T=/tmp/jieli/pi32v2/bin
L=/tmp/jieli/pi32v2/lib/r3
for kind in normal stress; do
  FLAGS='-target pi32v2 -I/tmp/jieli/pi32v2/include -mcpu=r3 -mfprev1 -ffp-contract=off -O2 -ffreestanding -fno-builtin -ffunction-sections -fdata-sections -DBR3_PCM_DUMP_LAB'
  if [ "$kind" = stress ]; then FLAGS="$FLAGS -DBR3_NATIVE_STRESS"; fi
  "$T/clang" $FLAGS -DBR3_SERIAL_REFERENCE -I"$S" -c "$S/linkcheck_main.c" -o "$O/dump_${kind}_serial_main.o"
  "$T/clang" $FLAGS -DBR3_DUAL_CORE -DBR3_PI32V2 -I"$S" -c "$S/linkcheck_main.c" -o "$O/dump_${kind}_dual_main.o"
  "$T/ld" --gc-sections -T "$S/linkcheck.ld" -e _start "$O/cpu0_entry.o" "$O/serial_engine.o" "$O/dump_${kind}_serial_main.o" --start-group "$L/libm.a" "$L/libc.a" "$L/libcompiler_rt.a" --end-group -o "$O/dump_${kind}_serial.elf"
  "$T/ld" --gc-sections -T "$S/linkcheck.ld" -e _start "$O/cpu0_entry.o" "$O/cpu1_entry.o" "$O/engine_live.o" "$O/br3_cpu1_runtime.o" "$O/br3_blackbox.o" "$O/dump_${kind}_dual_main.o" --start-group "$L/libm.a" "$L/libc.a" "$L/libcompiler_rt.a" --end-group -o "$O/dump_${kind}_dual.elf"
  for mode in serial dual; do
    /tmp/jieli/common/bin/objcopy -O binary -j .text "$O/dump_${kind}_$mode.elf" "$O/dump_${kind}_$mode.text"
    /tmp/jieli/common/bin/objcopy -O binary -j .data "$O/dump_${kind}_$mode.elf" "$O/dump_${kind}_$mode.data"
    "$T/nm" "$O/dump_${kind}_$mode.elf" > "$O/dump_${kind}_$mode.nm"
  done
  python3 - "$O" "$kind" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1]);kind=sys.argv[2]
for mode in ('serial','dual'):
  base='dump_'+kind+'_'+mode
  lines=p.joinpath(base+'.nm').read_text().splitlines()
  def sym(s):
    for line in lines:
      x=line.split()
      if len(x)==3 and x[2]==s:return int(x[0],16)
    raise ValueError(s)
  a=p.joinpath(base+'.text').read_bytes()
  b=p.joinpath(base+'.data').read_bytes()
  offset=sym('_data_load')-0x02000120
  assert offset>=len(a) and sym('_bss_end')<0x01c74000
  image=a+bytes([255])*(offset-len(a))+b
  assert len(image)<=0x8dfbc
  p.joinpath(base+'.bin').write_bytes(image)
  print("BR3_NATIVE_PCM_DUMP",base,"IMAGE",len(image),"SRAM_BSS_END",hex(sym('_bss_end')))
PY
  BR3_REQUIRE_PCM_DUMP=1 node "$S/compare_native.mjs" "$O/dump_${kind}_serial.bin" "$O/dump_${kind}_serial.nm" "$O/dump_${kind}_dual.bin" "$O/dump_${kind}_dual.nm" "$O/fm1_web.wasm"
done
echo 'PASS: all 32768 stereo PCM bytes identical in both native PI32 test scenarios'
