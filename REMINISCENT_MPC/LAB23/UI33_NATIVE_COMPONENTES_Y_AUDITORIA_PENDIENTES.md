# REminiSCENT UI33 — Controles MPC nativos y visuales vinculados · ESTADO EXACTO

Fecha: 14 nov 2026 Costa Rica.

## Evidencia del autor en MPC
- UI31 renderiza pantalla y pestañas; selector OSC y eclipse se pueden tocar.
- En UI32: porcentajes de Q-Links cambian, pero no sus marcas visuales ni las gráficas. MASTER BLEND cambia porcentaje, no planeta; ACOUSTIC BLEND tocado no toma Data Wheel. Listas A/B ilegibles por texto superpuesto. CHARACTER, MOD y SEND FX únicamente permiten cambiar EDIT; ON/OFF no responde.
- Arte antiguo Solaris apareció en el render, removido en PR36; sigue prohibido.

## Cambios reales en esta rama, base PR37 `95539f22541c869cd1fe893565aa90e325f63a11`
1. Reemplazo de **55 componentes de tipos falsos UI32_*** por widgets SDK **Knob** (edición/foco) y **Button** (ON/OFF) siguiendo estructuras de Origamidi V22 funcional. Todas las pestañas intactas.
2. Los 16 ON/OFF permanecen en sus mismos parámetros de host: A/B, FREEZE/REVERSE/TIDE, CHARACTER4, MOD3, SEND4; sin modificar DSP. Botón real con `numButtonsInGroup=1` y `buttonId=1`; **aún no probado físicamente**.
3. 10 elementos de imagen FilmStrip (OSC, eclipse BLEND, MEMORY y 4 marcas QLink) convertidos en **Knob FilmStrip** nativo con remapeo al mismo parámetro host real, para que el cambio sea visible. No ocultar ni borrar los 19 fondos originales.
4. Nuevas marcas móviles de 101 posiciones para cuatro QLinks, derivadas del propio aro/aguja LAB10 (no arte anterior). Sus parámetros 113–116 son proxies que ya muestra el host. El código generador conserva textura LAB10.
5. Las etiquetas A/B se pintan sobre una máscara del mismo panel original LAB10 y un `Label` host enlazado a Parameters 0/1; evita el texto estático más texto dinámico.
6. FILTER: 24 fotogramas de la curva original **renderizada del HTML LAB10**, enlazados al valor CUTOFF host Parameter 42. Esta animación solo representa CUTOFF; la interacción conjunta de ENV y TRACK aún NO está completada.
7. No hay Solaris, FM1 ni recurso histórico reaprovechado. **Los 254 WAV, ARM32/ARM64 y los 19 fondos originales son idénticos byte a byte a UI32 sin Solaris**.

## Pruebas realizadas
- `test_ui33_native.py` y `test_ui33_filter_release_gate.py`: PASS de tipos SDK, conexiones, recursos existentes y conservación de todos los archivos originales; el ZIP contiene 140 componentes y 254 WAV.
- Revisión visual local compositada de FILTER con sus 24 frames obtenidos de HTML LAB10. No prueba de renderer MPC.
- Gate obligatorio `audit_release_art.py`: **0 errores de tipo/arte prohibido**, pero **18 overlays aún sin cotejo individual y BLOQUEADOS por calidad**. No eliminar/relajar regla por comodidad.
- ZIP privado **solo como estado de código para continuidad**, no apto para pasar al autor como plugin listo: Biblioteca `/REminiSCENT MPC/UI33_FILTER_NATIVE_PRIVATE_BLOCKED.zip`; generadores y pruebas en esta rama.

## Pendiente — NO declarar terminado
- Revisar 18 capas contra HTML LAB10 y capturas visuales, especialmente punteros, gráficos dinámicos y limpieza de textos.
- FILTER ENV/TRACK deben afectar curva; RESONANCE (BODY/DECAY/EXCITE/MIX) y GRANULAR (SIZE/DENSITY/POSITION/MIX) requieren composición multivariable, no animaciones decorativas.
- ACOUSTIC BLEND: el control está convertido a Knob nativo; falta completar actualización visual de su barra/indicador, así como prueba Data Wheel en MPC.
- Validar en MPC real interacción táctil y visual, animaciones y persistencia. No repetir tests de audio sin evidencia.
- No cambiar master ni fusionar; no subir PCM privados a GitHub.
