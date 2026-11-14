#!/usr/bin/env python3
"""UI45 integrated UI43+UI44 invariant test. No hardware/runtime claims.

Use --ui43-tui to prove one exact semantic delta from UI43. Use --private-skins
to validate the exact original approved private assets during final assembly.
"""
import argparse, hashlib, json
from pathlib import Path

ORIGINAL_HEAD = "2b196cdd9f0db2888c1ed16623f8490854f54c22"
UI44_SHA={
 "lab10_blend_eclipse_live_16.png":"47e75e44a16fff9d2101d1d80e55a319b7963744230904d146ff9858c9eb2d56",
 "lab10_mpc_02.png":"37e4e51b08d1770d288f5e0659ab34a70d3b541c3e771193e40eea00b9e43607"
}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(tui,ui43=None,skins=None):
    curr=json.loads(tui.read_text())
    comps=curr['pageData']['tabs'][0]['componentDefinition']['componentsData']
    names={c['componentData']['name']:c for c in comps}
    assert len(comps)==len(names)==154
    assert len([s for s in names if s.startswith("TOUCH_TAB_")])==11
    assert len([s for s in names if s.startswith("UI43_")])==8
    custom=curr['pageData']['componentDefinitions']['localComponentDefinitions']
    defs=[x for x in custom if x['key']=='LAB10_SDK_FOCUS_S0_462_310_VERTICAL']
    assert len(defs)==1
    native=[x for x in defs[0]['value']['componentsData'] if x['componentData']['name']=='native handle editor']
    assert len(native)==1
    assert native[0]['componentData']['data']['dragOrientation']=='Horizontal'
    assert names['BLEND_ECLIPSE_TOUCH']['handle remapping']['map']==[{'key':'Data','value':'Parameter 20'}]
    eclipse=names['LIVE_BLENDECLIPSE_LAB10']
    assert eclipse['handle remapping']['map']==[{'key':'Data','value':'Parameter 20'}]
    assert eclipse['componentData']['data']['filmStrip']=='lab10_blend_eclipse_live_16.png'
    assert eclipse['componentData']['data']['numFrames']==16
    assert eclipse['componentData']['data']['dragOrientation']=='Horizontal'
    bindings=[('RADAR',p) for p in (38,39,40,41)]+[('GRANULAR',p) for p in (44,45,46,47)]
    for group,param in bindings:
        items=[v for k,v in names.items() if k.startswith('UI43_'+group+'_') and
               v['handle remapping']['map']==[{'key':'Data','value':f'Parameter {param}'}]]
        assert len(items)==1, (group,param)
        assert items[0]['componentData']['data']['numFrames']==16
    if ui43:
        from copy import deepcopy
        older=json.loads(ui43.read_text())
        expected=deepcopy(older)
        defs=expected['pageData']['componentDefinitions']['localComponentDefinitions']
        selected=next(x for x in defs if x['key']=='LAB10_SDK_FOCUS_S0_462_310_VERTICAL')
        native=next(x for x in selected['value']['componentsData'] if x['componentData']['name']=='native handle editor')
        assert native['componentData']['data']['dragOrientation']=='Vertical'
        native['componentData']['data']['dragOrientation']='Horizontal'
        assert expected==curr,"UI45 changes something beyond the single approved BLEND orientation"
    if skins:
        from PIL import Image
        for name,wanted in UI44_SHA.items():
            f=skins/name
            assert f.is_file() and sha(f)==wanted,(name,'SHA mismatch')
        with Image.open(skins/'lab10_blend_eclipse_live_16.png') as im:
            assert im.size==(613,392*16)
        with Image.open(skins/'lab10_mpc_02.png') as im:
            assert im.size==(1280,628)
        for group,key in [('RADAR',n) for n in ('BODY','DECAY','EXCITE','MIX')]+[('GRANULAR',n) for n in ('SIZE','DENSITY','POSITION','MIX')]:
            obj=names[f'UI43_{group}_{key}']
            name=obj['componentData']['data']['filmStrip']
            assert (skins/name).is_file(),name
            x,y,w,h=[int(n) for n in obj['bounds']['bounds'].split()]
            with Image.open(skins/name) as im:assert im.size==(w,h*16)
    print('PASS UI45: 154 components/11 tabs, UI43 all 8 overlays, UI44 Master Blend touch, approved images, no other TUI mutation')
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--tui',type=Path,required=True)
    p.add_argument('--ui43-tui',type=Path)
    p.add_argument('--private-skins',type=Path)
    a=p.parse_args()
    run(a.tui,a.ui43_tui,a.private_skins)
