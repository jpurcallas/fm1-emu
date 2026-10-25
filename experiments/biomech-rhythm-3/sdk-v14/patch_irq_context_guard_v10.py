#!/usr/bin/env python3
"""Experimental v0.10: prevent nested IRQ entry while ALNK owns the DSP callback.
SDK V14 real source only; retain the exact original fm1_audio_irq body.
Not a validated fix and never install to hardware.
"""
from pathlib import Path
import sys
if len(sys.argv)!=2: raise SystemExit("usage: patch_irq_context_guard_v10.py SDK_ROOT")
p=Path(sys.argv[1])/"app/board/audio.c"
s=p.read_text()
old='FM1_AUDIO_CODE __attribute__((interrupt(""))) void fm1_audio_irq(void)\n{'
new='static FM1_AUDIO_CODE void fm1_audio_irq_body(void)\n{'
if s.count(old)!=1:raise SystemExit("V14 audio IRQ signature mismatch")
s=s.replace(old,new,1)
needle='\nvoid fm1_audio_suspend(void)'
if s.count(needle)!=1:raise SystemExit("V14 audio suspend boundary mismatch")
wrapper='''
/* BIOMECH3 v0.10 experimental context gate: the original handler's
   render/ALNK work remains byte-for-byte in fm1_audio_irq_body.
   Save/restore the device IRQ mask on every exit, including the original
   early returns, to avoid nested service frames while rendering. */
FM1_AUDIO_CODE __attribute__((interrupt(""))) void fm1_audio_irq(void)
{
    uint32_t flags=fm1_device_irq_save();
    fm1_audio_irq_body();
    fm1_device_irq_restore(flags);
}
'''
s=s.replace(needle,"\n"+wrapper+needle,1)
p.write_text(s)
print("BR3_V10_IRQ_CONTEXT_GUARD; audio start unchanged; original DSP and six-track adapter unchanged")
