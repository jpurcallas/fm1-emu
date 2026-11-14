# Entrega privada del banco PCM de REminiSCENT para MPC
**Fecha:** 2026-11-13. **Prioridad actual:** entregar los WAV reales al autor para poder probar en MPC, no reconstruir el plugin ni reabrir decisiones aprobadas.

## Archivo entregado
- Nombre: `REminiSCENT_PCM_27_VOCES_254_WAV_PARA_MPC.zip`
- Ubicación: **Biblioteca personal del autor** `/REminiSCENT MPC/REminiSCENT_PCM_27_VOCES_254_WAV_PARA_MPC.zip` (NO publicado como asset en GitHub).
- Tamaño: **289642520 bytes** (276.2 MiB).
- SHA256: `798e4ec4c3072d0b2c549eccc9213f72422550d3d10a203b2c8092f71f49cfd5`
- Estructura ZIP: `samples/00/*.wav` ... `samples/26/*.wav` y `bank.tsv`.
- Auditoría ZIP Python `ZipFile.testzip()`: **sin errores**; **254 .wav**, **27 carpetas de voces**, index bank.tsv presente.
- `bank.tsv` fuente LAB19 **idéntico byte por byte** a `Content/bank.tsv` del proyecto LAB20 SDK ya compilado en Mac.
- **No modificación DSP/arte ni reprocesamiento de audio en esta entrega.** Se reutilizan WAV originales de LAB19; el archivo es solo samples + manifiesto.
- Las cuatro partes .bin anteriores y el ZIP LAB19 completo permanecen conservados; los enlaces previos fallaron al autor. Para entrega se usó un **único ZIP en Biblioteca**.

## Instalación de muestras en el SDK ya descargado/compilado en macOS
En `~/Downloads` debe estar `REminiSCENT_PCM_27_VOCES_254_WAV_PARA_MPC.zip`; en la misma carpeta, el SDK extraído como `REminiSCENT_MPC_LAB20_SDK_MAC`.

```bash
unzip -q -o "$HOME/Downloads/REminiSCENT_PCM_27_VOCES_254_WAV_PARA_MPC.zip" 'samples/*' -d "$HOME/Downloads/REminiSCENT_MPC_LAB20_SDK_MAC/mpc-plugin-builder-sdk-main/plugins/REminiSCENT_MPC_LAB20/Content"
bash "$HOME/Downloads/REminiSCENT_MPC_LAB20_SDK_MAC/PREPARAR_LAB20_MAC.command"
```
El lanzador encuentra las 254 muestras en `Content/samples`, reutiliza Zig del Mac, compila para ARM32 y comprueba que el output incluya 254 WAV. Produce `SALIDA_MPC/REminiSCENT_MPC_LAB20_ARM32_CON_27_VOCES.zip`. **No marcar como ejecutado en hardware** hasta prueba física del autor.

## Restricciones
- No publicar estos WAV en repo público sin revisión de las condiciones de redistribución (usuario aprobó bandoneón para pruebas).
- UI artística aprobada todavía no verificada en MPC: no confundir "banco completo y compilado" con "skin final".
- **Nunca pedir al autor repetir trabajo previo**: compilación ARM32 ya fue lograda en su Mac el mismo día.
