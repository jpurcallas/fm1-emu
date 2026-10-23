BIOMECH RHYTHM 3 — DUAL-CORE 3+3 C99 CHECKPOINT
23 octubre 2026 — ARCHIVO DE FUENTES EXPERIMENTALES
NO INSTALAR / NO FLASHEAR / NO CONSTITUYE FIRMWARE .FWSC

REALIZADO
- Render de seis pistas existentes, 1–3 en CPU0 y 4–6 en un trabajador
  independiente, con 64 slots globales de polifonía conservados.
- Preparación de eventos, envolventes y aleatoriedad compartida en CPU0,
  para preservar el orden, y cálculo de oscilador/filtro de pistas 4–6
  ejecutado simultáneamente por un pthread CPU1 de prueba.
- Mezcla de contribuciones de todas las voces en el orden ORIGINAL;
  efectos originales de ESTA referencia en el CPU0.
- Lotes de hasta 32 samples, partidos en eventos de secuenciador/roll/ratchet.
- Snapshot y recuperación de estado al simular fallos de CPU1.
- Puente PI32v2 para arranque directo de CPU1 y buzón verificado: FUENTES,
  SIN INTEGRACIÓN/ENLACE NATIVOS DE LA VERSIÓN MUSICAL TODAVÍA.
- BLACK BOX BR3BBX01 en RAM, con anillos por CPU y parser de export JSON.

PRUEBAS INTERNAS CORRECTAS (HOST, NO FM1)
- Tres escenarios: 6 pistas por MIDI, generador y secuenciador con FX,
  y 3074 disparos con 64 slots globales y robo de voz.
- PCM serial y paralelo: BIT A BIT IDÉNTICOS para los tres escenarios.
- PCM también idéntico con fallos simulados y fallback a CPU0.
- Compilación C99 de render y verificación sintáctica del puente PI32.

PENDIENTE CRÍTICO
- Portar y compilar el motor musical completo para la CPU PI32v2.
- Enlazar el puente nativo CPU1 en una copia experimental del arranque,
  impedir que el scheduler CPU1 del SDK tome control simultáneo.
- Asignar RAM y sección ejecutable de worker, enlazar audio de placa/DMA,
  y construir el .fwsc SOLO EMULADOR con su BLACK BOX.
- Comparar música con la versión audible BIOMECH 2 v0.2. Esta fuente
  está basada en la referencia C99 recuperada de la línea v0.37, no en
  un árbol FUENTE exacto de BIOMECH 2 v0.2.
- NO afirmar paridad con el firmware v0.2 ni mayor rendimiento en el FM-1.

FUENTES DE REFERENCIA INALTERADAS:
  original/biomech.c y original/biomech.h
NUEVO MOTOR DIVIDIDO:
  dualcore/biomech.c y dualcore/biomech.h
PUENTE PI32v2:
  dualcore/br3_cpu1_runtime.c, br3_cpu1_entry.S, br3_blackbox.*
PRUEBAS: ejecutar 'sh dualcore/build_host_tests.sh' en Linux/Mac con cc.

BIOMECH 2 v0.2 queda SIN MODIFICAR y en su propia rama checkpoint GitHub.
MASTER NO MODIFICADO.
