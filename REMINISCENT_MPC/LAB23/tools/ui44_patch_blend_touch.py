#!/usr/bin/env python3
"""Safe, idempotent UI44 assemble-time patch for *one* native touch gesture.

Never overwrites source TUI.json. All except one scoped custom Knob orientation
remain semantically byte-for-byte equivalent after JSON parsing. This isolates
UI44 from UI43 while both branches remain unmerged. Official MPC SDK v3
FilmStrip dragOrientation supports 'Horizontal' (ui-reference.md §6.4).
"""
from copy import deepcopy
from pathlib import Path
import argparse
import hashlib
import json

TOUCH_TYPE='LAB10_SDK_FOCUS_S0_462_310_VERTICAL'
NAME='BLEND_ECLIPSE_TOUCH'
GRAPHIC='LIVE_BLENDECLIPSE_LAB10'

def patch(tui):
    d=deepcopy(tui)
    page=d['pageData']
    comps=page['tabs'][0]['componentDefinition']['componentsData']
    touch=[c for c in comps if c['componentData']['name']==NAME]
    assert len(touch)==1
    touch=touch[0]
    assert touch['componentData']['type']==TOUCH_TYPE
    assert sum(c['componentData']['type']==TOUCH_TYPE for c in comps)==1, 'shared custom definition; unsafe patch'
    assert touch['handle remapping']['map']==[{'key':'Data','value':'Parameter 20'}]
    graphic=[c for c in comps if c['componentData']['name']==GRAPHIC]
    assert len(graphic)==1
    assert graphic[0]['componentData']['type']=='Knob'
    assert graphic[0]['handle remapping']['map']==[{'key':'Data','value':'Parameter 20'}]
    assert graphic[0]['componentData']['data']['dragOrientation']=='Horizontal'
    defs=[x for x in page['componentDefinitions']['localComponentDefinitions'] if x['key']==TOUCH_TYPE]
    assert len(defs)==1
    val=defs[0]['value']
    native=[x for x in val['componentsData'] if x['componentData']['name']=='native handle editor']
    assert len(native)==1
    dat=native[0]['componentData']['data']
    assert native[0]['componentData']['type']=='Knob'
    assert dat['knobType']=='FilmStrip' and dat['handleName']=='Data'
    assert dat['version']==3
    assert dat['dragOrientation'] in ('Vertical','Horizontal')
    dat['dragOrientation']='Horizontal'
    # Proof: the only semantic alteration is this one SDK orientation field.
    expected=deepcopy(tui)
    expected['pageData']['componentDefinitions']['localComponentDefinitions'][
        next(i for i,x in enumerate(page['componentDefinitions']['localComponentDefinitions']) if x['key']==TOUCH_TYPE)
    ]['value']['componentsData'][
        next(i for i,x in enumerate(val['componentsData']) if x['componentData']['name']=='native handle editor')
    ]['componentData']['data']['dragOrientation']='Horizontal'
    assert d==expected, 'Unexpected UI mutation: abort'
    return d


def apply(input_path,output_path):
    source=Path(input_path)
    output=Path(output_path)
    assert source.resolve()!=output.resolve(), 'Never mutate original/shared TUI.json'
    data=json.loads(source.read_text())
    patched=patch(data)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(patched,indent=2,ensure_ascii=False)+'\n')
    assert patch(patched)==patched, 'patch not idempotent'
    print('PASS: custom BLEND touch now Horizontal -> Parameter 20; TUI source untouched; one-field semantic delta only')
    print('source sha256',hashlib.sha256(source.read_bytes()).hexdigest())
    print('patched sha256',hashlib.sha256(output.read_bytes()).hexdigest())

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--input-tui',type=Path,required=True)
    p.add_argument('--output-tui',type=Path,required=True)
    a=p.parse_args()
    apply(a.input_tui,a.output_tui)