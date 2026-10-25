#!/usr/bin/env python3
"""BIOMECH 3 v0.9 experimental IRQ lifecycle: postpone fm1_audio_start.
This is NOT a general IRQ fix. Test whether V14 audio/ALNK startup during the UI
initializer races CPU0 context setup. Preserve the identical engine and UI.
Apply ONLY after v0.8 patches, in disposable V14 staging.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1])/"app/biomech/biomech_sdk_port.c"
s=p.read_text()
old="    (void)fm1_audio_start();"
if s.count(old)!=1:raise SystemExit("exact audio-start statement not found")
s=s.replace(old,"    /* BR3 v0.9: IRQ initialization deliberately deferred to the main tick. */",1)
old2="    if(BR_LOAD(&snapshot_state,__ATOMIC_ACQUIRE)==1U)\n        copy_snapshot();"
if s.count(old2)!=1:raise SystemExit("exact v0.8 main-tick point not found")
new2="""    /* Experimental: arm SDK audio only after the non-ISR UI has entered its
       periodic tick. Do not change ISR frames, CPU1 or the DSP engine. */
    if(!br3_audio_irq_armed && (uint32_t)(fm1_millis()-last_paint)>=500U){
        br3_audio_irq_armed=1U;
        (void)fm1_audio_start();
    }
    if(BR_LOAD(&snapshot_state,__ATOMIC_ACQUIRE)==1U)
        copy_snapshot();"""
s=s.replace(old2,new2,1)
mark='#include "fm1_audio.h"'
if mark not in s:raise SystemExit("fm1 audio header not staged")
s=s.replace(mark,mark+"\nstatic unsigned br3_audio_irq_armed=0U;",1)
# Because last_paint changes on each redraw, store a dedicated boot reference.
needle="    last_paint=fm1_millis();\n    /* Emulator LAB: explicitly start V14 audio."
if needle not in s:raise SystemExit("init timestamp missing")
s=s.replace(needle,"    last_paint=fm1_millis();\n    br3_audio_irq_boot_ms=last_paint;\n    /* Emulator LAB: explicitly start V14 audio.",1)
s=s.replace("(uint32_t)(fm1_millis()-last_paint)>=500U","(uint32_t)(fm1_millis()-br3_audio_irq_boot_ms)>=500U")
s=s.replace("static unsigned br3_audio_irq_armed=0U;","static unsigned br3_audio_irq_armed=0U;\nstatic unsigned br3_audio_irq_boot_ms=0U;")
p.write_text(s)
print("BR3_V09_AUDIO_IRQ_DEFERRED_500MS; original six-track musical engine unchanged")
