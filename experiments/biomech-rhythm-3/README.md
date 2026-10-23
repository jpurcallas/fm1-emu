# BIOMECH RHYTHM 3 — Dual Core Lab

ESTADO INICIAL 23 octubre 2026: no hay firmware BIOMECH 3 enlazado ni probado. SOLO EMULADOR, NO INSTALAR.

BIOMECH 2 reference FWSC SHA256: d99e8d61c483e9b0d770818ace669e912b7ccef81c0fd298cd84540bfbf5c3f0
BIOMECH 2 original emulator Git commit: 2d8af786a781108bcd3861376b56c1f42694d9a9
Preserved: checkpoint/biomech-rhythm-2-v02-audible-20261023
Experimental: experiment/biomech-rhythm-3-dualcore-3plus3-20261023

OBJECTIVE: render the same six musical voices, CPU0 voices 1–3 and CPU1 voices 4–6, keeping all algorithms, sequence, generative system, effects, and timbral parameters untouched. CPU0 coordinates events and mixes per-CPU separate accumulators, then processes global FX.

FIRST: recover exact C99 sources for BIOMECH 2 v0.2; do NOT silently replace them with previous BIOMECH 1 v0.35 sources. Existing experiments/biomech-rhythm-2/ contains host mailbox + blackbox + unlinked CPU1 entry code; not yet integrated in a BR2 binary.
SECOND: validate actual PI32v2 CPU1 selftest on a separate firmware build, with scheduler/cache safety and coexistence with SDK; HOST pthread tests do not establish success.
THIRD: delegate voices 4–6 with original state and preserve baseline PCM; compile an audible experimental FWSC early. No feature reduction, no changing master.
FOURTH: compare two, three and six voices on same pattern at 200 MHz, export WAV and blackbox; check worst block and DMA.

Success only if better audible results with full functionality. No BIOMECH 3 firmware yet.