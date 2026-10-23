# BIOMECH 3 — Memoria V14, umbral operativo y bloqueo de integración

**Fecha:** 23 de octubre de 2026 · **Autor:** Yeti Fingers / laboratorio FM-1 · **ESTADO: ensayo de emulador; NO INSTALAR, NO MERGE.**

## Resultado contrastado

La ausencia de controles, MIDI y audio de BIOMECH 3 se **reproduce con el V14 original sin BIOMECH** al reservar memoria BSS adicional, dejando el heap igual al de la compilación BIOMECH. El gate previo `_MALLOC_SIZE >= 49152` NO significa que el SDK funcione; solo verifica un mínimo de enlace definido en el laboratorio.

| Variante con el V14 STOCK | Heap (`_MALLOC_SIZE`) | Callbacks control | MIDI externo | PCM |
|---|---:|---:|---:|---|
| Stock sin reserva adicional, 800 quanta | 247372 B | 228 | 1 | 86498 frames con señal |
| Stock + 65536 B BSS, 320 quanta | 181836 B | 88 | 1 | 25071 frames con señal |
| Stock + 98304 B BSS, 320 quanta | 149068 B | 88 | 1 | 25071 frames con señal |
| Stock + 131072 B BSS, 320 quanta | 116300 B | 88 | 1 | 25071 frames con señal |
| Stock + 163840 B BSS, 320 quanta | 83532 B | **0** | **0** | **0** |
| Stock + 185184 B BSS, 800 quanta | 62188 B | **0** | **0** | **0** |
| Stock + 195040 B BSS, 800 quanta | 52332 B | **0** | **0** | **0** |

Control de reproducción: mismas señales MIDI y teclado en el emulador PI32v2 200 MHz JIT OFF. Diferentes duraciones de prueba indicadas; comparar disponibilidad de servicios, no las cantidades PCM entre corpus distintos. En los fallos la CPU siguió ejecutándose y el emulador no notificó halt. La reserva cambia la distribución BSS además del heap; la frontera **observada** está entre 83532 y 116300 B, no es una especificación de hardware ni una garantía para todas las tareas/periféricos.

