#!/usr/bin/env python3
"""One focused structural gate for REminiSCENT LAB26 UI, no DSP rerun."""
import json,sys
from pathlib import Path
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path("REMINISCENT_MPC/LAB23")
skin=root / ("Plugin Skins" if (root/"Plugin Skins").is_dir() else "skins")
d=json.loads((skin/"TUI.json").read_text())
pages=d["pageData"]["tabs"]
assert len(pages)==1
c=pages[0]["componentDefinition"]["componentsData"]
by={x["componentData"]["name"]:x for x in c}
page=lambda i:f"IndexedEnabling/{i}/11/Parameter 112"
mode=lambda i:f"IndexedEnabling/{i}/3/Parameter 111"
for i in range(11):
    label=["ACOUSTIC","OSC","BLEND","ENVELOPE","MEMORY","RESONANCE",
           "FILTER","CHARACTER","GRANULAR","MOD","SEND_FX"][i]
    tab=by["TOUCH_TAB_"+label]
    assert tab["componentData"]["data"]["buttonId"]==i
    assert tab["handle remapping"]["map"]==[{"key":"Data","value":"Parameter 112"}]
    refs=[x for n,x in by.items() if n.startswith(f"APPROVED_LAB10_SCREEN_{i:02d}")]
    assert refs and all(page(i) in x["bounds"]["additionalInvalidatingHandles"] for x in refs)
for i,idx in enumerate((113,114,115,116),1):
    assert by[f"Q_LINK_{i}_EDIT_AND_LIVE_VALUE"]["handle remapping"]["map"][0]["value"]==f"Parameter {idx}"
for name,param,conds in [
 ("LIVE_LFO_1_AUDIO_TRACE",118,[page(9),mode(0)]),
 ("LIVE_LFO_2_AUDIO_TRACE",119,[page(9),mode(1)]),
 ("LIVE_MEMORY_WET_AUDIO_WAVE",120,[page(4)]),
 ("LIVE_MEMORY_READ_PLAYHEAD",121,[page(4)])]:
    entry=by[name]
    assert entry["bounds"]["version"]==2
    assert entry["bounds"]["additionalInvalidatingHandles"]==conds
    handle=entry["componentData"]["data"].get("dataHandle") or entry["handle remapping"]["map"][0]["value"]
    assert handle==f"Parameter {param}"
    if entry["componentData"]["type"]=="Image":
        assert (skin / entry["componentData"]["data"]["image"]).is_file()
assert "LIVE_MOD_ENV2" in by and mode(2) in by["LIVE_MOD_ENV2"]["bounds"]["additionalInvalidatingHandles"]
assert not any("SOLARIS_V09_PLATE" in name or "MOD_WHEEL" in name for name in by)
assert len(by)==76
print("PASS 11 MPC touch sections, 4 Q-Links, LFO1/2, MEMORY wet/playhead; no blocking splash")
