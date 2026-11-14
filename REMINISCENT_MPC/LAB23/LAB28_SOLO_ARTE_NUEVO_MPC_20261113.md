# REminiSCENT — limpieza obligatoria de interfaz (solo arte aprobado)

Fecha 2026-11-13 Costa Rica. Regla: **DISCUSIÓN LIBRE, EJECUCIÓN FIEL**. Se revisaron acuerdos, PR #31, la rama, TUI real de LAB27 y la estructura funcional del ZIP Origamidi V22.

## Diagnóstico confirmado
- En LAB27 existía `FALLBACK_ACOUSTIC_ALWAYS_VISIBLE`, un componente gráfico sin condición de pantalla; incumplía la orden de eliminar toda interfaz de respaldo rechazada.
- Además el ZIP seguía transportando `solaris_v09_plate.png` (una imagen opaca), seis fotogramas de Solaris y otros PNG ya no referenciados. Aunque el TUI LAB27 no activaba este splash, se incumplía la prohibición de incluirlo en el paquete.
- En 23 componentes condicionados, `showWhenDataModelInvalid` seguía en `Show` a diferencia de Origamidi V22, que utiliza `Hide` con `IndexedEnabling`. Según SDK `docs/ui-reference.md` §§5.1-5.2 y 7.4, la nueva skin de REminiSCENT usa `Hide` para todos los componentes condicionados. **No se ha demostrado que este fuera el único motivo de la pantalla incorrecta.**
- Imagen real del autor: pantalla blanca con logo y WHITE/PINK; no corresponde a la interfaz aprobada. Es posible que el plugin haya cargado un paquete/skin antiguo instalado; no afirmar que es caché confirmado sin inspeccionar la SD. El SDK `docs/install-and-test.md` ordena reiniciar MPC si cambian skins.

## Cambio de fuente
`REMINISCENT_MPC/LAB23/skins/TUI.json` commit `392f014ff49b974502078c5e08c1d1cafc524f53`.
- Eliminado `FALLBACK_ACOUSTIC_ALWAYS_VISIBLE`.
- Los 19 fondos/estados visuales aprobados constituyen **11 páginas táctiles** indexadas 0..10 por `Parameter 112`.
- Los 23 componentes con `additionalInvalidatingHandles` que antes usaban `Show` ahora usan `Hide`, según patrón del Origamidi funcional.
- Sin cambiar posición, controles, Q-Links, DSP, PCM ni MIDI.

## Paquete privado de prueba
`/REminiSCENT MPC/REminiSCENT_UI11_SOLO_ARTE_NUEVO_ARM32_COMPLETO.zip`.
- **301.227.563 bytes**; SHA256 `ae3829e1361cb6c977d161aafa2fa3af96a5daf27ac5670886633bfe7c2b52a6`.
- 289 entradas, 254 WAV **byte idénticos a LAB27**, dos binarios ARM32/ARM64 **byte idénticos a LAB27 v0.27.0**, 26 PNG **todos y solo los referenciados por el TUI**, sin placa Solaris, sin fotogramas no usados, sin imágenes de respaldo.
- `TUI.json` SHA256 `909f67cbf4ee980a1d61755c0ca1ebcce9fb2e6dbee6f18e46ec1e767a240c33`, Git blob `93bd5d978212b8213348caa71e72834a1f041ce1`.
- Verificación ZIP `testzip()=None`, 11 índices de página, sin componentes de fallback, todos los parámetros en rango 0..124, **SDK check_skins: 0 errores, 0 advertencias**.
- Arte aprobado en los 11 módulos; nuevo TUI compilado/armado con los binarios LAB27 ya compilados; **render táctil REAL EN MPC TODAVÍA NO VALIDADO**. No se vuelve a sustituir el arte en caso de error.

## Instalación limpia (necesaria para evitar restos)
1. Retirar **todas** las copias anteriores de la carpeta `Yeti Fingers - VST - REminiSCENT` de las raíces `VST2 Plugins` usadas por la MPC (SD, USB y otros medios). No borrar otras carpetas ni plugins.
2. Descomprimir solo este ZIP, y copiar la única carpeta `Yeti Fingers - VST - REminiSCENT` dentro de `VST2 Plugins` de **una** unidad.
3. Reiniciar MPC y cargar REminiSCENT en un track nuevo; según SDK el reinicio permite releer skins. Si reaparece la pantalla rechazada, detenerse y verificar ubicación/duplicados, no improvisar fallback.

`master` intacta. Sin merge. No probar ni reescribir audio que ya pasó test.