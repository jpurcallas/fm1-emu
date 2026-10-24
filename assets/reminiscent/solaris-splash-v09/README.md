# REminiSCENT — SOLARIS splash v09 — APROBADO POR EL AUTOR

**Fecha de aprobación:** 24 de octubre de 2026 (Costa Rica).  
**Estado:** APROBADO COMO DISEÑO Y ANIMACIÓN DE ARRANQUE. **NO** integrado al firmware, NO probado sobre FM-1.  
**Alcance:** Archivo visual y laboratorio C99 reproducible en rama aislada. **NO MERGE / NO EDITAR MASTER**.

## Identidad visual aprobada

- **Inicio:** estación espacial fija, inmóvil y a la escala del arte aprobado. Encima: «DBA Corporation Presents:» (guiño a *Solaris*).
- **Match cut:** hasta el fotograma 66 inclusive, estación 100 % opaca, ondas invisibles. En el **fotograma 67 (2,68 s a 25 FPS)**, sustitución inmediata por las ondas; sin fundido, glitch, zoom ni movimiento de cámara.
- **Geometría del anillo/ondas:** la primera onda exterior coincide con centro, perspectiva, eje mayor/menor e inclinación de la circunferencia del anillo al producirse el cambio; después se expande. Geometría de laboratorio: centro (120,25338579; 129,86907726), semiejes (64,47929454; 22,62433963), ángulo 17,69680325 grados.
- **Ondas:** trazos matemáticos sencillos, de pocas líneas y movimiento fluido, **tres ciclos** que crecen y desaparecen; no usar fotogramas de onda como texturas precalculadas en el motor C99.
- **Final:** identidad visual original aprobada «REminiSCENT — ACOUSTIC MEMORY SYNTHESIZER — by Yeti Fingers» completa, sin recortar letras ni cubrir ondas con rectángulo.
- **Colores:** amarillo pastel / líneas oscuras. Resolución exacta: **240 × 240**.

## Archivos archivados

| Archivo | Función | SHA-256 |
| --- | --- | --- |
| `REminiSCENT_SOLARIS_ONDAS_SIMPLES_ENCAJE_Y_TITULO_v09_240x240.mp4` | Referencia visual principal, 6 s, 25 FPS | `cc328c4f295f7d27e98a628fff0cfcb01315de0a70592145848de095fac83414` |
| `REminiSCENT_SOLARIS_ONDAS_SIMPLES_ENCAJE_Y_TITULO_v09_240x240.gif` | Previsualización animada del mismo diseño | `18a93cacaedfaa62cf10dfd5432f3faeb7e123f476f07afb6646f362101fb887` |
| `REminiSCENT_SOLARIS_V09_MATEMATICO_LAB.zip` | Laboratorio integral con C99, renderizador Python, paneles originales, MP4/GIF y HTML | `cc0403bc3f0e7dd7afc1171bf48ed5992fd41fd771baa2fd0fe2f35f0cc7fb52` |
| `REminiSCENT_SOLARIS_v09_waves.c` | Cálculo de ondas en C99; fuente también en el ZIP original | Ver archivo |
| `REminiSCENT_SOLARIS_v09_render.py` | Renderizador host; fuente también en el ZIP original | Ver archivo |

La **copia íntegra adicional** del GIF, MP4, ZIP, HTML y fotogramas de referencia quedó guardada en la Biblioteca de ChatGPT bajo `/REMINISCENT/approved-splash/SOLARIS-v09/`.

## Reproducción del laboratorio en Mac

Extraer el ZIP y ejecutar el script `REminiSCENT_SOLARIS_v09_render.py` en un entorno con Python 3, Pillow, numpy, ffmpeg y compilador C. El código compila su núcleo matemático C99 en el host. Esta compilación **NO** equivale a compilar o ejecutar sobre el SDK V14/PI32v2 del FM-1.

## Integración futura

1. Usar este diseño y estos archivos **como madre visual aprobada**: no sustituirlos por reinterpretaciones.
2. Conservar los anclajes geométricos exactos y el punto de corte f67.
3. Adaptar el renderizador matemático y el dibujo estático al framebuffer/controlador LCD real; medir tiempo de render, memoria y coste de arranque en emulador y hardware.
4. Confirmar en pantalla física que el texto sigue legible y que no aparecen flashes, reescalados o geometría invertida.
5. Integrar únicamente con autorización del autor y sin alterar síntesis, PARTS ni firmware aprobado.

**Archivo de referencia para futura integración; NO es firmware instalable.**
