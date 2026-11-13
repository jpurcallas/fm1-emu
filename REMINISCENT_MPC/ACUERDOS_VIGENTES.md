# REminiSCENT — ACUERDOS VIGENTES Y PROTOCOLO OBLIGATORIO
Fecha: 2026-11-13. Proyecto prioritario: plugin externo nativo para **MPC One+**, MPC OS 3.10.1.
**Regla: discusión libre, ejecución fiel.** Los acuerdos del autor son la fuente de verdad. La rama principal y los artefactos aprobados no se sustituyen sin aprobación.

## Flujo obligatorio en cada intervención
1. Antes de cambiar código: leer este documento, la bitácora y el estado de integración; revisar PR y commit pertinentes.
2. No empezar implementaciones paralelas ni reconstruir algo que ya funciona. Basarse en el último código **aprobado**, no en la última versión experimental.
3. Implementar sobre rama aislada; documentar diff, pruebas, errores y limitaciones; distinguir **propuesto / implementado / compilado / ejecutado en host / probado por el autor en MPC / aprobado**.
4. Subir código y documentación nuevos a esta rama de GitHub al terminar la intervención, mediante PR; **no mergear ni publicar muestras de terceros sin autorización explícita**. No declarar éxito antes de comprobarlo.
5. En caso de fallos difíciles: caja negra que registre entrada MIDI, parámetros, carga de muestras, DSP, niveles y estado; no ajustes al azar.
6. Tras cada avance, actualizar el estado y las decisiones de forma que otra conversación pueda continuar desde allí.

## Aprobado por el autor
- **Bridge 16**: Hall espacial REVERB y MASTER PRESENCE ±12 dB, además de MEMORY, RESONANCE, LFO y demás DSP ya validado; conservar implementación.
- Bridge 17: **RECHAZADO** por ruido, ADPCM, colas truncadas, clicks, loops destructivos, efectos activados y saturación. Nunca usar como base acústica.
- Contrabajo G1 PCM original: validado por comparación A/B con motor y aprobado auditivamente.
- Banco de calidad LAB19: 27 fuentes acústicas / 254 samples PCM; preparación y pruebas de host, **no aprobación auditiva del conjunto**.
- Didgeridoo se conserva. Dos variantes de sustain A/B de 80 s **aprobadas por oído**; sus ciclos más cortos no pueden interpretarse como loop de 80 s.
- Duduk **excluido** por dificultad técnica y restricción de licencia. No reemplazar sin decisión.
- Bandoneón incluido por decisión del autor; procedencia/licencia archivadas, sin bloquear pruebas privadas.
- Los instrumentos deben responder a MIDI con referencia A4=440 Hz, conservando vibrato e inestabilidad natural; no autotune agresivo.
- Instrumentos de decaimiento natural: muestras completas sin loops artificiales; no degradar para reducir tamaño. Optimizar solo después de escuchar.
- Presets NUEVOS: DELAY/REVERB/MOD1/MOD2 OFF; LFO1/LFO2 OFF; LO-FI TAPE OFF; cutoff abierto 100%; RESONANCE MIX 0%; los cuatro SEND FX MIX 100%, los MOD DEPTH 100%, aun si sus efectos están apagados. Presets existentes conservan valores guardados.
- MOD1/MOD2 seleccionan algoritmo independientemente (chorus, flanger, phaser, tremolo, auto-pan) y los 4 Q-Links cambian según algoritmo.
- BLEND: identificar visualmente ACOUSTIC y OSC en eclipse o master dial; eliminar leyenda de laboratorio PRESENCE A/B / monitor +12dB.
- Mantener UI aprobada; no rediseñarla unilateralmente.
- El autor **no quiere entregas parciales de 2-3 voces**: siguiente revisión de voces en conjunto; prioridad llegar a plugin MPC real.

## Componentes que NO deben confundirse
- `REminiSCENT_AUDIO_DEV_MPC_ARM32_SOLO_PRUEBA.zip`: binarios externos ARM32/ARM64 previos, solamente 3 WAV; nunca probado físicamente en MPC.
- `REminiSCENT_MPC_SDK_MOTOR06_PREPARADO.zip`: proyecto de motor anterior para SDK.
- `REminiSCENT_BRIDGE16_HALL_ESPACIAL_PRESENCE_MAC_EXPERIMENTAL.zip`: DSP aprobado auditivamente en host.
- `REminiSCENT_LAB19_BANCO_27_VOCES_PCM_MAC_EXPERIMENTAL.zip`: 27 voces PCM con motor Mac, 254 archivos, ~301MB comprimidos; no equivale a plugin MPC.
- Evitar afirmar que fusionar código implica compilar para ARM32 o funcionar en hardware.
## Próximo objetivo
Migrar DSP de Bridge16/LAB19 y 27 fuentes PCM al plugin SDK ya iniciado; validar artefacto ARM32, parámetros, recursos Content, host simulator y luego con el autor en MPC. No borrar avances ni subir los samples con licencias sin revisar.
