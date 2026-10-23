# REminiSCENT 2 LAB v0.7 — primer FWSC V14 con CPU1 BLACK BOX

2026-10-23 — SOLO EMULADOR, NO INSTALAR, NO MERGE. Meta: firmware FM-1 físico; emulador como laboratorio.

**IMPLEMENTADO/COMPILADO/ENLAZADO:** copia intacta de v0.6 + código C99 portable 2+2 y guard fail-closed. JieLi PI32v2 r3, FM1 Open SDK V14 oficial. La ejecución paralela SOLO se arma con cesión explícita de CPU1 por SDK; esa cesión no ha sido demostrada y permanece DESHABILITADA. Blackbox R2TB única en rn_v12_audio.c registra eventos CPU1_PROBE=40 y CPU1_OBSERVATION=41, snapshots CPU1 sin reset/HOLD.

**EMPAQUETADO:** REminiSCENT2_v0.7_CPU1_PROBE_SOLO_EMULADOR.fwsc, SHA256 15cc57f606c45d6ac11afb58238bc7a345b8c2ba238c2f3dd30a80463a996d1a. App PI32v2 = 429712 bytes, límite 453921, margen 24209, SRAM estática enlazada 425928. Empaquetado sobre boot/loader particiones originales v0.6, CRC reconstruidos; app extraído byte igual que ELF compilado.

**EJECUTADO EMULADOR 200MHz, PLAY:** 420 llamadas de 128 muestras: 382 renders, 355 con PCM no nulo; 382 copias DMA, 355 con señal, 0 rejects de propiedad y deadline, 0 halt. Pico render 433697 ticks vs deadline 487420. Control v0.6 idéntico número de renders/DMA, max 433690 ticks.

**PARIDAD:** PCM de emulador completo, 393216 bytes Float32 stereo extraídos del AudioWorklet API, byte iguales v0.6/v0.7, SHA256 a838d5f7c0bf1a270469bc923ebff76610ed14f02eb58e35d39a0379727fc285. No demuestra continuidad real Chrome ni hardware físico.

**BLACK BOX nueva verificada por decodificador sobre RAM capturada:** 16 muestras, CPU1 CON=8, CLOCK=0, ENTRY=0x02000224, lease_verified=0, dual_jobs=0, attach_attempts=0, 0 registros de evento corruptos. Es una observación; NO prueba que CPU1 esté libre ni ocupado en SDK. Render actual SERIAL, no dar nombre 2+2 funcionando.

**ARTEFACTO reproducible en Library/conversación:** REminiSCENT2_v0.7_CPU1_SDK_BLACKBOX_SOLO_EMULADOR.zip SHA256 1f2653bbe1d72e49f1398f0460fedccd1c8fc8e5d6e182fb89d13ef7d421d8db. Contiene FWSC, fuentes modificadas, linker/objeto de control, decoder, RAM y PCM/JSON, README. Binario ZIP no subido al repo.

**SIGUIENTE:** identificar cesión temprana de CPU1 en SDK, verificar RAM/cache y propiedad antes de activar 2+2, medir ACK/TIMEOUT/bloque completo DMA y producir nuevo firmware audible. No reiniciar CPU1 ciegamente desde init tardío ni recortar musicalidad; madres v3.0.23 y v0.6, master intactos.