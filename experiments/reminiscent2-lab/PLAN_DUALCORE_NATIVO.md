# REminiSCENT 2 — LAB: plan operativo CPU0 + CPU1 nativos
**22 octubre 2026 | EXPERIMENTO SOLO EMULADOR | NO INSTALAR | NO MERGE A MASTER**

## Decisión del autor y objetivo

Probar deliberadamente una arquitectura propia para los **dos núcleos PI32v2 del FM-1**, prescindiendo del **servicio de coordinación y de arranque de CPU1 del SDK**, pero reutilizando las piezas de inicialización y periféricos imprescindibles en CPU0 hasta que exista un reemplazo probado. No significa borrar a ciegas todo el SDK. El experimento puede fallar: **cada fallo debe producir evidencia diagnóstica**, no meses de conjeturas.

**Objetivo verificable:** un nuevo firmware `.fwsc` identificable como REminiSCENT 2 LAB arranca en el emulador, CPU1 ejecuta **código propio y luego una tarea del sintetizador real**, CPU0 continúa con interfaz, eventos y audio, y ambos cooperan cumpliendo plazos de DMA. No se anuncia rendimiento mejorado sin medición de tiempos y continuidad. No se instalará en FM-1 físico sin decisión posterior del autor.

## Estado de partida verificado el 22-oct-2026

- Rama exclusiva: `experiment/reminiscent-2-lab-cpu1-libre-20261022`; punto de partida del emulador `master` en `61b51596d5756d09902fc16cc5e0ecd550d4501e`; esa referencia permanece intacta.
- REminiSCENT madre **v3.0.23**: SHA-256 declarado y verificado anteriormente: `8409b8fec212cdeb7ac36b8a9576db74ebfe4e77d0100b59430a891260313467`. No modificar ni sobreescribir ese firmware.
- Ya existe `dualcore_host_poc.c`: **256 bloques / cuatro PARTS simuladas / PCM serial-paralelo exacto en host**. Es un arnés con render sustituto: **no** constituye prueba de firmware, de CPU1 real, de DSP de REminiSCENT ni de continuidad.
- El archivo `REminiSCENT_2_LAB_INICIO_20261022_NO_INSTALAR.zip` contiene el **FWSC binario**, WAV y la prueba host, **no el código fuente completo, los objetos PI32v2 ni el enlazador de la compilación nativa**. Primero localizar y verificar el árbol de construcción exacto de v3.0.23 / SDK V14. Si no está, esto es un bloqueo de integración real, no una razón para fabricar un FWSC renombrado.
- Cerradas las observaciones previas de ACK y JIT; no volver a abrirlas como investigación general. Su utilidad aquí es como controles de arranque, NOTE OFF, audio y DMA. La diferencia entre teclado y MIDI sigue como **regresión funcional a observar**, no como dependencia para intentar CPU1 propio.

## Arquitectura de la apuesta

```
CPU0                                      CPU1 (entrada/stack/espera propios)
-----                                     ---------------------------------
boot y periféricos esenciales            arranque temprano, PC guard y pila
MIDI + teclado + 4 pistas y secuenciador  espera en RAM, sin scheduler del SDK
estado global, RNG, asignación voces      espera job_seq
snapshot inmutable de 4 PARTS   ------>   render de PARTS asignadas
render de las otras PARTS                  buffer y estado exclusivos
espera acotada / lee done_seq    <------   done_seq con barrera
mezcla ORIGINAL en orden 1,2,3,4
BLEND / envíos / efectos compartidos
máster -> DMA, contadores de plazo
```

No migrar a CPU1 los eventos, el RNG global, las colas MIDI, el secuenciador, la interfaz ni el mezclador hasta demostrar que son independientes. Si el render de una PART utiliza tablas, temporales o RNG compartidos, separar ese estado o mantener esa sección serial. El render serial permanece como **referencia de sonido**, no como recorte funcional.

