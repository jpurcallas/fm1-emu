# REminiSCENT 2 LAB v0.10 — CPU1 musical real dentro de V14 emulado, SDK cooperativo experimental

**2026-10-23, NO INSTALAR / NO MERGE.** El FM-1 físico es el objetivo. Esto es un experimento sobre una **copia del BINARIO enlazado del SDK V14**, NO una cesión oficial ni una prueba de seguridad de hardware. No modificar SDK original, madres v0.6 / v0.7 / v0.8 / v3.0.23 ni `master`.

## Cruce PR antes de experimentar

- BIOMECH 3 [PR #26](https://github.com/jpurcallas/fm1-emu/pull/26#issuecomment-6375079227) ahora produce audio real en SDK V14 al disparar una nota directamente, pero controles MIDI/panel aún no entregan eventos musicales. Ese resultado **obliga a separar** motor, transporte y DSP; no da a REminiSCENT propiedad de CPU1.
- Las BLACK BOX del autor en REM v0.7 mostraron CPU1 ejecutando código interno de SDK. Análisis posterior del *ELF real* v0.8 y `libfm1_engine.a(engine_startup.S.o)`: la rutina local `fm1_r_2c729ca92be9` llama en un lazo a `fm1_r_e7d3da61dac2`, que atiende `exchange` y `fm1_flash_worker_prepare`. No es un API público de trabajos DSP.
- En **v0.9**, firmware V14 con observador de IPC de SDK (solo lecturas; direcciones verificadas contra linker): compiló, arrancó emulado 200MHz, **1.212 renders/1.212 copias DMA en 1.250 quanta**, 0 rechazos, 0 halt, audio PCM bit-exacto v0.8 en 420 quanta; señales de solicitud/ACK estables en el corpus. No presupone un lease.

## v0.10 — intervención estrictamente en COPIA de firmware / trabajo REAL CPU1

**CAMBIO NO SOPORTADO EN SDK, SOLO EMULADOR:** en el ELF nativo V14 PI32v2 original enlazado con DSP, la llamada SDK CPU1 de `fm1_r_2c729ca92be9` en **0x01C0C56E** apuntaba al servicio SDK en **0x01C0C4C4** (`80 ff 50 ff ff ff`). En una copia *postlink*, únicamente esa llamada de 6 bytes se redirigió a `rn_cpu1_service_wrapper` en **0x01C060EC** (`80 ff 78 9b ff ff`). El wrapper ejecuta **primero** la rutina original del SDK y **después**, si hay una tarea firmada de nuestro buzón, `rn_dc_cpu1_part34` (PARTS 3–4) y publica ACK. CPU0 mantiene prepare, PARTS 1–2, FX global y DMA. Este injerto NO equivale a un handoff oficial, NO fue aprobado por SDK y **podría interferir los servicios del hardware real**, incluso si las pruebas musicales pasan.

**COMPILADO/EMPAQUETADO:** SDK Open V14 y compilador JieLi PI32v2 r3 de referencia, **aplicación 430.096 B**, margen app 23.825 B. FWSC **SOLO EMULADOR / NO INSTALAR** SHA256 `efbe441732a093810c8e972937ff515bf3f0ba5f1385af00854139fccc5f7374`, longitud 1.069.620 B.

**EJECUTADO, 200MHz PI32v2 emulado, JIT OFF:**
- 420 quanta PLAY: 382 renders, 382 DMA copies, 358 con señal, 0 ownership/deadline rejects, 0 halted; pico de render **391.120 ticks** (frente a 434.635 ticks v0.8, corpus diferente en instante inicial; valor favorable pero NO garantía de rendimiento físico). Plazo declarado 487.420 ticks.
- 1.250 quanta PLAY: buzón RAM huésped leído directamente por símbolos ELF, **1.212 aceptados / 1.212 completados**, fault=0, timeout=0, alive=`0xC10AC0DE`, lease cooperativo LAB=1 (NO SDK-approved), halted=false. El código DSP 2+2 musical real se ejecutó en el segundo núcleo.
- El inicio de audio aparece **3 bloques de 128 frames antes** que en v0.8, por desplazamiento de planificación inicial. Los archivos PCM RAW no son idénticos sin alinear. **Después de alinear exactamente 3 quanta, 159.616 frames estéreo Float32 son iguales BYTE POR BYTE**, 0 diferencias. Equivalencia de las muestras del DSP en esta secuencia automática, no equivalencia de todo el sistema.
- **Prueba MIDI de cuatro canales:** se enviaron NOTE ON/OFF en canales 0–3 durante la emulación; los binarios permanecieron vivos y el coprocesador aceptó trabajos. Después del primer evento, el PCM serial/coop **NO** es byte-idéntico ni tras alinear arranque o ajustar 3 quanta las entradas host. Puede existir desfase de planificación MIDI/RTOS, pero no está demostrado que esa sea la única causa; **la fidelidad MIDI sigue pendiente**.
- Reproductor diferido autónomo HTML de esta versión: test Node/WASM 4 s = 176.512 frames, 168.254 no nulos, pico 0,2714, WAV correcto. **Aún no escuchado por autor en Chrome.** Audio diferido no certifica tiempo real.

## Limitaciones antes de elevar esto a firmware real

1. Binarización modifica una llamada de SDK sin documentación oficial. No sabemos si `fm1_flash_worker_prepare` y otros servicios siguen cumpliendo todos sus plazos bajo carga/flash/BT/USB. El hecho de que la rutina original se invoque no basta.
2. La comunicación utiliza `csync` y un buzón compartido: **no** equivale a certificación de cache coherency, quiescencia, exceptions ni conducta en el FM-1 físico. Mantener fail-closed al vencer espera; el firmware no es instalable.
3. La diferencia temporal MIDI no está resuelta. Repetir la estrategia BIOMECH: instrumentar recepción real, colas de evento y disparo DSP ANTES de atribuir divergencia a síntesis.
4. No hay ensayo físico FM1 ni paridad de todos presets, 4 timbres, memoria acústica con bancos reales y efectos bajo carga.

## Evidencia recuperable del autor

Paquete de conversación `REminiSCENT2_v0.10_CPU1_V14_COOPERATIVO_LAB_SOLO_EMULADOR.zip`, SHA256 `37e7604ce1d5def8975886d24fff225e4f3dbe1321f67e1d1237f360c6844b88` (85 entradas; fuentes C99, pruebas, script de injerto, map, imágenes y HTML; SDK/binario del fabricante completo no incluidos). Reproductor autónomo `REminiSCENT2_v0.10_REPRODUCTOR_DIFERIDO_COOP_SOLO_EMULADOR.html` SHA256 `cfa8c23da9eabb40b317ae3f582643a8ef879a933ebc3660c83d3d6dd0e77912`. Binarios del autor **NO subidos a GitHub**, quedan en su chat y archivo de descarga.

**DECISIÓN:** Guardar v0.10 como **avance de LABORATORIO ejecutado** que demuestra posibilidad de cálculo musical CPU1 dentro del SDK copiado sin apagar el servicio; NO como diseño de firmware seguro ni como versión aprobada. Próximo gate: comparar tiempos de llegada NOTE ON/OFF entre ambos, proteger cronograma de worker original bajo escritura flash/servicios SDK y evaluar forma de integración soportada/compatible antes de hardware.
