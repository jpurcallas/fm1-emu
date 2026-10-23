# REminiSCENT 2 LAB v0.12 — MIDI/FX 2+2 sin rechazos DMA en corpus emulado

**23/oct/2026 — SOLO EMULADOR — NO INSTALAR — NO MERGE.** Este informe se basa en dos FWSC REminiSCENT V14 realmente ejecutados con 24 mensajes MIDI, no solamente pruebas HOST. El SDK original v14 y `master` no fueron editados.

## Consultas cruzadas GitHub antes y después de trabajar

- [REminiSCENT v0.11 PR #24](https://github.com/jpurcallas/fm1-emu/pull/24#issuecomment-6375541768): 152 rechazos DMA cooperativos entre 950 solicitudes bajo MIDI; sin MIDI, 0.
- [BIOMECH hallazgo nuevo de heap](https://github.com/jpurcallas/fm1-emu/pull/26#issuecomment-6375682987): el V14 *stock*, con heap reducido artificialmente a ~52–62KiB, pierde callbacks y audio aunque enlaza; con ~247KiB funciona. **No confundir umbral mínimo de linker con servicio funcional.** El ELF REminiSCENT v0.12 enlaza `_MALLOC_SIZE=0x16f8c` = **94.092 bytes**, y ejecutó 24 MIDI completos en este corpus, PERO ello NO certifica los demás servicios ni un mínimo universal.

## Medición por fase antes de optimizar (912 trabajos PI32v2)

Variante de profiler instrumentada sin alterar el DSP musical:
- `rn_dc_prepare`: ~4.702 ticks medios.
- `rn_dc_render_range` CPU0 PARTS 1–2: ~171.715 ticks medios, max 251.382.
- CPU0 `wait_done`: ~20 ticks medios.
- `rn_dc_finalize` (mezcla y cuatro FX globales): **~231.852 ticks medios**, principal coste constante.
- Ticks del guest no son tiempo real físico: no extrapolar cifras a FM1 real.

## Corrección metodológica imprescindible

Un **candidato temporal INVALIDO** de este laboratorio deshabilitó por error `fm1_output_mix(rendered)` al apagar la huella PCM y pasó de 152 a 5 rechazos. **Ese resultado se descarta totalmente**: no era equivalente al firmware real. Se corrigió para que el mezclador se ejecute incondicionalmente. Control corregido *solo quitando huella FNV por bloque*: **152 rechazos**, como v0.11. Control con solo simplificación de módulo y huella FNV completa: **152 rechazos**. No atribuir mejoras falsas a un DSP incompleto.

## Modificaciones genuinas y exactas

1. `rn_sends.c`: en posiciones reverb/allpass, modulo de cabezas circulares con longitud fija se sustituye por comparación/resta exacta manteniendo el invariante desde cero; cuatro expresiones y buffers originales.
2. `rn_sends_render` y `rn_dc_finalize`: acumuladores `int64_t`→`int32_t` **solo al sumar cuatro entradas Q23 limitadas a ±8.388.608**; la suma máxima en módulo es 33.554.432, muy inferior a 2.147.483.647. Cada producto, división y redondeo conserva su aritmética entera original de 64 bits.
3. Huella FNV32 post-`fm1_output_mix` muestreada **cada 16 bloques** en la ventana 176 de diagnóstico, manteniendo los contadores R2TB por **cada bloque**. No desactivar el mezclador nunca.
4. Resto C99 (cuatro PARTS, Acoustic Memory, secuenciador, DSP, envíos, efectos y secuencia, MIDI, DMA) y mecanismo cooperativo de v0.11 conservados. **El injerto SDK sigue siendo NO SOPORTADO; no es lease certificado.**

## Resultados PI32v2 200MHz JIT OFF, 950 llamadas/24 MIDI

| Métrica | v0.11 cooperativo | v0.12 cooperativo |
| --- | ---: | ---: |
| Renders | 912 | 912 |
| DMA correcto | 760 | **912** |
| Rechazos por plazo DMA | 152 | **0** |
| Rechazos por propiedad DMA | 0 | **0** |
| Trabajos CPU1 completos al final | 912 | 912 |
| MIDI RX / MIDI aplicado | 24 / 24 | 24 / 24 |
| Halt | no | no |
| Pico total IRQ, ticks guest | 501.362 | ~488.308 |

**Regresión sin MIDI** (420 solicitudes): 382 renders, 382 DMA, 0 rechazos, 382 trabajos CPU1 completados. No se desactivaron globales ni se usó bypass musical.

**Prueba de matemática exacta HOST GCC+Clang**: 150.000 muestras estéreo por implementación de FX, cuatro PARTS, cuatro buses, cinco modos de modulación, 57 cambios de parámetros; PCM y estado FX idénticos cada chequeo. FNV64 `c54d9ad7949db740`.

**Huella post-mezcla con MIDI**: v0.12 arranca dos quanta antes que v0.11 en estos ELF distintos. Con los MIDI de la prueba enviados deliberadamente dos quanta después para alinear *tiempo musical*, las 10/10 huellas post-mix de la ventana comparable coinciden (bloques 15–159 en la referencia; 17–161 nuevo). La primera muestra no es comparable por arranque. Esto **NO demuestra equivalencia de WAV completos con los mismos timestamps de host**. En secuencia automática sin MIDI se compararon 40.000 frames stereo Float32 **bit idénticos**, alineando 256 frames al principio.

## Entregables / integridad

- FWSC `REminiSCENT2_v0.12_MIDI_AB_COOP_SOLO_EMULADOR_NO_INSTALAR.fwsc` SHA256 `b1c6336e7f55b648bff08f56dd09af4ab74496b0dd01cb1d8d327ca9779d59ba`.
- HTML diferido `REminiSCENT2_v0.12_REPRODUCTOR_DIFERIDO_SOLO_EMULADOR.html` SHA256 `ea0189e154223c2bde90e58831c85061e89736b9759ef2fe0f27cdbd6b04ac4f`. Test Node/WASM sí generó 176.512 frames/4s WAV no nulo; **aún no confirmado por oído del autor**.
- ZIP completo conversación `REminiSCENT2_v0.12_CPU1_DMA_CERO_RECHAZOS_SOLO_EMULADOR_NO_INSTALAR.zip`, SHA256 `40248801f3ab176914c40ac5cae4b7973984ee1468fc81a05fd5167a6acf2a93`; 77 archivos y comprobación de hashes internos PASS. El ZIP NO se subió a este repositorio, solo documentado. Contiene FWSC, HTML, código C99, mapas, scripts, pruebas, JSON, WAV y patch.
- Esta rama publica por separado el **diff C99 exacto** con respecto al motor y laboratorios v0.11, para permitir auditoría cruzada sin acarrear el SDK ni tocar originales.

## Restricciones no resueltas

- El worker del SDK original se llama antes que PARTS 3–4 mediante un **injerto binario postlink de seis bytes** en una COPIA del SDK V14. No es interfaz oficial; falta comprobar operaciones reales flash, BT, USB, caché, fallos y quiescencia. **JAMÁS instalar en FM-1 físico**.
- Un corpus de 950 solicitudes con cero rechazos **no** demuestra que todos presets, bancos acústicos grabados, máxima polifonía, control físico, BT, USB, ni deadline de hardware cumplan. El AudioWorklet en vivo puede continuar saturado; escuchar WAV diferido no verifica tiempo real.
- Futuras pruebas: saturación musical y servicios V14 bajo carga sin perder PCM/DMA, obtener integración CPU1 compatible y posterior ensayo físico. No recortar funcionalidad por optimizar el emulador.

Versiones madre v3.0.23, v0.6, v0.7/v0.8 y `master` intactos. **DISCUSIÓN LIBRE, EJECUCIÓN FIEL.**