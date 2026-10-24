# REminiSCENT — Yeti Fingers UX 01: navegación y paleta de evaluación

**23 de octubre de 2026. Prototipo de interacción 240×240. No es firmware y no está conectado al DSP.**

## Identidad aprobada frente a propuestas

**Aprobado por el autor:** splash de cinco segundos con REminiSCENT / ACOUSTIC MEMORY SYNTHESIZER / by Yeti Fingers; ondas abstractas de resonancia detrás del nombre; fondo **amarillo pastel**; navegación característica Yeti Fingers con controles fijos MASTER, SELECT, PRESET, ALGORITHM y cuatro KNOB de edición, cuatro parámetros por submenú; ADSR, secuenciador y mixer gráficos; cuatro PARTS independientes y secuenciador de cuatro TRACKS.

**PROPUESTA PARA EVALUAR, NO APROBADA TODAVÍA:** colores complementarios de pantallas y distribución exacta de las páginas en secciones. No sustituir otros temas antiguos de diseño que pudiera recuperar el autor.

| Uso | Color web | Función visual |
| --- | --- | --- |
| Fondo aprobado | `#FFF1BB` | Amarillo pastel de la identidad REminiSCENT |
| Texto | `#274455` | Contraste en LCD |
| Memoria/SOUND | `#5699AA` | Cian desaturado |
| Edición / MIXER | `#DF887B` | Coral pastel |
| Secuenciador | `#78BCA3` | Menta suave |
| PERFORMANCE | `#9C95CB` | Lavanda |
| Superficies | `#FFF9E7` | Marfil cálido |
| Indicadores | `#D7A353` | Dorado suave |

## Norma de controles (intención aprobada)

| Control dedicado | Responsabilidad estable |
| --- | --- |
| MASTER | Volumen maestro global; NO recorre menús |
| SELECT | PART 1/2/3/4, sin resetear ni alterar otras PARTS |
| PRESET | Sonido/preset de la PART seleccionada; no cambia de submenú |
| ALGORITHM | Recorre exclusivamente los submenús de la sección principal activa |
| KNOB 1–4 | Editan exactamente los cuatro parámetros rotulados del submenú actual |

**SAVE** debe persistir presets en el firmware real; en UX01 es una demostración **solo en memoria temporal del navegador**. Los cuatro presets INIT/SOFT/GRAIN/PULSE son **datos ficticios para probar navegación**, NO el banco aprobado del instrumento ni la selección acústica definitiva.

## Orden de pantallas — propuesta para evaluar

**SOUND** (editor profundo de PART): `SOURCE → MEMORY → MOTION → RESONANCE → OSC → OSC EXTRA → FILTER → ENVELOPE (ADSR gráfico) → GRANULAR → CHARACTER → SENDS`.

**PERFORMANCE:** `ROUTING → LAYERS (gráfico de cuatro PARTS) → VOICE MODE → SPLIT`.

**MIXER:** `LEVELS (gráfico) → PAN (gráfico) → MUTE → SOLO → MOD A → MOD B → DELAY → REVERB`. Las cuatro barras LEVELS corresponden a las cuatro PARTS; buses FX MOD/DELAY/REVERB son **compartidos**, no cuatro copias de los efectos. Los SENDS pertenecen a cada PART y se muestran desde SOUND, con acceso futuro desde MIXER.

**SEQUENCER:** `STEPS (4 TRACKS simultáneos × 16 columnas, cuatro páginas = 64) → TRACK → LIVE REC → MOTION TARGET → MOTION PART`. El demo permite encender/apagar pasos pulsando la pantalla; no escribe en el motor C99.

**Criterio a debatir:** qué sección debería abrirse al terminar el splash (HOME / SOUND / SEQ). v0.13 abre SEQ; el demo UX01 abre SOUND para evaluar edición. No cambiar el comportamiento del firmware sin aprobación.

## Estado en el firmware existente v0.13 (auditoría basada en src/rn_hw_screen.c de v0.12 y parche v0.13)

- **Ya implementado en V14 previo:** LCD RGB565 240×240 por bandas 240×4; ADSR gráfico; secuenciador visual cuatro pistas; cuatro knobs por página; selección de PART con encoder; procesamiento de comandos hacia audio owner; splash vectorial v0.13; páginas SOUND distribuidas en enum.
- **NO implementado conforme a nueva lógica fija:** distinción estable del encoder PRESET frente al encoder ALGORITHM; el encoder `c->encoders[6]` actual recorre páginas en varias situaciones y modifica SEQ/ROUTING según contexto; MASTER/PRESET/ALGORITHM deben auditarse contra el mapeo real de FM-1. No afirmar que funciona en V14.
- **NO demostrado en FWSC:** gestión de presets persistentes; navegación completa por secciones SOUND/PERFORMANCE/MIXER/SEQUENCER; mixer gráfico de cuatro niveles y mute/solo conectado a parámetros reales; SPLIT completo, gestión de presets por PART y todo Motion Sequencing. No inventar su implementación.
- **Riesgos técnicos separados:** CPU1 V14 sigue dependiendo de un injerto experimental de SDK; AudioWorklet a 200MHz puede exceder tiempo real en el navegador (por eso UX01 no tiene audio); hardware físico no probado.

## Pruebas del prototipo

- HTML autocontenido con Canvas `width=240 height=240`; sin recursos externos; apertura local con Chrome (el navegador automatizado del entorno bloqueó file://, pero Playwright **set_content** sí ejecutó las mismas fuentes, dibujó Canvas y probó clicks).
- Ejecutado `node --check` y `test_ux01.cjs`: MASTER independiente; SELECT conserva ajuste ADSR propio de cada PART; PRESET independiente y SAVE demo restaura una edición; ALGORITHM avanza/regresa dentro de la misma sección; mixer compartido; matriz 4×64.
- Ejecutado Playwright Chromium: cambió SOUND→PERFORMANCE→MIXER→SEQUENCER; editó ADSR con KNOB1; SELECT cambió de PART y al regresar conservó valor; se capturaron cuatro pantallas reales de Canvas 240×240.
- **No incluye audio, SDK, MCU, temporización ISR/DMA ni guardado de flash.** Es una herramienta para que el autor evalúe navegación antes de portar decisiones al C99.

## Próximo checkpoint una vez revisado UX01

1. Autor valida/reordena grupos y etiquetas; conserva splash aprobado.
2. Implementar la capa C99 de navegación estable (sección/submenú/PART/preset) en rama aislada; enlazar los cuatro KNOB a parámetros DSP reales con BLACK BOX de eventos UI.
3. Añadir ADC/botones reales emulados y persistencia segura de presets, sin tocar `master` ni firmware aprobado.
4. Probar en pantalla real del FM-1 emulado y por escucha diferida donde el motor DSP deba cambiar.

**DISCUSIÓN LIBRE, EJECUCIÓN FIEL.**