#!/usr/bin/env python3
"""Emulator-only audible polyphony diagnostic; BR3 engine and FX untouched."""
from pathlib import Path
import sys
if len(sys.argv)!=2: raise SystemExit("usage: patch_polyphony_mac_v05.py SDK_ROOT")
p=Path(sys.argv[1])/"app/biomech/biomech_sdk_port.c"
src=p.read_text()
anchor="    br_fm1_render_q23(&runtime,out,frames);"
if src.count(anchor)!=1:
    raise SystemExit("BR3 audio render callsite changed; refusing patch")
# Add only emulator test counters and inject INSIDE the existing audio-owner call.
# 1..6 concurrent notes in one track, then 6 notes in 6 separate tracks,
# then release/silence. No MIDI callback or panel compatibility is claimed.
globals=r'''
/* BR3 v0.5 AUTO POLY TEST ONLY; no change to musical renderer */
volatile unsigned br3_poly_stage,br3_poly_triggers,br3_poly_audio_calls;
volatile unsigned br3_poly_rendered_frames,br3_poly_mode,br3_poly_offs;
volatile unsigned br3_poly_active_at_trigger;
'''
inject=r'''
    {
        static const unsigned notes[6]={48,52,55,60,64,67};
        static unsigned next_change,step,current_count,current_track_mode;
        unsigned i,kind,count;
        ++br3_poly_audio_calls;
        if(br3_poly_rendered_frames>=next_change){
            for(i=0;i<current_count;i++){
                br_note_off(&runtime.engine,current_track_mode?i:0,notes[i]);
                ++br3_poly_offs;
            }
            kind=step%8U;
            count=kind<6U?kind+1U:(kind==6U?6U:0U);
            current_track_mode=(kind==6U);
            for(i=0;i<count;i++){
                br_trigger(&runtime.engine,current_track_mode?i:0,100U,notes[i]);
                ++br3_poly_triggers;
            }
            current_count=count;
            br3_poly_active_at_trigger=0;
            for(i=0;i<BR_POLYPHONY;i++)
                if(runtime.engine.active[i].active) ++br3_poly_active_at_trigger;
            br3_poly_mode=count?(current_track_mode?2U:1U):0U;
            br3_poly_stage=kind+1U;
            ++step;
            next_change+=7000U; /* per DSP-owner render frames; emulator DMA/renders differ */
        }
        br3_poly_rendered_frames+=(unsigned)frames;
    }
'''
p.write_text(globals+"\n"+src.replace(anchor,inject+anchor,1))
print("BR3_POLY_MAC_PATCH_OK: original motor, FX, 6 tracks, DMA; deterministic audible polyphony on audio owner")
