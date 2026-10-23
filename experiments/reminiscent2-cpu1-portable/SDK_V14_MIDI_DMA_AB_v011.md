# REminiSCENT 2 LAB v0.11 — MIDI y DMA: A/B con dos FWSC de un mismo ELF V14

**2026-10-23 · SOLO EMULADOR · NO INSTALAR · NO MERGE.** Revisión de PR #24 y #26 efectuada antes de comenzar. BIOMECH aisló antes un problema de entrega MIDI/control a su propio DSP, no un DSP mudo; el análisis sirve de metodología, pero no se copiaron algoritmos ni direcciones.

## Qué se hizo realmente

- Partiendo de fuente v0.10 cooperativa, se añadió una sonda **RX/cola/aplicación MIDI** a `rn_hw_commands.c` y una huella FNV32 de los **256 enteros PCM tras `fm1_output_mix`, antes de copiar DMA** dentro de la ISR de audio. Las 4 PARTS, sonidos, secuenciador, filtros, efectos y rutinas musicales quedan sin sustitución.
- **Dos FWSC de UN MISMO ELF**: SERIAL deja intacto el CPU1 SDK; COOP redirige **solo una llamada de seis bytes** en una imagen temporal del SDK hacia el wrapper que primero ejecuta el servicio SDK original y después PARTS 3–4. El código C99 y su distribución son iguales en ambos. Esto no es una cesión segura de CPU1; intervención binaria exclusivamente de laboratorio.
- **Regresión descubierta y corregida:** al introducir la instrumentación el enlazador desplazó la función privada SDK. v0.10 dependía de una dirección absoluta hardcodeada; al moverla, COOP se detenía. v0.11 reemplaza esa dependencia por un puntero en RAM inicializada al que el empaquetador aplica el destino verdadero obtenido de **símbolos del nuevo ELF**, tras verificar opcode y destino de la instrucción original. Un intento inicial de referenciar directamente el símbolo desde C **falló al enlazar** (símbolo privado del SDK); no declararlo una API soportada. `master` y originales sin modificaciones.

## Ejecutado: dos escenarios, 950 quanta a 200 MHz, PI32v2 JIT OFF

| Medida | SERIAL sin MIDI | COOP sin MIDI | SERIAL con 24 notas MIDI | COOP con 24 notas MIDI |
|---|---:|---:|---:|---:|
| Renders CPU0 | 912 | 912 | **459** | **912** |
| Copias DMA efectivas | **912** | **912** | **88** | **760** |
| Rechazos deadline | 0 | 0 | **145** | **152** |
| Rechazos propiedad DMA | 0 | 0 | **226** | **0** |
| Overruns del firmware | 0 | 0 | **823** | **152** |
| Pico ticks, carga MIDI | — | — | **753.225** | **501.362** |
| CPU1 trabajos completos | 0 | 912 | 0 | 912 |
| Estado CPU halted | no | no | no | no |

Plazo declarado por R2TB: **487.420 ticks**; reloj reportado por SDK **192 MHz**, distinto del selector 200 MHz del emulador. La variante COOP recupera mucho DMA bajo MIDI, pero **152 pérdidas por plazo son un fallo de continuidad**, y su pico excede plazo. No es aún firmware tiempo real certificado ni más seguro físicamente.

En el corpus MIDI se enviaron **tres rondas NOTE ON/OFF × cuatro canales** (24 mensajes) al transporte real del firmware, no al C99 directamente. Ambas variantes **recibieron y aplicaron los 24 mensajes** (contadores y eventos de recepción/consumo del guest). La secuencia completa no pierde notas por falta de recepción, sino porque la ruta serial queda atrás en su capacidad de producir/cerrar bloques. Por ejemplo, el último grupo MIDI se aplica en el render **363** serial vs **616** cooperativo en la cronología de las 950 solicitudes del emulador.

## Paridad sonora y explicación de la divergencia WAV

- Las dos imágenes empiezan con **desfase de tres bloques de 128 frames**, ya medido desde v0.10. Para aislar DSP se comparó `serial_render[n+3]` con `coop_render[n]`, y se retrasó el envío MIDI de SERIAL tres quanta en el ensayo A/B, de forma **explícita** para alinear el evento musical. No equivale a un test de mismo timestamp absoluto host.
- FNV32 del buffer PCM producido por DSP dentro de ISR **ANTES de `fm1_output_mix`**: coincidencia en ventana del primer NOTE ON ensayada en pasada independiente.
- **DESPUÉS de `fm1_output_mix`**: los **144/144 bloques n=30…173** coinciden para corpus sin MIDI, y también **144/144** para corpus con NOTE ON, tras alineación de +3. Un hash FNV32 no es un dump PCM byte-a-byte; esta es una prueba de *huella de bloque* repetible, no una certificación universal de paridad.
- La salida de audio del **host emulador** ya no coincide después del primer MIDI, porque pierde/copía diferentes cantidades de bloques: SERIAL **88** vs COOP **760** copias. No declarar que el WAV entero coincide ni esconder bloques perdidos alineando muestras arbitrariamente.
- Contadores R2TB extraídos desde memoria huésped usando los símbolos `r2_box`/`statistics` del ELF exacto, no offsets de otro build. Tampoco confundir render guest con llamada `fm1_render` del host.

## Artefactos y límites

**Paquete verificable (85 archivos, ZIP íntegro):**
`REminiSCENT2_v0.11_MIDI_DMA_BLACKBOX_AB_SOLO_EMULADOR_NO_INSTALAR.zip`, SHA256
`a810afcd3886076a66dab61b870da89bc57c9952fd2dde047bc1770a1080637a`.
Incluye dos FWSC y sus fuentes, scripts de compilación/patcheo, emulador WASM fijado, capturas JSON/PCM RAW (4 corpus), trazas MIDI y README. ZIP se entregó como artefacto de conversación; **no** se subió código/binario de SDK completo al repositorio ni se hizo merge.

**Firmware SERIAL diagnóstico:** SHA256 `5b30c0ba17c085343006395698cd153117702e0ce9031def6ea63f1980b7c42c`.
**Firmware COOP diagnóstico:** SHA256 `ff478de98d9dee67e905e86dad642097f4f873865151fb15925093dce7992244`.
Son copias no instalables, **NO** versiones musicales aceptadas.

**Lo pendiente:** 1) medir/reducir las 152 pérdidas DMA en carga musical sin recortar funciones; 2) asegurar servicio CPU1 original del SDK bajo flash/BT/USB y coherencia/caché/quiescencia; 3) encontrar integración oficialmente compatible con propiedad del núcleo para FM-1 físico; 4) probar bancos acústicos auténticos, MIDI completo y continuidad real. La solución offline permite escuchar música auténtica pero NO arregla plazos DMA.

**Protecciones:** firmware madre v3.0.23, v0.6, v0.7, v0.8, v0.10 y `master` intactos. NO MERGE.
