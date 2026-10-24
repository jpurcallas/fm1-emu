# REminiSCENT 2 v0.14 UX03 — primera navegación Yeti Fingers en C99/SDK V14

**Fecha:** 23/oct/2026 · **SOLO EMULADOR** · **NO INSTALAR en el FM-1 físico** · **NO MERGE**.

## Qué contiene

- **Firmware .fwsc completo para cargar en FM1-LIVE-LAB de macOS**, derivado de v0.13 (que el autor escuchó correctamente en el Mac M4 Pro). Motor 4 PARTS, MIDI, secuenciador, CPU1 2+2, FX y splash 240×240 aprobado conservados.
- **Cambio REAL de la UI nativa** en C99: página y sección separadas; ALGORITHM mueve exclusivamente los submenús de la sección; PRESET carga temporalmente una ranura para la PART activa; SELECT cambia PART; MASTER queda bajo el control de volumen del SDK, sin reutilizarlo para navegación; los cuatro knobs controlan parámetros de la pantalla. Panel con base **amarillo pastel #FFF1BB**, colores de acento PROVISIONALES.
- **Mapa permanente 2×6** al pie de LCD, basado en BIOMECH RHYTHM v0.9.8, con la casilla relevante resaltada. Ocupa 30 px de altura en la pantalla real de 240×240.
- **ADSR gráfico**, secuenciador 4 TRACKS x 16 pasos x 4 páginas y **mixer gráfico de cuatro PARTS** mostrando acústico y digital por separado; la pantalla de performance da acceso real a MULTI/UNISON, tempo, PLAY y REC.

## Abrir y probar

1. Cerrá el FM1-LIVE-LAB anterior; abrí `ABRIR_FIRMWARE.command` desde tu instalación en Mac.
2. Elegí `REminiSCENT2_v0.14_UX03_NAVEGACION_YETI_FINGERS_SOLO_EMULADOR_NO_INSTALAR.fwsc`.
3. Corré a 200 MHz y dejá terminar el splash de cinco segundos.
4. Usá **el mouse sobre el panel** si el teclado español no coincide con atajos del emulador. El atajo REC del sintetizador no graba WAV del host.
5. Probá una nota musical en SOUND, editá la envolvente, seleccioná otra PART, cambiá presets de prueba, regresá a la PART anterior y escuchá el cambio. En la pantalla MIDI/SEQ probá cuatro pistas.
6. Cerrá FM1-LIVE-LAB normalmente para obtener BLACK BOX automática y compartila si hay fallos. La salida audible aún debe evaluarse en v0.14 por el autor: **no confundir compilación con escuchar**.

## Controles y shortcuts físicos

| Control físico FM-1 | Función implementada |
|---|---|
| MASTER | Volumen global existente del SDK, sin modificación |
| SELECT | PART activa 1–4 (siempre) |
| PRESETS | Ranura RAM 1–4 de esa PART (siempre), **no** cambia página |
| ALGORITHM | Submenú anterior/siguiente de la sección activa (siempre) |
| KNOB 1–4 | Cuatro parámetros de la pantalla, con etiquetas y valores |
| EDIT | SOUND / SOURCE |
| ENV | SOUND / ENVELOPE gráfico |
| LFO | MIX/FX / MOD A (**bus global existente**, no LFO por PART inventado; ALGORITHM avanza a MOD B) |
| SEL/SCL | MIXER gráfico de cuatro PARTS |
| FX | MIX/FX / SEND LEVELS (ALGORITHM recorre MOD A/B, DELAY y REVERB) |
| GLO | PERFORMANCE / ROUTING (cuatro casillas de LAYER) |
| HOME | PERFORMANCE / HOME (modo, tempo, PLAY, REC) |
| SEQ | SEQUENCER / STEPS (4×16 gráfico; OCT +/- cambia bloques de 16) |
| PLAY/STOP | Secuenciador real del motor |
| REC | Live REC del motor; NO es grabación WAV de FM1-LIVE-LAB |
| SAVE | Guarda la configuración actual de la PART a la ranura **solo RAM** |
| ARP | Sin asignar: no se inventa arpegiador |

### Pantallas de edición que ya modifican DSP C99

