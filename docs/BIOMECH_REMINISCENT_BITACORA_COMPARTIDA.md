# BIOMECH RHYTHM ↔ REminiSCENT — bitácora técnica compartida

**Inicio:** 2026-10-23 · **Repositorio:** `jpurcallas/fm1-emu`  
**Rama única de coordinación:** `coordination/biomech-reminiscent-shared-log-20261023`  
**Estado:** documento de intercambio entre proyectos, **NO MERGE** / no instalación de firmware.  
**Propósito:** lugar permanente donde ambos trabajos dejan hallazgos, evidencias, preguntas y experimentos reutilizables.

## 0. Acuerdo de ingeniería

- **Meta:** que **BIOMECH RHYTHM** y **REminiSCENT** funcionen completos y estables en el **FM-1 físico**. El emulador y su BLACK BOX son **herramientas de diagnóstico**, no el producto final.
- **Discusión libre, ejecución fiel.** No cambiar el alcance, degradar audio, recortar voces, cuatro PARTS, efectos o secuenciadores sin autorización del autor.
- Proteger versiones madres, archivos `.fwsc` originales y `master`. Trabajar con ramas/checkpoints reversibles y comparaciones que puedan auditarse.
- **No mezclar dos métricas:** (A) plazo real de firmware para producir y entregar audio al DMA; (B) tiempo de pared del navegador para simular CPU0+CPU1/JIT y reproducir AudioWorklet. Dividir DSP entre núcleos puede mejorar (A) y no necesariamente (B).
- Transferir **métodos y mecanismos demostrados**, nunca extrapolar automáticamente direcciones RAM, registros, instrucciones o causas de un firmware al otro.
- Ningún test con PCM silencioso demuestra paridad sonora musical. Exigir estímulo/patrón reproducible, señal no nula, contadores, comparaciones PCM cuando correspondan y prueba audible.
- Un resultado **en el emulador** no certifica automáticamente comportamiento ni rendimiento del hardware físico.

## 1. Cómo actualizar en cada conversación

1. Leer **esta misma URL** al iniciar trabajo cruzado (GitHub `fetch_file` con rama de coordinación). No fiarse de resúmenes antiguos de chat.
2. Antes de una nueva transferencia, leer la última versión del archivo y su **blob SHA**; después actualizar **el mismo archivo** con `update_file` usando ese SHA. Si la actualización falla por conflicto, volver a leer y reconciliar: nunca sobrescribir notas de la otra conversación.
3. Añadir al **registro cronológico**: fecha, proyecto emisor, versión/commit/PR, qué se demostró, qué NO se demostró, evidencia verificable y acción útil para el otro instrumento. Marcar claramente `PROBADO`, `HIPÓTESIS`, `PENDIENTE` o `DESCARTADO`.
4. Nunca mover ni fusionar automáticamente este PR con `master`, ni editar ramas experimentales del otro instrumento como parte de una mera transferencia de información.
5. Cada conversación puede escribir y consultar este documento **mediante GitHub conectado**. No existe sincronización autónoma de chats: la actualización se hace al consultar o guardar un hallazgo en el repositorio.

## 2. Estado de referencia (corte 2026-10-23)

### BIOMECH RHYTHM

