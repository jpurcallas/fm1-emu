# LAB20 — kit de compilación macOS, 13 nov 2026
Revisar antes: [ACUERDOS_VIGENTES.md](ACUERDOS_VIGENTES.md) y [ESTADO_INTEGRACION_LAB20.md](ESTADO_INTEGRACION_LAB20.md).

## Archivo preparado para el autor
`REminiSCENT_MPC_LAB20_COMPILAR_EN_MAC.zip` (654 822 bytes).
SHA-256: `faaca09e4bf86c6bc24962b38a9805e62c4b011b332cd6c5669c5176ba6e97eb`.
Contiene **SDK oficial + fuente LAB20** (27 bancos reconocidos, 105 parámetros, bank.tsv) y los lanzadores `PREPARAR_LAB20_MAC.command` / `compilar_lab20_mac.py`.

## Qué recuperamos del trabajo del 12 de noviembre
- `REminiSCENT_MPC_KIT_UNICO_DESCARGA_Y_COMPILACION_MAC_ARM32.zip`
- `PREPARAR_TODO_MAC.command`
- `REminiSCENT_MPC_RESPALDO_DESARROLLO_MAC_OFFLINE.zip` contiene Zig 0.17.1 oficial; SHA-256 del archivo Zig: `75f1bc7a1e9852f17ec9a0c1895f767c4ec56d46bc8a834920eece1d0359dd8d`
- Estos archivos ya se usaron para generar el prototipo ARM32 Audio DEV con solo 3 muestras, **no la compilación de LAB20**.

## Comportamiento del nuevo lanzador
1. Detecta Zig en PATH, SDK previo o backup offline; no reinstala herramientas si están disponibles.
2. Busca las **254 muestras PCM reales de LAB19**. No las inventa ni recorta.
3. Si encuentra todas, crea carpeta Content/samples portable, compila `--target all --no-ui`, verifica binario ARM32 ELF y que todos los WAV se empaquetaron, genera `SALIDA_MPC/REminiSCENT_MPC_LAB20_ARM32_CON_27_VOCES.zip`.
4. Si no encuentra las 254 muestras, puede comprobar la compilación de código pero **no genera paquete instalable ni afirma que la voz acústica funciona**.
5. Registra fallos de Terminal en `REGISTROS/`. No instala nada en la MPC automáticamente.
6. Incluye UI genérica MPC **sin el skin artístico aprobado**: pendiente. No hay prueba física.

## Restricción de entrega
Las 254 muestras pesan ~372 MB PCM; el ZIP de LAB19 anterior ~301 MB y sus 4 enlaces de descarga fallaron al autor. **Este kit es únicamente el código y compilador; NO incluye el banco**. Resolver el canal privado de entrega del banco sin degradar muestras sigue siendo bloqueo operativo real.

## Importante sobre GitHub
La rama GitHub conserva acuerdos, estado y el procedimiento de compilación. El paquete de fuentes LAB20 completo permanece en el artefacto ZIP; **todavía no está publicado como archivos fuente individuales en GitHub**. No hacer merge ni afirmar que toda la integración está en GitHub. Aún no se ha publicado binario ARM32 de LAB20.
