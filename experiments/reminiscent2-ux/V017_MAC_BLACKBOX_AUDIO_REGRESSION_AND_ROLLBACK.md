# REminiSCENT v0.17 — REGRESIÓN REAL DE AUDIO EN FM1-LIVE-LAB MAC / BLACK BOX
**24/oct/2026, Costa Rica. Estado: v0.17 RECHAZADA COMO CANDIDATO AUDIBLE. No instalar en hardware.**

## Prueba del autor
Al cargar `REminiSCENT_v017_MAC_ENLACE_RENOVADO_20261024.fwsc`, el autor escuchó sonido retrasado/deteriorado y percibió que el teclado no respondía. Contradice claramente el comportamiento anterior observado. Archivo de evidencia en conversación `FM1_BLACKBOX_1792854880894_exit.json`; **no se subió el dump de RAM ni rutas personales a GitHub**.

## Valores medidos del dump `FM1-NATIVE-BLACKBOX-v1`
- Firmware ejecutado v0.17 SHA256 `6ebdea2499af4097b5ea33a238e4de08b6f6c6dac9d8e71a01fe527eb1096424`, 200MHz emulador Mac nativo, trigger=exit.
- `emulator.ms=31399`; `hostAudioUnderruns=6315`; `halted=false`; CPU0 4.201.090.737 instrucciones, CPU1 589.309.443.
- RAM base 0x01c00000; ring `R2TB` encontró magic exacto 0x52325442 en 0x01c49880, offset 0x49880. CPU0 pad[0]=10701 bloques renderizados, pad[2]=10701 copiados al DMA, pad[4]=0 excedidos y pad[5]=0 pérdidas de ownership. Primer bloque con señal 8551, bloques con señal 2151; la BLACK BOX **no contiene historial de cuándo pulsó el usuario teclas**, no concluir que 25 segundos sea latencia de pulsación.
- Tiempo máximo render=377952 ticks, máximo render+mix=383289; deadline=487420 ticks. Últimos 4 eventos R2 alternan render 323–325k ticks y DMA_COPY 332–333k ticks, con CRC/commit; las dos CPU estaban ejecutándose al salir.

**Conclusión demostrada:** en esta captura la ruta de síntesis huésped completó todos los bloques y los copió a DMA dentro del plazo; **el anfitrión macOS acumuló 6315 underruns**. Hay una regresión audible que la prueba C99 + enlace PI32v2 anterior no descubrió. Esto **no establece todavía** si el causante preciso es recompilación/cambio de layout de código/ineficiencia JIT, ruta MIDI/teclado o la carga del host; comparar A/B nativo v0.16 vs v0.17 y perf sería la siguiente prueba causal. No optimizar DSP de forma especulativa ni culpar SOLARIS sin pruebas.

## Auditoría de fuentes
La diferencia `rn_hw_screen.c` UX07 antiguo → v0.17 introduce `sel_track`, PRESET cambiando fuente acústica y nuevas rutas de pantalla. La ruta `keys()` del C99 queda en el mismo patrón: **en pantalla STEPS el teclado edita los pasos en vez de emitir RN_HW_NOTE**, fuera de esa pantalla emite RN_HW_NOTE. Puede explicar *no escuchar teclado dentro de STEPS*, pero no demuestra la falta de respuesta fuera de esa vista. Recompilación -Oz y LTO modificó imagen APP; no hubo ensayo guest ni audio del v0.17 antes de entregarlo; esto fue un error del protocolo de entrega.

## Rollback disponible y verificable
Se creó una copia **idéntica byte a byte** del firmware v0.16 ORIGINAL entregado antes:
`REminiSCENT_ROLLBACK_v016_SOLARIS_AUDIO_ANTES_V017_SOLO_EMULADOR_20261024.fwsc`.
SHA256 `6a231bb51072490b0a819bf7b8a7e22cc0557fcf53bb6cb7aa698e7849668b15`, 1069620 bytes.
Paquete `REminiSCENT_ROLLBACK_v016_Y_DIAGNOSTICO_BLACKBOX_20261024.zip` incluye el FWSC, reporte resumido JSON, instrucciones. No es una v0.18 ni tiene los nuevos controles v0.17: es la referencia anterior sin esa regresión. v0.16 tuvo audio guest validado previamente; la confirmación de escucha Mac es la del autor.

**Prioridad siguiente:** no presentar nuevos FWSC sin A/B guest MIDI+teclado y, cuando se necesite, nuevo Mac blackbox en reproducción; restaurar mapeo SELECT PART/TRACK, PRESET acústico, ALGORITHM menú conservando comportamiento v0.16 y presupuesto temporal. No alterar `master` ni originales. NO MERGE/NO HARDWARE.
