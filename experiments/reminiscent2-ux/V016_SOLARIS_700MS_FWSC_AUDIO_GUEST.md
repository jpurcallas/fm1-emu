# REminiSCENT v0.16 — SOLARIS v09, estación reducida a 700 ms

Fecha 24/oct/2026 Costa Rica. **SOLO EMULADOR, NO INSTALAR, NO MERGE.**

## Procedencia y modificación aprobada por el autor
Se identificó en GitHub la rama `assets/reminiscent-solaris-splash-v09-20261024`, pero su HEAD continuaba en `61b51596d5756d09902fc16cc5e0ecd550d4501e`, sin los nuevos archivos de animación en el árbol remoto. Se recuperó el archivo ORIGINAL de la biblioteca del autor `REminiSCENT_SOLARIS_ONDAS_SIMPLES_ENCAJE_Y_TITULO_v09_240x240.html`, cuyo GIF embebido original tiene 42 cuadros (240x240): primer cuadro estacionario **2720 ms**, siguientes 41 cuadros **80 ms** = **6000 ms**.

A petición posterior del autor («podemos quitarle tiempo a la estación quieta»), se cambió **solo duración del primer fotograma a 700 ms**; los otros 41 se mantienen a 80 ms, nueva duración **3980 ms**. El GIF retimado conserva los 42 fotogramas completos, SHA-256 `63d53898a5b366db586fdbd384ec894b145fe9c8f02608d24e4fbe68fa731104`.

## Nuevo FWSC con sonido (COMPILADO + EJECUTADO guest)
Archivo entregado por conversación `REminiSCENT2_v0.16_SOLARIS_ESTACION_700ms_SOLO_EMULADOR_NO_INSTALAR.fwsc`, 1.069.620 bytes, SHA-256 **6a231bb51072490b0a819bf7b8a7e22cc0557fcf53bb6cb7aa698e7849668b15**. Paquete ZIP con FWSC, referencia GIF retimada, captura LCD guest y fuentes C99, SHA-256 **3d1525a2d1f3b0502f0f00cc0be540c30785951f2b3637b167a136110d1d809b**.

Partiendo del motor/GUI UX07 v0.15, se sustituyó **exclusivamente el splash**: máscara raster de la estación (incluye DBA Corporation Presents) y de la tipografía extraídas del GIF, y ondas geométricas dibujadas vectorialmente. **La animación dentro del firmware es una adaptación visual compacta, NO una reproducción píxel-exacta de los 42 cuadros originales**; esto está documentado y se entrega el GIF retimado exacto como referencia. No se quitó ningún motor musical, PART, efecto, pista ni fuente acústica; C99 DSP fuente sin cambios, aunque varios objetos fueron compilados con `-Oz` y por ello no se garantiza PCM bit-exacto con v0.15.

Espacio real en la partición: `app_area_head` payload 431023, comienzo APPDATA 288, capacidad APP 430735. Nuevo app.bin **430544B** (registro original 430352 + 192B del padding interno existente), margen **191B**. Reempaquetado conserva todos los bytes fuera del área de APP/CRC y todo el banco acústico. Este ajuste es **SOLO EMULADOR**; NO flashear en hardware.

**EJECUTADO guest:** SDK JieLi V14/PI32v2 R3 compila+enlaza, callback MIDI fuerte del proyecto presente, CRC/record verificados. Emulador WebAssembly interpretado JIT OFF 200MHz, 1600 bloques de 128 frames, estímulos MIDI por cuatro PARTS: **196689 instantes PCM no nulos, 34 bloques cortos, HALT=false**. v0.15 con el mismo estímulo también 34 bloques cortos; el SHA PCM difiere y no se declaró paridad exacta. Capturas LCD RGB565 reales: estación, ondas/título y regreso a HYBRID BLEND después del splash. A 1700 bloques gesto `fm1_enc(3,-16)` en K2: valor BLEND **127→115**, sin HALT.

**NO AÚN EJECUTADO:** escuchar v0.16 en FM1-LIVE-LAB nativo macOS ARM64 del autor; duración continua 14 minutos; hardware FM-1 físico; prueba de todos los efectos/modulaciones. v0.13 sigue como referencia auditiva del autor; v0.15 intacta.

## Transferencia a BIOMECH
Reutilizable: raster mascarillas 1-bit RLE por fila combinadas con RGB565 scanline y máquina de estados temporizada sin bloquear audio. No copiar datos, offsets, coordenadas ni presupuesto de APP del REM a BIOMECH sin medir su propio SDK y FLASH. Compilación/enlace correcto no sustituyen audio guest y escucha nativa.

Solo documentación en GitHub; binario y fuentes completas están archivados en los entregables de la conversación, NO se fusionó ni se publicó firmware en `master`.
