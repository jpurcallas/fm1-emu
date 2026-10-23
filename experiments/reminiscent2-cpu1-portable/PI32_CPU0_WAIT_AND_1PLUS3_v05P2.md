# REminiSCENT 2 — PI32v2 CPU0 polling diagnostic, 2+2 vs 1+3 (v0.5-PERF2)

**23 Oct 2026 · Experimental native lab; no FWSC, no SDK/ISR/DMA, no physical FM-1, NO MERGE.**

## Critical updated cross-project information

The newer [BIOMECH3 PR #26 discovery](https://github.com/jpurcallas/fm1-emu/pull/26#issuecomment-6373563978) **supersedes only its previous expectation that its 3+3 was necessarily slower**. With an ordered active-slot index in its 64 global voice slots, BIOMECH improved guest serial/dual wall time from 72/89 ms to **72/64 ms** in its 4096-frame corpus; under voice-stealing stress 427/403 ms; same musical checksum/peak, full six tracks, 128 CPU1 tasks. Still no SDK/ DMA/ physical confirmation.

**Important REminiSCENT difference:** before importing this result, original REminiSCENT v0.5 kernel was inspected. Its **12-slot active snapshot is already implemented** in `rn_dc_prepare()` and `rn_osc_render_selected()`; only active indices of the selected PART are rendered in original slot order. Do NOT duplicate that optimization or claim BIOMECH's gain automatically transfers.

## New v0.5-PERF2 test

- Starting point: native REminiSCENT 2 v0.5, C99 original music DSP unchanged; isolated 2+2 CPU1 laborarory and synthetic F16B ADPCM bank, PI32v2 r3 under WASM 200MHz.
- Added **test-driver-only** volatile counters: `rn_wait_spins_sum`, `rn_wait_spins_max`, `rn_wait_blocks`, recording CPU0 busy-poll iterations after completing its own PART work and before receiving CPU1 completion.
- Tested **an alternative allocation only inside the native lab**: CPU0 PART 1 / CPU1 PARTS 2–4 (1+3) with exact same sound functions, loops, ADPCM, FX, sends, mixing and ordered snapshot. The 2+2 approved experiment **remains default**; 1+3 is NOT adopted.
- Source + test scripts, native ELF/BIN, PCM captures and logs in checkpoint `REminiSCENT2_CPU1_PI32_CPU0_WAIT_PROBE_v0.5p2_NO_FIRMWARE.zip` SHA256 `ea92dcdde35548799e577484d729a0b47347a2b40691119d3c94e668b83122cf` (conversation file; ZIP **not** on GitHub). Build/test from source rerun and all checks passed.

| Native guest workload | Allocation | CPU1 jobs done | CPU0 poll iterations sum | Max in one block | Simulator calls to completion | PCM |
|---|---|---:|---:|---:|---:|---|
| Normal 4096 frames | **2+2** | 32/32 | **0** | **0** | 282 | Exact serial |
| Normal 4096 frames | **1+3 lab** | 32/32 | 742,818 | 28,289 | 320 | Exact serial |
| Stress 16384 frames/340 steals | **2+2** | 128/128 | **90,104** | 15,037 | 1956 | Exact serial |
| Stress 16384 frames/340 steals | **1+3 lab** | 128/128 | 3,411,093 | 47,616 | 1966 | Exact serial |

All four simulated native runs ended `PASS`, nonzero sound, **0 job failures / no emulator halts**, serial/2+2/1+3 **byte-identical Q23 PCM**:
- Normal SHA256 `61cf973ba956c6b1023b9c19684d109d10b692abf8a62cafed25e8234ea52ece`, 103 F16B decodes / 4 loops.
- Stress SHA256 `7c4a7f7b8a5e22180ea478086ded6223ddf4ceb8783613fc6c3315a63fed4344`, 834 F16B decodes / **340 stolen voices**.

**Interpretation:** CPU1 is already finished before CPU0 enters its wait loop for all 32 normal blocks with 2+2. Moving an additional PART to CPU1 creates **substantial CPU0 polling**, with more emulator calls and no sonic advantage. This supports keeping 2+2 as current reference, *not* a definitive physical timing verdict. The guest TIMER4 produced zeros; poll iterations are **neither cycles nor milliseconds**, and simulator call counts are not CPU deadlines.

Further testing should identify the CPU0 critical path (**ADPCM preparation / PARTS 1–2 / shared sends FX and mixing**) and the true hardware sample/deadline budget; do not optimize the emulator at the expense of musical behavior. More balanced alternative schedules require the same audible+PCM gates before adoption.

**Still missing:** CPU1 owner handoff when SDK V14 may already own it; shared SRAM-cache coherence, full V14 ELF packing, ISR/ALNK/DMA, physical FM1 and a playable experimental `.fwsc`. Originals v3.0.23 / v0.6 / `master` untouched. NO MERGE.
