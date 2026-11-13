#!/usr/bin/env python3
"""REminiSCENT LAB23 structural fidelity gate (does not emulate MPC artwork rendering).
python verify_approved_skin.py <LAB23-project> [assets-manifest.json]
Pure stdlib; runs offline, no reinstallation and no WAV redistribution.
"""
import json, hashlib, sys, struct
from pathlib import Path

PAGES = ('ACOUSTIC','OSC','BLEND','ENVELOPE','MEMORY','RESONANCE','FILTER','CHARACTER','GRANULAR','MOD','SEND FX')
FILMS = {'acoustic_source_lab10_27.png':(435,1296,27),'osc_lab10_eight_waves.png':(780,2712,8),
         'mod_lfo_shape_engine_5.png':(607,430,5),'memory_position_32.png':(750,2816,32)}

def check(root,manifest=None):
    d=json.loads((root/'skins/TUI.json').read_text(encoding='utf8'))
    assert len(d['pageData']['tabs'])==1, '11 touch pages must be carried in one native host tab'
    comps=d['pageData']['tabs'][0]['componentDefinition']['componentsData']
    entries={c['componentData']['name']:c for c in comps}
    assert len(comps)==len(entries), 'duplicate UI entry names'
    for i,name in enumerate(PAGES):
        bg=entries['original_art_'+name]
        assert bg['componentData']['type']=='Image'
        assert bg['componentData']['data']['image']==(f'fondos/03_adsr_no_static_curve.png' if i==3 else f'fondos/{i:02}.png')
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
    adsr=entries['LIVE_ADSR_NATIVE_LAB10']
    assert adsr['componentData']['type']=='Envelope'
    env=adsr['componentData']['data']
    assert env['envelopeType']=='ADSR' and env['envelopeStyle']=='WithoutHeader'
    assert [env[key+'Handle'] for key in ('attack','decay','sustain','release')]==[
        'Parameter 29','Parameter 30','Parameter 31','Parameter 32']
    assert adsr['bounds']['additionalInvalidatingHandles']==['IndexedEnabling/3/11/Parameter 112']
    # MOD has exactly three author-approved modules. Old LAB10 HTML is NOT
    # authority for bringing back a Mod Wheel.
    module_items=d['pageData']['componentDefinitions']['localComponentDefinitions']
    mod_buttons=next(x['value']['componentsData'] for x in module_items if x['key']=='page_buttons_9')
    assert len(mod_buttons)==6, 'three selectors and three ON/OFF switches'
    assert all('wheel' not in x['componentData']['name'].lower() for x in comps)
    for which,target in ((0,82),(1,86)):
        e=entries[f'LIVE_MOD_LFO{which+1}_SHAPE']
        assert e['componentData']['data']['image']=='mod_lfo_shape_engine_5.png'
        assert e['componentData']['data']['numFrames']==5
        assert e['handle remapping']['map']==[{'key':'Data','value':f'Parameter {target}'}]
        assert e['bounds']['additionalInvalidatingHandles']==[
            'IndexedEnabling/9/11/Parameter 112',
            f'IndexedEnabling/{which}/3/Parameter 111']
    e=entries['LIVE_MOD_ENV2']
    assert e['componentData']['type']=='Envelope'
    assert [e['componentData']['data'][name+'Handle'] for name in
            ('attack','decay','sustain','release')]==[
            'Parameter 88','Parameter 89','Parameter 90','Parameter 91']
    assert e['bounds']['additionalInvalidatingHandles']==[
        'IndexedEnabling/9/11/Parameter 112',
        'IndexedEnabling/2/3/Parameter 111']
    assert entries['LIVE_MOD_ENV2_BLANK']['componentData']['data']['image']=='mod_env2_graph_blank.png'
    e=entries['LIVE_MEMORY_POSITION']
    assert e['componentData']['data']['image']=='memory_position_32.png'
    assert e['componentData']['data']['numFrames']==32
    assert e['handle remapping']['map']==[{'key':'Data','value':'Parameter 35'}]
    assert e['bounds']['additionalInvalidatingHandles']==['IndexedEnabling/4/11/Parameter 112']
    assert (root/'skins/mod_env2_graph_blank.png').is_file()
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
    print('PASS 11 original page layouts + 11 touch nav controls + 4 Q-Link proxies + 3 live art strips + editable ADSR')
    print('PASS images, frame dimensions'+(' and SHA256 manifest' if manifest else ''))
    print('NOT TESTED: MPC hardware, render, touch focus, Data Wheel, DSP or ARM32')

if __name__=='__main__':
    if len(sys.argv) not in (2,3):
        raise SystemExit(__doc__)
    check(Path(sys.argv[1]),Path(sys.argv[2]) if len(sys.argv)==3 else None)
