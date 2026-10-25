#!/usr/bin/env python3
"""BIOMECH3 v18: minimally instrument the real V14 callback edges, no DSP edits.
After signed stage_adapter_v04.py + stage_coop_v16.py, disposable runner only.
The purpose is to find the FIRST missing entry edge for real MIDI/panel/audio.
"""
from pathlib import Path
import sys
if len(sys.argv)!=2: raise SystemExit("usage: stage_input_probe_v18.py STAGED_SDK")
root=Path(sys.argv[1])/"app"
port=root/"biomech/biomech_sdk_port.c"
screen=root/"screen.c"
midi=root/"midi_router.c"
injects=[
 ("br3_input_screen_callbacks","unsigned"),
 ("br3_input_midi_callbacks","unsigned"),
 ("br3_input_midi_last_source","unsigned"),
 ("br3_input_midi_last_length","unsigned"),
 ("br3_input_audio_callbacks","unsigned"),
 ("br3_input_audio_frames","unsigned"),
]
decls="\n".join("volatile "+ty+" "+name+";" for name,ty in injects)
extern="\n".join("extern volatile unsigned "+name+";" for name,_ in injects)
p=port.read_text()
marker='#include "biomech_sdk_port.h"'
assert p.count(marker)==1, "Port include anchor mismatch"
p=p.replace(marker,marker+"\n/* READ-ONLY V18 EDGE COUNTERS: NO DSP OR EVENT INJECTION */\n"+decls,1)
mark='int BR_RAMCODE biomech_sdk_audio(int32_t *out,unsigned frames){'
assert p.count(mark)==1,"Audio-owner anchor mismatch"
p=p.replace(mark,mark+'\n    ++br3_input_audio_callbacks; br3_input_audio_frames+=frames;',1)
port.write_text(p)
p=screen.read_text()
smark='#include "biomech/biomech_sdk_port.h"'
assert p.count(smark)==1,"Screen header mismatch"
p=p.replace(smark,smark+"\n"+extern,1)
smark='    biomech_sdk_control(); return; /* BIOMECH owns user input + LCD */'
assert p.count(smark)==1,"Screen dispatch mismatch"
p=p.replace(smark,'    ++br3_input_screen_callbacks;\n'+smark,1)
screen.write_text(p)
p=midi.read_text()
mmark='#include "biomech/biomech_sdk_port.h"'
assert p.count(mmark)==1,"MIDI header mismatch"
p=p.replace(mmark,mmark+"\n"+extern,1)
mmark='    biomech_sdk_midi_received(source,m,n); return; /* Defer MIDI to audio owner */'
assert p.count(mmark)==1,"MIDI route mismatch"
p=p.replace(mmark,'    ++br3_input_midi_callbacks;\n    br3_input_midi_last_source=(unsigned)source; br3_input_midi_last_length=(unsigned)n;\n'+mmark,1)
midi.write_text(p)
print("BR3_V18_PROBE_STAGED screen/midi/audio callback edges; musical synth unchanged")
