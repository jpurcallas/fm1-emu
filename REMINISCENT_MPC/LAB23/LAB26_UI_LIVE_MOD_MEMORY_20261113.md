# LAB26 — UI viva sobre las 11 pantallas MPC aprobadas

**Regla de origen:** se revisaron repositorio/PR #31/comentarios, acuerdos y la TUI LAB25 en HEAD `7aa9cc8ceb383016a0d7aa08d4e47175a60911d8`. El autor pidió continuar adaptando para probar pronto, sin rehacer motor, sin retrocesos ni pruebas inútiles.

## Implementado (interfaz SDK real; NO prueba de hardware)

- **Mismo diseño LAB10 aprobado:** 11 pantallas y 19 estados de fondo, con MOD solo LFO1/LFO2/ENV2 (sin Mod Wheel). No se devuelve el arte viejo de FM-1. Persisten los 11 botones táctiles vinculados a `ui.page` parámetro 112; 1 tab nativo SDK con 11 secciones visibles, no 11 tabs nativos. El usuario ya aprobó este diseño visual, no la ejecución hardware todavía.
- **MOD LFO 1:** widget nativo `Plotter` con señal real DSP `ui.live.lfo1` parámetro 118; visible solo página 9 y selector MOD=0; rastro de 3 segundos dentro del área de gráfico aprobada. Forma del oscilador mostrada mediante filmstrip existente vinculado a parámetro 82, situado dentro de su tarjeta sin tapar el gráfico vivo.
- **MOD LFO 2:** igual con señal DSP `ui.live.lfo2` parámetro 119; MOD=1; forma vinculada al 86. La envolvente nativa ENV2 (88–91) solo visible con MOD=2. Los tres controles están separados mediante `IndexedEnabling` del SDK y no se dibujan unos encima de otros.
- **MEMORY:** widget `Plotter` alimentado por el *wet* real del motor `ui.live.memory` parámetro 120 (no gráfica HTML fingida) + filmstrip existente de **32 estados** mostrando `ui.live.memoryPhase` parámetro 121, con dirección REVERSE ya corregida en el C++ anterior. Ambos visibles solo página 4.
- **Q-Links:** índices 113..116 y configuración `RowTopDown` sin cambios. Control de touch y Data Wheel permanece en widgets SDK. No hay overlay a pantalla completa de Solaris que congele o tape el instrumento. **Solaris v09 auto-intro todavía pendiente**, no eliminar arte original ni afirmar que ya funciona.
- **NO se cambia código DSP, sample bank, voces acústicas, valores musicales ni identificador VST**. No se cambia versión del binario compilado 0.25.0: LAB26 es una revisión **solo de skin** sobre ese mismo binario ARM32/ARM64.

## Código y archivos
- `skins/TUI.json` GitHub commit `d3a799f97a99176188855ea8d8016a34e21acc06`, blob `a2c243d0e3d8867ce9def44fcc179b277626e434`. **76 componentes**, de ellos 19 imágenes de pantalla condicionadas, 11 pestañas táctiles, dos trazas vivas LFO, un plotter MEMORY y un filmstrip de cabezal.
- `tests/verify_live_visuals_lab26.py` GitHub commit `21275279f9b48fec34ab8219fb3c98cfbdd0a3f1`. Prueba estructural enfocada, no se repitieron las pruebas DSP ya PASS.
- La skin compilada la valida SDK `tools/validate.py`: **0 errores, 1 warning** por 355 MB de muestras superiores a 256 MB. El aviso sigue y no autoriza recortar/alterar las 254 muestras.

## ZIP real privado
- `/REminiSCENT MPC/REminiSCENT_LAB26_MPC_UI11_LIVE_ARM32_COMPLETO.zip`.
- **309.547.270 bytes**, SHA256 `0ac2136e8bd2d6392891bc93372dade1b594efbbf6286e39c60e218b808adbfb`. Comprobación `ZipFile.testzip() == None`. **331 miembros, 254 WAV, 69 PNG, 2 binarios ARM**. Contiene `LAB26_PROVENANCE_AND_LIMITS.json`.
- `TUI.json` de este ZIP es **byte-idéntico** al blob GitHub `a2c243d0e3d8867ce9def44fcc179b277626e434`.
- **Biblioteca privada**, archivo subido y verificado por `files__manage_library` con resultado succeeded. Los PCM y gráficos siguen privados; el código fuente/bitácora pueden quedar en GitHub.

## Estado honesto y siguiente aceptación
- **Implementado:** sí, enlace de telemetría DSP LFO/MEMORY a los componentes gráficos aprobados, botones y mapeos conservados.
- **Compilado:** ARM32/ARM64 **de LAB25** reutilizados y previamente compilados en GitHub Actions `43544878539 SUCCESS`. No se ha compilado un motor nuevo porque no hubo cambios en C++.
- **Validado estáticamente:** sí; ZIP íntegro y SDK 0 errores.
- **Ejecutado/probado en MPC One+ el LAB26:** **NO**. No se puede asegurar dibujo/funcionalidad física desde el SDK ni afirmar que el nuevo ZIP fue aceptado por el autor. La prioridad sigue siendo comprobar las 11 pantallas, touch, Q-Links, LFO/MEMORY en la MPC.
- **NO MERGE, master intacto.** No entregar versiones anteriores como si fueran válidas.
