#!/usr/bin/env python3
"""BIOMECH 3 v0.8 native UI recovery: repaint isn't gated on audio snapshot.
Lab-only. Keep original six-track sound engine unchanged.
"""
import pathlib,sys
root=pathlib.Path(sys.argv[1])
p=root/"app/biomech/biomech_sdk_port.c"
s=p.read_text()
old="""    BR_STORE(&initialized,1U,__ATOMIC_RELEASE);
    /* Emulator LAB: explicitly start V14 audio."""
new="""    BR_STORE(&initialized,1U,__ATOMIC_RELEASE);
    /* Boot splash of the REAL existing BR3 panel, independent of audio
       snapshot publication, to avoid a completely black screen. */
    paint_screen();
    last_paint=fm1_millis();
    /* Emulator LAB: explicitly start V14 audio."""
if s.count(old)!=1:raise SystemExit("v08 boot paint hook mismatch")
s=s.replace(old,new)
old="""    if(BR_LOAD(&snapshot_state,__ATOMIC_ACQUIRE)==1U){
        copy_snapshot();
        if(fm1_millis()-last_paint>=90U){paint_screen();last_paint=fm1_millis();}
    }"""
new="""    if(BR_LOAD(&snapshot_state,__ATOMIC_ACQUIRE)==1U)
        copy_snapshot();
    /* UI refresh may never depend on audio snapshot availability.
       Audio owner still provides authoritative parameter updates. */
    if(fm1_millis()-last_paint>=90U){
        paint_screen();
        last_paint=fm1_millis();
    }"""
if s.count(old)!=1:raise SystemExit("v08 tick paint hook mismatch")
s=s.replace(old,new)
p.write_text(s)
print("BR3_V08_LCD_UNCONDITIONAL_BOOT_AND_TICK_PAINT")
