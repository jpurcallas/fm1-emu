# REminiSCENT MPC — estado técnico LAB20
Fecha: 2026-11-13. **STAGING, NO APROBADO EN HARDWARE.**
Leer primero [ACUERDOS_VIGENTES.md](ACUERDOS_VIGENTES.md).

## Comprobado en este entorno
- Plugin SDK VST2 integrado con DSP aprobado de Bridge16 y banco PCM LAB19.
- 27 instrumentos, 254 WAV, fuentes A/B, 105 parámetros exportados de los 113 campos (los 8 restantes son solo UI).
- Compilación **nativa Linux** exitosa; host_sim: **19 PASS, 0 advertencias, 0 fallos** a 44.1kHz (128/32/512 frames, sweep de parámetros, MIDI, restauración de estado por chunk, all-notes-off, salida finita). Los resultados son de la simulación nativa, no de una MPC.
- No hay UI/skin visual MPC aprobada integrada aún.
- Preload de los 254 WAV PCM a float estéreo en `prepare()`: riesgo de consumo de RAM en MPC One+; medir en hardware. **No optimizar audio destruyendo el timbre**.
- `REminiSCENT_MPC_LAB20/Content/bank.tsv` corresponde a 254 WAV de LAB19; sin archivos WAV no habrá audio acústico. En la copia de trabajo local, `Content/samples` es un enlace simbólico al banco LAB19: **no es un paquete portátil todavía**.

## ARM32: estado y compilación
- El SDK oficial de Akai usa Zig, con instalación automática en `.sdk-tools/zigenv` si no está en PATH.
- **En el entorno actual no hay Zig ni GNU ARM cross compiler**. La instalación con pip falló por falta de acceso a Internet/DNS. Por tanto, **LAB20 no tiene ARM32 compilado/verificado en este entorno**.
- Ayer existía un artefacto ARM32 independiente `REminiSCENT_AUDIO_DEV_MPC_ARM32_SOLO_PRUEBA.zip`; **ese prototipo solo usa 3 WAV y NO es LAB20**.
- Para verificar Zig en macOS, desde la carpeta raíz del SDK:
```bash
.sdk-tools/zigenv/bin/python -m ziglang version
# Alternativa si Zig está instalado globalmente:
zig version
```
- Cuando el proyecto esté copiado bajo `plugins/REminiSCENT_MPC_LAB20` y su carpeta `Content/samples` contenga los 254 WAV:
```bash
python3 tools/build.py plugins/REminiSCENT_MPC_LAB20 --target arm32 --no-ui
```
- El resultado ARM32 requiere inspección ELF/VSTPluginMain y prueba en MPC One+ MPC OS 3.10.1. No confundirlo con host_sim.
- ChatGPT no controla Terminal de macOS desde esta conversación; hace falta ejecutar los comandos allí para compilar con el Zig instalado en el Mac.

## Próxima acción sin desvíos
1. Convertir copia staging LAB20 en proyecto autocontenido con los 254 archivos; mantener bitácora exacta de hashes y parámetros.
2. Compilar ARM32 con Zig, aprovechar la instalación existente en Mac si la hay.
3. Validar en MPC hardware; ajustar uso de RAM/carga y skin MPC sin tocar el DSP aprobado.
4. **No hacer merge ni publicar el contenido acústico sin autorización.**

## Trazabilidad
- Fuente de DSP: Bridge16 (aprobado por oído).
- Fuente de PCM: LAB19, 27 voces 254 WAV (preparadas, pendientes de evaluación en MPC).
- Rechazado Bridge17.
- LAB20 simulador: 19 pruebas PASS, 105 params; sin prueba física.
