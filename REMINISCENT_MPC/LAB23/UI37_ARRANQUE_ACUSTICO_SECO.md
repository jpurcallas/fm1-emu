# UI37 — Arranque limpio para evaluar REminiSCENT en MPC

- Instrumento nuevo: A Piano VEL 3 encendido; B apagado.
- ACOUSTIC BLEND = 0. MASTER BLEND = 0 (sólo acústico).
- OSC LEVEL=0 y ahora **OscOn se deriva de ese nivel**; estaba **forzado a ON** aunque no existía control de OSC ON. Aumentar OSC LEVEL lo activa, pero para escucharlo se sube MASTER BLEND.
- MEMORY MIX=0; FREEZE, REVERSE, TIDE=OFF.
- RESONANCE MIX=0; GRANULAR MIX=0; filtro MIX=0 y LPF apagado; Acoustic Noise=0.
- CHARACTER cuatro OFF; SEND FX cuatro OFF; LFO1/LFO2/ENV2 OFF.
- Ninguno de estos valores se reimpone en prepare(), reset() ni al restaurar presets/proyectos: únicamente cambia la configuración por defecto de **instancias nuevas**.
- Sin cambiar arquitectura del motor ni volver a cargar WAV o introducir FLAC.
- Conservados todos los ID de parámetros, audio DSP, 254 WAV, 19 bases LAB10, GIF/Solaris prohibido.
- Test de regresión: tests/test_acoustic_only_start.py.
- **No está todavía comprobado en hardware**, y la interfaz UI36 sigue con otras correcciones pendientes. No fusionar ni describirlo como aprobado.
