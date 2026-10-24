# REminiSCENT UX07 — HYBRID/BLEND native C99 navigation candidate
**23 Oct 2026 — solo LAB; NO FWSC compilado, NO audio nuevo; NO MERGE, NO INSTALAR**

El autor pidió abandonar la secuencia de maquetas sin audio y llegar cuanto antes a una experiencia de sintetizador audible, donde pueda descubrir problemas musicales de ergonomía tocando. v0.13 sigue siendo la referencia auditiva en el emulador Mac nativo (14 minutos estables en la sesión reportada). El .fwsc v0.14 anterior falló en un ensayo WASM guest; no se declara resuelto.

## Resultado implementado C99
La interfaz UX07 parte del `rn_hw_screen.c` UX04 (derivado UX03 v0.14) y emplea la cola de comandos existente, **sin cambiar DSP**. SOUND comienza en HYBRID BLEND; K1 acoustic source / K2 BLEND 0..127 / K3 osc volume / K4 waveform. La vista combina campos originales `RN_UI_SOURCE` y `RN_UI_OSC` y encola `RN_HW_PARAM` de las páginas modificadas, nunca DSP directamente. SELECT conserva ediciones por PART. SOUND no duplica FX SENDS: único ajuste en MIXER/FX accesible con FX. OSC HARMONIC SPEED aparece pendiente sin acción falsa. El resto: MEMORY, MEMORY MOTION, RESONANCE, LOW PASS, ENV, GRANULAR, CHARACTER, MOD buses globales, 4 TRACKS ×64, shortcuts y splash preexistentes.

## Pruebas ejecutadas, con alcance
Clang C99 HOST (`-Wall -Wextra -Werror -fsanitize=address,undefined`) PASS, 1200 eventos aleatorios, 21.212 bandas LCD simuladas, 1.267 comandos. Aserciones directas sobre cambio SOURCE/BLEND/OSC VOL/WAVE y `RN_HW_PARAM` a página correcta, PART1/2 independencia, sin efecto para HARMONIC SPEED, FX → SENDS, ausencia de SENDS en SOUND y SEQ OCT+ hasta siguiente bloque de 16. Captura RGB565 240×240 generada con **mock host**, no guest.

## Entregable del autor, integridad
`REminiSCENT_UX07_NAVEGACION_REAL_C99_SIN_FWSC.zip` SHA-256 **cb56f9243518617b43740b1136481b03f646c8aaf5fa85a4129c7c9386ca3b4a**. Fuente `src/rn_hw_screen.c` SHA-256 **47559e1142318b81fc934051f83f08f0a9ea7deae7f8d192a24da68f614611a5**, diff `UX07_UI_ONLY.patch`, mock de prueba, screenshot y auditoría. **Los bytes del ZIP se entregaron en conversación del autor, no se añadieron a GitHub**; esta nota sirve de índice y bitácora, no como falsa evidencia de código compilado nativamente.

## Gate no superado
Paquetes v0.13/0.14 no tienen objetos baseline V14, `support/link_baseline.json`, SDK exacto ni toolchain PI32v2. No se consiguió recuperar/reinstalar la cadena y **no se construyó un nuevo .fwsc**. v0.14 dejaba 576 B libres en APP; UX07 podría superar el límite y requiere medirlo con linker real. Primero compilar/enlazar/reempaquetar; después guest cold boot y audio/black box; por último escuchar en FM1-LIVE-LAB nativo Mac y evaluar cambios reales de BLEND y FX. No deducir comportamiento de Mac a partir de HOST ni de un viejo ensayo WASM.

No se recortan cuatro PARTS, efectos, polifonía, secuenciador ni algoritmos. No se modifican master ni binarios originales.
