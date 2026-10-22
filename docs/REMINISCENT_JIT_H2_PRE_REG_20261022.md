# REMINISCENT FM-1 — pre-registered causal JIT experiment (2026-10-22)

## Immutable reference
- Firmware v3.0.23 `REMINISCENT_v323_SOLO_EMULADOR.fwsc`, SHA-256 `8409b8fec212cdeb7ac36b8a9576db74ebfe4e77d0100b59430a891260313467`.
- Original `fm1_web_BASELINE.wasm`, SHA-256 `7c2ae09ffc9d16db298aed2bda61e4b0c7546f8b7088332532bd604b6190f303`.
- Source base `master` commit `61b51596d5756d09902fc16cc5e0ecd550d4501e`.
- Instrumented diagnostic comparison with original PCM SHA-256 for 3.2 s at 200 MHz: `4a17e7723ea63c58601c6714eae071384c71c574fef319e56a3de53f5650cffb`.

## Measured cause
3.2 s, identical note script, profile OFF: 1,510 JIT compilations, 450 distinct origins, no region drops/resets, with `0x0200540c` origin 944 times under 944 different block IDs. The direct-mapped cache at this slot recorded 949 evictions by `0x01c0540c` (RAM vs XIP address alias).

## H2 (single changed cause)
The one-way direct-mapped decoded-block cache loses a hot XIP mapping when RAM and XIP PCs alias; repeated block rebuilding triggers unnecessary unique JIT modules and memory growth.

**One experimental change:** add a second way to the existing block cache for wasm32 only, keeping both colliding block IDs available with the existing RAM validity checks. Do not change instruction semantics, JIT emitter, SDK, firmware, DSP, MIDI, sample routing or timing.

**Predictions before edit:**
1. For the same 3.2 s pattern, PC `0x0200540c` compiles dramatically fewer times, ideally once, and total JIT region count falls below 1,510.
2. JIT short PCM SHA-256 exactly matches the original `4a17e772…` over all 128-frame quanta.
3. No JIT region invalidation/reset growth is introduced.
4. Heap/slots at 8 s fall materially, and a repeated 60 s run finishes without V8 OOM.
5. Must not claim real-time playback unless render deadline quantiles pass separately; browser remains untested until a dedicated Chrome run.

**Reject** if PCM diverges, native regression fails, input differs, or JIT OOM remains; do not merge into `master`. The diagnostic branch is unchanged and can be restored at any time.
