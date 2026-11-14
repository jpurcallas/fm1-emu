# REminiSCENT — UI30: interacción MPC reconstruida desde Origamidi V22
Fecha: 14 de noviembre de 2026 (Costa Rica).

## Origen verificable
- Base de código y sonido: PR #31, commit `55dcc1ad3d2d460a2c5116cd098aaf1168acf96d`, sin editar C++/DSP.
- Referencia estructural: `ORIGAMIDI_MPC_V22_MIDI_Y_QLINKS_VERTICALES.zip`, comprobado funcional en la MPC del autor.
- Arte: 19 vistas originales de LAB10 provenientes de `REminiSCENT_UI29_11PANTALLAS_PARAMETROS_SDK_CORREGIDOS.zip`; 11 módulos, 4 estados CHARACTER, 3 MOD, 4 SEND FX. Primera pantalla cotejada byte a byte con captura aprobada.
- **Sin copiar el arte Origamidi, sin fondos FM-1 ni fondos recortados LAB23/24, sin MOD WHEEL.**

## Fuente implementada
- `LAB23/skins/TUI.json`: una página SDK nativa con 11 vistas touch gobernadas por parámetro 112. Se reconstruyen controles usando los widgets originales `Button` y `Knob` del SDK que funcionan en Origamidi.
- **106 componentes:** 19 imágenes originales y 87 zonas táctiles editables (48 botones + 39 knobs).
- **Q-Links físicos 4**: proxies 113, 114, 115, 116; `Q-Links.json` original `RowTopDown`, ranuras 13..16. El motor no cambió: conserva `qLinkTarget`, los 11 mapas de cuatro destinos, selectores y `parameterChanged`.
- Toque de controles nativos enfoca su parámetro para Data Wheel: fuentes A/B (0/1), 8 ondas OSC (2), power A/B (3/4), BLEND (19/20), ADSR (29..32), MEMORY (5..7, 33,35,37), FILTER (42,107,108,43), RESONANCE (38..41), GRANULAR (44..47), CHARACTER cuatro submódulos (109 y 8..11), MOD tres submódulos (111,16..18 + destinos/sync/retrigger 92..102) y SEND FX cuatro submódulos (110,12..15 + algoritmos 103/104).
- Se agregan `replacementStrings` para opciones de fuentes, onda, algoritmos MOD y destinos LFO sin cambiar índices ni valores de los parámetros.

## Verificaciones ejecutadas (NO MPC física)
1. `test_ui30_control_interactions.py`: PASS 11 páginas, 19 fondos originales inalterados, 87 zonas táctiles, 8 ondas, 4 Q-Links, mapeos directos y estados seleccionables; sin cuarto MOD.
2. SDK `tools/validate.py` contra paquete extraído con binarios ARM32/ARM64 originales: **0 ERROR, 0 WARN**. Ambos ELF exportan `VSTPluginMain`; `uiversion=0.1.0.0`.
3. ZIP **privado** validado e íntegro: `/REminiSCENT MPC/REminiSCENT_UI30_CONTROLES_INTEGRADOS_CANDIDATO_PRIVADO.zip`, 301206762 bytes, SHA-256 `70b73f40370f2519098cf7cc89c87f50f84e27982ed811c73c72e82c0a385715`, 283 entradas, 254 WAV, 20 PNG (19 LAB10 + hit target transparente), 261 entradas no-skin con CRC y bytes idénticos a LAB29, ARM32/ARM64 binarios sin edición.
4. TUI de ZIP privado SHA256 `0befe77482dc42d5a1f765280c97a22afa8f72ca74f123b68e794dcbf5090690`. Versión GitHub reconstruida desde archivo de texto (mismo árbol JSON, posibles diferencias de formato). Prueba física no ejecutada.

## Límite **obligatorio**
**No declarar funcionamiento aprobado en la MPC.** La verificación anterior prueba integridad y enlaces estructurales, NO confirma que el renderer dibuje las 11 páginas, Data Wheel o Q-Links físicos. Además faltan los gráficos reactivos fieles del HTML LAB10 (ondas OSC, eclipse BLEND, ADSR/LFO/MEMORY), pues las 19 imágenes son capturas estáticas. No atribuir esto a una aprobación visual. Ningún DSP ni muestra WAV se tocó.

No publicar banco privado en GitHub. No merge. No pedir reinstalar SDK ni repetir pruebas de audio previas.