# UI44 BLEND / ECLIPSE — checkpoint técnico (14 nov 2026)

## Rama y alcance
- Base real: UI42 PR #48, commit `7516790b1a51b74a6fb8b0a9fb2ed6052e2089a7`.
- Rama aislada: `fix/reminiscent-ui44-blue-eclipse-blend-20261114`.
- NO MERGE. No se modificaron `skins/TUI.json`, `skins/Q-Links.json`, audio/DSP, PCM/WAV/FLAC, ni barras de UI42.
- UI43 (RESONANCE/GRANULAR) trabaja en rama separada; estos cambios solo afectan BLEND.

## Fuente aprobada y comportamiento
- Fuente privada exacta: Biblioteca `Cyan Eclipse Over Swirling Worlds.png` (1670×941; SHA256 `9d2586cf2b133a437abeb898fd0abd4aaf4088be8ecfa9396df64c0bfeaeceaa`).
- Sol cian fijo en centro; solo el planeta oscuro se mueve horizontalmente de izquierda (ACOUSTIC, 0%) a centro (eclipse total alrededor de 50%) a derecha (OSC, 100%). No rota ni cambia de tamaño.
- El eclipse **no** analiza sonido. Es el control nativo del mismo host Parameter 20 (MASTER BLEND). En UI42 se conserva:
  - `LIVE_BLENDECLIPSE_LAB10`: Knob FilmStrip 16 frames, `dragOrientation: Horizontal`, `Data -> Parameter 20`, bounds `192 178 613 392`.
  - `BLEND_ECLIPSE_TOUCH`: `Data -> Parameter 20`.
  - Q-Link 1: proxy 113, ruta `qLinkTarget(page=2,slot=0)` hacia campo 24 (MASTER BLEND). UI41 notifica explícitamente al host en ambos sentidos, aunque requiere prueba en MPC real.

## Nuevo trabajo reproducible
- `tools/ui44_build_blue_eclipse.py`: compila dos **recursos privados** partiendo exclusivamente del still aprobado y el fondo LAB10 original. Reconstruye solo el hemisferio solar oculto a partir de textura cian ya visible; genera fondo estelar oscuro sin emplear los intentos previos defectuosos. Se revisaron los 16 cuadros, incluidos sus bordes, evitando cortes verticales y halos naranja antiguos.
- `tools/ui44_patch_blend_touch.py`: CORRECCIÓN FUNCIONAL necesaria que no se puede resolver con PNGs. En UI42 el widget nativo embebido de `BLEND_ECLIPSE_TOUCH` sigue en orientación `Vertical`, pese al filmstrip horizontal. En **ensamblaje** cambia únicamente `dragOrientation` de ese widget a `Horizontal` en un `TUI` de salida separado. El custom `LAB10_SDK_FOCUS_S0_462_310_VERTICAL` tiene exactamente **un** consumidor, BLEND. La operación es idempotente, comprueba un único delta semántico y prohíbe sobrescribir el TUI fuente. Cuando se combinen UI43/UI44, ejecutar el parche sobre el TUI integrado **vigente**, no copiar un TUI anterior.
- `tests/test_ui44_blue_eclipse.py`: validador de assets privados y contrato SDK (tacto/foco/wheel, filmstrip y Q-Link). CI ejecuta el contrato sin subir imágenes privadas. La comparación visual se hace fuera de GitHub.

## Recursos privados ya guardados
En Biblioteca ChatGPT: `/REminiSCENT MPC/UI44_BLEND/`.
- `lab10_blend_eclipse_live_16.png`: 613×6272, 16 cuadros de 613×392, SHA256 `47e75e44a16fff9d2101d1d80e55a319b7963744230904d146ff9858c9eb2d56`.
- `lab10_mpc_02.png`: fondo exclusivo BLEND de 1280×628, SHA256 `37e4e51b08d1770d288f5e0659ab34a70d3b541c3e771193e40eea00b9e43607`. Respeta a nivel píxel las pestañas superiores, todo el panel de Q-Links y los bordes LAB10 existentes.
- `UI44_ASSET_MANIFEST.json`: hashes fuente + salida + desplazamiento de cada cuadro.
- `UI44_VISUAL_CONTACT_QA.png`: composición de los estados 0%, ~50%, 100% (solo para auditoría).
- Copias de los scripts de generación y prueba. **No incluye muestras de audio**.

## Verificación y estado honesto
- **IMPLEMENTADO localmente**: dos PNG privados y código reproducible de animación con fuente artística exacta.
- **PASS local estático de assets**: 16 cuadros de 613×392; ancho/alto correcto; centro repetido en cuadros 7 y 8; movimiento monotónico; textura del planeta consistente durante la traslación; bordes del filmstrip compatibles con fondo; regeneración determinista por SHA256; parte superior, Q-Links y borde exterior preservados.
- **PASS local de parche**: aplicada a TUI anterior compatible para verificar semántica de cambio único; UI42 actual y sus widgets se inspeccionaron directamente en GitHub. CI de esta rama comprobará el TUI UI42 exacto cuando se ejecute.
- **SDK**: cotejado con `inmusic-software/mpc-plugin-builder-sdk` @ `febd2ca5bd9eb16c4a412837196e145566bc981b`, docs `ui-reference.md` §6.4 (Knob FilmStrip, vertical strip, 16 frames, DragOrientation v3), §7 handles, §8 Q-Links.
- **NO EJECUTADO en hardware MPC One+**: drag, foco Data Wheel, retorno de Q-Link, lectura por host, gráficos con renderer hardware. La lógica C++ bidireccional es UI41 ya existente, NO se modificó ni se recompiló aquí.
- **NO APROBADO VISUALMENTE POR EL AUTOR** todavía: la nueva animación y hemisferio solar reconstruido deben cotejarse con la aprobación del still antes de entrega instalable.
- **NO ENTREGAR ZIP INTERMEDIO**: todavía quedan UI43 y la validación integral/QA en MPC.

## Integración futura sin conflicto con UI43
1. Conservar intactos los cambios de UI43 en TUI; no usar un TUI UI37/UI42 viejo para sobreescribirlos.
2. Copiar solo los dos PNG privados **con sus nombres exactos** a `Plugin Skins/`.
3. Ejecutar `ui44_patch_blend_touch.py --input-tui TUI_integrado.json --output-tui TUI_ui44_ready.json`; contrastar un único delta semántico y usar **solo el resultado combinado** en el paquete final.
4. Correr CI + asset tests con imágenes privadas + revisión visual real + pruebas físicas en MPC. Conservar los límites hasta tener evidencia.
