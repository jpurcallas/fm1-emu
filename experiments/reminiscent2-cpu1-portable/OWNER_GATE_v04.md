# REminiSCENT 2 LAB — v0.4 CPU1 ownership gate

**Date**: 2026-10-23 · **Status**: HOST-test only; NO firmware, NO SDK integration, NO INSTALL, NO MERGE.

## Before engineering: fresh BIOMECH3 input

BIOMECH3 [PR #26](https://github.com/jpurcallas/fm1-emu/pull/26#issuecomment-6372651784) found that a **late CPU1 reset/boot inside V14 initialization could clobber an existing SDK owner**. Their guard now refuses an unverified owner rather than claiming the core. PI32v2 guest standalone 3+3 has passed earlier tests; the complete SDK adapter has NOT. Their memory-reduction figures are engine-specific and must not be copied to REminiSCENT. [CI on 8-/16-frame BIOMECH guest work](https://github.com/jpurcallas/fm1-emu/actions/runs/40009089555) is independent proof, not an implied design mandate.

## Change from REMIN v0.3

- Preserve the original REminiSCENT LAB v0.6 sound sources, `rn_v12_dsp.c`, oscillator algorithm, acoustic decoding, sequencer, effects and ISR→PCM→ALNK/DMA reference.
- Extend `rn_dc_executor` with an optional `ready(ctx)` preflight **BEFORE** `rn_dc_prepare` mutates the shared musical state. Return code `-5` means the previous CPU1 work might still be writing; do not process another block or commit DMA.
- Implement new `rn_v12_cpu1_guard.c/h` that **never boots, resets or claims CPU1**; it requires injected platform functions `owns_cpu1`, `memory_coherent`, `send`, bounded `wait_complete`, and independently verified `quiesced`.
- Following a rejected completion, the in-flight job stays quarantined and gate rejects all following renders without even advancing sequence/acoustic/voices. Rearm requires a separately proven CPU1 quiescence, owner lease and coherence.
- This is a **contract**: no implementation of real SDK V14 ownership, cache flush/invalidate, PI32 `csync`, timebase or ALNK is provided or claimed here.

## Executed evidence: complete standalone HOST bundle

Downloadable conversation artifact:
`REminiSCENT2_CPU1_2X2_OWNER_GATE_v0.4_NO_FIRMWARE.zip`
SHA256 `35869d61ed533eff5a1d742bc38c2421ea87a0dd01c3d0f4b2bd751b9d39d26e`.
It contains 66 entries including C99 musical sources v0.6, the ownership guard, previous 2+2 kernel, simulated guard tests and reproducible Clang/GCC scripts. **Only the coordination modules are in this Git branch**, not full v0.6 and tests; don't claim CI parity using this partial tree.

**Compiled and executed HOST**, using the intact original serial DSP against split 2+2:
- F16B synthetic acoustic bank (ADPCM/cache/loops) + four PARTS, 2048×128 frames, zero PCM differences, matching FNV64 `5b2ce61806994eb5`.
- Additional voice-stealing stress 2048×128 frames, 1241 stolen voices, zero PCM differences, matching FNV64 `5aaa95efcde134e2`.
- Guard test: accepted work, ownership lost, deadline missed, re-entry blocked **without changing DSP state**, late completion cannot implicitly unlock quarantine, explicit quiescence required.
- HOST sizeof(`rn_v12_dsp`) = 191,320 bytes and sizeof(`rn_dc_job`) = 64 bytes. **NOT** PI32 guest memory figures.
- ABI regressions Clang/GCC pass; warn-on-indentation messages in original v0.6 are preexisting and don't imply musical edits.

## Missing gates

1. Obtain verified Jieli PI32v2 compiler and full native v0.6 sources in same CI/local environment, then compile and execute a **non-silent real REminiSCENT** serial-vs-2+2 guest comparison.
2. Ensure **CPU1 ownership before SDK launches other services**; verified cache-line layout and coherent shared memory, bounded deadline (whole audio path), exception logging; never reuse address constants from BIOMECH.
3. Only after SDK V14 ownership and test pass, link `.fwsc` emulator-only, preserve `rn_v12_audio.c` unchanged, compare BLACK BOX/DMA output, let author evaluate actual audible checkpoint.
4. Physical FM-1 is the product goal; emulator remains a diagnostic tool.

**Version classifications**: Proposed platform handoff; implemented C99 preflight and quarantine; compiled/executed HOST; **NOT built or executed on PI32v2**, NOT integrated into SDK, NOT proven in hardware. Master and all mother FWSC untouched.
