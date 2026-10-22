# REMINISCENT v3.0.23 — IRQ11 readiness experiment (2026-10-22)

Reference firmware SHA256: 8409b8fec212cdeb7ac36b8a9576db74ebfe4e77d0100b59430a891260313467.
Original emulator source: diagnostic/reminiscent-keyup-exact-store-20261022; profile OFF, separate Node processes, 200 MHz.

Question: Why is the same exact guest store (PC 0x01C00E9E, RAM 0x01C1993F) performed in different IRQ11 half events for C4 / C#4? It is 179 emulated cycles after IRQ11 entry in both modes.

Single diagnostic change: snapshots of four guest RAM windows at IRQ11 entry, plus a bounded watch on candidate store bytes previously found by comparison of release-vs-hold guest RAM. Opt-in only. No guest-time advance or RAM write. No assumed musical semantics for candidate fields.

Predictions: a candidate readiness condition may distinguish the IRQ11 entry that consumes key-up from earlier IRQ entries. If no difference, identify additional input/queue state; do not alter scheduling based on a guess.

STRICT PCM control for 500:C4,1400:C4^: JIT ON 05a8d7d3a3c0fa790a0f08ce7326435d61ae74a4d3817e99f0a65c2214c1e2ed; JIT OFF b18314a131e5febb5885d09db84ad0537af3145d5b41970f6e15c470e41aaa96.
Hold control ON/OFF: 8577355a65060b9edadeb2fe9dcbd49c2c3aea608fa567351f7e9cefec48b81f.

Acceptance: six independent C4/C#4/D4 release runs plus C4 replication, PCM exact for each against original per-mode baselines, note every IRQ11 half and first exact store. Do not merge master; do not generate firmware, change DSP or claim real-time success.