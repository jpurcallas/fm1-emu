# UI42 — primera integración real de barras en el TUI ACTIVO

Origen: UI41 PR #47 commit \`2457038a8d38c84b1f80ad03b7540e57dbd81cbb\`.
Este commit modifica **TUI.json activo**, no sólo generadores ni maquetas.

- MEMORY: conserva 3 botones de encendido bool 5/6/7 y **agrega** MEMORY_EDIT_FREEZE / REVERSE / TIDE seleccionando el host index 117 (grupos 0,1,2).
- CHARACTER: cuatro ON/OFF 8–11 y cuatro EDIT índice 109; cambia posición y estado visual de los botones.
- MOD: tres ON/OFF 16–18 y tres EDIT índice 111.
- SEND FX: cuatro ON/OFF 12–15 y cuatro EDIT índice 110.
- 12 variantes de fondo existentes referencian las versiones privadas reversibles \`ui40_lab10_mpc_*.png\`; los controles activos requieren 12 PNGs de overlays. **El origen completo LAB10 sigue intacto.**
- El contenido privado de 24 PNGs está preparado en la Biblioteca/ensamblaje local privado, **no se publica en el repositorio**, igual que en las anteriores versiones: el repositorio contiene TUI/scripts/tests y la distribución lleva \`Plugin Skins/\` completos.
- La prueba \`test_ui42_integrated_tui.py\` verifica exactamente 14 ON/OFF, 14 EDIT, 12 fondos, 12 overlays, 11 tabs y preservación de otras gráficas. \`--asset-dir\` valida las 24 imágenes reales en el ensamblador privado.
- Separamos el test de generador UI40 del test sobre la TUI ya integrada: NO ejecutar el generador dos veces contra la TUI UI42.

**Puerta abierta:** paquete físico con todos los recursos, QA SDK \`validate.py\` y prueba MPC. UI41/C++ incluido sin tocar. Falta compositor nativo radar/ADN, eclipse azul aprobado e integración final del paso 2.

NO MERGE / NO DESCARGA INTERMEDIA.
