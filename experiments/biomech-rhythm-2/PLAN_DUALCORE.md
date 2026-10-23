# BIOMECH RHYTHM 2 — experimento dual-core directo

Estado: PLAN EXPERIMENTAL, NO INSTALAR. Rama: experiment/biomech-rhythm-2-dualcore. No modificar master.

## Objetivo
Crear un prototipo **ejecutable y audible**, no una investigación abierta, que conserve las seis voces, secuenciador, sistema generativo, efectos y mezcla de BIOMECH. Medir continuidad DMA y tiempo del bloque completo frente al mismo control.

## Decisión de arquitectura
Mantener el arranque y los servicios indispensables del SDK, pero introducir un buzón de trabajo *propio* del instrumento en memoria compartida. No asumir que el buzón de servicio observado en v0.35 sea una API de síntesis. No copiar direcciones absolutas entre firmwares ni reemplazar CPU1 a ciegas.

* CPU0: MIDI/secuenciador/eventos, asignación de voces, RNG compartido, preparación de parámetros y estados, render de voces 1–3, efectos y mezcla final en orden canónico.
* CPU1: ejecutar una tarea de render de voces 4–6 sobre estado independiente preparado por CPU0 y escribir su acumulador parcial en un buffer separado.
* Buzón: secuencia de solicitud, tipo de trabajo, punteros/buffers alineados, número de frames y secuencia de finalización; publicación/consumo con barreras de memoria y coherencia de caché verificada. Sin malloc ni espera indefinida en la ruta de audio.
* Ante fallo, timeout o colisión con los servicios del SDK: diagnóstico explícito; en una fase posterior agregar fallback CPU0 seguro. No usar el buzón SDK observado como si fuese libre.

## Iteración A: prototipo que ejerce CPU1
1. Establecer baseline y snapshot hash del firmware v0.35, 6 voces sin recorte.
2. Integrar buzón propio en rama experimental; enviar una tarea de prueba con datos conocidos y verificar que CPU1 escribe una respuesta correcta SIN alterar salida musical.
3. Compilar y ejecutar en emulador. Registrar éxito o fallo y ubicación exacta. Si la responsabilidad existente de CPU1 lo impide, decidir modificación controlada del dispatcher/servicio en la copia.

## Iteración B: reparto musical
1. Extraer serialmente eventos, voces, parámetros, RNG y modulaciones compartidas.
2. Renderizar 1–3 en CPU0 y 4–6 en CPU1 con estados independientes; mezcla en el orden original, evitando acumulación no determinista.
3. Conservar effects/sequencer/6 voices; compilar y ejecutar. Entregar .fwsc SOLO EMULADOR ante el primer candidato funcional audible para evaluación del autor.

## Iteración C: decisión medida
Mismo firmware-control, notas, CC, velocidades, duración, JIT y tamaño de bloque. Comparar PCM (igualdad o diferencias explicadas), tiempo end-to-end (preparación+ambos núcleos+espera+efectos+mezcla+copia), worst-case frente a 2.90ms disponibles, underruns, copias y pérdidas DMA, y escucha del autor.

**Aceptar** solo mejora real de continuidad/plazos sin recortes. **Descartar o rediseñar** si no reduce el peor bloque, genera glitches, destruye servicios o no conserva sonido. Compilación y PCM por sí solos NO cuentan como mejora.

## Límites y checkpoints
Toda prueba de riesgo se hace exclusivamente en esta rama y el emulador; NO MERGE y NO INSTALAR en hardware hasta una validación aparte. No afirmar que CPU1 está disponible, ni mejora acústica, ni éxito de ejecución antes de medirlos. Tras uno o dos cambios técnicos producir checkpoint audible si compila y arranca, sin esperar a perfección.
