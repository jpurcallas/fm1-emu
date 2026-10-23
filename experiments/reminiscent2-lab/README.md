# REminiSCENT 2 — LAB (CPU1 libre)

**22-oct-2026 · EXPERIMENTO · NO INSTALAR**

Propuesta del autor: crear una segunda vida experimental para REminiSCENT, donde se permite sustituir el servicio de CPU1 y su arranque del SDK, en lugar de prolongar indefinidamente el diagnóstico del protocolo existente.

## Punto de partida conservado

- **Firmware madre:** REminiSCENT v3.0.23, SHA-256 `8409b8fec212cdeb7ac36b8a9576db74ebfe4e77d0100b59430a891260313467`, recuperado de un checkpoint previo. Esta rama no lo contiene ni modifica.
- **`master` original:** `61b51596d5756d09902fc16cc5e0ecd550d4501e`. Esta rama comienza exactamente allí y no se fusiona con master.
- La versión LAB no es apta para instalar. Las pruebas de ejecución van primero **solo en emulador**.
- **No se recortan voces, cuatro PARTS, efectos, secuenciador ni parámetros** para facilitar el resultado. El trabajo se redistribuye, no se sustituye el instrumento.

## Hipótesis radical a probar

1. CPU0 procesa entrada, secuenciador, controles y cualquier azar/estado compartido en serie.
2. Un CPU1 *propio*, arrancado sin el servicio de síntesis del SDK, recibe un trabajo acotado por bloque.
3. CPU0 y CPU1 calculan PARTS independientes con buffers separados; CPU0 espera su finalización y mezcla en orden original, aplica efectos compartidos y publica DMA.
4. Ante fallo de arranque, plazo, escritura simultánea o diferencia no explicada, solo el LAB vuelve al render en CPU0 o descarta ese intento.

**Primer riesgo deliberado:** detener CPU1 del SDK en la copia LAB, arrancar un CPU1 propio y obtener un latido verificable; a continuación una tarea de síntesis real. No tocar el ejecutable madre. No confundir un ACK, una prueba host o la compilación con audio a tiempo real.

## Primer resultado ejecutado

`dualcore_host_poc.c` simula en dos hilos el reparto de cuatro PARTS y verifica igualdad de PCM en 256 bloques con orden de mezcla y etapa de efectos compartida. **PASÓ** en Linux/GCC. Es una prueba de estructura de coordinación **con render sustituto**, no prueba de código original, compilación PI32v2, arranque físico, ahorro real ni firmware audible. No autoriza instalar.

## Próximo corte utilizable

Portar una rutina propia de entrada CPU1 (IRQ deshabilitadas, pilas separadas, ventana de PC, código de espera en RAM), con cuidado de guardas y escritura de flash. Integrarla con **fuentes y enlazador reales de v3.0.23**, producir una copia .fwsc exclusivamente para el emulador, comparar A/B de audio y medir plazos/continuidad. No crear un .fwsc ficticio a partir de una copia renombrada.

Experimentos anteriores de ACK, fase RELEASE y JIT se conservan como referencias, **sin repetirlos**.

### Fuente de orientación técnica

- [X0X, dual core y reloj](https://github.com/charlesvestal/fm1-x0x/blob/main/docs/plans/2026-10-04-dual-core-and-clock.md)
- [Clipper FM-1](https://github.com/isod89/clipper-fm1)

El arnés host es original y no traslada archivos de firmware ni fragmentos de código de terceros.
