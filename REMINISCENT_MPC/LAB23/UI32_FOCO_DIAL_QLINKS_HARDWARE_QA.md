# REminiSCENT UI32 — SDK focalización Data Wheel / Q-Links en caja LAB10
**Origen:** UI31 probado en MPC (render y 11 tabs funcionan), PR #33, commit `b78d8dbc8fadb6e4a3da93b4e80631e6ae7b895d`. **No modificar arte LAB10, DSP, samples ni binarios ARM existentes.** El autor observó Q-Links físicos inoperantes y marco/foco fuera de caja; Data Wheel nunca sale de selección de plugin, etc. No está confirmado que Origamidi controle bien el Data Wheel.

## Código implementado
- Basado en `mpc-plugin-builder-sdk/docs/ui-reference.md` §§3.6, 4.2, 6.1–6.5, 8.2–8.4, y definiciones reutilizables de Origamidi V22, no en suposición de hardware.
- Se incorporan **39 wrappers de foco** `UI32_FOCUS_*` alrededor de los Knob/ValueSlider de UI31. Cada uno contiene el mismo widget valor original más un `Focus` de aparición solo al enfocarlo; acciones oficiales `Mouse Down -> Q-Link`, `Double Click` / `Enter Pressed -> Show Overlay`. Overlay `knob overlay` copiado de la referencia funcional Origamidi; no se sustituye el skin.
- `ACOUSTIC_BLEND_TOUCH` adopta `dragOrientation=Horizontal` coherente con la barra horizontal aprobada. También MEMORY WINDOW/POSITION/MIX.
- Los **11 ON/OFF** de CHARACTER (4), MOD (3), SEND FX (4) pasan a un hotspot custom con acciones SDK `Mouse Down/Enter Pressed -> Toggle Switch` del parámetro real. No altera los botones SELECT/EDIT ni sus coordenadas ni la imagen base.
- `Q-Links.json` conserva el encaminamiento hacia los mismos proxies `113,114,115,116` y `RowTopDown`, pero **llena las 4 filas/bancos**: 1–4, 5–8, 9–12 y 13–16. Evita que el banco activo se quede sin parámetro.
- `TUI.json` `qlinkBoundsData` sustituye `1127 218 114 390` por **`1015 173 245 405`**, repetido para cada banco, de forma que el marco cubre toda la **caja de Q-Links LAB10** que ya existe. Las cuatro superficies de datos originales permanecen en sus posiciones aprobadas; no se mueve ni modifica arte.

## Pruebas realizadas
- SDK oficial `tools/validate.py`: **0 errors, 0 warnings**. Se verificó el paquete descomprimido con ambos binarios ARM.
- ZIP `ZipFile.testzip() is None`: **296 entradas, 254 WAV**, SHA-256 `23ea1811c708093a1f8b33c023765a48f1811745cda5358c4da438ad59196ee8`. Diferencias CRC respecto a UI31 limitadas **estrictamente** a `Plugin Skins/TUI.json` y `Plugin Skins/Q-Links.json`. Todas las imágenes LAB10 y Solaris, sprites, muestras PCM y binarios ARM originales coinciden byte a byte.
- Comprobaciones de mapeo: 39 wrappers focalizables, 11 hotspots Toggle Switch, 11 pestañas originales, 16 asignaciones por cuatro bancos, 32 componentes Image conservados, 254 WAV sin cambios.
- Paquete instalable **PRIVADO** (contiene samples): `/REminiSCENT MPC/REminiSCENT_UI32_FOCO_DIAL_QLINKS_TOUCH_CANDIDATO.zip`, 310+ MB. Código de rebuild `LAB23/tools/build_ui32_focus_qlinks.py`.

## Limitaciones: distinguir implementado / validado / probado / aprobado
- **Implementado, verificado estáticamente y empaquetado**: sí.
- **Compilado código DSP de nuevo:** NO; se reutilizan binarios ARM de UI31, sin alteraciones.
- **Probado físicamente en MPC:** NO; las acciones de foco/overlays, el Data Wheel, Q-Links y toggles necesitan la comprobación del autor. No afirmar funcionamiento hasta esa prueba. Si no responden, investigar modo Q-Link host/overlay y foco SDK con evidencia, no tocar arte ni repetir test PCM.
- **No resueltos por este cambio aislado**: disparo de intro Solaris v09 (autor informa que no aparece) y cualquier comportamiento visual de MEMORY MOTION no capturado por el simple cambio de orientación/touch. Registrados en PR #33. No esconder ni afirmar resueltos.
- **Sin merge**; master queda sin cambios.
