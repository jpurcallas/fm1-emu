# GUARIA CONTROLLER — by Yeti Fingers

**Estado: CONCEPTO EN RESERVA (23 de octubre de 2026). NO ES UN FIRMWARE.**

Nombre **estrictamente provisional**. "Guaria" alude a la guaria morada, orquídea/flor nacional de Costa Rica, y funciona como guiño a *Orchid* de Telepathic Instruments / Kevin Parker. No hay nombre definitivo, arquitectura aprobada ni compromiso de implementación.

## Intención musical aprobada como dirección de exploración

La meta **no** es acumular motores ni voces de síntesis: el autor ya trabaja con un MPC One+ y contempla sintetizadores analógicos externos. Se buscan **nuevas maneras de descubrir, componer e interpretar música**.

GUARIA sería un **controlador MIDI armónico independiente en FM-1**, no un instrumento diseñado específicamente para REminiSCENT. Los generadores sonoros externos actuarían como esclavos MIDI. Una pareja especialmente atractiva para el autor es un futuro **Behringer PRO-800** analógico polifónico; deben seguir siendo posibles otros sintetizadores y el MPC.

El interés se centra en **pads armónicos expresivos**, acordes inusuales, relaciones entre escalas y progresiones, transformaciones de voicing/conducción de voces y, como hipótesis, una **libertad armónica** inspirada en el principio FREEDOM de BIOMECH (no copiar su motor rítmico). Explorar armonías contextualizadas sin sustituir arbitrariamente las decisiones musicales del intérprete.

Ejemplos **PROPUESTOS, NO APROBADOS COMO FUNCIONES**:
- Pads para disparar y transformar armonías, no solamente almacenar tríadas.
- Escalas/modos/progresiones como contexto, con libertad graduable, tensiones, cromatismos y acordes protegidos (*anchors*).
- Conducción de voces, inversiones, extensiones, *slash chords*, acordes por cuartas y cambios expresivos durante la interpretación.
- MIDI como salida principal; sin obligación de motor DSP propio.
- Investigar cómo realizar el enrutamiento MIDI hacia módulos externos, con o sin host, sin dar por probada una conexión física concreta.

## Lo que NO se ha decidido

- Nombre final, disposición de pads y controles, gramática de menús, repertorio de escalas/acordes, algoritmos armónicos, arquitectura MIDI, topología de conexión, firmware/base SDK, presupuesto de memoria/CPU.
- No afirmar compatibilidad física, USB host, BLE MIDI ni distribución de canales sin pruebas posteriores.
- No asumir que los mecanismos internos de BIOMECH o REminiSCENT se reutilizan literalmente.

## Prioridades / regla de espera

1. **Primero terminar los prototipos audibles y navegables de BIOMECH RHYTHM y REminiSCENT.**
2. GUARIA queda para conversaciones esporádicas e ideas, sin abrir tareas de firmware, compilación, migración de DSP o pruebas que compitan con esos proyectos.
3. La idea se reevaluará cuando los dos prototipos estén terminados. Cualquier nuevo requisito es propuesta hasta decisión expresa del autor.

## Coordinación histórica entre firmwares y futuros proyectos

Las conversaciones de PR existentes son una bitácora, no un mandato de retomar trabajos obsoletos:
- [PR #24, REminiSCENT](https://github.com/jpurcallas/fm1-emu/pull/24)
- [PR #26, BIOMECH RHYTHM](https://github.com/jpurcallas/fm1-emu/pull/26)

**Antes de una nueva investigación**, leer descripción y comentarios recientes del PR pertinente. Al transferir un hallazgo importante, dejar comentario append-only en el PR receptor con **resultado, versión/commit, evidencia, límites y posible aplicación**. Separar expresamente **PROPUESTO / IMPLEMENTADO / COMPILADO / EJECUTADO** y, si corresponde, **ESCUCHADO POR EL AUTOR**. Registrar qué se reutilizó y qué requirió adaptación. Una conclusión corregida debe indicar claramente qué conclusión antigua reemplaza, manteniendo el historial.

Nunca trasladar direcciones de CPU, patches, linker scripts ni conclusiones de rendimiento entre BIOMECH, REminiSCENT o GUARIA sin volver a verificarlos. Mantener originales y **master** intactos. **NO MERGE** a partir de esta rama conceptual.

## Estado verificable de GUARIA en esta entrada

- **PROPUESTO:** nombre de trabajo y dirección musical, para conservar memoria del concepto.
- **IMPLEMENTADO:** únicamente este documento de idea/seguimiento en una rama separada.
- **COMPILADO:** NO.
- **EJECUTADO / PROBADO / SONANDO:** NO.
- **Hardware físico / MIDI:** NO PROBADO.

**Este archivo no autoriza empezar el tercer firmware.**
