# REminiSCENT — UX 02: mapa de shortcuts como BIOMECH v0.9.8

**Estado: PROTOTIPO HTML jugable y probado en Chromium. NO firmware C99/V14 ni control real de hardware.** Se deriva de UX01; conserva firmware v0.13, splash aprobado y UX01 intactos.

## Origen validado

En `biomech_rhythm_v098_unified_genstatus.html` del laboratorio aprobado de BIOMECH se encuentra `panelMiniMap`, un recuadro **permanente de 30 píxeles** dentro de los 240×240, en una rejilla de **2 filas por 6 columnas**. Muestra el nombre lógico de cada botón físico y **resalta la función activa**. La asignación original de BIOMECH es fila superior `FX | MIX (SEL) | ENV | LFO | VOICE (EDIT) | PERFORM (GLO)`; fila inferior `HOME | SAVE | ROLL (ARP) | SEQ | PLAY | REC`. No copiamos su identidad gráfica ni asumimos que las doce acciones deban tener idéntico significado en REminiSCENT.

## Mapeo UX02 propuesto, PENDIENTE DE APROBACIÓN DEL AUTOR

| Botón serigrafiado FM-1 | Texto mini-mapa REminiSCENT | Acción en prototipo |
|---|---|---|
| FX | FX | Salta a MIXER / MOD A (buses compartidos), luego ALGORITHM navega FX |
| SEL | MIX | Salta a MIXER / LEVELS |
| ENV | ENV | Salta a SOUND / ENVELOPE gráfico |
| LFO | LFO | Salta a SOUND / LFO 1, ALGORITHM avanza a LFO 2 |
| EDIT | SOUND | Salta a SOUND / SOURCE |
| GLO | PERF | Salta a PERFORMANCE / ROUTING |
| HOME | HOME | Regresa a SOUND / SOURCE **provisionalmente**, hasta diseñar HOME |
| SAVE | SAVE | Guarda **solo en memoria del navegador** la PART seleccionada |
| ARP | ARP? | **Sin función aprobada; no crea arpegiador** |
| SEQ | SEQ | Salta a SEQUENCER / STEPS gráfico |
| PLAY/STOP | PLAY | Cambia estado PLAY/STOP **solo de la UI de prueba**, no audio |
| REC | REC | Cambia estado REC DEMO, **no graba MIDI ni Motion reales** |

## Regla de navegación

La botonera física es **solo una capa de shortcuts**, no reemplaza los cuatro controles permanentes: MASTER = volumen; SELECT = PART actual; PRESET = banco/sonido de PART actual (demo); ALGORITHM = recorrer submenús de la sección actual. KNOB 1–4 siempre muestran/editan exactamente cuatro parámetros del submenú abierto. SELECT no borra valores de otras PARTS. El mini-mapa se pinta como dos filas de seis celdas y conserva la posición física; casilla activa en coral sobre base azul petróleo, todo sobre el fondo **amarillo pastel** aprobado. La edición de envelopes sigue gráfica, el secuenciador mantiene cuatro tracks 16×4 páginas y MIXER cuatro partes.

`LFO 1` y `LFO 2` se añadieron en UX02 a la lista SOUND para materializar el acceso directo LFO, con RATE/DEPTH/SHAPE/TARGET **parámetros de maqueta**, que no sustituyen ni especifican aún el esquema real C99 del motor. Las asignaciones de FX/SEL/EDIT/GLO/HOME/ARP quedan sujetas a revisión musical del autor.

## Verificación ejecutada

- Sintaxis Node 22 PASS; prueba JS de estado: 12 botones, ENV gráfico, LFO1→LFO2 con ALGORITHM, SEL→MIX, FX→MOD A, GLO→PERFORMANCE, EDIT→SOUND, SEQ→STEPS, PLAY/REC variables de demo, ARP intacto, SELECT preserva edición de PARTS.
- Chromium real con `page.set_content` de HTML autocontenido: botones 12, click ENV retorna SOUND/ENVELOPE; captura Canvas LCD en 240×240 y capturas LFO y SEQ. Navegación browser bloquea `file://` en entorno automatizado (`ERR_BLOCKED_BY_ADMINISTRATOR`), pero el HTML se verificó en DOM real y puede abrirse como archivo local en el navegador del autor, como UX01.
- **NO** se ha compilado al SDK V14 ni se ha medido espacio en FM-1, ni se ha probado respuesta al panel físico, recepción DSP, persistencia o audio. Todo es evaluación de interacción sin audio de navegador.

## Resultado y protecciones

En pantalla (240×240), la franja inferior de **30 píxeles** muestra 12 funciones y resaltados; los 4 parámetros usan una franja de ~46 píxeles justo encima. Es una solución legible como en BIOMECH sin mostrar un segundo panel ficticio. Más abajo en la página HTML se incluyen botones virtuales equivalentes a los físicos, clicables, con serigrafía y nombre lógico.

**No fusionar con `master` ni sustituir v0.13** antes de aprobación expresa de posición, legibilidad y asignaciones de shortcuts. Próxima etapa: autor usa UX02 y acuerda qué hace cada botón; después integrar en FWSC C99 sin recortar motor, verificar encoders, navegación y audio por separado.