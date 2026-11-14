# UI35 — prueba aislada de foco y bancos nativos del SDK de Akai

Origen: UI34 PR40 @ b1cd02edff4a217ab0e86901bfd9c386a557c001.
**No se usa Origamidi como referencia funcional**: el autor indica que su comportamiento también está pendiente.

Fuente de diseño de controles: SDK oficial inmusic-software/mpc-plugin-builder-sdk @ febd2ca5bd9eb16c4a412837196e145566bc981b, docs/ui-reference.md, secciones 3.6, 4.1–4.5, 8.3.

- Construcción del componente custom conforme a SDK: `Mouse Down` invoca `Q-Link` con `Parameter 113..116`, según la posición del control dentro de los cuatro proxies; `Double Click` y `Enter Pressed` usan `Show Overlay` con el `knob overlay` previamente definido en el TUI, foco `Focus` y `Knob` nativos.
- **40 superficies de edición** con foco para Data Wheel y selección del banco hardware en una página nativa con 11 vistas touch. Mantener 143 componentes de la UI base; no modificar el sonido, 254 WAV, ni arte LAB10.
- `qlinkBoundsData`: 4 rectángulos coincidentes `1015 173 245 405`, la caja nativa que rodea los cuatro QLinks visibles en la derecha. El SDK mueve la caja de acuerdo al banco seleccionado cuando se configuran bancos diferentes; aquí los 16 slots del archivo Q-Links.json repiten cuatro proxies para una única caja de cuatro. **No afirmar que se desplaza a subgrupos en esta disposición**. Si se requieren ocho controles en dos cajitas, hay que definir bancos y rectángulos realmente distintos.
- El Data Wheel debe seguir el componente enfocado según el comportamiento oficial, pero **no se ha probado en MPC**.
- Los filmstrips de pointers de QLink y el eclipse siguen sin prueba física. **El eclipse actual conserva una tira 613×392 con recorte rectangular 4:3 observado por el usuario; esta rama no lo corrige, por lo tanto no entregar como UI final ni instalar aún**.
- Los gráficos RESONANCE/GRANULAR siguen sin animación multivariable. Pruebas de la rama: JSON válido, 40 controles con foco SDK, 89 definiciones registradas. No declarar SDK validate completo ni render MPC sin ejecutarlos.
- Audio FLAC PR39 fuera de alcance; WAV actual conservado. No merge/master.

Fuentes reproducibles: tools/ui35_sdk_native_focus.py, skins/TUI.json.
