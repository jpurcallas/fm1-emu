# REMINISCENT v3.0.23 — XIP 0x0200A5CE schedule/IRQ chronology

2026-10-22. Diagnostic only. NO MERGE.

Reference FWSC SHA256 8409b8fec212cdeb7ac36b8a9576db74ebfe4e77d0100b59430a891260313467.
Parent: diagnostic/reminiscent-irq11-readiness-20261022. Original v3.0.23 and master remain unchanged.

## Single hypothesis
C4 and C#4 reach identical producer store PC 0x0200A5CE in different DMA halves because scheduling/IRQ phase after common GPIO read differs with JIT ON/OFF. D4 is the control with PCM identity and same half. Need identify earliest scheduler event or return-PC difference between event acknowledgement and producer store, not assume which service routine owns the event.

## Single diagnostic
Read-only, opt-in bounded chronology of IRQ 3 (OS tick), 5, 11 (ALNK0), 127, including emulated cycle, DMA half, IRQ handler and interrupted return PC, and three RAM status bytes. Existing producer/consumer store watch unchanged. Recorder is disabled by default. No guest cycles advanced. Captures are not claims about hardware clocks or DAC consumption.

## Gates
Run 500:C4,1400:C4^ and matching C#4/D4 separately, 200 MHz, JIT ON and OFF, profile disabled, cold boot per process. Compare full 1660 ms PCM hashes to immutable references. Repeat C4 in new processes. Exact PCM is mandatory: altered PCM means discard the new trace.

Expected observation is either an IRQ/task dispatch phase difference correlated with producer execution or a result excluding this IRQ set; neither proves a particular firmware defect. No timing fix or DSP edit until causal condition is established.
