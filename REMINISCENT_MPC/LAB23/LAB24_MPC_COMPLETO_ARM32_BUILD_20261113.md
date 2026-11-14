# REminiSCENT v0.24.0 — compilación MPC completa (punto 1)

**Fecha:** 13 nov 2026 (Costa Rica). Estado: **COMPILADO / EMPAQUETADO / VALIDADO POR SDK**. No probada la ejecución en la MPC física; puntos 2 y 3 quedan estrictamente fuera del alcance de esta intervención.

## Origen autoritativo y control de cambios

- Repositorio `jpurcallas/fm1-emu`, rama aislada `work/reminiscent-mpc-integracion-20261113`, PR #31.
- Código fuente de compilación: **`ffeece5d11e6fda183da529ca2aabc6adb30dbe2`**, incluyendo DSP LAB24, corrección VST2, gráficos vivos, Solaris v09, UI exacta de 11 pantallas y el nuevo selector WHITE/PINK.
- Compilación automatizada reproducible: `.github/workflows/build-reminiscent-lab24-arm32.yml` (commit `ffeece5d`), evento **push**, GitHub Actions run **43538250006**, conclusión **SUCCESS**.
- SDK oficial de Akai/inMusic fijado al commit **`febd2ca5bd9eb16c4a412837196e145566bc981b`**, repositorio `inmusic-software/mpc-plugin-builder-sdk`.
- Compilador **Zig 0.14.1**, targets `arm-linux-gnueabihf.2.31`, `cortex_a17` (MPC One+) y `aarch64-linux-gnu.2.31`, `cortex_a55`; verificación ELF32 ARM hardfloat/ELF64 AArch64, ambos `VSTPluginMain`, sin dependencias glibc mayores a 2.31.
- Binario ARM32 SHA256 **`90645a49cb36edfe6cccb243ed832f1b35938fc5b16be3fe04270cd6c1bed781`**.
- Binario ARM64 SHA256 **`7568c03f1210c0df8c2272e21dad9985b7b81e10f9bcb14196e39030b0f428ef`**.
- `plugin.json`: nombre **REminiSCENT**, fabricante **Yeti Fingers**, versión **0.24.0**, UID **Rm20** (conservado para continuidad), ambos `file32/file64` realmente presentes; `version.xml` con `uiversion=0.1.0.0`.

## Artefacto privado completo

Guardado en la Biblioteca privada del autor, NO publicado en GitHub:

`/REminiSCENT MPC/REminiSCENT_LAB24_MPC_ARM32_COMPLETO.zip`

- Tamaño exacto: **302.022.375 bytes** (aprox. 302 MB decimal).
- SHA256: **`e1548be47864fa0a7d8c568607f0e6128c179bf8d7989c8d33238eae992a7215`**.
- 321 entradas en ZIP; `testzip() == None`.
- Carpeta de instalación única: **`Yeti Fingers - VST - REminiSCENT/`**.
- `VST/reminiscent-arm32.so` y `VST/reminiscent-arm64.so`: binarios GitHub CI, no simulados ni binarios de escritorio.
- `Plugin Skins/TUI.json`, `Q-Links.json`: copias exactas del GitHub commit compilado, más **58 PNG** (11 fondos originales y los estados dinámicos y splash).
- `Content/bank.tsv` y **254 WAV PCM privados originales**, distribuidos por 27 fuentes acústicas. No se agregó Duduk ni se editaron, transcodificaron, comprimen audio con pérdidas o eliminaron muestras.
- `SDK_VALIDATION.txt` y `PROVENANCE_SHA256.txt` incluidos fuera de la carpeta del plugin para auditoría.
- Recursos privados, procedencia: `REminiSCENT_LAB24_58_PNG_WHITE_PINK_PRIVADO.zip` y `REminiSCENT_PCM_27_VOCES_254_WAV_PARA_MPC.zip`, conservados aparte en la Biblioteca del autor. El código y el flujo de compilación no contienen material binario con restricciones de licencia.

## Validación de empaquetado

SDK `tools/validate.py` ejecutado contra el plugin **con ambos ARM ELF y la totalidad del banco/skin**:

**0 errores, 1 advertencia.**

La advertencia es **`Content/ is over 256 MB`**: los 254 WAV ocupan unos **355 MB** sin comprimir. Es una advertencia de memoria/carga del hardware, NO un fallo de compilación ni motivo para alterar muestras sin aprobación. 254/254 entradas del banco resuelven a rutas reales; 58/58 PNG coinciden con hashes y dimensiones del manifiesto.

**No se afirma instalación, carga real en MPC One+, funcionamiento táctil, uso de RAM físico ni aceptación del autor**. Eso corresponde a los puntos 2 y 3. Esta intervención no reabre ni vuelve a probar funciones DSP, animaciones ni cambios creativos.

`master` sin modificaciones; **NO MERGE**.
