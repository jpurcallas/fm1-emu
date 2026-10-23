#!/bin/sh
# BIOMECH RHYTHM 3 3+3: independent PCM regression, HOST ONLY.
# Run from any directory: sh build_host_tests.sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REF="$HERE/../original"
OUT="$HERE/../tests-output"
mkdir -p "$OUT"
CC=${CC:-cc}
CFLAGS="-std=c99 -O2 -ffp-contract=off -fno-fast-math -fno-strict-aliasing"
"$CC" $CFLAGS -pthread "$REF/biomech.c" "$HERE/test_render.c" -lm -o "$OUT/reference"
"$CC" $CFLAGS -pthread -DBR3_DUAL_CORE "$HERE/biomech.c" "$HERE/test_render.c" -lm -o "$OUT/three_plus_three"
for MODE in 0 1 2; do
  "$OUT/reference" "$OUT/reference-$MODE.pcm" "$MODE"
  "$OUT/three_plus_three" "$OUT/three-plus-three-$MODE.pcm" "$MODE"
  cmp "$OUT/reference-$MODE.pcm" "$OUT/three-plus-three-$MODE.pcm"
  BR3_INJECT_CPU1_ERRORS=1 "$OUT/three_plus_three" "$OUT/fallback-$MODE.pcm" "$MODE"
  cmp "$OUT/reference-$MODE.pcm" "$OUT/fallback-$MODE.pcm"
  echo "PASS mode=$MODE: CPU0/CPU1 real parallel pthread and simulated fallback bit-exact"
done
"$CC" -std=c99 -Wall -Wextra -c "$HERE/br3_blackbox.c" -o "$OUT/br3_blackbox.o"
"$CC" -std=c99 -DBR3_DUAL_CORE -DBR3_PI32V2 -fsyntax-only "$HERE/br3_cpu1_runtime.c"
echo "PASS all C99 checks (HOST). PI32v2 binary integration not yet verified."
