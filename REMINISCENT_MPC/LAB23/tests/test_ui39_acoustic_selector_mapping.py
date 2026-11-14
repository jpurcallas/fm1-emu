#!/usr/bin/env python3
"""UI39 presentation-only acoustic selector regression: original samples stay in place."""
from pathlib import Path
import json, re
root=Path(__file__).resolve().parents[1]
cpp=(root/"src/REminiSCENTMPC.cpp").read_text()
contract=(root/"src/ui07_contract_generated.hpp").read_text()
tui=json.loads((root/"skins/TUI.json").read_text())
names=["PIANO","HARPSICHORD","BANDONEON","VIBRAPHONE","MARIMBA","GLASS HARP","MBIRA","BALAFON","HANG","VIOLIN","CELLO","BOWED PSALTERY","HARP","DOUBLE BASS","NYLON GUITAR","STEEL GUITAR","ARCHTOP GUITAR","OCARINA","HARMONICA","DIDGERIDOO","TRUMPET","FLUTE","CLARINET","TENOR SAXOPHONE","TUBA","TROMBONE","FRENCH HORN"]
mapping=[0,24,4,20,7,26,1,8,11,3,14,25,13,5,10,18,19,12,21,9,2,15,16,17,6,22,23]
assert len(mapping)==len(names)==27 and sorted(mapping)==list(range(27))
assert 'kUiVoiceToLegacy{{'+','.join(map(str,mapping))+'}}' in cpp
assert 'ui.acoustic.voiceA' in cpp and 'ui.acoustic.voiceB' in cpp
assert 'syncVoiceUi();' in cpp
assert 'hostIndices_[k]' in cpp
p=tui['pageData']
for key in ('Parameter 128','Parameter 129'):
    assert next(x for x in p['replacementStrings'] if x['key']==key)['value']==names
components=p['tabs'][0]['componentDefinition']['componentsData']
for name,handle in (('ACOUSTIC_SOURCE_A','Parameter 128'),('ACOUSTIC_SOURCE_B','Parameter 129'),('VOICE_0_LIVE_HOST_VALUE','Parameter 128'),('VOICE_1_LIVE_HOST_VALUE','Parameter 129')):
    c=next(x for x in components if x['componentData']['name']==name)
    assert c['handle remapping']['map']==[{'key':'Data','value':handle}]
# Enforce no replacement of the legacy source contract; current saved projects must still refer to historical voices.
assert '"a","choice",0,26,0,"Piano VEL 3|Mbira de Zimbabue' in contract
assert '"b","choice",0,26,1,"Piano VEL 3|Mbira de Zimbabue' in contract
print("PASS: all 27 names, reversible mapping, A/B UI-only handles, legacy sample identifiers unchanged")
