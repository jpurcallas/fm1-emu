#!/usr/bin/env python3
"""Emulator-only audible polyphony diagnostic. Does not modify the BR3 DSP."""
from pathlib import Path
import sys
if len(sys.argv)!=2: raise SystemExit("usage: patch_polyphony_mac_v05.py SDK_ROOT")
root=Path(sys.argv[1])
p=root/"app/biomech/biomech_sdk_port.c"
src=p.read_text()
anchor="    br_fm1_render_q23(&runtime,out,frames);"
name="void biomech_sdk_audio("
if src.count(anchor)!=1 or src.count(name)!=1:
    raise SystemExit("BR3 v0.4 port was changed; refusing unsafe patch")
# Each stage is ~0.6 s at BR3's unchanged 44.1 kHz sample rate.
# Stages 1..6 play 1..6 *simultaneous notes on one track*;
# stage 7 plays six tracks concurrently; stage 8 gives silence.
# All note writes run on the audio owner before rendering, not CPU1/ISR hooks.
lab=r'''
/* EMULATOR LAB ONLY: real six-track C99 motor, deterministic note stimulus.
 * NO change to BR3 DSP, voices, FX, sequencer, DMA, hardware routing or MIDI.
 * No front-panel control claim: this is an AUTO polyphony listening test. */
volatile unsigned br3_poly_stage, br3_poly_triggers, br3_poly_audio_calls;
volatile unsigned br3_poly_rendered_frames, br3_poly_mode, br3_poly_offs;\nvolatile unsigned br3_poly_active_at_trigger;
static void br3_poly_before_audio(unsigned frames) {
    static const unsigned notes[6]={48,52,55,60,64,67};
    static unsigned next_change,step,current_count,current_track_mode;
    unsigned i,kind,count;
    if(!frames) return;
    ++br3_poly_audio_calls;
    if(br3_poly_rendered_frames>=next_change) {
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
        br3_poly_mode=count?(current_track_mode?2U:1U):0U;
        br3_poly_stage=kind+1U;
        ++step;
        next_change+=26460U; /* 0.6 seconds in BR3 44.1 kHz */
    }
    br3_poly_rendered_frames+=frames;
}
'''
src=src.replace(name,lab+"\n"+name,1)
src=src.replace(anchor,"    br3_poly_before_audio(frames);\n"+anchor,1)
p.write_text(src)
print("BR3_POLY_MAC_PATCH_OK unchanged DSP, 1..6 mono-track poly notes + 6 different tracks, audio-owner scheduling")
