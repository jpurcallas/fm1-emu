# LAB27 — MPC real: audio audible, skin vacía, inicio lento. Corrección controlada.

## Evidencia del autor en MPC One+ (13 nov 2026 Costa Rica)
- REminiSCENT LAB26 **suena cuando se toca un pad**.
- La interfaz de pantalla está **completamente vacía**. La foto de la MPC confirma que no se dibuja arte ni elementos de navegación.
- La carga es lenta. **Origamidi en la misma MPC sí muestra el arte y la animación**, de modo que el fallo no se atribuye sin evidencia a la pantalla o firmware de la MPC.
- LAB24 tuvo una pantalla blanca atascada. LAB25/26 corrigieron el overlay pero **siguieron en blanco**. La corrección LAB27 es **candidata, no validada físicamente**.

## Interfaz: corrección contra referencia funcional Origamidi
Se compararon ZIP reales de `ORIGAMIDI_MPC_V22_MIDI_Y_QLINKS_VERTICALES.zip` y `REminiSCENT_LAB26_MPC_UI11_LIVE_ARM32_COMPLETO.zip` y SDK oficial. Ningún PNG referenciado faltaba. La causa exacta de que TUI no se renderice **aún no está demostrada**.

Cambio `TUI.json` GitHub commit `4fef7c0c4a75f3dce1f55c2ed9099a6fa7bc187e`, blob `dfdeed8ef39bba52a45fbbc763ca4cb9f8d22f6d`:
- Retira **21 definiciones de componentes no utilizados**, evitando que el parser de MPC procese definiciones arrastradas de LAB antiguos.
- Crea fondo inicial **siempre visible** `FALLBACK_ACOUSTIC_ALWAYS_VISIBLE` con `lab10_mpc_00.png`, aunque falle la condición de selección visual de la página. Color base opaco de seguridad.
- Conserva **11 páginas táctiles aprobadas** y sus estados/controles, LFO/MEMORY live, Q-Links 113..116, Envelope y MOD sin Mod Wheel. NO se regresa al arte FM1.
- Sigue **una pestaña nativa SDK con 11 pantallas touch internas**, no se afirman once pestañas nativas.
- Solaris sigue fuera de la UI activa, **pendiente de implementar sin bloqueo**.

## Motor de audio: mmap original, sin compresión con pérdida
- Antes `Bank::loadWav()` abría y copiaba los **254 WAV originales** completos a `std::vector<uint8_t>`, cada instancia ~372 MB solo PCM antes de sonar.
- Nuevos cambios `engine.hpp` commit `54578fdda9f136b00583fe60dbbd2f4107de52da` y `engine.cpp` commit `5ed2ffa0e931e58e1772d3d54038a1a1ffbedeca`: **mmap read-only** en Linux/macOS; WAV se analiza por cabeceras sin cargar la sección data. La lectura DSP interpreta los **bytes originales exactos**, no hay resample, conversión ni pérdida. Fallback portable a lectura tradicional si mmap falla. El puntero permanece válido con RAII `shared_ptr`.
- Prueba host local enfocada sobre **los mismos 254 WAV**, en el mismo sistema y con 5 notas cortas:
  - Loader anterior: **1.481 s**, pico memoria residente **368,132 KiB**, 254 muestras.
  - Loader mmap: **0.070 s**, pico memoria residente **4,608 KiB**, 254 muestras **254/254 con mmap**, sin fallback.
  - Sumas absolutas en 5 pares de instrumentos: coinciden numéricamente entre los dos motores (3.57043, 3.5708, 0.861275, 0.855373, 0.684876). Solo esta prueba dirigida: no se rehicieron DSP históricos ya comprobados.
- **Advertencia real**: en MPC la lectura desde SD/USB durante audio puede producir fallos de página y latencia. NO se ha comprobado la estabilidad en hardware. Se requiere probar notas largas y cambio de instrumento para confirmar. El ZIP sigue ~309 MB; no se ha reducido la calidad ni el tamaño del banco. Una compresión sin pérdida FLAC/ADPCM necesitaría decoder/QA separado: NO se añadió ahora.
- Formatos originales observados en muestras: PCM 16 y 24 bits, mono/estéreo a 44.1/48 kHz. No bajar resolución unilateralmente.

## Compilación definitiva y paquete
- Versión binaria y manifiesto: **0.27.0** (UID Rm20 conservado), compilación GitHub Actions **SUCCESS** run `43548957311`, fuente commit `84866e68e0953868388b7234b00f40124ed2f56b`, SDK fijado a `febd2ca5bd9eb16c4a412837196e145566bc981b`, targets ARM32 MPC One+ y ARM64.
- ZIP completo privado, **309,015,255 bytes**, SHA256 **`d99e23368477ade5dcb4310d2e724c93bfb7df71d9a272e165c141a042965407`**, guardado en Biblioteca: `/REminiSCENT MPC/REminiSCENT_LAB27_MPC_UI11_CARGA_RAPIDA_ARM32_COMPLETO.zip`.
- ZIP: **331 entradas, 254 WAV idénticos byte por byte al LAB26, 69 PNG, dos binarios recompilados**, `testzip() == None`. Metadatos `LAB27_PROVENANCE_AND_LIMITS.json`. Los archivos `TUI.json` y `plugin.json` coinciden exactamente con GitHub CI compilada. Se conserva `uiversion=0.1.0.0` **por compatibilidad SDK** (no aumentarlo a 0.27, ello impediría cargar el plugin).
- SDK `tools/validate.py` sobre **paquete completo extraído**: **0 errores y una advertencia por Content/ >256 MB**. Este aviso es estático y no comprueba la nueva estrategia mmap.
- El paquete privado está en Library; **no se subieron WAV ni arte con licencia a GitHub**.
- **No probado aún en MPC física** y no aprobado. Ni asegurar que el parche visual arregló la pantalla ni que mmap evitará glitches desde la SD. No tocar `master` ni hacer merge sin autorización.

## Acceptance checkpoint
Primera apertura en MPC: debe mostrar **ACOUSTIC** con los gráficos LAB10 antes de tocar un pad. Debe poder navegar por las 11 páginas. Probar carga y 5 notas sin clicks/lag. Si sigue blank, descartar diagnóstico de invalidating modifiers como causa única: recopilar logs de UI parser de MPC y corregir sobre el caso real, no más sustitución a ciegas.
