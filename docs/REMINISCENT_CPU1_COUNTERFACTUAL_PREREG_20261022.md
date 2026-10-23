# REminiSCENT FM-1 v3.0.23 — Controlled CPU1 scheduling isolation

**Reference firmware** SHA256 8409b8fec212cdeb7ac36b8a9576db74ebfe4e77d0100b59430a891260313467
**Reference emulator source** master 61b51596d5756d09902fc16cc5e0ecd550d4501e; reference WASM SHA256 7c2ae09ffc9d16db298aed2bda61e4b0c7546f8b7088332532bd604b6190f303.
**Documented public antecedent** joakimeriksson/fm1-emu docs/stock-firmware.md, section The second core, explains JIT/interpreter interleaving differences for multi-core firmwares. Not a cause identified in REminiSCENT.

## Hypothesis before change
CPU1 interleaving could alter when CPU0 consumes C4 key-up events. If CPU1 scheduling is necessary for the measured C4 ON/OFF divergence, freezing CPU1 after the normal boot may remove the 514-frame offset; if offset persists, CPU1 execution is not necessary for it within the test. Freezing core1 is a counterfactual experimental emulator change, not a performance fix.

## Only changed variable
Export fm1_diag_freeze_cpu1_after(ms): 0 keeps original run_dual; 1000 allows normal startup then suspends CPU1 execution for the remainder of an isolated emulated run. CPU0 and note script are unchanged. This modifies emulator scheduling by design; it does not edit DSP, firmware or flash.

## Identical input conditions
Node 22/Linux, WASM, 200 MHz emulated, profile OFF, script 500:C4,1400:C4^; separately C4 held (500:C4), JIT ON/OFF, independent cold boots. Exact PCM hash check against reference with the switch disabled before interpreting counterfactual.

## Acceptance and interpretation
1. With freeze=0, PCM JIT ON 05a8d7d3a3c0fa790a0f08ce7326435d61ae74a4d3817e99f0a65c2214c1e2ed and JIT OFF b18314a131e5febb5885d09db84ad0537af3145d5b41970f6e15c470e41aaa96 for the same 1660ms benchmark; if different, discard the test.
2. Freeze=1000: verify CPU1 retired instruction counter stops increasing; compare first PCM release-vs-hold response per JIT mode, and JIT ON-vs-OFF hashes / first different frame.
3. If no sustained audio, abort or defer causality; do not call CPU1 irrelevant. If divergence persists while CPU1 frozen, CPU1 does not need to be running during key-up for the difference to appear. A changed divergence alone does not prove why because freezing can change scheduling.
4. Never merge to master, install on hardware or change musical engine. Declare Chrome realtime and physical DAC untested.