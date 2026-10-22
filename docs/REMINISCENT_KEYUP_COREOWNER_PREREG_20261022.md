# REMINISCENT v3.0.23 — CPU owner of the first key-up voice-state transition

2026-10-22 · PR diagnostic only · NO MERGE

## Immutable references
Firmware SHA256 `8409b8fec212cdeb7ac36b8a9576db74ebfe4e77d0100b59430a891260313467`. Source branch derives from `diagnostic/reminiscent-keyup-voicewatch-20261022`, not master.

## Question (before experiment)
At 200 MHz, `500:C4,1400:C4^` triggers key-state RAM update at cycle 280126569 in both JIT modalities, while note register `0x01c1993f` is first observed changed at cycles 295486534 (ON) vs 293166534 (OFF). Which core's execution slice contains the first change? Is it associated with different scheduler/IRQ phases?

## Single change
At existing CPU0/CPU1 scheduler slice boundaries, compare three already-observed RAM bytes only during the 1380–1540 ms window, recording core id, PC at END OF SLICE (not actual store PC), emulated cycle, DMA half number, IRQ depth. Diagnostic opt-in, no firmware modification and no JIT code emission change.

## Acceptance / disproof
- JIT ON and OFF PCM hash for 1660 ms must match their respective original reference results exactly.
- First transition to `voice=1` is logged once with stageCore 0 or 1, and precedes the first PCM difference.
- Re-run the same case in an independent process for reproducibility.
- If PCM changes, discard trace and do not conclude which core writes.
- Report core ownership cautiously: an observation after a slice is not an instruction-level write trace.

No alteration to DSP, firmware, keyboard algorithm, audio timing, or master.
