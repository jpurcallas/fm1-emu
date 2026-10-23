# REminiSCENT 2 native PI32v2 2+2 — Node/WASM A/B profiling v0.5-PERF1

**Date 2026-10-23. NO FWSC / NO MERGE.** This is a separately packaged timing investigation of the *same unchanged* v0.5 native serial and CPU0/CPU1 musical PI32v2 ELF binaries: it does **not** measure the physical FM-1 chip, DMA ISR, SDK V14 nor any hardware deadline.

## Source and provenance

- Baseline musical native binaries: `REminiSCENT2_CPU1_PI32_NATIVE_2X2_v0.5_NO_FIRMWARE.zip` (musical algorithms from protected REminiSCENT 2 LAB v0.6).
- Full reproducible benchmark package: `REminiSCENT2_CPU1_PI32_AB_TIMING_v0.5p1_NO_FIRMWARE.zip`, SHA256 **`512798a07f4df3d1d41b9bd91ff37c5c8f06ff2ae0e514c2420534ecc8c0ea42`**. It includes 4 original PI32 native `.bin` + matching `.nm`, `profile.mjs`, `fm1_web.wasm`, JSON for 5 pairs, and README. The ZIP is in the author's conversation/Library, **not committed to GitHub**.
- Exact WASM `fm1_web.wasm` SHA256 `cb5542916e464a6efb96b6ab4ec043829ad50ae60fac7348ad53708513fe7f04`, from JIT LAB v0.3 `smk37`, JIT disabled via `fm1_jit(0,0)`. Emulator given 200 MHz.
- Procedure: warmup pass, alternate serial→dual and dual→serial order, validate CPU1 completion and **PCM SHA256** after every timed emulation, capture elapsed wall time of `fm1_render(128,50000)` calls until program finishes. Requested 7 measured pairs; execution time limit interrupted after **5 COMPLETE paired runs**, so only those 5 are reported (20 fully measured program runs across two scenarios), never an invented 7/7.
- Last recheck: extracted benchmark runnable from packaged folder for one new pass; all hashes and CPU1 counters passed.

## Five-run A/B medians

| Guest scenario | Serial wall time | Dual 2+2 wall time | Dual difference | `fm1_render` calls to completion (serial / dual) |
| --- | ---: | ---: | ---: | ---: |
| 32×128=4,096 frames, acoustic + digital | **467.169 ms** | **512.189 ms** | +9.64% | 379 / 283 |
| 128×128=16,384 frames, 340 voice steals | **2363.168 ms** | **2524.978 ms** | +6.85% | 2450 / 1957 |

Variability is material. A previous 3-run test gave +2.0% and +3.85%; one individual verification run even observed a faster *normal* dual trial while stress was still slower. **Do not treat percentages as precise hardware predictions or stable gains/losses.** The consistent observation across available multi-run comparisons is **no demonstrated Node/WASM wall-time speedup**.

**Audio passes:** normal PCM SHA256 serial=dual `61cf973ba956c6b1023b9c19684d109d10b692abf8a62cafed25e8234ea52ece`, 32/32 CPU1 tasks. Stress PCM SHA256 serial=dual `7c4a7f7b8a5e22180ea478086ded6223ddf4ceb8783613fc6c3315a63fed4344`, 128/128 CPU1 tasks, 340 steals. Both have nonzero PCM, no halt/timeout.

**Two clocks to keep distinct:** fewer *emulator rendering calls* to reach a completed program does not guarantee better *host wall time*; likewise neither metric measures exact firmware cycles or meets the real 128-frame DMA deadline. `TIMER4` of this standalone PI32 image had not returned usable ticks, as already documented in v0.5. JIT performance is not the musical target.

## BIOMECH comparison and next gate

BIOMECH 3 reported an analogous negative wall-time result in an **independent different musical corpus** — 72 ms serial vs 89 ms 3+3 for 4,096 frames ([PR #26](https://github.com/jpurcallas/fm1-emu/pull/26#issuecomment-6373070838)); 8/16/64/128 batch changes failed to beat serial. This was reviewed **before** profiling REMIN. The results do NOT imply identical performance bottlenecks or architectures. Neither project should simplify DSP nor force smaller/more frequent jobs based on speculation.

Next: instrument and separate **CPU0 preparation**, mailbox publication, CPU0 PARTS 1–2, CPU1 PARTS 3–4, **CPU0 waiting/polling**, common FX/mix and **actual ISR/DMA copy deadline**, using reliable per-core timing/counters. Then gate safe SDK V14 CPU1 ownership/coherency and deliver a full musical `.fwsc` for emulator-only auditory review. No SDK ownership, audio DMA, bank recording authenticity or physical hardware is validated by this package.

Mother v3.0.23, REminiSCENT 2 v0.6 and `master` unchanged. NO MERGE.
