#!/usr/bin/env python3
"""REminiSCENT LAB23 structural fidelity gate (does not emulate MPC artwork rendering).
python verify_approved_skin.py <LAB23-project> [assets-manifest.json]
Pure stdlib; runs offline, no reinstallation and no WAV redistribution.
"""
import json, hashlib, sys, struct
from pathlib import Path

PAGES = ('ACOUSTIC','OSC','BLEND','ENVELOPE','MEMORY','RESONANCE','FILTER','CHARACTER','GRANULAR','MOD','SEND FX')
FILMS = {'acoustic_source_lab10_27.png':(435,1296,27),'osc_lab10_eight_waves.png':(780,2712,8)}

def check(root,manifest=None):
    d=json.loads((root/'skins/TUI.json').read_text(encoding='utf8'))
    assert len(d['pageData']['tabs'])==1, '11 touch pages must be carried in one native host tab'
    comps=d['pageData']['tabs'][0]['componentDefinition']['componentsData']
    entries={c['componentData']['name']:c for c in comps}
    assert len(comps)==len(entries), 'duplicate UI entry names'
    for i,name in enumerate(PAGES):
        bg=entries['original_art_'+name]
        assert bg['componentData']['type']=='Image'
        assert bg['componentData']['data']['image']==f'fondos/{i:02}.png'
        assert bg['bounds']['bounds']=='0 0 1280 628'
        assert bg['bounds']['additionalInvalidatingHandles']==[f'IndexedEnabling/{i}/11/Parameter 112']
        btn=entries['TAB_'+name]
        val=btn['componentData']['data']
        assert btn['componentData']['type']=='Button'
        assert val['buttonId']==i and val['numButtonsInGroup']==11
        assert val['gestureBehaviour']=='Instant'
        assert (val['onImage'],val['offImage'])==(f'nav_{i:02}_on.png',f'nav_{i:02}_off.png')
        assert btn['handle remapping']['map']==[{'key':'Data','value':'Parameter 112'}]
        assert btn['bounds']['bounds']==f'{15+113*i} 2 110 40'
        for png in (val['onImage'],val['offImage'],bg['componentData']['data']['image']):
            assert (root/'skins'/png).is_file(),png
    for i in range(1,5):
        q=entries[f'Q{i}_knob']
        assert q['componentData']['type']=='Knob'
        assert any(x['value']==f'Parameter {112+i}' for x in q['handle remapping']['map']), f'Q{i} not routed'
    for name,index,file,frames,page in (
        ('LIVE_SOURCE_A_LAB10',0,'acoustic_source_lab10_27.png',27,0),
        ('LIVE_SOURCE_B_LAB10',1,'acoustic_source_lab10_27.png',27,0),
        ('LIVE_OSC_WAVE_LAB10',2,'osc_lab10_eight_waves.png',8,1)):
        e=entries[name]
        assert e['componentData']['type']=='Image'
        assert e['componentData']['data']['imageType']=='FilmStrip'
        assert e['componentData']['data']['image']==file
        assert e['componentData']['data']['numFrames']==frames
        assert e['handle remapping']['map']==[{'key':'Data','value':f'Parameter {index}'}]
        assert e['bounds']['additionalInvalidatingHandles']==[f'IndexedEnabling/{page}/11/Parameter 112']
    for file,(w,h,n) in FILMS.items():
        blob=(root/'skins'/file).read_bytes()
        assert blob[:8]==b'\x89PNG\r\n\x1a\n',file
        iw,ih=struct.unpack('>II',blob[16:24])
        assert (iw,ih)==(w,h) and ih%n==0,file
    if manifest:
        data=json.loads(manifest.read_text(encoding='utf8'))
        assert len(data['assets'])==data['asset_count']
        for item in data['assets']:
            asset=root/item['path']
            assert asset.is_file(),item['path']
            assert hashlib.sha256(asset.read_bytes()).hexdigest()==item['sha256'],item['path']
    print('PASS 11 original backgrounds + 11 touch nav controls + 4 Q-Link proxies + 3 live art strips')
    print('PASS images, frame dimensions'+(' and SHA256 manifest' if manifest else ''))
    print('NOT TESTED: MPC hardware, render, touch focus, Data Wheel, DSP or ARM32')

if __name__=='__main__':
    if len(sys.argv) not in (2,3):
        raise SystemExit(__doc__)
    check(Path(sys.argv[1]),Path(sys.argv[2]) if len(sys.argv)==3 else None)
