# REminiSCENT 2 LAB — Lecciones verificadas de X0X y Clipper

Fecha: 22 de octubre de 2026. **SOLO EXPERIMENTO / NO INSTALAR / NO MERGE**.

## Por qué son los dos precedentes principales

**X0X y Clipper ya superaron la barrera conceptual de hacer cooperar los dos núcleos del FM-1 sin emplear el servicio de render paralelo del SDK como scheduler de la aplicación.** Ambos respetan las necesidades físicas del chip —secuencia de arranque y entrada por ROM, registros de control, pilas propias, sincronización— y construyen su **propio protocolo de entrega de trabajo y mezcla**. Esta distinción es importante: “nativo nuestro” significa **no depender de la arquitectura de síntesis y coordinación del SDK**, no intentar reemplazar la ROM del silicio ni ignorar el mecanismo necesario para arrancar CPU1.

Evidencia consultada, fijada a revisiones para no depender de modificaciones futuras:

- **X0X**: `charlesvestal/fm1-x0x` commit `54194c54bb01e9d9b3fe9d641b3ddfa512ac04a3`.
  - [Informe con mediciones reales](https://github.com/charlesvestal/fm1-x0x/blob/54194c54bb01e9d9b3fe9d641b3ddfa512ac04a3/docs/plans/2026-10-04-dual-core-and-clock.md)
  - [HAL C de CPU1](https://github.com/charlesvestal/fm1-x0x/blob/54194c54bb01e9d9b3fe9d641b3ddfa512ac04a3/firmware/hal/fm1_cpu1.h)
  - [Arranque ensamblador](https://github.com/charlesvestal/fm1-x0x/blob/54194c54bb01e9d9b3fe9d641b3ddfa512ac04a3/firmware/hal/fm1_cpu1.S)
- **Clipper**: `isod89/clipper-fm1` commit `e69067211c4690f34e494b5b896e4585163dcc2b`.
  - [CPU1, boot y comprobación inicial](https://github.com/isod89/clipper-fm1/blob/e69067211c4690f34e494b5b896e4585163dcc2b/firmware/src/cpu1.c)
  - [Protocolo de ejecución](https://github.com/isod89/clipper-fm1/blob/e69067211c4690f34e494b5b896e4585163dcc2b/firmware/hal/fm1_cpu1.h)
  - [Prueba paralela host e inyección de fallos](https://github.com/isod89/clipper-fm1/blob/e69067211c4690f34e494b5b896e4585163dcc2b/tests/cpu1_host.c)
  - [README: reparto de voces, alcance y reservas de hardware](https://github.com/isod89/clipper-fm1/blob/e69067211c4690f34e494b5b896e4585163dcc2b/README.md)

**Atribución y licencias:** código de X0X y Clipper bajo GPL-3.0. Usar sus decisiones como referencia, y no copiar componentes textuales sin revisión de licencias y obligaciones de redistribución. El nuevo protocolo REminiSCENT tendrá implementación propia y trazabilidad de procedencia.

## Transferencia concreta al LAB (no reinventar estos problemas)

| Hallazgo de precedentes | Riesgo demostrado/observado | Decisión para REminiSCENT 2 |
| --- | --- | --- |
| **X0X: CPU1 se arranca temprano**, antes del audio y timers. Arrancarlo tarde puede no alcanzar su entrada. | “No respondió CPU1” puede ser secuencia de boot, no incapacidad del motor. | Arranque único controlado al inicio del LAB. Registro ordenado `BOOT0 → C1_ENTRY → C1_RAM_LOOP → C1_ALIVE`. |
| **X0X: abrir límites de PC** para que CPU1 complete el tramo por ROM y volver a armarlos. | La protección bloquea la transición de ROM a código propio. | Snapshot de guard/PC antes y después; no copiar registros sin inspeccionar la configuración real del LAB. |
| **X0X: el trabajo corre con su pila de usuario `usp` tras `rti`.** Un stack pequeño corrompió variables. | Sobreescritura que parece un bug DSP aleatorio. | Dos pilas propias, marcas de profundidad, guardas y contador high-water; dimensionarlas con el motor real. |
| **X0X: bucle de espera en RAM y enlazado realmente dentro de la imagen.** | PC en flash borrada / conflicto al escribir flash. | Verificar en map/objdump las secciones, copy table y PC efectivo. Estacionar CPU1 y confirmar ACK antes de operaciones de flash. |
| **X0X: protocolo más reciente con comprobación del trabajo, contador monotónico, flags en líneas de caché independientes y registro de lecturas malas.** | En ciertas unidades, CPU1 lee valores incoherentes; una orden mal leída podría ejecutar función incorrecta. | Mailbox propio con `seq, task_id, params/checksum, ack, bad, bad_value`, barreras y alineación verificadas; tareas enumeradas o despachador restringido, no punteros arbitrarios sin comprobar. Si rechazo, no ejecutar. |
| **X0X: fallback persistente tras fallos del segundo núcleo y hold antes de reset.** | Un cuelgue seguido de otro arranque dual puede generar un ciclo de reinicios. | LAB debe arrancar con modo *un núcleo* tras fallo crítico registrado. Para hardware futuro requerir recuperación independiente; por ahora solo emulador. |
| **X0X: balancear por costo real**, no repartir “dos sonidos y dos sonidos” a ciegas. | Un primer reparto parecía mejorar, pero el núcleo lento seguía causando dropouts; redistribuyeron y bajaron los picos. | Medir costo individual por PART y efectos; cambiar asignación únicamente por carga, conservando suma y estado exactos. |
| **Clipper: calcular la modulación/estado compartido antes de repartir voces.** | Dependencias de RNG, tablas y temporales rompen la equivalencia sonora. | CPU0 prepara notas, secuenciador, RNG y snapshots; CPU1 solo cambia memoria de la PART/voz que posee durante ese job. |
| **Clipper: pruebas en 1/2 hilos, retrasos aleatorios y jobs perdidos.** | Una prueba determinista de 256 bloques no detecta carreras, ausencia de respuesta ni fallos de temporización. | Tres modos host: `INLINE`, `PARALLEL`, `CHAOS`; inyectar `MISSING_JOB` y `BAD_MAILBOX`; usar TSAN donde esté disponible. |
| **Clipper: boot con autocálculo de prueba en CPU1**, luego audio. | `ALIVE` no demuestra que el CPU1 esté realizando cálculo correcto. | Tras latido inicial exigir checksum calculado por CPU1 y verificado por CPU0 antes del primer job DSP. |
| **Clipper: contador LATE, PEAK y carga real**, control on/off. | Un sintetizador puede sonar en un ensayo y fallar en acordes largos o con UI/MIDI. | Registrar latencia peor/bloque, CPU0 activo, CPU1 activo, espera, DMA half, 0 underruns; comparación con referencia y escucha por autor. |

### Resultados que no deben exagerarse

**X0X sí publicó números de su propio hardware:** se pasó de un caso de sobrecarga de 115% a aproximadamente 81% con el primer reparto; al cambiar la asignación reportaron peor caso ~68% y ningún dropout en la prueba documentada. Las cifras **no predicen** REminiSCENT. También identificó contención potencial en caché compartida y una tarea CPU1 más lenta que CPU0.

**Clipper publica que su división de voces mantiene PCM idéntico en pruebas host y usa ambas CPU**; sus propias notas advierten que el firmware 1.x es experimental y que falta más comprobación en equipos físicos. Las pruebas host/ThreadSanitizer **no comprueban** por sí solas estabilidad eléctrica en un FM-1 real.

**El código X0X moderno es más defensivo que una copia antigua de Clipper**: el HAL de X0X actual incluye validación `fn/arg/seq` y contador de lectura errónea, mientras la versión consultada del HAL Clipper mantiene `job/done` sencillo. Por tanto **no** importaremos su protocolo más corto sin reforzarlo.

## Especificación técnica incorporada al primer experimento

1. `REM2_NATIVE_CPU1` en una rama LAB separada. Reproducir la madre, localizar su build PI32v2, map y enlazador antes de integrar; no generar un paquete `.fwsc` renombrado.
2. Al entrar CPU1: `core_id`, PC, `usp/sp/ssp`, marca de stack, momento en timer, guard PC y estado de habilitación. Doble ring buffer escrito un solo núcleo por buffer. Volcador del emulador independiente de LCD, serial y USB.
3. En el primer mailbox: `version, seq, job_kind, offset, length, payload_checksum, reply_checksum, done_seq, bad_reads` con alineación explícita y barreras. CPU0 nunca modifica la solicitud hasta `done_seq` confirmado. CPU1 acepta solamente `seq == last+1` y checksum válido.
4. Jobs escalonados: `HEARTBEAT` → `CHECKSUM` → `FAULT_INJECTION` → **una PART de REminiSCENT sin reducción de funciones** → dos y cuatro PARTS con reparto real medido.
5. Fallo deliberado 1: retener un job sin responder. Evidencia obligatoria: `last_good_seq`, `PC0`, `PC1`, `SP0`, `SP1`, `wait_ticks`, `DMA_half` y momento exacto del timeout. Fallo 2: corromper un campo del mailbox; CPU1 debe negarse a ejecutarlo, registrar `BAD_MAILBOX` y permitir diagnóstico.
6. **Timeout:** detener/estacionar CPU1 **antes** de que CPU0 toque la memoria que estaba procesando. Un mero timer agotado no significa que el otro núcleo dejó de escribir; volver a renderizar sobre buffers compartidos antes de confirmar el hold introduciría corrupción. El fallback solo se activa tras hold seguro.
7. Audio: seguir estrictamente el orden de PARTS, BLEND y FX original. Test NOTE OFF por teclado/MIDI, 4 pistas/secuenciador, notas sostenidas, granos, efectos, presets, ahorro a flash y larga duración. Comparar PCM por muestras cuando los algoritmos lo permitan.
8. Publicación: después de un máximo de dos cambios técnicos sustanciales, dar al autor un checkpoint `.fwsc` LAB *real y audible en emulador* si arranca, acompañado de WAV A/B y contadores. Nunca usar el éxito del host como sustituto de sonido.

## Decisión final que habilita

**Sí al riesgo de sustituir el controlador de CPU1 del SDK por uno propio**. **No** a ignorar las reglas del silicio, ni a asumir que el segundo núcleo será fiable en todas las unidades, ni a sacrificar el motor para “hacerlo entrar”. Los precedentes nos ahorran repetir descubrimientos; la caja negra propia convierte un fallo en información utilizable.

**Estado:** fuentes de terceros estudiadas; todavía no se ha integrado el firmware real ni corrido CPU1 nativo REminiSCENT 2 en un binario PI32v2. Esto es un plan operativo y revisión técnica, no una compilación ni prueba audible.
