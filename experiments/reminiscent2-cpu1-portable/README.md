# REminiSCENT 2 LAB — núcleo DSP portable 2+2 v0.3

**ESTADO: SOLO FUENTES DE LABORATORIO, NO INSTALAR / NO MERGE.**
**Fecha:** 23 de octubre de 2026.
**NO es firmware FM-1, NO es un .fwsc y NO se ha ejecutado aún en PI32v2.**

## Propósito

Preparar la misma función DSP de REminiSCENT 2 LAB v0.6 para calcular PARTS 1–2 en CPU0 y PARTS 3–4 en CPU1, preservando la señal musical. Hardware FM-1 físico es la meta; emulador y ensayos HOST son instrumentos de diagnóstico.

Este directorio guarda cuatro fuentes C99 **byte a byte idénticas a la versión empaquetada v0.3**:

- `rn_v12_dualcore_kernel.c/h`: prepara (secuenciador, banco acústico, snapshot global de voces), procesa intervalos independientes por PART y finaliza (mezcla/FX global).
- `rn_v12_dualcore_dispatch.c/h`: contrato `submit`/`wait_done`; no accede a registros del SDK ni decide la propiedad de CPU1; retorna sin mezclado final en fallo de submit o espera.
- Requiere además las **fuentes originales completas del proyecto v0.6**, en especial `rn_v12_dsp.h`, `rn_osc_render_selected` (función añadida, algoritmo de voz original intacto), los módulos DSP y el banco acústico.
- **NO** copiar el arranque o las direcciones de BIOMECH 3. Comprobar primero coexistencia y ownership de CPU1 con SDK V14, stacks, linker, `csync`, coherencia de caché, ISR/ALNK/DMA y plazos.

## Prueba de referencia ejecutada en HOST

ZIP completo con copia de fuentes v0.6, harness, generador F16B sintético y scripts en la entrega original:
`REminiSCENT2_CPU1_2X2_PORTABLE_CORE_v0.3_NO_FIRMWARE.zip`.

SHA256 ZIP: `e05a68a75c0f63b2c6fd329a59699f29663fc26928ed04fe7bc540f173961ce3`.

Con Clang y GCC bajo Linux, mismos samples Q23 serial vs 2+2 (`memcmp` de 2048 bloques de 128):
- Acústico (banco **sintético** válido F16B de 69 entradas/15 instrumentos) + digital, 262144 frames: hash FNV64 `5b2ce61806994eb5`, 12640 decodificaciones y 1657 vueltas de loop.
- Estrés adicional de 1241 robos de voz, 262144 frames: FNV64 `5aaa95efcde134e2`, 17019 decodificaciones.
- Se comparó el estado acústico *por campos* porque `f16b_note` puede contener bytes de padding indeterminados que no son estado sonoro.
- Pruebas del contrato: submit no aceptado = -3; espera fallida = -4; nunca finaliza mezcla tras fallo. **No prueba recuperación de CPU1 todavía en ejecución.**

**Límites:** esas pruebas HOST no acreditan memoria/cache de PI32v2, integración SDK, velocidad en hardware, banco acústico con grabaciones originales ni firmware audible.

## Próximo trabajo

1. Compilar y enlazar las fuentes originales v0.6 + núcleo portable en PI32v2 **en rama propia**. Comparar PCM serial/no nulo.
2. Integrar con un dispatcher de CPU1 cuyo arranque/ownership se haya verificado en la aplicación y registrar CPU0/CPU1, tarea, cola, IRQ y audio por bloque (BLACK BOX).
3. Sin tocar la cadena PCM → DMA de v0.6, entregar `.fwsc` **SOLO EMULADOR** únicamente cuando compile y produzca un checkpoint musical verificable, no un stub.
4. Medir disponibilidad real de CPU1, deadline, coste entero del bloque y finalmente FM-1 físico.

**Historial compartido:** [PR #24](https://github.com/jpurcallas/fm1-emu/pull/24) / [PR #26](https://github.com/jpurcallas/fm1-emu/pull/26).

Protegidos: `master`, firmware original v0.6 y madre v3.0.23. Ninguno fue editado para esta prueba.
