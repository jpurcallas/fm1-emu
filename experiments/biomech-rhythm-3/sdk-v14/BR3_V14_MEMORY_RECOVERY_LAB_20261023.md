# BIOMECH 3 / V14 — recuperación de memoria, ensayo ROM de fábrica y límites

23 de octubre de 2026 · Rama `experiment/biomech3-v14-memory-recovery-20261023` · **NO INSTALAR / NO MERGE**

## Consulta cruzada previa REminiSCENT
El PR #24 y PR #26 se leyeron **antes** de iniciar el ensayo. REminiSCENT v0.12 obtuvo en el emulador V14 **912/912 entregas DMA, cero deadline rechazos** para 24 mensajes MIDI y cuatro PARTS 2+2, después de optimizaciones algebraicamente equivalentes de efectos. Sigue usando un injerto CPU1 experimental no instalable; no se transfirieron offsets ni hook binario a BIOMECH. Fuentes: [PR #26, v0.12](https://github.com/jpurcallas/fm1-emu/pull/26#issuecomment-6375827047), [informe v0.12](https://github.com/jpurcallas/fm1-emu/blob/experiment/reminiscent2-v12-exact-fx-dma-20261023/experiments/reminiscent2-cpu1-portable/SDK_V14_DMA_EXACT_FX_OPT_v012.md).

## Hecho, compilado, ejecutado
Se construyó **únicamente en copia efímera de CI del SDK V14** un banco DX7 expandido en ROM en lugar del buffer BSS `factory_raw` de 16.384B. El algoritmo de descompresión original se ejecutó en build-time sin pérdidas, cotejado con el SHA256 de los 128 programas originales:

`ecad0b8620f9d784d46c8da1e3c5de02c40214649ed8dec218026431046aad25`.

Se compiló el C99 completo de seis pistas BIOMECH/FX/SEQ, se enlazó PI32v2, se empaquetó FWSC V14 y se ejecutó en el emulador con 800 quanta de inyección MIDI + teclas:

| Métrica | V14 + BIOMECH habitual | V14 + BIOMECH ROM diagnóstico |
|---|---:|---:|
| `_MALLOC_SIZE` | 62.188 B | **78.700 B** |
| Recuperación neta SRAM | — | **16.512 B** |
| Callbacks control | 0 | 0 |
| Callback MIDI | 0 | 0 |
| PCM externo no nulo | 0 | 0 |
| `dma_ok` | 791 | 791 |
| Halt | No | No |

**Hallazgo de seguridad:** el contador de la función `groove_fm_factory_raw` en el SDK huésped detectó **3 llamadas** aun bajo la aplicación BIOMECH; no suponer que el banco DX7 está completamente inactivo. Mover una fuente de datos a ROM podría causar lecturas durante programación de Flash y no queda validado para FM-1 físico. **No adoptar aún la variante ROM**; no modifica ningún archivo original, no reemplaza el motor BIOMECH, se preserva la alternativa SRAM.

- [CI ROM exacto + FWSC real 40033161570](https://github.com/jpurcallas/fm1-emu/actions/runs/40033161570)
- [CI ROM + contador de accesos 40033432334](https://github.com/jpurcallas/fm1-emu/actions/runs/40033432334)
- [Auditoría memoria V14 con mapa ELF 40031886100](https://github.com/jpurcallas/fm1-emu/actions/runs/40031886100)

## Límite restante y próximo gate

El menor heap V14 **STOCK** ensayado con audio, MIDI y pantalla fue 116.300 B. Con 83.532 B y menos V14 stock no los atendió en ese corpus. La variante ROM alcanza solo 78.700 B, y no resuelve el arranque musical. Aún faltan **37.600 B** para alcanzar el mínimo stock con funcionamiento observado y habría que sumar margen.

`fm1_fx_states` (48.832 B) es un símbolo local del módulo monolítico `libfm1_engine.a:engine_startup.S.o`; comparte ese módulo con servicios SDK, por lo que `--no-whole-archive` no recupera memoria. El hecho de que el compilador muestre cero relocaciones simbólicas externas a ese estado **NO** demuestra que el SDK jamás lo lea o escriba internamente; no se permite solaparlo con efectos BIOMECH sin trazas completas.

Próximo paso conservador: capturar **lecturas y escrituras reales** del intervalo de RAM de FX heredados por ambos CPU, con JIT OFF, en boot/UI, MIDI, audio, Flash/BT si es emulable; antes de estudiar reutilizarlo o dividir el objeto SDK. La aceptación exige recuperar el espacio físico con memoria y coherencia verificadas, restaurar callbacks MIDI/control y PCM/DMA bajo firmware real, y conservar las seis pistas y FX exactamente. No aplicar un patch binario cooperativo CPU1 de REM a BIOMECH.

**Estados:** optimización ROM construida y probada como LAB; banco byte exacto; recuperó 16.512 B; acceso fábrica 3; seguridad Flash desconocida; firmware musical controlable NO recuperado; CPU1 3+3 V14 NO aprobado. Madres SDK, BIOMECH, REminiSCENT y `master` intactas.

## Comprobación adicional: región SDK FX en RAM huésped (candidatos originales y ROM)

Se implementó y ejecutó `trace_v14_fx_ram.mjs`, que localiza `fm1_fx_states` mediante el mapa de símbolos PI32v2 de cada build y comprueba sus **48.832 bytes** tras cada quantum de render V14, JIT OFF, con notas MIDI y controles físicos inyectados. La traza reporta modificación de **8 bytes** en ambos candidatos:

| FWSC | Dirección enlazada de `fm1_fx_states` | Modificaciones observadas | Frames renderizados | Halt |
|---|---|---:|---:|---|
| BIOMECH 3 sin cambios | `0x01C4F6A0` | 8 | 793 bloques | No |
| Variante ROM experimental | `0x01C4B620` | 8 | 793 bloques | No |

En ambos casos la huella RAM pasó de `c3759cc5` (inicialmente cero) a `bdbda7fd`. Es evidencia de actividad real del SDK en una región etiquetada como estado de efectos heredados. No afirma qué función produjo la escritura, y tampoco demuestra que las otras 48.824 posiciones jamás se lean. Por tanto se descarta **solapar todo el bloque** con `effects` de BIOMECH sin instrumentación de lecturas/escrituras por CPU0/CPU1 y garantía de no interferencia. No se tocaron ni deshabilitaron los efectos de BIOMECH.

- [BLACK BOX FX RAM del firmware original — CI PASS](https://github.com/jpurcallas/fm1-emu/actions/runs/40033782232)
- [BLACK BOX FX RAM de ROM experimental — CI PASS](https://github.com/jpurcallas/fm1-emu/actions/runs/40033761181)
- [Código de comparación de RAM, JIT OFF, símbolos por ELF](https://github.com/jpurcallas/fm1-emu/blob/experiment/biomech3-v14-memory-recovery-20261023/experiments/biomech-rhythm-3/sdk-v14/trace_v14_fx_ram.mjs)

**Situación:** 16.512 bytes recuperados experimentalmente pero no aprobados por seguridad Flash; no se han recuperado los 37.600 bytes restantes ni restaurado entrada musical externa. Se requiere ingeniería de servicios y memoria verificable, no un alias de bloques.
