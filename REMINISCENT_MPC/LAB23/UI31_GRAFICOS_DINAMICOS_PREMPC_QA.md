# UI31 — REminiSCENT: gráficos dinámicos integrados antes de probar en MPC
Fecha local: 2026-11-13/14 (Costa Rica). Estado: **IMPLEMENTADO en TUI y recursos; validado estáticamente; NO probado ni aprobado en hardware MPC**.

## Origen
- Se partió de UI30, PR #32, HEAD `b64e5a05225ecf0b542b07dc443c63370099fe74`.
- Referencia estructural: Origamidi V22, funcional en la MPC del autor.
- Fuente visual aprobada: REminiSCENT LAB10, 11 módulos y 19 variaciones. No usar arte FM-1 ni fondos LAB23/24 rechazados. Conservadas exactamente las 19 imágenes base.
- C++ DSP, 27 voces y 254 WAV no modificados. ARM32 y ARM64 se reutilizan exactamente del paquete anterior: **no recompilación**.

## Implementado en UI31
1. OSC: 8 formas de onda vinculadas a host Parameter 2, más iluminación contextual de selección del mismo parámetro.
2. BLEND: eclipse animable con 16 posiciones vinculadas a Parameter 20, sin sustituir composición LAB10.
3. ENVELOPE: ADSR nativo conectado a Parameters 29–32; fondo LAB10 preservado.
4. MOD: LFO1/2 reales procedentes del DSP y parámetros host 118/119 (Plotter), visibles por selección LFO1/LFO2. ENV2: segunda curva independiente nativa conectada a 88–91 (no Mod Wheel).
5. MEMORY: traza de audio real post-MEMORY de host 120 + cabezal de lectura 121 con 32 estados; pantalla LAB10 intacta.
6. Solaris v09: seis spritesheets de 25 fotogramas c/u, 25 FPS con grupo 122 y frame 123; aparece al inicio y está configurado para ocultarse en estado DONE, sin ocultar permanentemente la interfaz.

## Controles y estado
- 11 páginas táctiles / 19 fondos LAB10 originales; 87 controles táctiles heredados UI30 y cuatro Q-Links dinámicos 113–116. Motor C++ conserva mappings y guardado previamente auditados en host.
- El TUI final contiene 124 componentes. La validez estructural del SDK NO demuestra funcionamiento táctil ni representaciones animadas físicas en MPC.

## Verificaciones realizadas
- `tests/test_ui31_live.py`: `SDK 36 PASS / 0 WARN / 0 FAIL`; 11 pantallas originales, 87 controles, OSC/BLEND/ADSR/MEMORY/LFO/Solaris; 19/19 fondos base idénticos, sprites dentro del límite de textura 8192px.
- ZIP íntegro `ZipFile.testzip()=None`, 296 entradas, 254 WAV, 33 PNG, 2 binarios ARM originales. Auditado con la misma verificación de byte-preservación de WAV/DSP del staging de UI30.
- SHA256 del ZIP: `6d9fbfcc65d8091c7b4f414c76c3b03a84fe9a89dc350c928e2f106c3016408f`; tamaño 310909963 bytes.
- Archivo privado entregado a Biblioteca: `/REminiSCENT MPC/REminiSCENT_UI31_LAB10_DINAMICA_PREMPC_COMPLETA.zip`. No publicar muestras privadas en GitHub.
- Fuente de ensamblado: `LAB23/tools/build_ui31_live.py`; fuente de verificación: `LAB23/tests/test_ui31_live.py`; skin: `LAB23/skins/TUI.json` en rama aislada.

## Lo que queda, sin confundir etapas
**Antes de MPC:** la implementación y verificación estática del punto gráfico están cerradas, pero NO existe una prueba del renderizador visual real de la MPC.
**En MPC:** verificar carga/visibilidad de las 11 vistas, foco touch/Data Wheel, cuatro Q-Links, movimiento de OSC/BLEND/ADSR/LFO/MEMORY, ocultación Solaris, audio/CPU/RAM, proyecto/presets. Si la UI vuelve a aparecer blanca, no afirmar que la hipótesis se corrigió; usar la evidencia del dispositivo, conservar intacto el arte y no seguir parchando a ciegas.

No merge, no tocar `master`.