# BIOMECH RHYTHM 3 — Ruta CPU1 propia (decisión experimental)

Fecha: 2026-10-23. Rama: experiment/biomech-rhythm-3-dualcore-3plus3-20261023
**NO INSTALAR. No modificar `master` ni BIOMECH 2. Todavía no constituye firmware BIOMECH 3.**

## Razón
El autor propone priorizar una ruta técnica ya recorrida por desarrolladores de FM-1 antes de forzar la coordinación CPU0/CPU1 del SDK V14.
En pruebas del checkpoint de BIOMECH 2 v0.2: dos voces audibles correctamente a 200 MHz y degradación perceptible al introducir una tercera. Esto NO demuestra por sí solo que el reparto 3+3 lo resuelva.

## Antecedentes públicos comprobados
- **X0X** `charlesvestal/fm1-x0x/firmware/hal/fm1_cpu1.{h,S}`: arranque directo de CPU1 con secuencia de registros de JieLi, pila propia, buzón y handoff de trabajo con `csync`; timeout y desactivación de CPU1 si falla. La propia documentación cita `EnableOtherCpu` del SDK AC79 como fuente del protocolo de arranque, pero no delega el *despacho musical* al servicio estándar de coordinación.
- **Clipper** `isod89/clipper-fm1/firmware/src/cpu1.{c,h}`: REUTILIZA la HAL de X0X mediante SLOOP; no constituye un segundo descubrimiento independiente. Hace autoprueba con trabajo real en CPU1, reparte el render, expone estado y tiene fallback de un núcleo. El HAL también reconoce influencia de Melodee.
- X0X advierte de lecturas corruptas de CPU1 en algunas unidades FM-1 (#10); su protocolo valida trabajo recibido, y puede deshabilitar el segundo núcleo. El éxito de simulación no prueba confiabilidad en todas las unidades físicas.

Fuente X0X: https://github.com/charlesvestal/fm1-x0x/blob/main/firmware/hal/fm1_cpu1.h
Fuente Clipper: https://github.com/isod89/clipper-fm1/blob/main/firmware/src/cpu1.c

## Elección de BIOMECH 3
1. Mantener los servicios de SDK estrictamente indispensables de periféricos/arranque, pero **no depender del worker/despachador SDK para encargar la síntesis**: CPU1 ejecutará el bucle propio BIOMECH 3 y su buzón.
2. Adoptar las ideas comprobadas (pila propia, autoprueba, barreras `csync`, ownership y líneas de caché, validación de secuencia y errores, deadline explícito, fallback a CPU0), pero **escribir implementación propia**; X0X/Clipper contienen código GPL-3.0, no copiar sin revisar compatibilidad/licencias.
3. Antes de repartir voces, montar copia de firmware PI32v2 con un único BR3_SELFTEST que se vea completado **por el verdadero CPU1 del emulador**; CPU1 del SDK existente no puede usarse/reiniciarse a ciegas. Registrar PC, respuesta, bytes, timeouts y bloqueo sin esperar indefinidamente.
4. Primera variante de audio: preparación común CPU0, render 1–3 CPU0 / 4–6 CPU1 sobre estados separados, mezcla y FX CPU0. No tocar algoritmos, seis voces, secuenciador, modulaciones ni diseño musical.
5. Primer candidato `.fwsc` audible SOLO EMULADOR en cuanto arranque y ejecute. Pruebas iniciales: mismo patrón de dos y tres voces del checkpoint v0.2 a 200 MHz, luego seis voces; exportar WAV + BLACK BOX y comparar finalización antes de DMA.

## Limitación material pendiente
El paquete recuperado `BIOMECH2_v0.2_FIRMWARE_EMULADOR_BLACKBOX_LISTO_PARA_PROBAR.zip` contiene `.fwsc` de BIOMECH 2 y emulador, **no** fuentes C99 exactas de esa versión. El directorio `experiments/biomech-rhythm-2/` contiene un búzon prototipo y un arranque PI32v2 no enlazado, no firmware audible 3+3. No es válido afirmar que se portó el DSP v0.2 al compilar solamente un autodiagnóstico.

## Condición de aceptación
BIOMECH 3 solo reemplaza a BIOMECH 2 tras demostrar audio igual o mejor con seis voces y funciones originales y cumplimiento del plazo end-to-end del DMA; pruebas HOST, boot de CPU1 o compilación sin escuchar no bastan.