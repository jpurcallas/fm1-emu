# REminiSCENT 2 — v0.17 controles corregidos; SOLO EMULADOR (24/oct/2026)

**Contrato de controles confirmado por el autor:**
- MASTER: volumen global (potenciómetro; no navega).
- SELECT: elige PART 1–4 fuera de SEQUENCER, TRACK 1–4 en SEQUENCER.
- PRESET: elige uno de los **15 instrumentos acústicos** de la PART correspondiente (piano, trompeta, etc.). **No** selecciona ranuras temporales de patch ni cambia pantalla.
- ALGORITHM: cambia submenú dentro de la sección activa.
- K1–K4: parámetros visibles. HYBRID: K1 GAIN, K2 BLEND, K3 OSC VOL, K4 WAVEFORM; la fuente acústica pertenece exclusivamente a PRESET.
- OCT+/- recorre páginas 16×4 en STEPS.

**Solicitud posterior del autor:** posponer tipografía del splash SOLARIS, especialmente “by Yeti Fingers” ilegible en LCD 240×240. Conservar el splash v0.16 y trabajar primero los menús.

**IMPLEMENTADO:** cambio de las rutas de encoder en `rn_hw_screen.c`, selección TRACK separada de PART, PRESET encolando `RN_HW_PARAM` de `RN_UI_SOURCE` para la PART elegida, ajuste de pantalla HYBRID sin duplicar selector de fuente. Se conservó el splash SOLARIS, 700ms estación y 41 cuadros a 80ms, y toda la fuente DSP de v0.16.

**COMPILADO Y VERIFICADO:** JieLi PI32v2 r3, SDK Open V14; strong `fm1_app_midi_received`; esquema CPU1 cooperativo postlink validado por opcode/destino y verificado en la imagen. FWSC `REminiSCENT2_v0.17_SOLARIS_CONTROLES_CORREGIDOS_SOLO_EMULADOR_NO_INSTALAR.fwsc` SHA256 **6ebdea2499af4097b5ea33a238e4de08b6f6c6dac9d8e71a01fe527eb1096424**, 1.069.620 B, APP efectiva 430.352 B, APP record 430.544 B, libre 192 B. Repack CRC decode/reverse PASS. No particiones ni banco acústico alterados fuera de APP. ZIP `REminiSCENT2_v0.17_SOLARIS_CONTROLES_CORREGIDOS_PRUEBA_MAC.zip` SHA256 **e624c025ed32683f3c899980cf7d151fd78c84a22f937e891c57620774ca02d5**. Binarios y fuente completos entregados en conversación, no subidos a GitHub.

**PRUEBA REAL C99:** Clang ASan/UBSan HOST PASS: PRESET piano→trompeta sin navegación; SELECT PART2; PRESET bandoneón en PART2 sin tocar PART1; ALGORITHM navegación; SEQ SELECT TRACK3 sin modificar PART2; K2 envía BLEND al comando OSC de PART2 sin tocar PART1.

**PENDIENTE (no exagerar):** v0.17 todavía NO ha sido ejecutado en guest PI32v2 ni escuchado en FM1-LIVE-LAB Mac; la evidencia audible anterior pertenece a v0.16. Solicitar prueba del usuario antes de aprobar la versión. **SOLO EMULADOR, NO INSTALAR, NO MERGE**. v0.13/v0.15/v0.16 y master intactos.