**Protocolo nativo mínimo**: una casilla de trabajo y un contador monótono `job_seq` escritos por CPU0; una respuesta `done_seq` escrita por CPU1; buffers independientes; parámetros publicados antes del contador y leídos después con barreras de memoria PI32v2; sin malloc/printf en interrupciones. Verificar en emulador y luego en dispositivo la visibilidad de caché/alineación. Usar un único escritor por bandera. Evitar que CPU0 modifique la entrada hasta que CPU1 confirme; no liberar ni reutilizar buffers ante un timeout sin confirmar que CPU1 quedó estacionado.

**Riesgos del arranque**: el SDK vigente YA emplea CPU1. En LAB se debe impedir *su* arranque previo o reemplazarlo explícitamente, no arrancar dos servicios incompatibles en el mismo núcleo. Partir de una sola ruta de boot, antes de audio/timers; pila de usuario y de excepción propias; retorno `rti` y límites de PC; bucle de espera en sección ejecutable copiada a RAM, incluida realmente en la imagen. El arranque/código en flash, el guard de PC y la escritura de flash necesitan disciplina de estacionamiento del segundo núcleo. Son condiciones observadas en implementaciones públicas de X0X/ChoralRoot; **direcciones y linker deben verificarse en nuestro binario**, no copiarse sin comprobación.

## Caja negra: registrar *por qué* falla

Crear dos anillos de trazas en RAM reservada (uno escrito por cada núcleo, sin contención), más un lector externo del **emulador** que pueda volcarlos incluso si el firmware entra en bucle. Estructura fija, sin asignación dinámica, cada registro con `build_id`, `evento`, `ciclo/timer`, `núcleo`, `PC`, `SP`, `job_seq`, `done_seq`, `dma_half`, `audio_late`, `checksum` y bandera de desbordamiento. Eventos: `BOOT0`, `C1_START`, `C1_ALIVE`, `ISSUE`, `C1_BEGIN`, `C1_DONE`, `JOIN`, `DMA_PUBLISH`, `TIMEOUT`, `PC_GUARD`, `FAULT`, `FLASH_PARK`, `REBOOT`.

Cuando haya bloqueo, guardar también **las últimas ventanas PC de ambos núcleos y el último job válido** mediante instrumentación del emulador; no fiarse de que el LCD o USB sigan funcionando si CPU0 cae. Snapshot + descripción automática: *último paso bueno / primer evento faltante / contador de pérdidas DMA / hash PCM hasta el fallo*. RAM **no garantiza** conservación tras corte de energía; durante las pruebas se extrae por emulador. **No escribir logs en flash en mitad del ISR** ni tocar sectores de presets.

**Prueba de que la caja negra funciona:** inyectar un trabajo de CPU1 deliberadamente bloqueado en LAB, verificar que aparece `TIMEOUT` con PC/counters de ambos núcleos, que el emulador sigue recuperable y que la madre produce el mismo sonido que antes. Si falla el propio registro, arreglarlo antes de portar DSP.

## Ejecución por cortes, con una decisión al final de cada uno

| Corte | Cambio que sí hacemos | Prueba decisiva / salida | Si falla |
|:--|:--|:--|:--|
| **0 · Conservar y construir** | Inventario del fuente C99 real, enlazador, SDK V14, mapa, build reproducible, baseline de v3.0.23. Configuración LAB con etiqueta visible. | Original reproducible y sus SHA; relación fuente→imagen verificable. | Reportar pieza exacta ausente; no producir binario ficticio. |
| **1 · CPU1 rebelde** | Deshabilitar reemplazo de CPU1 por SDK solo en LAB; entrar a nuestro código, pilas y espera RAM; CPU0 conserva audio serial. | En emulador: `C1_ALIVE` auténtico, PC CPU1 en bucle propio, C4 audible sin nuevos underruns. | Volcar boot/PC/SP y decidir: límite PC, startup, pila o competencia SDK. |
| **2 · Protocolo y avería provocada** | `job_seq/done_seq`, tarea pequeña de checksum ejecutada de verdad por CPU1 y traza fija; prueba de timeout forzado. | Prueba válida de ida/vuelta nativa, reporte diagnóstico en fallo, CPU0 publica audio intacto. | Corregir orden de memoria, stack, visibilidad y estacionamiento. |
| **3 · Una PART real** | Mover **el render íntegro de una PART real** a CPU1; las otras tres siguen en CPU0. Conservar efectos y mezcla. | Comparación PCM serial / paralelo de los mismos presets y eventos; WAV A/B y medidas de bloque, jitter, DMA. | Identificar **primera** dependencia compartida; revertir solo ese corte. |
| **4 · Cuatro PARTS completas** | Buscar reparto 2+2 o adaptativo en función del bloque sin alterar timbres, granos ni voces; RNG y preparación permanecen seriales. | Peor bloque incluyendo preparación, comunicación, espera, mezcla, FX y copia; cero dropouts durante escena de estrés. | Repartir de otra manera; no reducir instrumento. |
| **5 · Robustez** | Secuenciador 4×64, NOTE OFF MIDI/teclado, LFO, BLEND, granos, delays/reverb, presets, almacenamiento y fallos simulados. | Soak en emulador sin fallos, comparación audible aprobada por el autor, mapa de SRAM/flash y margen de CPU documentados. | Etiquetar LAB no aprobado; original permanece operativo. |

