# REminiSCENT — FLAC lossless 253 (rama de integración, independiente de la interfaz)
Fecha 2026-11-14. Base UI33 `6c583f501b94fd90611e54ae574d1706438bace9`.

## Fuente autorizada de ayer (sin recomprimir)
- Archivo privado: `/REminiSCENT MPC/REminiSCENT_BIBLIOTECA_FLAC_LOSSLESS_253_PRIVADA_NO_INSTALAR.zip` (141845756 bytes, 253 archivos FLAC).
- El autor autorizó **eliminar únicamente didgeridoo B**: `samples/10/037_B.wav`; conservar `samples/10/037_A.flac` con afinación +50.8 cents para las dos selecciones A/B de la voz.
- 253 de 253 PCM SHA256 comparados con sus originales, iguales; 12 WAV portaban metadatos RIFF `smpl`, respaldados en manifest, sin recortes ni cambio de bucles.
- Metadatos de contenido `Content/bank.tsv` actualizados exactamente a `bank_flac_253.tsv` (253 filas y una sola A). Los samples físicos siguen **privados** y no se suben al repositorio.

## C++ implementado
- `src/third_party/dr_flac.h`: decodificador MIT-0/public-domain (upstream blob `29edb66fbb8bcb022790f99245305f7fc5fb1cb0`), uso offline, no proceso de audio.
- `src/flac_loader.cpp`: `Bank::loadFlac`, preserva frecuencia/canales/profundidad 16/24/32 bits, decode s32 sin dithering y copia PCM crudo con byte order little-endian, solo al preparar plugin.
- `src/bank_loader.cpp`: si `.flac`, cargar 253; si WAV legacy, cargar 254; didgeridoo A obligatorio en FLAC; el B no se precarga ni se vuelve a introducir. `Engine::noteOn` existente ya usa banco fuente10 en A y B cuando no hay didgeridooB.

## Riesgos y pendientes antes de instalación
- **CAMBIO IMPORTANTE DE RAM:** las 253 muestras FLAC ocupan 141496358 bytes almacenadas, pero la primera versión del decoder expande aprox. **351025743 bytes** PCM en RAM durante `prepare()` en lugar del anterior `mmap` WAV. Por tanto se ahorra almacenamiento, **no RAM**; no lanzar al usuario sin validar RAM real, latencia y repetición de `prepare()` en MPC.
- Requiere compilar ARM32/ARM64 con SDK fijado, validar `VSTPluginMain`, probar muestras y A/B; no afirmar compilado ni probado hasta evidencia CI/hardware. Conservar WAV de respaldo fuera de la instalación y evitar sobrescribir paquete del usuario.
- NO mezclar esta rama con la entrega UI33 BLOQUEADA por auditoría de 19 overlays; integrar únicamente después de controles visuales aprobados y validación.
