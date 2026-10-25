#!/usr/bin/env python3
"""BIOMECH3 v19: measure actual CPU0 render and six DSP phase timer intervals.
Runs AFTER signed v04 adapter, cooperative SDK-first bridge and v18 input probe.
Only the disposable staged SDK copy is modified; no musical logic/FX altered.
"""
from pathlib import Path
import sys
if len(sys.argv)!=2: raise SystemExit("usage: stage_phase_probe_v19.py STAGED_SDK")
root=Path(sys.argv[1])/"app/biomech"
engine=root/"biomech.c"
src=engine.read_text()
if not all(x in src for x in ("#ifdef BR3_PROFILE_PHASES", "br3_phase_ticks[6]", "br3_phase_segments")):
    raise SystemExit("Missing original DSP phase hooks")
engine.write_text("#define BR3_PROFILE_PHASES 1 /* V19 diagnostics only */\n"+src)
port=root/"biomech_sdk_port.c"
src=port.read_text()
include='#include "biomech_sdk_port.h"'
if src.count(include)!=1:raise SystemExit("Port header marker changed")
decls="""
volatile uint32_t br3_v19_render_calls,br3_v19_render_total_ticks;
volatile uint32_t br3_v19_render_max_ticks,br3_v19_render_last_ticks;
"""
src=src.replace(include,include+decls,1)
needle="    br_fm1_render_q23(&runtime,out,frames);"
if src.count(needle)!=1:raise SystemExit("Audio render gate not unique")
replacement="""    {
      /* TIMER4 24MHz guest time, before/after actual DSP+Q23 wrapper.
         No guest clock writes, no bypass and no fake notes. */
      uint32_t start=*(volatile uint32_t*)(uintptr_t)0x00010804u;
      br_fm1_render_q23(&runtime,out,frames);
      uint32_t elapsed=(uint32_t)(*(volatile uint32_t*)(uintptr_t)0x00010804u-start);
      br3_v19_render_calls++;
      br3_v19_render_total_ticks+=elapsed;
      br3_v19_render_last_ticks=elapsed;
      if(elapsed>br3_v19_render_max_ticks)br3_v19_render_max_ticks=elapsed;
    }"""
src=src.replace(needle,replacement,1)
port.write_text(src)
print("BR3_V19_PHASE_TIMING_STAGED",str(root),"original synthesis unchanged",
      "BR3_PROFILE_PHASES=1, TIMER4 local read-only")
