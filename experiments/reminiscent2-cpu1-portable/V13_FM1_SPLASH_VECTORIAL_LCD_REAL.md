# REminiSCENT 2 v0.13 — splash vectorial integrado en FWSC SDK V14

**23/oct/2026 · SOLO EMULADOR · NO INSTALAR · NO MERGE.** Se revisaron los PR #24 y #26 antes de empezar. Instrumento final: FM-1 físico.

## Diseño respetado

LCD **240 × 240 RGB565**; amarillo pastel RGB(255,241,187), ondas concéntricas abstractas cian/azul (no agua literal), nombre **REminiSCENT** por delante de las ondas (mini minúscula), subtítulo **ACOUSTIC MEMORY SYNTHESIZER** y firma **by Yeti Fingers**. Duración **5 segundos**, 80 estados a 16fps, transición a menú. La fuente C99 de 5×7 es una traducción técnica del concepto aprobado; requiere valoración visual del autor.

## Implementado

Renderer C99 matemático Q14, sin floats, GIF, tablas de cuadros, heap ni framebuffer duplicado. Usa las bandas RGB565 240×4 y el blit existente. Integración en groove_screen_init y groove_screen_control como estado no bloqueante gobernado por fm1_millis; audio, controles y DSP siguen activos. La RAM compartida del SDK y todo el motor v0.12 permanecen.

**Aviso de espacio:** la primera app con GUI -O2 pesó 432016 B y NO cabía en el registro REAL app.bin de 430352 B aunque el enlazador diera margen. **Descartado** sin reubicar cfg_tool.bin. Recompilamos SOLO GUI con -Oz, manteniendo DSP: control sin splash = 426320 B app/428360 B SRAM; splash = **427920 B app/428424 B SRAM**. COSTE NETO aislado splash **+1600 B de programa y +64 B de RAM estática**. Paquete V14 conserva registros y regiones del fabricante y CRC; cfg_tool.bin verificado byte idéntico.

FWSC experimental 1069620 B, SHA256 **99c44e7e6ae59bdc68e84823065d6720c7ff177ff4203dd070da057da1c7a5e5**. El CPU1 2+2 conserva la cooperación postlink NO soportada del v0.12: no instalar.

## Ejecución y BLACK BOX

**Emulador PI32v2, 200 MHz, JIT OFF**: capturamos el LCD auténtico RGB565 mediante fm1_lcd(), con expansión de ondas y retorno al secuenciador tras splash. GIF extraído solo como evidencia visual (no en firmware): REminiSCENT_v0.13_SPLASH_LCD_REAL_EMULADO.gif, **147458 bytes**, SHA256 **99acfac3ab2f83e5019fe0c4f2d1466607f61b525fc2519744e2170661f02da2**. El GIF incluye un segundo de interfaz posterior al splash para mostrar transición.

**Comparación 950 solicitudes con NOTE ON/OFF en las cuatro PARTS, 24 mensajes:** v0.12 = 912 renders / 912 DMA / 24 MIDI RX y aplicados; v0.13 = **914 renders / 914 DMA / 24 MIDI RX y aplicados**. Ambas sin DMA_LATE, sin OWNER_LOST, sin halted ni fault CPU1. No interpretar los dos bloques extra como ganancia de velocidad física.

**Ensayo extendido v0.13 2100 solicitudes y MIDI:** 2064 renders y **2064 DMA**, cero rechazos, halted=false; 2064 trabajos CPU1 completos, otro en vuelo al instante de lectura (2065 aceptados). No afirmar continuidad ni propiedad CPU1 física, ni paridad PCM byte-exacta de todos los presets/MIDI.

## Evidencia / paquete del autor

Artefacto descargable desde esta conversación (binario NO subido al repositorio): **REminiSCENT2_v0.13_SPLASH_VECTORIAL_FM1_SOLO_EMULADOR_NO_INSTALAR.zip** SHA256 **3e895c9ed3a9872cefe9343c1e69556815c7988ca1dd88033a8a33a29b7d6c40**; incluye .fwsc, captura GIF del LCD real, fuentes C99 rn_splash.c/h, patch sobre pantalla v0.12, scripts de build, informe AB MIDI y BLACK BOX. La fuente exacta está en el ZIP del autor, no en esta rama; conservar esa distinción.

## Próximo paso de producto

Valorar splash técnico contra diseño aprobado y luego navegación Yeti Fingers (MASTER, SELECT, PRESET, ALGORITHM y cuatro KNOB editando cuatro parámetros por submenú), envolvente, secuenciador y mixer gráficos; sin declarar la UI funcional hasta enlazar los controles físicos con DSP y persistencia. No modificar master ni madres originales.