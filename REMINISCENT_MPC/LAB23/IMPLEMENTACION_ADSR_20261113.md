# REminiSCENT MPC LAB23 — implementación directa de ADSR nativo (13 nov 2026)

## Base comprobada antes de intervenir
PR #31, rama `work/reminiscent-mpc-integracion-20261113`, origen `b137c8d45d117d4cb995ad58bd79b1c06c29ef91`; comentarios recientes y `ACUERDOS_VIGENTES.md` consultados. Se preserva `master` y el DSP Bridge16. No usar Bridge17.

## Cambio real implementado
- `skins/TUI.json`, commit `45f1136a203ce8e36ed5df387c91338161efeb0a`: componente nativo **Envelope ADSR** sobre la región aprobada de la página ENVELOPE (rectángulo `65 249 555 185`), sin header, con fondos transparentes y controles circulares. Cuatro handles de etapa conectados a parámetros MPC **29 Attack, 30 Decay, 31 Sustain, 32 Release**, que ya existen en motor Bridge16. Componente visible sólo en módulo táctil 3/11 mediante `IndexedEnabling/3/11/Parameter 112`.
- La imagen fija del fondo `fondos/03.png` se conserva en el respaldo como referencia exacta e inmutable; la página operativa usa `fondos/03_adsr_no_static_curve.png`, misma imagen original con **solamente la curva fija retirada** (región de píxeles modificados x49..643, y233..458). Marco, rótulos, satélites, franjas, tabs y Q-Links originales preservados. No se cambia código del motor ni el sonido.
- Manifiesto del PNG adicional, commit `a299af46ea75cd0af23c5f6488f0d5793200b1db`: 43 archivos.
- Gate del código de interfaz actualizado con los 4 handles y fondo operativo, commit `90ad1281d12d51ce387921a74938e2744929344b`.

## Recursos privados
- Respaldo completo de **43 PNG + manifiesto + README** en `/REminiSCENT MPC/REminiSCENT_LAB23_43_PNG_ADSR_INTERACTIVO_PRIVADO.zip` (Biblioteca, subida confirmada).
- ZIP **6.006.178 bytes**, SHA256 **`3f641a75775037cca1f83e2edf6f3378b7dbaef2ef8d9154b715269e2ed08924`**, `testzip() == None`, **43/43 SHA256 y dimensiones comprobados**, 45 entradas.
- Recurso nuevo: `skins/fondos/03_adsr_no_static_curve.png`, **403.727 bytes**, SHA256 `cf795e2abfbf1757aa11606d0fd028e16e17f7f0f69600e1b012edf8cedcf3a7`, 1280×628. El arte binario se conserva privado; la ruta y hashes en GitHub público.

## Límites y siguiente integración
Este avance **IMPLEMENTA** la curva editable en el formato del SDK, pero **NO demuestra render ni manipulación física** en MPC One+ y no constituye aprobación visual final. La representación interna del Envelope nativo podría requerir ajustes de estilo tras la prueba MPC para respetar la curva y satélites exactos de LAB10; no se aprueba ninguna sustitución visual unilateral.

Siguen pendientes LFO/MEMORY dinámicos, splash Solaris v09, conexión de `spread/filterEnv/filterTrack` aún sin conducta DSP aprobada; `acousticNoise` sigue PROPUESTO, no se inventa; ARM32 LAB23, audio/CPU/RAM/presets, prueba de navegación táctil/Data Wheel y aprobación del autor. El banco LAB19 privado de 254 WAV permanece sin alteraciones. **NO publicar instalador incompleto ni hacer repetir pruebas anteriores al autor. NO MERGE.**