## Instrumentos de aceptación (no confundirlos)

- **Se ejecutó CPU1**: no basta `ACK`. Exigir PC/stack CPU1, contador de trabajos y checksum generado por código nativo.
- **Se conservó la música**: cuatro PARTS reales, motor completo, 16 fuentes, secuenciador y efectos; pruebas de NOTE OFF, preset y automatización. Igualdad PCM bit por bit cuando procede; cualquier diferencia intencional se documenta y escucha.
- **Se ganó velocidad**: misma imagen de firmware base, mismos presets/eventos/carga, misma frecuencia y configuración emulada; comparar tiempos `prepare + max(CPU0, CPU1 incl. espera) + mix + FX + DMA`, peor bloque y percentiles, mitades perdidas, continuidad y latencia. **Sólo** declarar mejora si hay margen y no aparecen discontinuidades. Las cifras de otro firmware (p.ej. 2,90 ms BIOMECH o ~11,61 ms X0X) **no** sustituyen el presupuesto propio de REminiSCENT.
- **Se puede oír**: después de **dos pasos técnicos significativos como máximo**, entregar el primer `.fwsc` LAB que realmente compile y arranque en el emulador, con WAV A/B o enlace de emulador. No encadenar semanas de métricas sin escuchar. Si solo existe prueba no audible, reconocerlo.
- **Se puede volver atrás**: binario madre intacto; cambios exclusivos en LAB; build IDs distintos; comparar `master` antes/después; backup de flash/patches antes de cualquier futuro hardware. **No instalar LAB en FM-1 real sin autorización explícita y ruta probada de recuperación**: el archivo digital es recuperable, pero un fallo del bootloader o una escritura errónea de flash sí puede dejar el equipo inaccesible.

## Primera acción autorizada por este plan

Recuperar árbol real de REminiSCENT v3.0.23 y mapa de enlace; crear `lab_fault_trace` (RAM + volcador del emulador), agregar una **entrada CPU1 nativa** aislada y un selector de compilación `REM2_NATIVE_CPU1`. En el primer corte, arrancar CPU1 *sin tocar el DSP*. En el segundo, enviarle un checksum y provocar un timeout controlado. En el tercero, trasladar la primera PART real. **No volver al estudio general del ACK ni a reoptimizar JIT como prerequisito.**

## Referencias de diseño, no dependencias de código

- X0X: https://github.com/charlesvestal/fm1-x0x/blob/main/docs/plans/2026-10-04-dual-core-and-clock.md (boot temprano, PC guard, pilas, RAM y flash parking; medición de espera real).
- ChoralRoot: https://github.com/Quixotic7/ChoralRootFM1/blob/main/docs/DUALCORE.md (control serial de eventos/RNG, jobs por bloque, efectos, fallback y trazas).
- Clipper: https://github.com/isod89/clipper-fm1 (reparto de voces, PCM, estrés y métricas).
- Resultados previos: REminiSCENT JIT/ACK/RELEASE solo como controles; BIOMECH como receptor posterior de hallazgos, **sin copiar offsets entre imágenes**.

**Estado actual: plan y prototipo host existentes; NO hay firmware nativo REminiSCENT 2 compilado ni mejora de audio probada.**
