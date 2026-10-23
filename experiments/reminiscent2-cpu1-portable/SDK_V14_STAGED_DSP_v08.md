# REminiSCENT 2 LAB v0.8 — primera ejecución V14 de fases DSP 2+2

**23-oct-2026. NO MERGE, SOLO EMULADOR, NO INSTALAR.** Objetivo: avanzar del dsp 2+2 standalone a aplicación FM1 Open SDK V14 en uso real sin reclamar el CPU1 del SDK sin verificar su cesión.

## GitHub consultado antes

- PR #26: [BIOMECH3 V14 stock+DSP+CPU1 enlazados](https://github.com/jpurcallas/fm1-emu/pull/26#issuecomment-6374157238), más reciente rama `experiment/biomech-rhythm-3-dualcore-3plus3-20261023` commit `c97868ad4348966231ff54bbe258738b78bfe63e`: construye candidato completo V14 con el módulo `br3_cpu1_no_owner.c`. **Ninguna cesión de CPU1 demostrada**. El método fail-closed se mantiene.
- PR #24: el autor **oyó** el WAV de v0.7 renderizado en Chrome con HTML diferido; por tanto ahora hay una vía de escucha válida, sin fingir tiempo real.
- IMPORTANTE: las BLACK BOX **reales** del autor a 100/200 MHz mostraron CPU1 PC `0x01C0C4D4` y conteos de instrucciones 4.396.912 y 8.658.912. El mapa exacto del SDK v0.7 coloca ese PC **dentro del código opaco de SDK** `fm1_r_e7d3da61dac2` (`0x01C0C4B4`–`0x01C0C53E`), miembro `libfm1_engine.a(engine_startup.S.o)`. Es evidencia de ejecución de SDK en CPU1 en ambos instantes; no una concesión para reinicio ni un API de handoff.

## Cambio implementado en V14 musical real

La compilación parte de copia independiente v0.7, con idénticos originales y en formato de aplicación V14:
- ISR de audio / entrega DMA siguen idénticas a v0.7.
- Se retiene el módulo DSP aprobado con **cuatro PARTS, osciladores/acoustic memory, secuenciador, FX y mezcla** sin sustitución.
- Cambia **solo la ruta serial** en `rn_v12_native.c`: en lugar de `rn_v12_dsp_render`, llama `rn_dc_prepare`, después `rn_dc_render_range(job,0,2)`, `rn_dc_render_range(job,2,4)`, y `rn_dc_finalize` **todavía todo desde CPU0**. La ruta del guard no se habilita ni se miente sobre CPU1.
- Se conserva fail-closed de propiedad `rn_cpu1_lease_confirmed=0` y sondas R2TB CPU1. No reset, no hold, ni parches a binario opaco.

## Compilado/enlazado/empaquetado/EJECUTADO

- Compiler JieLi Clang 4.0.1 PI32v2 r3, SDK FM1 Open V14 oficial preservado; ELF `e_machine=0xF1`.
- Aplicación nueva: **429.776 bytes**, margen enlace 24.145 bytes, RAM estática enlazada 425.736 B, FWSC 1.069.620 bytes. Los bytes de bootloader/particiones originales de v0.6 permanecen y se recalculan CRC.
- [FWSC SHA256] `84aaec7dee3d199a9cc44f21d67d562687d0797f987cb011adbde1e58e081028`: `REminiSCENT2_v0.8_STAGED_2X2_CPU0_SOLO_EMULADOR.fwsc`.
- **Ejecución PI32v2 emulada 200MHz, PLAY 420 quanta:** 382 renders, 355 con PCM; 382 DMA copies, 355 con señal; **0 rechazos** por plazo/propiedad DMA; halted false.
- **393.216 bytes PCM stereo Float32 byte-exactos** contra FWSC v0.7, SHA256 en ambos `a838d5f7c0bf1a270469bc923ebff76610ed14f02eb58e35d39a0379727fc285`. No se trata solo de comparar hash, byte a byte `cmp`.
- v0.7 pico render 433.697 ticks; v0.8 pico render 434.635 ticks contra deadline 487.420 ticks. Corpus reducido; NO extrapolar a estrés/hardware.
- Reproductor diferido autónomo con **v0.8 embebido** generado y ejecutado en harness Node/WASM: 176.512 frames en 4 s, pico 0,2714, 168.382 frames no nulos, WAV válido. **Todavía no confirmado el audio en Chrome del autor con esta variante**.
- CPU1 blackbox: `lease_verified=0`, `dual_jobs=0`, `CON=8`, `CLK=0`, `ENTRY=0x02000224`. **No hubo cálculo 2+2 entre dos núcleos** y no debe declararse.

## Prueba y entrega

Paquete de conversación/Library `REminiSCENT2_v0.8_V14_STAGED_2X2_Y_REPRODUCTOR_SOLO_EMULADOR.zip`, SHA256 `8d37e3bc3bb0748edaa5ffbb3ab0e9fb918b1eae56e883da34f84a7e556f053f`; contiene .fwsc, HTML autónomo para escuchar, diff mínimo v0.7→v0.8, fuentes C99 de integración, map, ELF, PCM y JSON, instrucciones. No distribuir binarios por GitHub sin decisión autoral; no confundir archivo de evidencia con firmware instalable.

**Próxima etapa:** identificar mecanismo temprano **aceptado por SDK** para que el núcleo asignado pueda ejecutar `rn_dc_cpu1_part34` sin interferir sus servicios. Únicamente al verificar cesión, barreras/caché, timeout/quiescencia se sustituye el segundo `render_range` CPU0 por `submit/wait_done` en CPU1, medir PCM exacto, tiempo ISR→DMA y BLACK BOX, luego hacer revisión auditiva.

Originales v0.6, v0.7, v3.0.23 y `master` intactos. Hardware FM-1 es meta; el emulador no es la meta.
