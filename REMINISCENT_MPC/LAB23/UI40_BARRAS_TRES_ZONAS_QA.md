# REminiSCENT UI40 — Barras de tres zonas: implementación sin instalación

## Fuente de verdad
- UI39 PR #45 head: 7fb7d527bab1991ad925cc75eb791cb315915669.
- Aprobación explícita del autor: capturas 14-nov-2026 de MEMORY (FREEZE/REVERSE/TIDE) y lista consolidada de 11 módulos.
- Contrato: conservar estética y marcos de la skin actual; **identidad / ON-OFF / EDIT** en tres zonas; ON/OFF independiente de selección EDIT en MEMORY, CHARACTER, MOD y SEND FX. El HTML viejo no autoriza volver a la interacción antigua.
- **No cambiar DSP, 254 WAV, presets, contract host, otras pantallas ni master.**

## Implementación fuente
Generador: tools/ui40_build_approved_three_zone_bars.py
- Trabaja sobre TUI.json de UI39 y los PNG originales de esa misma skin (en el paquete privado, no publicados en GitHub).
- 14 interruptores Button nativos: parámetros 5–18 según módulo, separados de 14 selectores EDIT.
- Tres selectores MEMORY_EDIT_* nuevos, todos apuntando a **Parameter 117**, valores 0,1,2.
- CHARACTER EDIT -> Parameter 109; MOD -> 111; SEND -> 110.
- Power conserva bool histórico independiente. Cada Button tiene imágenes de estado ON/OFF o EDIT seleccionado/no seleccionado.
- Produce 12 imágenes de página **nuevas y reversibles** para las variantes actuales de las cuatro pantallas, preservando el marco y todos los píxeles fuera del interior de las barras. Los 12 PNG originales quedan intactos.
- Genera 12 overlays PNG reutilizables, TUI.json y manifest SHA256. Usa la estética/paleta de la interfaz actual; el esquema negro/verde era solamente funcional, NO un nuevo tema de color.
- No introduce un parámetro de host nuevo. Conservar 11 pestañas.

## Reproducción y QA
Instalar Pillow para el generador fuera de la MPC. Ejecutar con el TUI y los PNG de la skin actual:
python tools/ui40_build_approved_three_zone_bars.py --tui /ruta/TUI.json --assets /ruta/skins --out /ruta/salida
python tests/test_ui40_three_zone_bars.py --tui /ruta/TUI.json --assets /ruta/skins --out /ruta/verificacion

La prueba compara mappings, áreas táctiles, selección independiente, imágenes existentes, 12 páginas y conservación de otras piezas; no es una prueba física.

## Estado y puerta de entrega
- **Implementado:** código fuente reproducible y prueba estructural.
- **Probado localmente:** contra el paquete WAV UI37 conservado; validación estructural PASS, sin tocar fuentes.
- **Pendiente:** ejecutar exactamente sobre archivos de skin UI39 de ensamblaje, empaquetar resultado con ARM de UI39/actual, comprobar validador oficial SDK y MPC real.
- **No es aún versión para instalar. NO MERGE. NO ENTREGA DE INTERMEDIOS.**
- Eclipse nuevo aprobado, RESONANCE radar, GRANULAR ADN, FILTER MIX y demás correcciones de la lista permanecen pendientes: **no declarar UI completo**.
