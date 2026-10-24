# REminiSCENT 2 v0.15 UX07 — firmware PI32v2 AUDIBLE en guest, candidato MAC
Fecha: 23 octubre 2026 (Costa Rica). **SOLO EMULADOR, NO INSTALAR, NO MERGE**.

## Resultado NUEVO: compilación y guest ejecutados
Se recuperaron de la biblioteca del autor **el SDK V14 FM1 Open y el compilador JieLi Linux 20260730.1**. Se recompiló el SDK stock en Linux x86_64 con PI32v2 r3, link PASS, y se reconstruyeron los objetos baseline y la app C99 de REminiSCENT v0.12 + splash v0.13 + UI UX07. No cambió código DSP, ni las cuatro PARTS, FX, secuenciador o fuentes acústicas.

**Se hizo una comparación control real antes de declarar UX07 audible:**
1. v0.13 original FWSC del autor: guest produce sonido, referencia v0.13 además escuchada estable **14 minutos en Mac nativo** por autor.
2. v0.13 **recompilado** con enlace de SDK sin restaurar mapeo original: guest silencioso, pese a callback MIDI correcto y enlace PASS; evidenció que la regresión no la causaba UX07.
3. Se reconstruyó el layout exacto observado en el `sdk.map` v0.12: reservar **.bss.undo, scratch, pattern, drum_active, clocks, lengths, queue, maps, selection, storage** en RAM caché (`.cache_ram_bss` ANTES de comodín `.bss.*`), con `RAM_MALLOC_SIZE >=8192`; enrutar **solo** `.volatile_ram_code.fm1_synth_dx7*, fm1_dx7*, fm1_fm1_dx7*, fm1_bass303*, fm1_drum808*, fm1_psg*, fm1_PSG*, fm1_fm_exp2_fixed, fm1_advance, fm1_advance.*` del SDK a ROM, antes del comodín para los restantes códigos activos en RAM. No suprimir funciones, simplemente restituir ubicación.
4. v0.13 recompilado con el layout histórico restaurado: **428.424 B SRAM estática** (exactamente cifra original) y **36.593 frames sonoros de 350×128**, halted=false. El A/B identifica como causa del silencio del **rebuild** la pérdida del layout, no necesariamente explica por sí solo TODO lo observado con el anterior binario UX03.
5. UX07 C99 con mismo layout: compilación/enlace SDK V14/PI32v2 PASS, strong `fm1_app_midi_received` comprobado, empaquetado FWSC conservando resto del payload de v0.13 y CRC/metadata PASS.

## Archivo real emitido, en conversación del autor
`REminiSCENT2_v0.15_UX07_HYBRID_BLEND_AUDIBLE_SOLO_EMULADOR_NO_INSTALAR.fwsc` 
SHA-256 **79554802efdb897bd4a89e80774f348d11dbae1c46a83f28f5c454de08fbbc4b**
1069620 B. APP **429648 / 430352** B reservados = **704 B** libres. SRAM **427464 B**; mismo esquema de DSP cuatro PARTS de v0.13. 
`REminiSCENT2_v0.15_UX07_AUDIBLE_PRUEBA_MAC_SOLO_EMULADOR.zip` SHA-256 **6aef4599d896401de17a73fa8f483d9f93fb5b8c89e0824c2c271cf04b2f8034**. ZIP íntegro: firmware, C99 UI, linker recuperado, logs JSON, capturas RGB565 de guest y README de prueba musical. **Binary no se subió a GitHub**.

## Evidencia PI32v2 guest, no HOST
- Emulador WebAssembly PI32v2 interpretado JIT OFF 200MHz: boot=0; 950 bloques PCM de 128 con NOTE ON/OFF de 4 canales/PARTS + tecla local; **113.382 frames PCM no nulos; 34 bloques cortos**, idéntico conteo de bloques cortos respecto a referencia original v0.13 en este ensayo; **halted=false**; LCD revision progresa.
- Al sobrepasar 5 s de tiempo huésped, captura **LCD real RGB565 240×240** de pantalla HYBRID BLEND (no pantalla host fake). Gesto físico de **fm1_enc(3, -16)** (K2) después de splash: **BLEND 127 → 111**, barra acústico/digital y valor cambian, revisión LCD avanza, CPU no se detiene. `fm1_enc(3,+16)` con BLEND ya en máximo 127 no produce modificación: saturación esperable, no error.
- Los ensayos anteriores **HOST C99 + ASan/UBSan de 1.200 operaciones** siguen complementarios, no sustituyen el guest.

## Límites / siguiente gate
**Todavía NO escuchado por el autor en FM1-LIVE-LAB Mac ARM64**; no hay prueba de 14 minutos UX07, hardware real ni paridad completa de efectos, polifonía, modulación, BLEND o secuenciador. Firmware SOLO EMULADOR; no instalar. El paso que sigue es experiencia musical del autor en Mac con BLACK BOX, y corregir UX/audio observado sin disminuir DSP ni capacidades. NO cambiar `master`, madre, v0.13 estable ni ramas ajenas.

## Coordinación con BIOMECH
Transferible la técnica **reconstrucción A/B del firmware *de referencia* antes de diagnosticar UX**, layouts ROM/SRAM/cache históricos revisados por `sdk.map`, y distinción clara guest audio vs host vs escucha Mac. No copiar dirección, parche, símbolos ni datos de REM a BIOMECH por supuesto; comparar su propio SDK, headroom y runtime. 
**Reemplaza exclusivamente** la declaración en `UX07_NATIVE_C99_LAB_STATUS.md` de que faltaba toolchain y no existía FWSC: ahora existe y se ejecutó, no implica aprobación sonora del autor.
