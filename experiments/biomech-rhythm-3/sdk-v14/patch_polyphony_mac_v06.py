#!/usr/bin/env python3
"""V14 emulator-only A/B polyphony. Preserve original BR3 C99 engine, FX and scheduler."""
import os,sys
from pathlib import Path
if len(sys.argv)!=2: raise SystemExit("usage: patch_polyphony_mac_v06.py SDK_ROOT")
mode=os.environ.get("BR3_V06_SCENARIO","tracks6")
allowed={"single":(1,0),"chord6":(6,0),"tracks6":(6,1)}
if mode not in allowed: raise SystemExit("invalid scenario: "+mode)
n,track_mode=allowed[mode]
p=Path(sys.argv[1])/"app/biomech/biomech_sdk_port.c"
src=p.read_text()
anchor="    br_fm1_render_q23(&runtime,out,frames);"
if src.count(anchor)!=1: raise SystemExit("audio-owner callsite not unambiguous")
# Inject six notes *together* at first render, as a completely independent guest test.
# The previous v0.5 instrument stalled before the sixth timed stage.
counters=String if False else r"""
/* BR3 V06 EMULATOR AUTO NOTES (not a production voice dispatcher).
   No DSP source or effects change. Note events in the original audio owner. */
volatile unsigned br3_v06_scenario,br3_v06_notes_sent,br3_v06_active_at_start;
volatile unsigned br3_v06_audio_calls,br3_v06_guest_frames,br3_v06_render_returned;
"""
inject=r"""
    {
       static unsigned started;
       if(!started) {
          static const unsigned notes[6]={48u,52u,55u,60u,64u,67u};
          unsigned i;
          started=1;
          br3_v06_scenario=BR3_V06_SCENARIO_ID;
          for(i=0;i<BR3_V06_NOTE_COUNT;i++) {
             br_trigger(&runtime.engine,BR3_V06_TRACK_MODE?i:0u,100u,(int)notes[i]);
             ++br3_v06_notes_sent;
          }
          for(i=0;i<BR_POLYPHONY;i++)
             if(runtime.engine.active[i].active) ++br3_v06_active_at_start;
       }
       ++br3_v06_audio_calls;
       br3_v06_guest_frames+=(unsigned)frames;
    }
"""
inject=inject.replace("BR3_V06_SCENARIO_ID",str(["single","chord6","tracks6"].index(mode)+1))
inject=inject.replace("BR3_V06_NOTE_COUNT",str(n)+"u")
inject=inject.replace("BR3_V06_TRACK_MODE",str(track_mode)+"u")
src=counters+"\n"+src.replace(anchor,inject+anchor+"\n    ++br3_v06_render_returned;",1)
p.write_text(src)
print("BR3_V06_PATCH_APPLIED",mode,n,track_mode,"BR3 6-track DSP intact; only input stimulus and counters")
