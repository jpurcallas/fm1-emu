# REminiSCENT 2 LAB — Corte 1: caja negra y recuperación externa

22 octubre de 2026. Solo laboratorio. NO INSTALAR. NO MERGE.

## Trabajo realizado

Se implementaron un registrador C99 de dos anillos independientes y un lector pasivo de imágenes RAM. El registrador almacena versión de compilación, hash del código host, número de tarea/bloque, inicio y fin de cada núcleo, espera, copia y plazo DMA, PC/SP cuando estén disponibles, último estado válido y banderas de excepción. Cada entrada utiliza 64 B; 32 entradas por CPU + metadatos ocupan 4352 B, cuyo encaje en SRAM real todavía debe validarse.

Archivos subidos a esta rama:
- [rem2_trace.h](rem2_trace.h): registro fijo sin memoria dinámica ni E/S.
- [rem2_dump.py](rem2_dump.py): extracción desde memoria sin pedir respuesta al firmware.

## Pruebas corridas en Linux host (NO PI32v2 ni REminiSCENT DSP)

- NORMAL: 4 tareas sintéticas, principio/fin, esperas y copias DMA dentro de plazo de prueba.
- TIMEOUT: se congeló el proceso hijo en trabajo 4. Otro proceso pudo recuperar su memoria compartida; se observa último trabajo empezado, ausencia de finalización y último bloque válido.
- BAD_MAILBOX: orden deliberadamente inválida en trabajo 3; el lector recupera la marca y no hay trabajo terminado.
- TORN: la escritura se interrumpió; 1 entrada incompleta fue descartada correctamente.
- DMA_LATE: copia sintética posterior al plazo detectada sin avanzar el último bloque válido.
- Dos hilos POSIX concurrentes: 256 bloques, cuatro PARTS de render sustituto; PCM serial y paralelo idéntico. No se trata de los cuatro motores reales del sintetizador.

## Coste: medición, no conclusión de rendimiento

12 rondas de 100.000 eventos por modalidad, mediana ~6,3 ns por llamada con traza activa versus ~0,54 ns desactivada (Linux host). En 12 A/B del render sustituto, la mediana de duración media por bloque fue 2,195 us con traza y 2,083 us sin traza; peores bloques observados 171 us y 126 us, afectados por la planificación del host. No extrapolar al FM-1: todavía hay que medir con Timer4, DMA real/emulado y continuidad audible.

El último evento es un indicio temporal, no una prueba de causalidad. Los PC/SP del ejemplo de bloqueo son campos sintéticos para ejercitar el esquema; no se observaron registros PI32v2. Recuperación desde el emulador REAL aún pendiente de integrar.

## Bloqueo identificado y siguiente ejecución

Se recuperaron fuentes y objetos PI32v2 del paquete REminiSCENT v3.21, parches v3.22/v3.23 y linker/SDK V14. En este entorno no está el compilador Jieli PI32v2 usado originalmente, por lo que NO se generó un firmware LAB ni se arrancó CPU1 del hardware. El siguiente corte es reproducir un enlace del firmware base, insertar este registrador en una región SRAM verificada, permitir lectura de RAM desde el emulador incluso con el firmware congelado, y solo entonces sustituir el arranque CPU1 del SDK por nuestra entrada nativa de laboratorio.

Firmware madre v3.0.23 intacto, SHA256 8409b8fec212cdeb7ac36b8a9576db74ebfe4e77d0100b59430a891260313467. No modificar master. No reducir voces, cuatro PARTS, efectos ni secuenciador. Antecedentes X0X/Clipper ya vinculados en el plan del LAB.

El paquete ZIP completo de este corte, con código de pruebas, volcados, JSON, comparaciones A/B y madre, se entrega como artefacto descargable en la conversación.
