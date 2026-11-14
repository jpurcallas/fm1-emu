# REminiSCENT LAB23 — evidencia de audio y persistencia, 13 noviembre 2026

## Alcance y procedencia
- Rama exclusiva: `work/reminiscent-mpc-integracion-20261113`, PR #31; NO MERGE.
- Arte y DSP aprobados: LAB10 + Bridge16 + LAB19; no se alteraron muestras, filtros, efectos, fuentes ni diseños.
- Banco privado original: `/REminiSCENT MPC/REminiSCENT_PCM_27_VOCES_254_WAV_PARA_MPC.zip`, SHA256 documentado `798e4ec4c3072d0b2c549eccc9213f72422550d3d10a203b2c8092f71f49cfd5`. No se ha publicado audio de terceros en GitHub.
- Código LAB23 + revisión de Q-Link en commit `467eb281a0a82c6b400a80f314f239588c115cef`; pruebas fuente en `tests/test_qlink_state.cpp` (commit `986b6fb48dc97f6d7d9734974651b60a7e9fcfe5`) y `tests/test_all_acoustic_27.cpp` (commit `d2c3e30eb2d355a86517f4656672011e02dee88d`).

## Hallazgo causal y corrección
El `parameterChanged()` original actualizaba el parámetro musical a partir del proxy del Q-Link incluso cuando el valor discreto mostrado **no había cambiado**. Al cargar `effSetChunk`, un proxy entero podía pisar una normalización de punto flotante perfectamente restaurada. En la ejecución de diagnóstico previa a la corrección, la diferencia fue **únicamente** el parámetro 105 (`params.acousticNoise`): plain `48 -> 48`, norm `0.376799941 -> 0.377952754`. De ahí surgía la advertencia de chunk no idéntico, aunque los 118 valores visibles parecieran restaurados.

**Corrección aplicada**: antes de propagar un movimiento de Q-Link al destino, comparar el *plain value* cuantizado del destino con el valor que el proxy intenta establecer. Si son iguales, no sobrescribir la normalización restaurada. Si cambian, el Q-Link sigue actualizando el DSP.

## Pruebas realmente realizadas en Linux host (NO MPC física)
1. Fuente LAB23 compilada como VST2 nativo con el SDK ya recuperado y **254 WAV privados**, sin recompilar el firmware FM-1 ni cambiar Bridge16.
2. `host_sim test --seconds 2 --notes 60 --sr 44100 --block 128`: **19 PASS, 0 WARN, 0 FAIL** tras el fix; el chunk guardado, restaurado y guardado otra vez es **idéntico byte por byte**, 3.032 bytes. Previamente: 18 PASS, 1 WARN, 0 FAIL. La prueba incluye carga repetida de PCM, bloques de 32/128/512, barrido de parámetros, notas y audio finito.
3. Q-Link 1 probado con su destino concreto en cada una de las **11 páginas**: 11/11 cambios llegaron al destino previsto; luego `effGetChunk/effSetChunk/effGetChunk` conservó los bytes. **No demuestra Data Wheel ni touch en MPC**, únicamente el ruteo de host y persistencia.
4. Banco acústico real: 254 WAV cargados, 27 fuentes catálogo audible y finitas, además de **didgeridoo B**, usando la nota raíz central de cada banco, oscilador OFF, A sola, master/presence controlados y 120 bloques de 128 frames. Resultado: **27/27 PASS**, B PASS, ningún sample faltante. Pico RSS medido en el proceso nativo: **368.128 KB**; no es una medición de la RAM disponible en MPC.
5. **Riesgo registrado, NO corregido sin autorización acústica:** con master/A al máximo y OSC/B desactivados, 13/27 fuentes muestran picos numéricos mayores que `1.0`. Con los valores normales de LEVEL A (96/127) y MASTER OUTPUT (100/127), pero fuente A aislada, 7/27 fuentes siguen superando `1.0` (IDs 01, 05, 12, 13, 14, 17, 18). Esto **no demuestra clipping en el preset completo**, que mezcla otras rutas; requiere prueba de ganancia y escucha autorizada antes de modificar el DSP o los PCM. Ningún limitador, normalización, ADPCM, loop artificial o compresión añadido.
6. Skin local de 42 recursos (40 anteriores + 2 live overlays): SDK `check_skins` sobre 118 parámetros pasó sin errores ni advertencias; es **validación de estructura**, no render en firmware.

## Pendientes sin cambio
- Gráficos dinámicos exactos ADSR/LFO/MEMORY, splash de 6 s aprobado; no sustituirlos por gráficos genéricos.
- Cuatro rutas de DSP no cerradas (`acousticNoise` sigue PROPUESTA, `spread`, `filterEnv`, `filterTrack`); verificar acuerdos antes de implementar, no inventar.
- Integración portátil del banco PCM y 42 PNG privados con fuentes versionadas, sin incluir WAV de terceros en repositorio público.
- Compilación ARM32 **de LAB23 corregido**, instalación y prueba física MPC One+ de 11 tabs touch, Data Wheel, Q-Links, audio/CPU/RAM, presets/guardar/reabrir. Nada de esto puede inferirse de pruebas nativas.
- **No entregar ni pedir al autor pruebas de versiones incompletas**. `master` permanece intacta; ninguna fusión autorizada.

Estado: **implementado/parcialmente validado en host**, NO completado, NO probado en MPC física, NO aprobado.

## Comprobación de plataforma (sin intervención del autor)
- SDK local recuperado y fuente LAB23 disponibles, pero **no hay Zig ni cross GCC ARM instalado en el contenedor de trabajo**. Se intentó instalar `ziglang`; la descarga falló por DNS/red del entorno. También falló la descarga de la distribución Linux oficial. **No se generó ARM32 LAB23 y no hay prueba física.** El autor ya tiene Zig funcional en su Mac por la compilación LAB20; no repetir diagnóstico de ese entorno ni pedirle recompilar una versión parcial.
- Para ADSR se comprobó en `docs/ui-reference.md` del SDK que existe un componente nativo `Envelope` con handles `attack/decay/sustain/release`, pero **no está demostrada su fidelidad exacta** a los satélites, curva y disposición gráfica LAB10 aprobados. No se ha reemplazado la skin de GitHub por una visualización genérica. Prueba local de composición visual sin adopción en rama: el gráfico fijo puede retirarse dentro de su marco sin alterar otros píxeles de `fondos/03.png`; el render de Envelope nativo en MPC sigue sin comprobarse.
