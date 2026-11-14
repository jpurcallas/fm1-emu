# UI45 — integración de UI43 + UI44, preservando UI42 y audio original

**Orden del autor:** integrar REminiSCENT MPC UI43 RESONANCE/GRANULAR y UI44 BLEND/eclipse azul; GitHub primero, evitar rehacer trabajo; no editar master ni fusionar PR sin orden.

**Bases verificadas en GitHub 14-nov-2026**
- UI42 PR #48 commit \`7516790b1a51b74a6fb8b0a9fb2ed6052e2089a7\`
- UI43 PR #49 commit \`2b196cdd9f0db2888c1ed16623f8490854f54c22\` (base de esta rama)
- UI44 PR #50 commit \`bfd58f9e59a12b3d7fe9bd958e5daaf8e4aaacc5\`
- Este PR integra **sin merge**; copia los cinco archivos añadidos por UI44 (sus Git blob SHA intactos) y cambia únicamente \`skins/TUI.json\` de UI43.

**Único cambio semántico al TUI de UI43:**
En el custom exclusivo de \`BLEND_ECLIPSE_TOUCH\`, \`LAB10_SDK_FOCUS_S0_462_310_VERTICAL\`, el Knob \`native handle editor\` cambia \`dragOrientation\` de \`Vertical\` a \`Horizontal\`. Control y filmstrip usan \`Parameter 20\`. Q-Link 1 conserva proxy 113. Comprobado contra JSON íntegro de UI43 y script UI44 original, idempotente.

**Funciones preservadas**
- 11 pestañas, 154 componentes; las 14 parejas ON/OFF–EDIT de UI42.
- 8 overlays UI43 con 16 cuadros por control: radar BODY/DECAY/EXCITE/MIX (38–41) y ADN SIZE/DENSITY/POSITION/MIX (44–47).
- DSP y 254 WAV originales SHA256 idénticos a la fuente preservada; no cambios C++, otros presets ni compresión FLAC.

**Recursos privados**
Se ensamblan, sin publicar arte en repositorio, desde /REminiSCENT MPC/UI44_BLEND/:
- \`lab10_blend_eclipse_live_16.png\`, SHA256 \`47e75e44a16fff9d2101d1d80e55a319b7963744230904d146ff9858c9eb2d56\` (613×6272, 16×613×392).
- \`lab10_mpc_02.png\`, SHA256 \`37e4e51b08d1770d288f5e0659ab34a70d3b541c3e771193e40eea00b9e43607\` (1280×628).
- En staging completo: 64 referencias gráficas no vacías, todas presentes; 80 PNG; 254 WAV; ARM32 y ARM64 originales UI41 sin recompilar.

**QA hecha localmente**
- \`test_ui45_integrated_ui43_ui44.py\`: dif único orientacion, nombres/host/16 cuadros; script UI44 idempotente.
- \`test_ui44_blue_eclipse.py\` original: TUI SDK, datos privados, fuente still aprobada, 16 frames, fronteras sin recuadros, SHA determinista PASS (con arte LAB10 original SHA \`1b2cc...\`).
- Auditoría de contenido completa \`qa_integrated_ui45.py\` local: 47 comprobaciones PASS de bindings, 64 referencias, tamaño de filmstrips, 2 asset hashes, ARM/ELF, 254 WAV SHA, Q-links, motor intacto.
- GitHub CI adicional controla regresión UI42, UI43, UI44 y UI45.

**Limitaciones, explícitas**
- El SDK/VST ARM no ha sido ejecutado en MPC One+ físico con esta combinación: toque, Q-Links, Data Wheel, carga/refresh de layers y visual final siguen sin verificar en hardware.
- La animación UI44 usa un hemisferio solar reconstruido a partir del still aprobado; **su nueva secuencia requiere aprobación visual del autor**. No asumir aprobación de movimiento solo por aprobación del still.
- NO hacer merge a master. No confundir compilado/CI con probado en MPC.
