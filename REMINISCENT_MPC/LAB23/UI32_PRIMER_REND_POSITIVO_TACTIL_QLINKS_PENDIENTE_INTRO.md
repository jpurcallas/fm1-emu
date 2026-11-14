# REminiSCENT UI32 — primera prueba positiva en MPC y correcciones acotadas
Fecha local: 2026-11-13 / 2026-11-14 (Costa Rica).

## Evidencia real del autor
- UI31 (PR #33): **por primera vez el plugin muestra sus 11 pantallas en la MPC One+**. Navegación táctil por tabs funcional, selección OSC de ocho formas funcional, eclipse BLEND funcional. Esta base NO se reemplaza ni rediseña.
- Falla confirmada: cuatro Q-Links físicos no funcionan; ACOUSTIC BLEND no responde al tacto; FREEZE/REVERSE/TIDE y controles MEMORY MOTION no responden; no se muestra área WINDOW de selección sobre la onda; ON/OFF en CHARACTER, MOD y SEND FX no opera aunque EDIT sí selecciona; intro Solaris v09 no aparece.

## UI32 implementada sin cambiar DSP, binarios, PCM ni fondos
1. En `TUI.json`, 39 sliders táctiles quedaron dentro de componentes enfocables que copian la estructura de Origamidi V22: acción `Mouse Down → Q-Link`, `Enter/Double Click → KnobOverlay`, `dragOrientation: Horizontal` en ACOUSTIC BLEND y MEMORY WINDOW/POSITION/MIX. El control puede ser seleccionado para Data Wheel.
2. **16 ON/OFF verdaderos** con acción `Mouse Down → Toggle Switch`, separados de EDIT: ACOUSTIC A/B, MEMORY FREEZE/REVERSE/TIDE, CHARACTER x4, MOD x3, SEND FX x4. Se añaden **11 indicadores de estado del efecto**, visibles sólo si su parámetro real está ON y no por la selección EDIT.
3. `Q-Links.json` asigna los proxies 113–116 a las 16 posiciones hardware, repetidos en los cuatro bancos, en ambos modos Screen y Program; no queda banco sin asignar. El motor original mantiene el enrutamiento dinámico de 4 Q-Links por módulo.
4. MEMORY recobra la ventana visible en el buffer mediante lámina de 64 frames vinculada al Parameter 33 (WINDOW), más marcador 64 frames vinculado al Parameter 35 (POSITION). **Límite gráfico**: sus dos señales se renderizan de forma independiente, no es un rectángulo calculado conjuntamente desde el par de parámetros; por lo tanto una representación completamente exacta de la selección aún requeriría composición con ambos valores en la capa del motor. No afirmar equivalencia total con el HTML LAB10.

## Pruebas ejecutadas (estáticas, no hardware)
- `tests/test_ui32_touch_memory.py` PASS 137 componentes, 39 focos/drag, 16 toggles reales, 11 estados LED independientes, 4 bancos de Q-Links, 19 fondos LAB10 idénticos, 254 WAV íntegros, ARM32/64 byte idénticos. `zipfile.testzip()=None`.
- SDK oficial `validate.py --strict`: **0 errores, 0 advertencias**.
- ZIP privado `/REminiSCENT MPC/REminiSCENT_UI32_QLINKS_TOUCH_MEMORY_ONOFF_CANDIDATO.zip`: 310925132 bytes; SHA256 `880e12859acefe67704bb158938c97c9d8850108e30b7f895bf72f1d221136ca`; 299 archivos, 254 WAV. El único cambio de originales son dos JSON de skins y tres PNG nuevos. Sin recompilar motor.
- Los archivos fuente de la corrección y tests quedan en esta rama. Los PNG se producen programáticamente por el builder y sólo se distribuyen completos en el ZIP privado.
- **NO se ha probado en la MPC física**. No declarar éxito de Q-Links ni tacto sin prueba autor.

## Intro Solaris v09 — pendiente explícito, no ocultar
Su reloj se calculaba con samples de audio: `advanceVisuals` completa 150 ticks/6 s incluso mientras el usuario aún no ha abierto el editor. Para cuando el renderizador aparece, `ui.splash.group = DONE`. La skin no tiene evento conocido de `editor open` en el SDK; los 150 frames existen pero NO se pueden garantizar visibles al abrir la vista por sólo modificar TUI. No introducir activación manual/repetitiva ni parches de audio sin acuerdo. Está pendiente identificar o implementar un disparador verdadero de apertura de UI, con su prueba en hardware.

No cambiar `master`, no merge, no publicar PCM de terceros.
