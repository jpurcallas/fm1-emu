# BIOMECH RHYTHM — Recuperación sin pérdida de avances

**24 de octubre de 2026 — rama de recuperación aislada**  
**Estado:** referencia trazable restaurada a nivel Git; **FWSC audible aún no recuperado ni ejecutado**.

## Fuente de partida comprobada

- `checkpoint/biomech-rhythm-2-v02-audible-20261023`, commit `d05d22cddbcd259a190c0c04d810b59aadd95a8d`.
- Último firmware reportado por el autor como audible: `BIOMECH_RHYTHM_2_v0.2_BLACKBOX_DESDE_ARRANQUE_SOLO_EMULADOR.fwsc`, SHA-256 `d99e8d61c483e9b0d770818ace669e912b7ccef81c0fd298cd84540bfbf5c3f0`.
- En v0.2 el autor validó **dos voces audibles a 200 MHz**, con problemas al agregar tercera. Esta es la última *validación subjetiva audible* documentada, **no un firmware final de seis voces**.
- **El checkpoint es una rama histórica**, no una copia demostrada del archivo binario `.fwsc`. No confundir creación de rama con reconstrucción efectiva del paquete.
- Origen de avance posterior: `experiment/biomech3-native-mac-validation-20261024`; el `compare` reporta 172 commits por delante de la base común (172 archivos/cambios no equivale a 172 funciones) y preserva todos los experimentos en GitHub.

## Mejoras posteriores que NO debemos perder

| Subsistema | Fuente preservada | Estado verificado | Regla |
| --- | --- | --- | --- |
| Motor musical BIOMECH 3, 6 pistas y 3+3 | `experiments/biomech-rhythm-3/musical-3plus3/biomech.c`, `.h`, `reference/` en rama v3 | implementado, builds PI32v2 y gates de PCM parciales | No reemplazar motor por el de v0.2; integrar funcionalidad con pruebas audibles |
| Runtime CPU1 y buzón | `br3_cpu1_runtime.c`, `native-cpu1/` | CPU1 ejecutado en autoprueba, no integración musical completa certificada | Preservar, pero no atribuir rendimiento hasta medir |
| SDK V14 | `sdk-v14/build_v14_base.py`, `stage_adapter_v04.py` | FWSC experimental compilado | Comparar inicialización, MIDI, botones, screen y audio con referencia funcional |
| Polifonía 6 notas y timbres | `patch_polyphony_mac_v05.py`, `v06.py`, `v07.py` | six-voice PCM test parcial; no experiencia musical completa | Reintegrar sin inyección obligatoria de notas de laboratorio |
| Pantalla LCD | `patch_lcd_v08.py` | LCD visible, sin interacción validada; luego halt a 4,15 s guest | Preservar el código, investigar regressión antes de usarlo |
| Diagnóstico BLACK BOX y emulador | `br3_blackbox.c`, perfil FM1 LIVE LAB y PR #26 | fallo repetido a `0x00013e09`, soporte de tracing | No convertir el diagnóstico en producto ni encadenar ensayos sin candidato |
| Variantes v0.9/v0.10 | `experiment/biomech3-v09-deferred-audio-irq-20261024` y `experiment/biomech3-v10-irq-context-guard-20261024` | v0.9 silenciosa; v0.10 audio pero falla | Preservadas como historia, **NO PROMOVER** |

## Ruta de rescate acordada

1. Recuperar el **archivo FWSC exacto** de BIOMECH 2 v0.2 (artifact, adjunto o copia local). Verificar SHA-256 y escucharlo en un emulador estable antes de atribuirle estado restaurado.
2. Proteger esa referencia como **golden build** y registrar su audio/controles: arranque, botones, knobs, reloj, dos voces. Si el .fwsc no aparece, reconstruirlo desde fuentes exactas cuando estén disponibles; **no inventar binario ni prometer bit-exactitud sin prueba**.
3. Comparar el flujo **ejecutable** del baseline con v3: arranque → MIDI/teclado → secuenciador → DSP → DMA → LCD; identificar primer cambio que perdió funcionalidad. La inyección de notas v05–v07 no sustituye al pipeline de entrada.
4. Reaplicar **solo cambios del motor 3+3 y demás mejoras que pasen controles de regresión**, en rama experimental derivada de recuperación; mantener las seis pistas/diseño deseados y realizar checkpoints audibles frecuentes. No alterar los artefactos madres.
5. **Criterio de aceptación**: audio tocable y controlable, pantalla reactiva, seis pistas, secuenciador y efectos, estabilidad >4,2 s guest; pruebas automáticas no sustituyen evaluación del autor.

## Protección

- Esta rama parte del checkpoint v0.2; no hace merge ni modifica `master`.
- La rama original `checkpoint/...`, las ramas BIOMECH 3 y la historia del PR #26 quedan intactas.
- **Sin FWSC recuperado, no afirmar que existe un firmware restaurado listo para descargar.**
