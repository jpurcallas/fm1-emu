# REminiSCENT 2 LAB v0.5 — PI32v2 CPU1 2+2 executed musical proof

**2026-10-23 · NO MERGE / NO INSTALL / NO FWSC.** Guest PI32v2-r3 stand-alone *musical source* experiment, using intact REminiSCENT v0.6 engine functions and experimental v0.4 portable CPU1 2+2 kernel. The detailed reproducible 554-KB source, native binaries, PCM capture, script and logs are in the conversation/Library package named `REminiSCENT2_CPU1_PI32_NATIVE_2X2_v0.5_NO_FIRMWARE.zip` (SHA256 `d2169b2c4c9f62a3eabe265d4817f18bde3920070e3f6d2deea01e368396f9df`). The ZIP itself is not in the GitHub repo; these notes allow either project to discover it and understand its limitations.

## Compiler/inputs

- Recovered **original author-provided** JieLi Linux PI32v2 toolchain, Clang 4.0.1, r3; tar SHA256 `a1545cddbc451a06bac43eb5cd96d831470c42a97c5c0b1f98879a20fc7647bd`, verified via a [GitHub Actions handoff](https://github.com/jpurcallas/fm1-emu/actions/runs/40012818467). The toolchain is NOT bundled into the checkpoint ZIP.
- Compiled 17 native musical/2+2 C99 modules into ELF32 machine `0xF1`, linked two stand-alone programs under a test linker map `0x02000120` XIP entry, no SDK.
- Both programs booted in FM1 emulator at 200MHz: **serial CPU0 only**, and **dual CPU0 PARTS 1–2 / real emulated CPU1 PARTS 3–4**. Unlike host `pthread`, CPU1 itself executed `rn_dc_cpu1_part34` via a separate test startup. Its stand-alone boot is **NOT safe to transplant into V14 late initialization**.
- Synthetic, structurally valid **F16B ADPCM** bank, 69 note entries in 15 instrument groups, 38104 bytes, plus digital oscillator, effects, acoustic decoder. NOT the approved authentic recorded samples.

## Verified native PI32 guest evidence

| | Standard | Stress |
|---|---:|---:|
| Frames / 128-frame blocks | 4096 / 32 | 16384 / 128 |
| Real CPU1 jobs complete / failures | 32 / 0 | 128 / 0 |
| Acoustic decodes / loop wraps | 103 / 4 | 834 / 0 |
| Voice steals | 0 | 340 |
| Nonzero Q23 PCM (byte output) | YES | YES |
| Both paths identical PCM *byte for byte* | YES | YES |
| Captured PCM SHA256 both programs | `61cf973ba956c6b1023b9c19684d109d10b692abf8a62cafed25e8234ea52ece` | `7c4a7f7b8a5e22180ea478086ded6223ddf4ceb8783613fc6c3315a63fed4344` |
| Checksum / peak Q23 | 715404003 / 6967960 | 3800312296 / 8123935 |

Full array capture for each stand-alone guest program, comparing all 8192 and 32768 Q23 stereo words respectively using `cmp`. Test `rn_status=0x524EA11F` PASS, `rn_cpu1_done=32/128`, `rn_fails=0`, `halted=false`. Tests rebuilt from source and re-executed with exact result hashes. No original DSP functions replaced, no reduced PARTS/FX.

## Critical limits

- **EJECUTADO PI32v2 emulado**, but NOT full FM1 V14 SDK, CPU1 ownership under SDK, coherent cache, screen, MIDI transport, ALNK/ISR/DMA, hardware, or audible `.fwsc`. ISR PCM→DMA chain of protected v0.6 remains unchanged.
- `rn_v12_cpu1_guard` v0.4 compiled but not used to claim a live SDK core; this test begins with a core that the isolated app itself owns.
- The stand-alone TIMER4 counters stayed zero. Emulator iteration counts are *not* a hardware-cycle or deadline measurement, and no speed-up is claimed. BIOMECH3 recently found parallel 3+3 **slower** than serial in its different corpus [PR #26](https://github.com/jpurcallas/fm1-emu/pull/26#issuecomment-6373070838). Measure REMIN separately once timing is reliable.
- F16B bank is synthetic. All presets, automation, and actual acoustic sample authenticity require further regression.

**Next integration gate:** ownership/handoff of CPU1 **before** stock SDK claims it, SRAM/cache-line memory map, full 128-frame timing of prep→CPU0/CPU1→FX→DMA, compare exact approved v0.6 audible reference, create .fwsc emulator-only after compiling integrated SDK. Physical FM-1 is final product, emulator diagnostic tool.

Protected: original mother v3.0.23, original v0.6 and `master`. NO MERGE.