# Auditoría obligatoria — procedencia de arte y bloqueo de entregas

Motivo: autor reiteró que está **prohibido utilizar arte anterior/rechazado**. La MPC mostró el recuadro blanco Solaris sobre ACOUSTIC, además de nombres de voces ilegibles por texto sobre texto. La pantalla no debe volver a recibir un paquete con recursos sin cotejar.

## Evidencia y hallazgos (UI32 sin Solaris)
- Las 6 imágenes Solaris viejas se retiraron en PR #36 y no aparecen en el ZIP UI32_SIN_ARTE_ANTIGUO.
- **19 fondos base `lab10_mpc_*`** tienen hashes SHA256 fijados en `tests/art_gate_manifest.json`; su identidad con el conjunto candidato LAB10 anterior está comprobada. **Esto NO certifica que cada vista haya sido cotejada manualmente contra el HTML LAB10 original**: tal cotejo visual y espacial sigue pendiente para todos menos el primer fondo ACOUSTIC previamente comparado.
- **10 overlays adicionales** (ADSR, eclipse BLEND, MEMORY fondo/cabezal/WINDOW/POSITION, MOD ENV2, OSC ondas/selección y LED ON) existen en el paquete, pero **no se ha demostrado de forma individual** su coincidencia con el arte aprobado. Deben quedar bajo revisión, nunca afirmarse aprobados por nomenclatura.
- **55 controles tienen tipos personalizados `UI32_FOCUS_*` y `UI32_TOGGLE_*`** en TUI.json en vez de tipos SDK nativos. No operan como widgets reales (el usuario confirma que ON/OFF no responde y Data Wheel no sigue el toque). El validador general SDK dejó pasar este problema; el nuevo gate lo rechaza.
- Texto sobre texto: la propia imagen base rasteriza etiquetas donde se superpusieron textos dinámicos, por lo que es necesario retirar/ocultar **solo** texto original en las zonas correspondientes o usar una capa limpia verificada, preservando composición y tipografía aprobadas. El gate de hashes por sí solo **no detecta** un texto superpuesto: requiere revisión renderizada de las 11 páginas.

## Control de calidad nuevo
Ejecutar `python tests/audit_release_art.py /path/al/ZIP.zip` con el manifest al lado. **Exit status 1** si existe cualquier elemento prohibido, componente no nativo o overlay sin aprobación. El informe JSON `tests/UI32_VISUAL_AUDIT_FAIL.json` muestra **release_gate=BLOCK**, 55 errores y 10 recursos por revisar. **Nunca eliminar el rechazo del gate para forzar un PASS:** primero verificar, corregir y registrar el SHA del recurso.
- Mantener archivados todos los originales históricos para trazabilidad, pero excluirlos de la carpeta distribuible.
- Los archivos de sonido/DSP se preservan: esta rama **solo contiene auditoría**, sin cambios a binarios, PCM, ni a `skins/TUI.json`.
- El estado de UI32 es **no apto para entrega final** aunque UI31 fue la primera versión cuya pantalla efectivamente renderizó en MPC.
- `master` y PR #35/#36 sin merge.

Regla explícita: **No publicar otra versión hasta pasar la auditoría de procedencia y verificación visual, aparte de pruebas SDK/hardware**.
