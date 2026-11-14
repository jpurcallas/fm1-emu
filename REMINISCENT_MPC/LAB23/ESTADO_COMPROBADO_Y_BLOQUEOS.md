# LAB23 — Fuentes incorporados; arte binario en respaldo privado

**Base:** LAB22 (último staging con navegación táctil y PCM); **cambio LAB23:** vínculo táctil de BLEND + guard de empaquetado. **No es versión aprobada ni entrega para prueba.**

## Evidencias verificadas (2026-11-13)
- Commit GitHub `447b54029b11574f785c38330bdac5333401d0da`: fuentes reales `REMINISCENT_MPC/LAB23/src/`, `plugin.json`, `skins/TUI.json`, `skins/Q-Links.json`, `Content/bank.tsv`, scripts Mac, notas. **Se guardó fuente real, no solo informe.**
- SDK en staging: `TUI.json` con **1 tab nativa**, navegación interna mediante 11 imágenes/páginas controladas por el parámetro 112; no declarar "11 tabs MPC" hasta prueba física. La UI incluye 11 fondos `fondos/00.png…10.png`. El autor aprobó **navegación táctil entre once módulos**, no está autorizado sustituirla por botones de hardware.
- **40 archivos PNG requeridos** en `skins/` (11 fondos + estados de navegación + sprites). Los archivos están conservados en el workspace LAB23 y respaldo privado; **todavía NO están versionados como binarios GitHub** por limitación de transferencia binaria del conector. Este faltante impide que un checkout del PR por sí solo reconstruya la skin artística. Registrar explícitamente, no anunciar repositorio completo.
- Banco 254 WAV en Biblioteca privada: `/REminiSCENT MPC/REminiSCENT_PCM_27_VOCES_254_WAV_PARA_MPC.zip`; **NO** incorporado en este repo público por licencias/procedencia. `bank.tsv` está versionado y su índice permite validar nombres.
- Compilación LAB23 `native`: registrada como completada en `LAB23_NATIVE_BUILD.log`. `host_sim`: 18 PASS, 1 warning (chunk re-guardado), 0 FAIL; prueba G1 audio igual a LAB22; archivo `ESTADO_REAL_Y_LIMITES.txt`.
- **ARM32 de LAB23 NO compilado aquí**; prueba MPC One+ real NO realizada; UI animada y cuatro controles DSP todavía pendientes. No solicitar al usuario otra compilación/descarga parcial.
- El autor compiló ARM32 de LAB20 en su Mac, pero **esa prueba no se transfiere automáticamente a LAB23**. No confundir.

## Estado real
- Implementado (staging): UI 11 páginas dibujadas sobre artwork original, touch-navegación interna, Q-Link de cuatro destinos, motor PCM 27 voces, mapeo de parámetros.
- Compilado: host nativo LAB23; ARM32 sólo versión antigua LAB20 compilada por el autor.
- Probado: host_sim LAB23 (18 PASS, 1 WARN).
- **NO probado/NO aprobado:** render/touch/Q-Link/Data Wheel en hardware MPC; audio completo de 27 instrumentos en MPC, performance, animaciones ADSR/LFO, splash.
- No entregar instalador ni pedir descargas hasta completar las condiciones del autor.
