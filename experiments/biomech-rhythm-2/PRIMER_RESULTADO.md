# BIOMECH RHYTHM 2 — Primer prototipo ejecutado

**NO INSTALAR.** Buzón propio CPU0/CPU1, laboratorio de dos trabajadores HOST. Comprobación ejecutada: 1000 trabajos, respuestas correctas; todavía NO ejecutado en FM-1 / PI32v2.

Código: `biomech2_mailbox.h` y `mailbox_host_test.c`.
Compilar host: `cc -std=c11 -O2 -Wall -Wextra -pthread mailbox_host_test.c -o mailbox_host_test && ./mailbox_host_test`

Referencia conceptual: X0X (arranque y líneas de caché por dueño), Clipper (autoprueba antes de usar CPU1); no se copió código GPL. Separamos bandera de solicitud / completado y verificamos integridad. No hay todavía BR2_RENDER: el opcode está reservado.

**Próxima prueba hardware:** insertar en copia experimental entrada/pila propia de CPU1, publicar BR2_SELFTEST, verificar respuesta con emulador bajo SDK, registrar estado de servicios existentes. Si interfiere, corregir el arranque de la copia. Después delegar voz, sin eliminar efectos/secuenciador ni cambiar seis pistas; PCM y DMA bajo mismos estímulos.

El archivo del firmware .fwsc NO ha sido construido. Master y los originales intactos.
