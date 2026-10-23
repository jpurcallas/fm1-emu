# REminiSCENT 2 — reproducción diferida sin simular falsamente tiempo real

Fecha: 23/oct/2026 — experimento aislado NO MERGE. No cambia DSP, firma FWSC, SDK, ISR, ALNK ni DMA. `master`, madre v3.0.23 y firmware v0.6 intactos.

## Problema observado en el navegador real del autor

El usuario no escucha REminiSCENT v0.7 en el emulador web a 200MHz. Su captura muestra carga de audio 142–147%. BLACK BOX real: firmware vivo, 1889 renders y copias DMA, 1264 no nulas, pico después de DMA 0.2714, pero quanta de Chrome tardan 3–57ms frente a 2.902ms por 128 frames. A 100MHz: 732 renders, 0 copias DMA, rechazos por pérdida de la ventana/propiedad de DMA. Véase [diagnóstico compartido](https://github.com/jpurcallas/fm1-emu/pull/24#issuecomment-6374424617).

## Nuevo producto de laboratorio — artefacto ejecutado

`REminiSCENT2_REPRODUCTOR_DIFERIDO_v0.1_ABRIR_EN_CHROME.html` (HTML autocontenido, 4.82 MB, SHA256 `f2606a68c65f7fadf265d3f9a4ad79fb5313920a5c9a1567160c10ed29ed7d79`). Contiene el **mismo WebAssembly PI32v2** que se utilizó para el render anterior, SHA256 `ec664fa4561580adbb1e8ad1086e3a467f606f770d2f6b36e6146ede0a7ecb30`, y el **FWSC v0.7 exacto**, SHA256 `15cc57f606c45d6ac11afb58238bc7a345b8c2ba238c2f3dd30a80463a996d1a`. No requiere red ni servidor ni instalar herramientas: usuario guarda el HTML y lo abre en Chrome. Admite abrir otros .fwsc locales. **El HTML binario completo no se subió al repositorio**; se entregó en la conversación/Library, junto con las fuentes, su generador y las pruebas.

Funcionamiento: WebAssembly interpreta el firmware completo con JIT OFF y reloj 200MHz inicial; arranca una **sesión nueva** desde el `.fwsc`; opcionalmente pulsa `fm1_key(12,1)` en bloque 60 y suelta en bloque 65 (**PLAY específico de REminiSCENT v0.7**); ejecuta `fm1_render(128,4_000_000)` tantas veces como exija la duración, guarda ambos canales `fm1_out_l`/`r`, y al acabar exporta WAV PCM16 estéreo 44100 Hz. La interfaz tiene reproductor de audio, progreso y descarga WAV + informe JSON (checksums PCM/WAV, bloques cortos, pico/RMS/no-nulos, tiempo de cálculo host). No intenta engañar a Chrome fingiendo tiempo real ni alterar el DSP.

## Prueba reproducible

- Código JS probado con Node 22 simulando controles DOM y llamando al **mismo WASM/firmware**: 4s seleccionados -> 1379 bloques, 176512 frames, 168382 frames no nulos, pico ~0.2714, 18 bloques devueltos cortos al arranque, guest activo; WAV estéreo PCM16 válido, 44.1kHz.

- **Paridad byte por byte del WAV:** comparados los 353024 valores PCM16 estéreo con los primeros cuatro segundos del WAV offline anterior de v0.7 -> 0 diferencias. No es sonido sintético de sustitución.

- Entrega reproducible: `REminiSCENT2_REPRODUCTOR_DIFERIDO_v0.1_LAB_COMPLETO.zip` SHA256 `ff071e899d1f28691d5c12c4e28ec0458116ab60521913b87663901c80444f16`, contiene HTML, `offline-player.js`, `build_standalone.py`, `node_integration_test.cjs`, WAV de prueba y README. Está en Library/conversación del autor, no en el árbol GitHub.

- **Limitación de comprobación UI:** el navegador automatizado Chromium del contenedor bloqueó navegación a archivos locales y localhost con `ERR_BLOCKED_BY_ADMINISTRATOR`, por lo que todavía **NO** hay validación de click/audio de la página en Chrome del autor. No declararla probada hasta el ensayo manual. La prueba Node de lógica/WASM y la paridad WAV sí pasaron.

## Límites innegociables

Esto es un reproductor para **escuchar música calculada**, no una certificación de que el firmware real cumple plazos ni de que CPU1 pertenece al firmware bajo SDK V14. La sesión es nueva: cambios temporales hechos en otro emulador (perillas/MIDI live) no se heredan; en v0.1 solamente se inyecta PLAY y se reproduce el secuenciador preconfigurado. Mantener BLACK BOX independiente para medir guest deadline, ISR/DMA y ownership; más adelante integración 2+2 + SDK V14 sin recortar cuatro PARTS/FX. Meta FM-1 físico, no el navegador.

## Próximas pruebas del autor

Abrir HTML en Chrome, pulsar Renderizar (200MHz, 6s, PLAY activado), escuchar/repetir, descargar WAV e informe si hace falta. Si falla UI, corregir reproductor; NO modificar motor musical por ello.