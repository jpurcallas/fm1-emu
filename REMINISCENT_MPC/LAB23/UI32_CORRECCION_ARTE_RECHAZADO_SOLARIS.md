# UI32 — retiro obligatorio de arte rechazado (SOLARIS)

Evidencia real del autor: fotografía MPC con recuadro blanco/logo antiguo encima de la pantalla ACOUSTIC, expresamente rechazado previamente. Confirmado: seis componentes Image llamados `SOLARIS_V09_SEGMENT_0` a `5` cargan `solaris_v09_00.png` a `05.png` dentro de la skin UI32, en las coordenadas `482 195 316 316`. Esa capa se superpone al diseño aprobado LAB10 y debe desaparecer.

**Intervención aislada:** retirar los 6 componentes de `LAB23/skins/TUI.json` y los seis PNG del paquete privado. Ningún otro archivo del ZIP cambió excepto TUI: comprobado byte por byte. Se mantienen 19 fondos LAB10 aprobados, 254 WAV PCM y ambos binarios ARM originales; Q-Links, MEMORY y ON/OFF de UI32 intactos.

**Entrega verificada:** `/REminiSCENT MPC/REminiSCENT_UI32_SIN_ARTE_ANTIGUO.zip`, 306331500 bytes, SHA256 `5e0e768b99bd4caf4f2fac734c64023c5c9c3310eb3d7d699e7ab2a3dc7a002c`, 293 miembros, ZIP testzip=None. TUI SHA256 `6600a9a0930d87088062d16b7c1d602fc793c7dc0839eee0df638dcfd1807848` (versión privada); 131 componentes. **No prueba de hardware de esta revisión aún.**

**IMPORTANTE:** La intro Solaris NO está reparada; se desactivó expresamente por contener arte rechazado. No reintroducir ninguna versión ni sustituirla por otra sin cotejar con la animación original aprobada. No publicar PCM de terceros ni hacer merge.
