# UI34 — filtro dinámico LAB10: ENV y KEY TRACK
Fecha: 2026-11-14. ESTADO: fuente implementada, no instalada ni aprobada.

Base: UI33 PR38. Fondo LAB10 original conservado.
- Parámetros visuales host 125 (posición efectiva), 126 (frame), 127 (grupo), añadidos al final; DSP sin cambiar.
- Fórmula LAB10 exacta: effective=clamp(cutoff+(env-64)*37/127+(track-64)*15/127,0,127).
- C++ syncFilterVisual() responde a host cutoff42, env107 y track108.
- Dos tiras de 32 fotogramas en 595×7392 cada una (límite de textura 8192); línea fantasma de filtro original teal discontinua extraída de LAB10. La imagen principal se regenera desde HTML original ocultando su curva fantasma antigua para impedir duplicación.
- UI34 TUI 143 componentes, originales 19 fondos LAB10 sin editar. Fuente reproducible: tools/ui34_filter_envtrack_from_approved_html.py.
- LIMITACIONES: MIX host43 todavía no modifica fielmente todas las curvas. RESONANCE 4 parámetros y GRANULAR 4 parámetros todavía no están visualmente conectados; coverage test en PR38 da BLOCK. Gate de procedencia PR37 permanece BLOCK; falta validación hardware.
- Audio comprimido FLAC253 mantenido separado en PR39 (didgeridoo A único) sin mezclar cambios ni publicar muestras.
NO MERGE. NO ENTREGA AL AUTOR HASTA QA.