- Prioridad presente: experimentar con arranque y coordinación de **CPU1** y reparto del procesamiento, sin alterar el motor musical completo.
- PR experimental [#28](https://github.com/jpurcallas/fm1-emu/pull/28), rama `experiment/biomech-rhythm-2-dualcore`: contiene propuesta de arranque propio, mailbox y BLACK BOX. **NO es todavía evidencia definitiva de firmware multinúcleo estable en hardware.** No prometer la adopción hasta comprobarla.
- Otros PR de observación relevantes: [#23](https://github.com/jpurcallas/fm1-emu/pull/23) disponibilidad CPU1, [#25](https://github.com/jpurcallas/fm1-emu/pull/25) stores coordinación CPU0/CPU1, [#26](https://github.com/jpurcallas/fm1-emu/pull/26) lecturas RAM y [#27](https://github.com/jpurcallas/fm1-emu/pull/27) lecturas JIT directas. Cada uno conserva sus propias condiciones de aceptación.
- En diagnóstico previo, el opcode PI32v2 `ftof floor` requirió distinguir una limitación del emulador de un defecto del DSP; véase [#8](https://github.com/jpurcallas/fm1-emu/pull/8). **Método transferible:** verificar primero ISA y arranque antes de culpar al firmware.

### REminiSCENT

- Madre independiente **v3.0.23**: referencia inmutable; **REminiSCENT 2 LAB v0.6** es otro experimento, no sustituto de la madre.
- La **v0.6** trae una prueba musical preconfigurada para pulsar **PLAY** sin navegar por pantallas: PART 1, oscilador SAW, BLEND y nivel digital activos, secuencia de 16 pasos con C3–E3–G3–C4 a 100 BPM, y efectos no necesarios para la prueba.
- BLACK BOX de Chrome del 23-oct-2026: a **100 MHz**, hubo generación interna informada de audio pero **0 cuadros PCM no nulos en AudioWorklet**; a **200 MHz**, la salida reportó **90.574 cuadros no nulos**, pico aproximado **0,271**, primeros cuadros no nulos a **3.283 ms huésped**, pero **1.782/1.782 quanta tardíos**: no se ha conseguido audición continua confirmada por el autor. Esto prueba pasos internos, **no** audio estable.
- A 200 MHz ya se ha observado transferencia a DMA; una incapacidad de Chrome para sostener tiempo real no implica por sí misma un fallo de DMA en hardware.
- JIT LAB v0.1–v0.3, en variantes aisladas; **la prueba CI `trace-fastgate` [rama](https://github.com/jpurcallas/fm1-emu/tree/experiment/rem2-jit-trace-fastgate-20261023)** usó `sidplayer.fwsc`, no REminiSCENT v0.6: su paridad PCM no basta para certificar este sintetizador. Mantener distinguidos benchmarks Node de pruebas de Chrome.
- PR anteriores útiles: [#14](https://github.com/jpurcallas/fm1-emu/pull/14) captura de PC de stores JIT directos y [#16](https://github.com/jpurcallas/fm1-emu/pull/16) correlación productor/consumidor e IRQ11.
- **Próximo cruce de arquitectura:** transferir a REminiSCENT **únicamente el mecanismo de CPU1 comprobado por BIOMECH** y después repartir DSP gradualmente, comparando PCM/muestreo y los plazos DMA. Conservar la cadena de audio de REminiSCENT como referencia de cada modificación.

## 3. Intercambio técnico confirmado

| Fecha | Emisor → receptor | Clasificación | Lección / evidencia | Condición antes de adoptarla |
|---|---|---|---|---|
| 2026-10-22 | REminiSCENT → BIOMECH | PROBADO (diagnóstico de emulador) | Algunas escrituras de RAM generadas por el JIT **no atraviesan** `Soc::write8/16/32`; observación completa precisa callback también en stores inline. [PR #14](https://github.com/jpurcallas/fm1-emu/pull/14). | Verificar que observador pasivo conserve PCM exacto para el estímulo de BIOMECH. |
| 2026-10-22 | REminiSCENT → BIOMECH | MÉTODO | Correlacionar PC **productor** de estado, PC **consumidor** (IRQ), ciclos, halves DMA, entrada de tecla y diferencia JIT ON/OFF. [PR #16](https://github.com/jpurcallas/fm1-emu/pull/16). | No importar PCs ni direcciones RAM de REMINISCENT. |
| 2026-10-22 | BIOMECH → REminiSCENT | MÉTODO / prueba ISA | Validar contra el compilador JieLi la decodificación PI32v2 de instrucciones desconocidas antes de cambiar DSP. [PR #8](https://github.com/jpurcallas/fm1-emu/pull/8). | Aislar operación de CPU y comparar JIT ON/OFF con audio no nulo. |
| 2026-10-23 | BIOMECH → REminiSCENT | PENDIENTE | Reutilización de arranque CPU1/mailbox tras validación real. [PR #28](https://github.com/jpurcallas/fm1-emu/pull/28). | Exigir prueba de ejecución CPU1, intercambio de resultados, bloques a tiempo y preservación de audio, **antes de migrar el DSP**. |
| 2026-10-23 | REminiSCENT → BIOMECH | PROBADO (instrumentación Chrome) | Diferenciar PCM interno, commit a DMA, salida del AudioWorklet y retardo real de Chrome. A 200 MHz la salida contiene muestras no nulas pero no es continua en tiempo real. | Capturar y documentar cada etapa por separado en el firmware receptor. |

## 4. Puertas de adopción para CPU1

- **P1. Arranque real:** CPU1 entra a código propio, registra PC/estado y no cuelga CPU0 ni los periféricos.
- **P2. Mailbox real:** CPU0→CPU1 publica bloque/trabajo; CPU1 procesa y responde con ACK y resultados correctos; medir esperas y errores.
- **P3. Audio fiel:** un cambio de reparto mantiene, para el mismo estímulo, el audio esperado (comparación PCM bit-a-bit cuando la aritmética y orden lo permitan; documentar cualquier divergencia y verificarla auditivamente).
- **P4. Deadline real:** medir inicio, fin y bloqueo de ambos núcleos, instante de publicación y commit DMA, discontinuidades y excepciones.
- **P5. Portabilidad:** aplicar el mecanismo a REminiSCENT sin copiar lógica musical, sin reducir PARTS/efectos/patrón, e investigar la mejora o regresión sobre el FM-1 real.
- **P6. Emulador aparte:** medir tiempo de pared y saturación del AudioWorklet por separado; no imponer artificialmente este presupuesto como restricción musical del producto.

## 5. Registro cronológico — próximas entradas

> Añadir nuevas entradas por encima de esta línea, conservando las antiguas. Plantilla:

### YYYY-MM-DD — [BIOMECH | REminiSCENT] → [ambos] — [PROBADO | HIPÓTESIS | PENDIENTE | DESCARTADO]
- **Versión / rama / PR / commit:**
- **Experimento y configuración:** firmware exacto, MHz, JIT, estímulo, duración, PCM, CPU0/CPU1, DMA, Chrome/hardware.
- **Resultado reproducible:**
- **Qué no demuestra:**
- **Información que puede usar el otro proyecto:**
- **Próxima comprobación concreta:**

---
**Nota permanente:** Este archivo es una bitácora compartida, no una orden de fusionar código ni una prueba de que una optimización sonora funciona en hardware.