**Evidencia ejecutada:**
- [V14 stock original con callbacks](https://github.com/jpurcallas/fm1-emu/actions/runs/40030180676)
- [V14 stock con heap 62188/52332 B, ambos fallan](https://github.com/jpurcallas/fm1-emu/actions/runs/40031139423)
- [Barrido stock 83532–181836 B](https://github.com/jpurcallas/fm1-emu/actions/runs/40031378175)
- [Lote BIOMECH3 real: seis pistas intactas con heap 62188 B](https://github.com/jpurcallas/fm1-emu/actions/runs/40026572401)

**Consecuencia inmediata:** aumentar el heap de BIOMECH 3 desde 62188 B al menos **54112 B** para alcanzar los 116300 B ensayados positivamente en V14 stock; recomendable dejar margen por encima de ese umbral antes de llamar al candidato estable. Esta cantidad es recuperación RAM, NO autorización para reducir el motor.

## Auditoría de memoria enlazada (SDK original V14 + BIOMECH3 16f)

[Mapa real ELF + `nm -S --size-sort` + artefactos](https://github.com/jpurcallas/fm1-emu/actions/runs/40031886100).

- `_MALLOC_SIZE` 62188 B; `_ram0_bss_size` 363168 B.
- `CACHE_RAM_SIZE` 7 ways × 4096 = **28672 B**. `.cache_ram_data` 32 B, `.cache_ram_bss` **21360 B**. Margen nominal en cache **7280 B**; no asumir otras regiones ni introducir alias sin mapa/canary/cache-coherency.
- `SDRAM_SIZE=0` en el linker V14. No existe SDRAM utilizable por solo declarar una dirección.
- **Símbolos exactos destacados (ELF):** `effects` **115044 B** RAM0; `fm1_fx_states` **48832 B** RAM0; `runtime` **26308 B** RAM0; `br3_seg` **20556 B** RAM0; `factory_raw` **16384 B** RAM0; `shadow_engine` **21360 B** ya en caché; `snapshot` 7100 B RAM0; `pixels` 3840 B RAM0; `br3_blackbox` 1664 B RAM0.
- **`fm1_fx_states` es parte del SDK monolítico**, `libfm1_engine.a:engine_startup.S.o`, el **único miembro** de esa biblioteca. En el mismo módulo viven `fm1_engine_render`, `fm1_engine_pause`, `fm1_control_request`, `fm1_transport_bt_pcm`. [Propiedad exacta confirmada por `nm -A`](https://github.com/jpurcallas/fm1-emu/actions/runs/40032067048). El listado de símbolos externos no revela los accesos internos al bloque de FX: no afirmar que pueda borrarse sin riesgo.

El ensayo de eliminar `--whole-archive` recuperó **0 B** y no restauró control/MIDI ([A/B](https://github.com/jpurcallas/fm1-emu/actions/runs/40031664062)), precisamente porque el único miembro del archivo SDK sigue seleccionado por funciones esenciales.

## Hipótesis descartadas (en su alcance probado)

- Cortar temporalmente TODO el cálculo DSP BR3 disminuyó CPU0 de ~489M a ~44M instrucciones, pero **no** recuperó callbacks ([A/B carga](https://github.com/jpurcallas/fm1-emu/actions/runs/40030321306)). Por tanto, «CPU0 sobrecargada» no basta para explicar el defecto.
- Solicitudes repetidas de `fm1_control_request` (desde audio o control) no devolvieron llamadas sostenidas; **NO** usar llamada desde ISR en hardware sin documentar seguridad ([A/B scheduling](https://github.com/jpurcallas/fm1-emu/actions/runs/40029940762)).
- Reordenar `fm1_audio_start`, proseguir el init Groove y/o llamar al render del motor stock no recuperó callbacks con RAM restringida ([orden de arranque](https://github.com/jpurcallas/fm1-emu/actions/runs/40030806964)).
- Saltarse `biomech_sdk_init` no restauró los servicios con todo BR3 ya enlazado ([comparación](https://github.com/jpurcallas/fm1-emu/actions/runs/40030967354)).
- En una prueba controlada positiva el motor C99 original produce 89844 frames con señal al recibir una nota directa o por su cola MIDI interna ([CI 40027230994](https://github.com/jpurcallas/fm1-emu/actions/runs/40027230994)). El DSP, la cola y DMA pueden funcionar; el problema actual es arranque/servicios con presupuesto RAM insuficiente.

## Próximo trabajo de implementación, sin recortar DSP

1. Auditar referencias **internas** de `engine_startup.S.o` a `fm1_fx_states`, `fm1_transport_bt_pcm` y demás arrays monolíticos. Separar plataforma (OS, UART MIDI, panel, ALNK/DMA, BT, Flash, CPU1 SDK) de DSP Groove **solo tras verificar dependencias**, en branch/copia del SDK. Un `--defsym` hacia un buffer demasiado pequeño o PSRAM inventada sería corrupción de memoria, NO una solución.
2. Cuantificar qué estados de stock Groove son realmente inactivos durante BIOMECH y cuáles están ligados a inicialización; comparar mapas RAM y conservar el margen para callbacks del SDK. Evaluar reutilización de scratch con vidas disjuntas **demostradas**, o memoria física verificada, manteniendo datos, longitudes de delay/reverb y parámetros.
3. Alcanzar más de 116300 B de heap real, idealmente con margen adicional y verificaciones de stack/uso dinámico; compilar, empaquetar un `.fwsc` SOLO EMULADOR y comprobar **controles recurrentes + MIDI callback + nota en motor BR3 + PCM/DMA**. No promover un binario mudo.
4. Después, comprobar coherencia/capacidad a 100/200 MHz; la cesión segura de CPU1 y reparto 3+3 son objetivos **separados**, aún no aprobados para el hardware.

El principio **DISCUSIÓN LIBRE, EJECUCIÓN FIEL** aplica: originales de BIOMECH 2, REminiSCENT, SDK V14 y `master` intactos; todas las pruebas se realizaron en copias temporales de Actions y la rama experimental `experiment/biomech3-control-scheduler-a-b-20261023`. No ocultar ningún cambio que altere timbre o características.
