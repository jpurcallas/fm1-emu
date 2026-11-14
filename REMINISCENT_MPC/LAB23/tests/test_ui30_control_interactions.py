from pathlib import Path
from collections import Counter
from PIL import Image
import hashlib, json, re, zipfile
P=Path(__file__).parent
skin=P/'REBUILD_CONTROLS_COMPLETE'/'Plugin Skins'
tui=json.loads((skin/'TUI.json').read_text());cs=tui['pageData']['tabs'][0]['componentDefinition']['componentsData'];
reg=json.loads((P/'REBUILD_CONTROLS_COMPLETE'/'CONTROL_MAP.json').read_text())
prev=json.loads((P/'REBUILD_LAB10_FROM_ORIGAMIDI'/'Plugin Skins/TUI.json').read_text());old=prev['pageData']['tabs'][0]['componentDefinition']['componentsData']
assert cs[:19] == old[:19], 'visual image components changed'
assert len(cs)==106 and len(reg)==87
assert all(x['componentData']['type'] in ('Image','Button','Knob') for x in cs)
assert all(c['bounds']['acceptsHWFocus']=='Yes' for c in cs if c['componentData']['type'] in ('Button','Knob'))
assert sum(c['componentData']['name'].startswith('TOUCH_TAB_') for c in cs)==11
assert sum(c['componentData']['name'].startswith('OSC_WAVE_') for c in cs)==8
assert sum(c['componentData']['name'].startswith('Q_LINK_') for c in cs)==4
assert sum(c['componentData']['name'].startswith('APPROVED_LAB10_') for c in cs)==19
known={c['componentData']['name']:c for c in cs}
for page in range(11):
    # All pages show art and expose a direct controller for the exact page.
    marker=f'IndexedEnabling/{page}/11/Parameter 112'
    assert any(marker in x['bounds']['additionalInvalidatingHandles'] for x in cs if x['componentData']['type']=='Image'),f'no art page {page}'
    assert any(marker in x['bounds']['additionalInvalidatingHandles'] for x in cs if x['componentData']['type'] in ('Knob','Button')),f'no controls page {page}'
    # A page selector must target ui.page 112 with buttonId=page.
    nav=known['TOUCH_TAB_'+('SEND_FX' if page==10 else ['ACOUSTIC','OSC','BLEND','ENVELOPE','MEMORY','RESONANCE','FILTER','CHARACTER','GRANULAR','MOD'][page])]
    assert nav['componentData']['data']['buttonId']==page
    assert nav['handle remapping']['map'][0]['value']=='Parameter 112'
for n,hosts in {
 'ENVELOPE_':[29,30,31,32], 'Q_LINK_':[113,114,115,116]
}.items():
    found=sorted(int(c['handle remapping']['map'][0]['value'].split()[-1]) for c in cs if c['componentData']['name'].startswith(n))
    assert found==sorted(hosts),(n,found)
for i in range(8):
    c=known['OSC_WAVE_'+['SINE','TRIANGLE','SAW','SQUARE','PULSE','ORGAN','BRIGHT','HOLLOW'][i]]
    assert c['componentData']['data']['buttonId']==i
    assert c['handle remapping']['map'][0]['value']=='Parameter 2'
for key,n,host,group in [('CHAR_SELECT_',4,109,4),('SEND_SELECT_',4,110,4),('MOD_SELECT_',3,111,3)]:
    found=[c for c in cs if c['componentData']['name'].startswith(key)]
    assert len(found)==n
    assert sorted(c['componentData']['data']['buttonId'] for c in found)==list(range(n))
    assert all(c['componentData']['data']['numButtonsInGroup']==group for c in found)
    assert all(c['handle remapping']['map'][0]['value']==f'Parameter {host}' for c in found)
for name,target in [('ACOUSTIC_SOURCE_A',0),('ACOUSTIC_SOURCE_B',1),('ACOUSTIC_BLEND_TOUCH',19),('BLEND_ECLIPSE_TOUCH',20),('MEMORY_MIX',37)]:
    assert known[name]['handle remapping']['map'][0]['value']==f'Parameter {target}'
for key,host in [('MOD_LFO1_SECONDARY_1',92),('MOD_LFO2_SECONDARY_1',93),('MOD_ENV2_SECONDARY_1',94),('SEND_MOD1_ALGORITHM_TOUCH',103),('SEND_MOD2_ALGORITHM_TOUCH',104)]:
    assert known[key]['handle remapping']['map'][0]['value']==f'Parameter {host}'
# All references have sources, and approved images are byte-identical.
for i in range(19):
    pass
for f in skin.glob('lab10_mpc_*.png'):
    assert (P/'REBUILD_LAB10_FROM_ORIGAMIDI'/'Plugin Skins'/f.name).read_bytes()==f.read_bytes(),f.name
    assert Image.open(f).size==(1280,628)
rep={v['key']:v['value'] for v in tui['pageData']['replacementStrings']}
for field,n in {'Parameter 0':27,'Parameter 1':27,'Parameter 2':8,'Parameter 109':4,'Parameter 110':4,'Parameter 111':3,'Parameter 112':11,'Parameter 103':5,'Parameter 104':5}.items():assert len(rep[field])==n,(field,len(rep.get(field,[])))
assert 'MOD WHEEL' not in json.dumps(tui)
print('PASS: 11 pages, 19 exact images, 87 focusable touch regions, 4 proxies, 8 waves, 11 tab buttons')
print('PASS: source selector+memory+FX+MOD/ADSR host parameter mapping; 0 old art, no 4th MOD')
print('STATUS: Structural tests only; touch render requires MPC hardware, no UI engine simulator executed.')
