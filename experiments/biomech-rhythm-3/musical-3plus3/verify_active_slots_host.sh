#!/bin/bash
# Long-form six-track, 64-slot HOST parity including MIDI, sequence/generative
# steps and forced post-join CPU1 fallback; no audio/DSP substitutions.
set -euo pipefail
S=experiments/biomech-rhythm-3/musical-3plus3
O=/tmp/biomech3-host-active
mkdir -p "$O"
for CC in gcc clang; do
  COMMON='-std=c99 -O2 -ffp-contract=off -fno-fast-math -fno-strict-aliasing'
  "$CC" $COMMON -pthread -I"$S/reference" "$S/reference/biomech.c" "$S/test_render.c" -lm -o "$O/serial_$CC"
  "$CC" $COMMON -pthread -DBR3_DUAL_CORE -DBR3_ACTIVE_SLOTS_LAB -I"$S" "$S/biomech.c" "$S/test_render.c" -lm -o "$O/active_$CC"
  for MODE in 0 1 2; do
    "$O/serial_$CC" "$O/serial_$CC-$MODE.pcm" "$MODE"
    "$O/active_$CC" "$O/active_$CC-$MODE.pcm" "$MODE"
    cmp "$O/serial_$CC-$MODE.pcm" "$O/active_$CC-$MODE.pcm"
    BR3_INJECT_CPU1_ERRORS=1 "$O/active_$CC" "$O/fallback_$CC-$MODE.pcm" "$MODE"
    cmp "$O/serial_$CC-$MODE.pcm" "$O/fallback_$CC-$MODE.pcm"
    echo "BR3_ACTIVE_HOST_PASS compiler=$CC mode=$MODE bytes=$(stat -c%s "$O/serial_$CC-$MODE.pcm") $(sha256sum "$O/serial_$CC-$MODE.pcm" | cut -c1-16)"
  done
done
echo 'PASS: serial vs active-only 3+3 vs CPU1 failure fallback, six voices, all three corpuses, GCC and Clang, bit-identical full PCM'
