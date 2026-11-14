# LAB24 — DSP integrado: WHITE/PINK, SPREAD, FILTER ENV, KEY TRACK

**Prioridad actual del autor:** punto 2, conectar todos los DSP antes mostrados como pendientes. Sin reducir 11 pantallas. No se integra MOD WHEEL. ACOUSTIC NOISE pasa a ser elección **WHITE/PINK**, tal como indicó expresamente el autor.

## Origen, alcance
- Rama `work/reminiscent-mpc-integracion-20261113`, PR #31; inicio de esta intervención `cb676c562801ac7e2ac67942abeb66c4754a5305`.
- Acuerdos vigentes y comentarios del PR consultados antes de editar. Referencia acústica aprobada Bridge16 y banco LAB19 de 27 fuentes/254 WAV; no modificar el material PCM ni integrar Bridge17.
- Cambios en motor y plugin SDK en esta rama, nunca en `master`.
- Los 4 parámetros GUI previamente sin DSP usan sus índices y valores ya guardados: noise 105, spread 106, filter env 107 y key track 108. WHITE/PINK se añade **al final** de la lista de 124 parámetros existente, índice 124 (125 en total), para no renumerar los anteriores.

## Implementado en C++ (fuentes, no simulación)
1. **ACOUSTIC NOISE:** síntesis procedural por voz (independiente de oscilador, muestras y otra generación de ruido), WHITE pseudorrandom y PINK mediante 16 filas Voss–McCartney. Nivel `params.acousticNoise` 0..127; selector `ui.acousticNoiseType` WHITE/PINK. Nivel por defecto cero deja material aprobado intacto. Se suma sobre A/B antes del ADSR.
2. **OSC SPREAD:** descorrelación de fase entre L/R para el oscilador. El valor guardado 64/127 es neutro (estéreo OSC no afectado).
3. **FILTER ENV:** envolvente ADSR principal de voces activas modulando frecuencia de corte del LPF compartido. Profundidad bipolar; 56/127 es neutro, como estaba guardado.
4. **KEY TRACK:** centro de altura de notas activas ponderadas por envolvente/velocidad modifica el corte relativo a C4. 64/127 es neutro, como estaba guardado.

Fuentes GitHub:
- `engine.hpp`: `e618a86cbe6cdf5050a5f2170b9c90a2584c7d2f`.
- `engine.cpp`: `45956f70209c3f62b1ee98d87476c9250ff6e6af`.
- `REminiSCENTMPC.cpp`: `d692d02c475ab893e0b87c05845bea2e578d0ef0`.
- `skins/TUI.json` WHITE/PINK botones: `13b2321a6d14f3790f0d3e3bbf499f161089b86a`.
- Manifiesto de **58 recursos privados** (54 anteriores + 4 botones): `1dcc12f665137bbf051afb700e3b2dea9e65706f`.

## Prueba concreta y evidencia (host nativo, no MPC One+)
- Compilación nativa de host local con LAB24: completada.
- Prueba de señales ejecutada con **254 WAV reales**, notas MIDI; audio numéricamente finito:
  - WHITE vs sin ruido RMS(diff) = `0.024228`.
  - PINK vs sin ruido RMS(diff) = `0.014089`.
  - WHITE vs PINK RMS(diff) = `0.027974`.
  - OSC SPREAD neutral estéreo 0.000000000, expandido `0.081489` y polaridad opuesta `0.082783` (RMS diferencia estéreo).
  - FILTER ENV diferencia frente a neutro `0.035828`; KEY TRACK diferencia `0.018112`.
  - Resultado prueba DSP focalizada: `PASS DSP 4 functions and WHITE/PINK choice`.
- Fuente de esta regresión está en `LAB23/tests/test_dsp_lab24.cpp` commit `23568154a3bd2603e18d0e53d51da1b0e3c9a7ad`.
- **Advertencia honesta:** host_sim VST completo corrido en el mismo ambiente LAB24 produjo `17 PASS / 1 WARN / 6 FAIL`, por **parámetros de telemetría gráfica 118-121 y reloj Solaris 123 que no retornan byte idénticos tras setChunk**. No es un fallo demostrado de los cuatro DSP nuevos; sí impide declarar completo el plugin o aprobación del guardado. Debe resolverse antes de entrega. No decir 19/0 para esta versión.
- No hubo prueba de hardware MPC; no hay ARM32 LAB24 compilado.

## Recursos privados
- ZIP integral de **58 PNG, manifiesto y README**, archivado en Biblioteca privada en `/REminiSCENT MPC/REminiSCENT_LAB24_58_PNG_WHITE_PINK_PRIVADO.zip`.
- Tamaño `10.888.047` bytes, SHA256 `5be0b82bb5ef0963dc34ef7d2fa74f64766b330d30a6a10747048ef973242351`, integridad ZIP OK, 58/58 rutas y hash SHA256 de PNG correctos.
- No se publicaron muestras PCM ni arte binario privado en GitHub.

## Estado y siguientes puertas
DSP focalizado: **implementado, compila y presenta diferencias audibles en host**, NO probado en hardware, NO aprobado por el autor todavía. La versión del plugin completa sigue pendiente de corrección de estado de telemetría visual, paquete ARM32 actualizado, 11 tabs táctiles/Data Wheel/Q-Links y prueba MPC física. No alterar sonido original ni poner un limitador no aprobado.
**NO MERGE. No pedir al autor descargar/probar builds parciales.**

## Resolución posterior — restauración de la interfaz (LAB24)
El resultado anterior de `17 PASS / 1 WARN / 6 FAIL` **queda superado por una corrección nueva, no borrado del historial**.
- Causa comprobada: el SDK restaura todos los parámetros correctamente, pero el primer bloque después de `effSetChunk` llamaba `reset()` y luego `advanceVisuals()`. Eso sobrescribía LFO (118–119), MEMORY (120–121), y Solaris (123); `reset()` reiniciaba Solaris.
- Implementación: `REminiSCENTMPC.cpp`, commit `91eefee02d28819451d52d05bcb3efd67572ae65`. Añade marcador de extra-state `VI1` al chunk VST2 y un *hold* de la **telemetría exclusivamente visual** tras cargar un proyecto. El motor se resetea como pide el SDK, pero no sobreescribe la instantánea visual durante silencio. En la siguiente nota real se reanuda la actualización y Solaris se salta porque es presentación de arranque, no de recuperación de proyecto. Las 125 identidades de parámetros, los 4 DSP LAB24 y el banco de 254 WAV no se modificaron.
- Prueba de simulador nativo ejecutada en 44.1 kHz / 128 frames / 254 WAV: **19 PASS / 0 WARN / 0 FAIL**. Los **125/125** parámetros recuperados y `effGetChunk → effSetChunk → effGetChunk` **idéntico byte por byte (3205 bytes)**. Se conserva en local el log `host-sim-lab24-state-fixed.log`.
- Prueba dirigida ejecutada: instantánea preservada después de 20 bloques silenciosos, reanudación al recibir nueva nota MIDI y Solaris en estado DONE (PASS ambos). Fuente de regresión en GitHub: `tests/test_state_resume.cpp`, commit `66f02df729b8561dfab61096ef46661fdfc33345`.
- **Límite:** probado con código nativo host Linux, no compilado en ARM32 LAB24 ni probado en MPC física. Las imágenes y su render SDK tampoco quedan certificados por este arreglo. Los proyectos de una edición preliminar sin marcador `VI1` siguen siendo cargables por el SDK pero no tienen el nuevo bloqueo de instantánea visual; no afirmar fidelidad retroactiva byte a byte para esos chunks.
