# UI39 — Contrato de selector acústico en inglés (sólo pantalla)

**Origen verificado:** UI38 PR #44 head `b1bd68de779d2add2dac0b0f1c4380531697aeb8`. Esta rama se basa en ella y conserva 254 WAV originales.

## Criterios aprobados
- 27 nombres ingleses, simplificados, en MAYÚSCULAS. Misma lista para A/B.
- Orden fijado: PIANO, HARPSICHORD, BANDONEON, VIBRAPHONE, MARIMBA, GLASS HARP, MBIRA, BALAFON, HANG, VIOLIN, CELLO, BOWED PSALTERY, HARP, DOUBLE BASS, NYLON GUITAR, STEEL GUITAR, ARCHTOP GUITAR, OCARINA, HARMONICA, DIDGERIDOO, TRUMPET, FLUTE, CLARINET, TENOR SAXOPHONE, TUBA, TROMBONE, FRENCH HORN.
- Nombres antiguos del contrato de host `ui07_contract_generated.hpp` **intactos** y 27 bancos originales intactos. `a`/`b` históricos siguen en índices 0/1 y conservan el orden físico del banco.
- Dos parámetros **sólo interfaz**, añadidos al final (`Parameter 128` y `129`) exponen los nombres y nuevo orden; la tabla `kUiVoiceToLegacy` asigna el índice visible al índice del contrato antiguo, con inversión para presets antiguos. No se renombra ni reordena ningún fichero WAV ni DSP.
- Se corrigieron los valores mostrados por `ACOUSTIC_SOURCE_A/B` y `VOICE_0/1_LIVE_HOST_VALUE` en el TUI.
- Comprobaciones: 27 entradas bijectivas sin duplicados y exactas; regresión `tests/test_ui39_acoustic_selector_mapping.py`. GitHub workflow `test-reminiscent-ui39-acoustic.yml` PASS run 43622096797. ARM32/ARM64 PASS run 43622096765.
- **No probado en MPC real aún**, no actualizar paquete del usuario antes de completar UI funcional. No fusionar ni tocar master. Falta solucionar botones A/B y barras ON/OFF/EDIT, animaciones de radar/ADN, eclipse aprobado.

## Correspondencia visible → índice interno
`0,24,4,20,7,26,1,8,11,3,14,25,13,5,10,18,19,12,21,9,2,15,16,17,6,22,23`.

La secuencia vieja de `bank.tsv` y los ajustes de proyectos grabados se mantienen como fuente de verdad.
