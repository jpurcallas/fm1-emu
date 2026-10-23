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

## Primer resultado real de CPU1 (2026-10-23)
**PASS, emulador PI32v2, prueba aislada SIN síntesis musical.** Fuentes propias en `native-cpu1/` y artefactos de compilación en `native-cpu1/artifacts/`.

- Compilación, enlace y ELF PI32v2 reales con herramienta JieLi y XIP en `0x02000120`; binario 648 bytes.
- CPU0 ejerció directamente los registros de arranque de CPU1, sin despachador musical del SDK.
- El CPU1 emulado ejecutó su propio `br3_cpu1_main`, leyó una solicitud firmada de la RAM compartida, ejecutó 64 iteraciones y respondió.
- Evidencia de ejecución del huésped: `br3_status=0xB3300003`; trazas `CPU0=0xC0000003`, `CPU1=0xC1000002`; resultado esperado=observado=`0x8AA2F20D`; `halted=false`.
- Evidencia CI: https://github.com/jpurcallas/fm1-emu/actions/runs/39986469523
- **No es FWSC musical ni prueba 3+3 ni validación de hardware físico.** Tampoco prueba coherencia de caché bajo carga ni disponibilidad de CPU1 dentro del SDK original. Los resultados de CPU1 no autorizan reemplazar el motor de BIOMECH 2.
- Siguiente implementación: preservar y recuperar el código C99 exacto del DSP de v0.2 y montar la entrada CPU1 propia en un FWSC experimental separado; primero trabajo sin DSP, luego transferencia de voces con igualdad funcional y audio comparado.


## Segundo resultado: DSP musical nativo 3+3 vs serial en PI32v2 (23/oct/2026)

**EJECUTADO Y COMPILADO:** [GitHub Actions](https://github.com/jpurcallas/fm1-emu/actions/runs/39998936634) valida el mismo motor musical C99 de seis pistas, con la versión original serial y la versión repartida CPU0 (pistas 1–3) / CPU1 (4–6), ambas realmente compiladas como PI32v2 y ejecutadas bajo el emulador a 200 MHz. Se contrastaron 32 bloques × 128 frames = **4096 frames**, sin ISR de DAC.

- Referencia serial: `br3_test_checksum=4134146915`, pico float32 bits `1063004406`, `br3_test_rendered=32`, sin halt.
- Reparto 3+3: **mismo checksum y pico**, `br3_completed_jobs=128`, `br3_timeouts=0`, `br3_fallback_jobs=0`, sin halt. BLACK BOX `BR3BBX01` visible en SRAM.
- La comparación HOST anterior fue byte a byte para tres escenarios con secuenciador, MIDI, robos de voz y fallback. La nueva comparación PI32v2 valida **hash + pico**, no byte a byte de muestras volcadas; no extrapolar más allá del corpus probado.
- **Limitaciones vigentes:** ejecutable PI32v2 independiente: todavía no es FWSC con panel, audio ISR, DMA, servicios SDK ni una demostración de rendimiento en hardware. Tampoco verifica igualdad con el firmware audible BIOMECH 2 v0.2, cuyas fuentes precisas siguen sin estar disponibles.
- No solicitar al autor ninguna prueba de este binario aislado. Próxima implementación: integrar la misma ruta 3+3 en la aplicación FM-1 completa con secuenciador/UI/FX, entrega DMA y BLACK BOX, compilar, probar internamente y solo entonces generar un .fwsc SOLO EMULADOR.
