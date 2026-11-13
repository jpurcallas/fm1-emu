# REminiSCENT MPC — lo que falta para trasladar fielmente la UI aprobada
Fecha: 2026-11-13. Ver primero [ACUERDOS_VIGENTES.md](ACUERDOS_VIGENTES.md).
Estado: AUDITORÍA DE BRECHAS. **No implica que estos puntos estén implementados**.

## Hechos comprobados
1. El autor compiló **LAB20 ARM32 ELF** en su Mac con el SDK/Zig existente, el 13 nov. También se construyó ARM64 y prueba nativa. No incluye 254 WAV en su Mac; el script advirtió NO INSTALAR EN MPC. No se probó físicamente.
2. El kit `REminiSCENT_MPC_LAB20_COMPILAR_EN_MAC.zip` (654822 bytes) contiene `src/REminiSCENTMPC.cpp`, motor Bridge16, `Content/bank.tsv`, 105 parámetros exportados. **NO CONTIENE directorio `skins/` ni `ui.json` para la UI definitiva**. Por ello, sin TUI/Q-Links MPC cae a skin genérica del SDK.
3. La referencia gráfica es `REminiSCENT_UI_LAB_10_INTEGRATION.html` más los contratos v0.3, y Bridge16/UI de trabajo autorizada: 11 módulos ACOUSTIC/OSC/BLEND/ENVELOPE/MEMORY/RESONANCE/FILTER/CHARACTER/GRANULAR/MOD/SEND FX. No recrear desde cero.
4. El SDK (`docs/ui-reference.md`) soporta `TUI.json`, `Q-Links.json`, PNG/JPEG, componentes con geometría arbitraria y **hasta 32 tabs**, con 8 sub-tabs por función; sus tabs documentadas usan `fnKeyIndex`/subíndices y acción touch `Mouse Down`. **No está demostrado en MPC** que la navegación EXACTA de 11 pestañas táctiles visibles se pueda reproducir tal cual. Esto requiere diseño de navegación y prueba de hardware, no asumir que tener 32 tabs lo resuelve visualmente.
5. De los 113 campos de la UI, se exportan 105 parámetros MPC; ocho quedaron excluidos: `selectedMemory`, `selectedChar`, `selectedSend`, `selectedMod` (estado visual de selección), y `params.acousticNoise`, `params.spread`, `params.filterEnv`, `params.filterTrack` (sin correspondencia completa DSP verificada). Revisar decisión/contrato de cada uno; no ocultar controles.
6. El adaptador usa índices de campo v[0]...v[112] para `applyParams`; comprobar mapeo **pantalla→parámetro→DSP→audio** y restauración de estado. Variables visuales no son automáticamente parámetros DSP.
7. Contrato v0.3: DATA WHEEL al tocar parámetro, eclipse BLEND, Q-Links por pantalla, selectores, satélites ADSR; ninguna de estas interacciones está aún comprobada en skin nativa.
8. Los 254 WAV PCM de 27 voces todavía NO forman parte de la compilación ARM32 instalada en Mac. La optimización de RAM anunciada en staging no sustituye a una prueba real con los 254 samples.
9. SDK advierte: sin `TUI.json` usa UI genérica; errores de parseo de TUI pueden dejar **ninguna pestaña**. Exige validación estricta de JSON, rutas, imágenes y Q-Links antes de instalar.

## Orden obligatorio de ejecución
- [ ] Convertir la UI aprobada (recursos gráficos y 11 pantallas) a **skin real** `skins/TUI.json`, `skins/Q-Links.json`, assets; fidelidad de arte y disposición; **no UI genérica ni simplificación**.
- [ ] Implementar navegación táctil de once pantallas y revisar visualmente cada estado (incluido A/B, OSC, MOD algoritmo y env).
- [ ] Auditar los 105 parámetros + los ocho campos no exportados; conectar o modelar estado visual, completar DSP cuando corresponda sin inventar comportamientos; cambios requieren fidelidad a acuerdos.
- [ ] Probar toque→foco→Data Wheel y Q-Links (grupos de cuatro), selectores, modos dependientes de MOD, readouts y presets/proyecto.
- [ ] Incluir 254 WAV PCM de LAB19 en `Content/samples` real/portátil con hashes; no symlink ni ADPCM ni loops no aprobados. Comprobar consumo RAM y latencia de carga en MPC.
- [ ] Validar JSON de skin/índices/rutas y builds de host+ARM32 sobre código definitivo; no confundir compilación con UI renderizada.
- [ ] Prueba física en MPC One+ OS 3.10.1: lista de 11 pantallas; toques, Data Wheel, Q-Links, audio seco, reverb, presence, 27 voces, CPU/RAM, guardado, apertura proyecto; caja negra ante fallos.
- [ ] Registro de evidencia y aprobación del autor ANTES de declarar completo o unir rama.

**No entregar plugin como terminado mientras cualquiera de los ítems anteriores no esté implementado y validado.**
