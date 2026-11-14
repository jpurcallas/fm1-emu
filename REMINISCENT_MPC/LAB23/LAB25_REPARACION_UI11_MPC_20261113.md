# LAB25 — Recuperación de las 11 pantallas MPC aprobadas

## Resultado concreto y origen
- El autor instaló LAB24, que mostró una superficie clara con Solaris y WHITE/PINK y no permitió navegar. La imagen real de MPC y la protesta del autor invalidan la entrega LAB24. No presentar LAB24 como interfaz aprobada.
- **Origen visual, no FM1:** las 11 vistas del HTML original `REminiSCENT_UI_LAB_10_INTEGRATION.html` que se mostraron y confirmaron explícitamente en esta conversación. Captura a 1280x800, adaptada a los **1280x628** del área UI MPC; se descarta el pie de laboratorio. La vista MOD proviene del HTML corregido sin Mod Wheel.
- La interfaz se conserva en **un tab nativo SDK con 11 secciones/páginas táctiles**, como en el prototipo aprobado: botones originales arriba ligados a `ui.page` **Parameter 112**. Esto **no** se debe describir como 11 tabs nativos de la MPC. Sí son once páginas seleccionables desde el touch. El diseño de 11 pestañas tiene prioridad respecto del número de teclas físicas.
- Las cuatro zonas de valores Q-Link responden por los proxies originales 113..116, con la asignación física `Q-Link 13..16`, `RowTopDown`. Data Wheel usa widgets `Knob/ValueSlider` del SDK. Los selects de A/B, las activaciones FREEZE/REVERSE/TIDE, CHARACTER, MOD y SEND FX usan widgets SDK.
- Hay **22 capturas/artes** de UI LAB10: 11 estados base más 11 estados adicionales de CHARACTER (4), MOD (3) y SEND FX (4), todos derivados del HTML aprobado, no dibujos nuevos. La skin activa contiene 72 componentes y 19 instancias de pantallas condicionadas por parámetros. MOD incluye **LFO1 / LFO2 / ENV2**, sin Mod Wheel.
- **Solución al bloqueo blanco observado:** se retira por completo de la UI renderizada la capa opaca `SOLARIS_V09_PLATE` y las seis tiras a pantalla completa; no se vuelven a componer encima de la UI. Los assets de Solaris están preservados pero la animación introductoria v09 queda **PENDIENTE de restitución fiable**. NO declararla completada.
- **Sin diseño FM1 en el paquete:** los 12 `fondos/*.png` anteriores se excluyeron, y no hay referencias a `fondos/` en los componentes activos del nuevo TUI.
- El audio Bridge16+LAB19, WHITE/PINK/SPREAD/FILTER ENV/KEY TRACK, 27 bancos y 254 WAV son los mismos: **no se han reescrito ni comprimido samples ni modificado DSP**.

## Código y compilación
- Fuente antigua de fallo, PR #31: `2f074015be4fb55b3f1cb6859fab77c695f90800`.
- TUI corregido `REMINISCENT_MPC/LAB23/skins/TUI.json`: commit `1a2325a5bcfd36a7622fc8c330cdf81903abaaa6`, blob `f512a5bd42f2e8dc0f703944efe81e584fb350c7`; SHA256 de texto exacto en paquete `1c615cd486bbe14f23b24886d1a0d94efb16cb426047011332a3501d6e0d0509`.
- Scripts fuente para regenerar capturas de HTML privado: `tools/build_approved_ui11.py` commit `fc9d904c` y `tools/build_approved_ui11_modes.py` commit `0f965463`; no se publican imágenes privadas en GitHub.
- Binarios nuevos **v0.25.0** Zig ARM32 y ARM64, fuente `a14f82654af5b7ea2a68df70b71615e1861b5a02`, SDK oficial Akai fijado `febd2ca5bd9eb16c4a412837196e145566bc981b`. CI push `43544878539`, **SUCCESS**. Nombre REminiSCENT, UID **Rm20** conservado, targets glibc2.31.

## Paquete completo privado
`/REminiSCENT MPC/REminiSCENT_LAB25_MPC_UI11_CORREGIDO_ARM32_COMPLETO.zip`
- Archivo creado y enviado satisfactoriamente a Biblioteca privada; **311.232.386 bytes**, SHA256 `a3147b0eb5a4cf14dc6d2ef1948084aff63f2c984cdc783db4a6cd133ad2a836`.
- ZIP íntegro, 332 miembros: **254 WAV sin modificaciones**, 69 PNG (incluidos 22 LAB10) y 2 binarios ARM32/ARM64 oficiales de CI.
- `plugin.json` y `version.xml` versión **0.25.0**, nuevo build para evitar reutilizar recursos de LAB24. `uiversion=0.1.0.0`.
- Validación SDK de la skin: **0 errores**; advertencia conocida del contenido PCM de 355 MB mayor a 256MB, sin ninguna normalización, recorte ni eliminación de voces.
- **NO hay comprobación de la vista ni respuesta táctil real en la MPC física para LAB25; no afirmar aprobación ni que se haya demostrado en hardware.**
- **NO MERGE, master intacto.** No solicitar al autor repetir trabajo de diseño ni instalar paquetes parciales.

## Próximo requisito de aceptación
El usuario debe poder ver el arte exacto del LAB10 y pasar de Acoustic a Send FX mediante las 11 pestañas superiores. Si no sucede, considerar defecto de implementación/SDK y corregir desde la evidencia física; prohibido volver a los fondos FM1, alterar audio, quitar módulos o presentar validación estática como prueba MPC.
