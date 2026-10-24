# REminiSCENT v0.14 UX03 — guest cold-boot regression and proposed memory fix

23 Oct 2026 Costa Rica. Branch `diagnostic/reminiscent-v014-boot-silence-ux03-20261023`. **NO INSTALL, NO MERGE.**

## Objective evidence (EXECUTED)
Source FWSC files recovered from the author's Library; SHA256:
- v0.13: `99c44e7e6ae59bdc68e84823065d6720c7ff177ff4203dd070da057da1c7a5e5`
- v0.14: `200c2fdc7b862d6cfffff904ef0621daab2970a8f00f9d4e6ce3ff388a3d6efe`

Reproduced with previously delivered v0.12 standalone emulator WebAssembly, JIT OFF, 200MHz, 950 × 128 host PCM requests, PLAY key 12 and 3 sets of 4 PART MIDI ON/OFF notes:
- v0.13: boot return=0, **113,380 nonzero audio frames, 34 short blocks, no HALT**; PCM float SHA256 `3c7b3ff99cf079a5d944d73155f1cfe7626accc76602849ee99bdb0262f6574b`.
- v0.14: boot return=0, **0 nonzero frames, 950 short blocks, no HALT**; PCM float SHA256 `fbe601b2e2f18d7f64011657a851686a1d60c03fbcc0eb9de379398c100a05be`.
- CPU snapshots: after 60–299 requests, v0.14 CPU0 consistently at ROM PC `0x0200c1d4`, SP `0x01c7e75c`; CPU1 remains `0x01c062b0`, suggesting incomplete SDK service boot. No claim that the specific PC names the precise cause.
- v0.13 CPU0 continues inside IRQ/audio code, CPU1 actively changes PC; user had previously heard v0.13 in native macOS FM1-LIVE-LAB.

**This REPLACES the previous 'v0.14 only compiled and not guest-tested' status. New status: v0.14 original EXECUTED, guest AUDIO REGRESSION reproduced in older WASM guest. Not yet tested on native macOS FM1-LIVE-LAB; no hardware claim.**

## Hypothesis (NOT yet confirmed)
v0.14 adds **+1,536B static RAM**, mostly `ram_patches[4][4][RN_UI_PAGE_COUNT][4]` = **1,472B**, replacing a v0.13 that booted. V14 stock has previously shown a RAM/heap-dependent lost callback/audio state. Test whether main-heap loss triggers v0.14 incomplete startup instead of attributing it to the navigation code without A/B.

## C99 source correction candidate (IMPLEMENTED, HOST TESTED; NOT PI32v2 BUILT)
Patch `UX03_V014_PRESET_RAM_FIX.patch`:
- Persist **all** per-PART local SOUND patch pages `RN_UI_SOURCE..RN_UI_SENDS`, not HOME/SEQ/global pages.
- 4 PARTS × 4 slots × 11 pages × 4 parameters = **704B** (old 1,472B). Place in `.memp_memory_x` cache BSS instead of main SRAM. Preserve 16 volatile audition slots, SAVE behavior and all musical DSP unchanged.
- Adjust save/load memcpy region and audition OSC index.
- Host Clang ASan/UBSan: 1,200 synthetic inputs PASS; additional patch roundtrip checks of all local SOUND parameters, PART isolation, HOME and shared REVERB unchanged PASS.
- **Important**: v0.12 SDK linker map found RAM_MALLOC_SIZE 9,280B, and a cache heap minimum assert 8,192B. New 704B cache usage would leave ~8,576B in that old map, subject to current link, layout and alignment. This is not a proof that v0.14 will boot.

The v0.14 ZIP does **not** carry the PI32v2 SDK, JieLi compiler, or `support/baseline_objs`; this environment does not have those paths, so **no fixed .fwsc was built**, and the original v0.14 binary is unchanged.

## Next acceptance
Compile this candidate in a complete original SDK/toolchain environment; inspect actual main/cache heap and APP/FS limits; package FWSC only for emulator; repeat guest cold boot, MIDI control RX → applied → postmix PCM → DMA and native Mac listening/BLACK BOX. Don't reclassify as 'audio fixed' before that. Do not cut PARTS/FX. Keep master and approved binaries untouched.

## Transfer BIOMECH
Relevant method: **cold-boot real FWSC A/B**, do not use SDK link or host control tests as musical boot evidence, and treat even ~1.5KB extra main SRAM as potentially material while memory/SDK services are marginal. **No code/offset transfer to BIOMECH**; verify its own RAM map and callback/audio trace.