- SOUND: SOURCE, OSC, OSC EXTRA, ENVELOPE, MEMORY MAIN, MEMORY MOTION, RESONANCE, LOW PASS, GRANULAR, CHARACTER, SEND LEVELS.
- PERFORMANCE: ROUTING (capas PART1–4) y HOME (K1 MULTI/UNISON, K2 tempo, K3 PLAY, K4 REC).
- MIX/FX: MIXER (K1 nivel acústico, K2 nivel digital, K3 encendido de PART, K4 **MUTE DEL TRACK**), SEND LEVELS, MOD A, MOD B, DELAY, REVERB. El mixer no es todavía un mezclador post-DSP con SOLO por PART; no presentar TRACK MUTE como silencio total.
- SEQUENCER: STEPS (K1 paso, K2 nota, K3 velocidad, K4 página), TRACK CONTROL (K1 longitud, K2 mute, K3 solo, K4 activar), LIVE REC, MOTION TARGET y MOTION PART. Cuatro TRACKS visibles, página 1–4 de dieciséis pasos, pulsación de teclado blanco en STEPS conmuta un paso.

### Presets: alcance exacto

- La UI ofrece **4 ranuras de ensayo por PART (16 memorias RAM efímeras)** para verificar `PRESETS`, `SAVE` y el cambio audible entre timbres. Los slots 2–4 inicialmente varían el BLEND del oscilador; **NO son bancos artísticos o definitivos**.
- `SAVE` copia parámetros por PART a RAM; se pierden al cerrar/reiniciar emulador. No hay escritura flash. PRESETS/LOAD emite mensajes al audio owner mediante la cola oficial del proyecto para reaplicar parámetros a la PART seleccionada.
- **Pendiente:** preset guardado permanente, bancos de fábrica/usuario, full mixer con SOLO de PART, LFOs independientes de las cuatro PARTS según laboratorio original, completar correspondencias gráficas aprobadas y seleccionar definitiva paleta secundaria. No se han eliminado funciones originales; la navegación no equivale a concluirlas.

## Integridad y resultados de desarrollo

- Recompilado y enlazado con **JieLi PI32v2 Clang R3, SDK Open V14**. `fm1_app_midi_received` continúa enlazado a implementación propia fuerte.
- **Aplicación v0.13 427.920 B → v0.14 UX03 429.776 B (+1.856 B)**; registro de app.bin V14 reservado: **430.352 B**, quedan **576 B**. RAM estática del enlace **428.424 B → 429.960 B (+1.536 B)**. Son cifras de enlace, no medidas de carga real del FM-1 físico.
- Las partes externas a app.bin y a registros CRC/cabecera del paquete `.fwsc` son **byte a byte idénticas** a v0.13 (verificador de Python PASS). Misma longitud 1.069.620 B. No se movieron particiones, cfg_tool.bin ni parámetros del fabricante.
- En comparación A/B con v0.13, **22/24 objetos PI32v2 del proyecto compilados resultaron byte idénticos**; cambian `app_screen.c.obj` y `rn_hw_commands.obj` (este último por nueva constante en `rn_hw_commands.h`; código de comandos de DSP no se editó). Mismo módulo `rn_splash.c`.
- Prueba separada en **C99 HOST con AddressSanitizer y UndefinedBehaviorSanitizer**: 1200 acciones aleatorias; check de ENV, PRESETS, SELECT, ALGORITHM, botón LFO, MIXER y parámetro acústico/digital, SEQ/OCT, HOME y MULTI/UNISON, 0 accesos fuera de rango. Capturas de 240×240 generadas desde **el renderizador nativo C99 bajo mocks**, NO del emulador PI32v2.
- **PENDIENTE** prueba en FM1-LIVE-LAB del autor: pantallas con los botones reales, procesamiento PCM, BLACK BOX, playback continuo, MIDI, latencia de interfaz y test físico FM-1. Ni la prueba HOST ni el enlazador demuestran esto.
- SHA-256 del FWSC: `200c2fdc7b862d6cfffff904ef0621daab2970a8f00f9d4e6ce3ff388a3d6efe`.

## Reproducibilidad

- `src/rn_hw_screen.c`, `src/rn_hw_commands.h`: código modificado. `tests/` mock host/ASAN y capturas. `build_native_v321.py` y `build_fwsc_v13.py` son scripts del laboratorio adaptados a rutas del entorno de compilación; requieren las mismas fuentes DSP v0.12, objetos base SDK, toolchain JieLi y SDK V14, conservados en entregas previas. Este ZIP no redistribuye el SDK ni el compilador.
- El FWSC deriva de v0.13, aplica de forma controlada el mismo parche experimental CPU1 (NO soportado) y es **SOLO EMULADOR**, aunque FM1-LIVE-LAB permita reproducirlo.
- GitHub PR #24 para REminiSCENT, #26 para compartir experiencia con BIOMECH. **No cambiar master** ni las madres aprobadas.