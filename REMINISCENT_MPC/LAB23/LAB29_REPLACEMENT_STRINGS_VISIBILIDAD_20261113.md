# REminiSCENT LAB29 — corrección de navegación de 11 páginas basada en Origamidi funcional

Fecha 2026-11-13 (Costa Rica). Se inspeccionaron PR #31, acuerdos, SDK docs/ui-reference.md §7.4, el ZIP privado Origamidi V22 y el ZIP privado REminiSCENT LAB28 antes de modificar.

## Problema medible
El TUI.json de Origamidi V22 —funcional en MPC One+ según autor— incluye en `pageData.replacementStrings` todas las opciones de sus controladores de visualización (`Parameter 41` 3 opciones; `Parameter 44` 10 opciones). En REminiSCENT LAB28, `IndexedEnabling/0..10/11/Parameter 112` gobierna las 11 pantallas táctiles, pero `replacementStrings` sólo declaraba `Parameter 124 WHITE/PINK`. Las opciones de las páginas 112, subpaneles 109..111, Memory 117 y Solaris 122 faltaban. El SDK documenta que para `IndexedEnabling` el denominador debe igualar el número de opciones declarado en `replacementStrings`. **No es prueba definitiva de que este sea el único fallo de render en hardware; sí es una discrepancia concreta contra el SDK y Origamidi.**

## Cambio acotado
Fuente `REMINISCENT_MPC/LAB23/skins/TUI.json` commit `71c71d89e6b23ccfd68b7905d4c30a5e94400e9c`:
- `Parameter 109`: 4 opciones Character
- `Parameter 110`: 4 opciones SEND
- `Parameter 111`: 3 opciones MOD (LFO1/LFO2/ENV2, sin Mod Wheel)
- `Parameter 112`: **11** opciones touch (ACOUSTIC, OSC, BLEND, ENVELOPE, MEMORY, RESONANCE, FILTER, CHARACTER, GRANULAR, MOD, SEND FX)
- `Parameter 117`: 3 opciones MEMORY
- `Parameter 122`: 7 estados Solaris
- `Parameter 124`: dos opciones WHITE/PINK ya existentes, conservadas
Se comprobaron las 22 expresiones IndexedEnabling únicas contra los tamaños y rangos declarados. **No se cambia ninguna posición, imagen, condición visual de LAB28, parámetro de C++, componente ni interfaz rechazada.**

## Paquete de prueba privado
`/REminiSCENT MPC/REminiSCENT_UI29_11PANTALLAS_PARAMETROS_SDK_CORREGIDOS.zip`.
- ZIP **301.227.774 bytes**, SHA256 **`789dd44b5c88f74d8f94689aa83624dc28740bd5e4f7d069775fe401864eb4ff`**; ZIP.testzip()=None.
- 289 entradas, 254 WAV, 26 PNG, dos ELF ARM, todos sin edición respecto a LAB28.
- **ÚNICO ARCHIVO DIFERENTE ENTRE LAB28 Y LAB29: `Plugin Skins/TUI.json`**; byte compare todas las entradas.
- Git blob del TUI: `e531ba98734cefe4b4e70b458e0508e044e4ec90`, corresponde al contenido instalado.
- SDK oficial `validate.check_skins`: **0 errores/0 advertencias**, todos los handles 0..124.
- Guardado con upload confirmado en Biblioteca privada, no subido a GitHub el audio/arte de terceros.

## Límites / próxima prueba
No se ha visto esta variante LAB29 en MPC física. No asegurar que el problema gráfico está arreglado antes de verificar render de las 11 páginas. Si falla, NO usar imágenes viejas, no atribuirlo a instalación anterior ya descartada por el autor. Investigar trazas de renderer y bindings conforme a SDK y Origamidi. No repetir test DSP/audios exitosos. `master` intacto; sin merge.