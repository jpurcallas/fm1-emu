# BIOMECH RHYTHM 3 · Reparto musical 3+3 · Checkpoint C99

**Fecha:** 23/oct/2026. **NO INSTALAR.** El producto `.fwsc` de BIOMECH 3 **todavía no está generado**.

## Código musical implementado

`dualcore/biomech.c` contiene un ejecutor dividible en la ruta real del render de seis pistas, conservando los 64 slots globales de polifonía. CPU0 programa las notas y transporta el estado común, procesa las envolventes y prepara los consumos de ruido en el orden canónico; calcula las pistas 1–3. CPU1 calcula las secciones de oscilador, LFO, textura, filtro y bit-reduction de pistas 4–6 sobre copias privadas. CPU0 espera el resultado, integra las voces por su índice original y ejecuta **la cadena FX recuperada de esta fuente de referencia**.

La precomputación común es necesaria para conservar la secuencia RNG cuando las pistas intercaladas reutilizan slots. La ruta de CPU1 no utiliza funciones de audio sustitutas ni reduce pistas. El trabajo compartido de preprocesamiento sigue siendo una carga importante sobre CPU0; **no se ha probado aún si ofrece velocidad suficiente en FM-1**.

El reparto usa lotes de hasta 32 muestras y corta exactamente en cualquier evento, paso del secuenciador o roll. Reutilizar un slot global para otra pista invalida la identidad del propietario anterior (fallo localizado y corregido); la copia privada se refresca completa en cada lote.

## Comprobaciones y límites de paridad

Se comparó PCM serial, utilizando el archivo C99 recuperado sin alterar (`original/biomech.c`), con el render 3+3 de pthread en un host. Tres escenarios de pruebas: 30 triggers MIDI, 28 triggers de secuenciador generativo con BPM cambiante, y 3074 triggers con robos de voz. En todos: PCM byte por byte idéntico, incluidas pruebas de fallo recuperable. No se ha verificado paridad contra el firmware musical **BIOMECH 2 v0.2** ni contra todos sus presets/efectos.

El archivo de referencia recuperado usa `BR_FM1_COMPACT_FX` para el perfil del FM-1; esa elección **preexistía** al reparto y omite el resonador en ese perfil. No atribuirle por ello la funcionalidad total del diseño original. No se hicieron recortes adicionales al convertir el render, pero resolver la paridad musical completa continúa siendo requisito del proyecto.

## Puente CPU1 de hardware y BLACK BOX

`br3_cpu1_runtime.c` implementa un buzón directo (firma por secuencia, `csync`, límites de tiempo según número de muestras, opción fallback únicamente cuando CPU1 está detenido) y entrada privada `br3_cpu1_entry.S`. El material ha pasado verificación sintáctica HOST. **No se enlazó aún junto al motor en un ELF PI32v2**. La prueba previa PI32v2 realmente ejecutada en el emulador es la autoprueba nativa separada de GitHub, no este render musical.

`br3_blackbox.c` escribe en SRAM el registro `BR3BBX01`, anillos por CPU y contadores de trabajo, tiempo de espera, fallos y confirmación DMA (solo cuando lo invoque la futura aplicación). `br3_extract_blackbox.py` extrae la estructura del volcado RAM en JSON del emulador. La prueba de lectura de un RAM simulado pasó; todavía falta una ejecución del firmware con este registro.

## Próximo bloque de desarrollo (no pruebas manuales del autor)

1. Recuperar y verificar la integración compilable SDK y la fuente musical correcta contra BIOMECH 2, sin reemplazos silenciosos.
2. Reservar correctamente la ejecución de CPU1 y una pila propia; reubicar el worker a RAM cuando sea necesario; validar el protocolo nativo bajo carga.
3. Enlazar motor 3+3, secuenciador, panel, DMA y BLACK BOX en un `.fwsc` **SOLO EMULADOR**.
4. Probarlo internamente, luego entregar la primera versión audible al autor. No solicitar pruebas para cada autodiagnóstico previo.

## Referencia y protección

BIOMECH 2 v0.2 FWSC SHA-256: `d99e8d61c483e9b0d770818ace669e912b7ccef81c0fd298cd84540bfbf5c3f0`.

GitHub: `checkpoint/biomech-rhythm-2-v02-audible-20261023` (conservar) y `experiment/biomech-rhythm-3-dualcore-3plus3-20261023` (desarrollar). `master` no se tocó.
