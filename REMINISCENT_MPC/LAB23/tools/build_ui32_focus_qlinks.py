#!/usr/bin/env python3
"""UI32 isolated SDK control/focus/q-link correction; preserves all sound and art bytes."""
import copy, json, zipfile, hashlib, pathlib, shutil, subprocess, tempfile, collections
BASE=pathlib.Path('/mnt/data/REminiSCENT_UI31_LAB10_DINAMICA_PREMPC_COMPLETA.zip')
OUT=pathlib.Path('/mnt/data/REminiSCENT_UI32_FOCO_DIAL_QLINKS_TOUCH_CANDIDATO.zip')
WORK=pathlib.Path('/mnt/data/reminiscent_blackbox/UI32_FOCUS')
ORIG=pathlib.Path('/mnt/data/reminiscent_blackbox/ORIGAMIDI_MPC_V22_MIDI_Y_QLINKS_VERTICALES.zip')
PREFIX='Yeti Fingers - VST - REminiSCENT/'
TUI=PREFIX+'Plugin Skins/TUI.json'; QLINKS=PREFIX+'Plugin Skins/Q-Links.json'
with zipfile.ZipFile(BASE) as z:
    src_json=z.read(TUI); t=json.loads(src_json);q=json.loads(z.read(QLINKS)); oldnames=set(z.namelist())
with zipfile.ZipFile(ORIG) as z:
    orig=json.loads(z.read('plugins/ORIGAMIDI/skins/TUI.json'))
origdefs={x['key']:x['value'] for x in orig['pageData']['componentDefinitions']['localComponentDefinitions']}
assert 'knob overlay' in origdefs and 'sliderWithFocus' in origdefs
root=t['pageData']['tabs'][0]['componentDefinition'];cs=root['componentsData'];defs=t['pageData']['componentDefinitions']['localComponentDefinitions']
assert len(cs)==124 and not defs
# Official Akai SDK actions/overlay; control widget itself stays identical to UI31, but is nested in a focusable slot.
TRANSPARENT={'version':1,'focussed':{'version':1,'colour':'00000000','image':''},'unfocussed':{'version':1,'colour':'00000000','image':''}}
def action(when,handler,extra=''):
    return {'version':1,'onAction':when,'handler':handler,'handleName':'Data','additionalData':extra}
def child(name, typ, data, bounds, focus='No',visible='Always'):
    return {'version':2,'componentData':{'version':1,'name':name,'type':typ,'data':data},
            'handle remapping':{'version':1,'map':[]},
            'bounds':{'version':1,'acceptsHWFocus':focus,'showWhenDataModelInvalid':'Show',
                      'whenVisible':visible,'boundsType':'Absolute','bounds':bounds}}
def defn(name,child_type,child_data,actions):
    focus=child('focus outline','Focus',{'version':1,'backgroundColour':'00000000','outlineColour':'99e3a968','backgroundInset':1.0,'outlineThickness':1.0},'0 0 200 120',visible='WhenFocussed')
    # Bounds of children are resized per instance: root wrapper contains a one-slot child at full bounds.
    widget=child('value editor',child_type,copy.deepcopy(child_data),'0 0 200 120')
    return {'key':name,'value':{'version':2,'actions':actions,'backgroundData':copy.deepcopy(TRANSPARENT),
           'ignoreMousePresses':False,'disableCoarseDataWheel':False,'componentsData':[focus,widget]}}
# Generic wrapper: fine-grained focus and full surface touch/drag, the visual-only knob remains the same.
# Separate definitions because child full bounds need actual per-widget dimensions.
for k,item in enumerate(cs):
    if item['componentData']['type']!='Knob':continue
    n=item['componentData']['name'];original=copy.deepcopy(item['componentData']['data']);
    x,y,w,h=map(int,item['bounds']['bounds'].split())
    if n=='ACOUSTIC_BLEND_TOUCH':
        original['dragOrientation']='Horizontal'  # LAB10 has a horizontal blend bar; old UI31 used vertical.
    if n.startswith('MEMORY_') and ('WINDOW' in n or 'POSITION' in n or n=='MEMORY_MIX'):
        original['dragOrientation']='Horizontal'  # LAB10 represents these as horizontal visual controls.
    name='UI32_FOCUS_'+n
    d=defn(name,'Knob',original,[action('Mouse Down','Q-Link'),action('Double Click','Show Overlay','knob overlay'),action('Enter Pressed','Show Overlay','knob overlay')])
    d['value']['componentsData'][0]['bounds']['bounds']=f'0 0 {w} {h}'
    d['value']['componentsData'][1]['bounds']['bounds']=f'0 0 {w} {h}'
    defs.append(d)
    item['componentData']['type']=name
    item['componentData']['data']={'version':1,'handleName':'Data'}
    item['bounds']['acceptsHWFocus']='Yes'
# Don't change any working OSC waveform or tab button. Fix ON/OFF touch separately from EDIT radio buttons.
# They are a standard SDK Toggle Switch action rather than an overlapping second radio button.
toggle_names=[]
for item in cs:
    n=item['componentData']['name'];
    if not (n.startswith('CHAR_ONOFF_') or n.startswith('MOD_ONOFF_') or n.startswith('SEND_ONOFF_')):continue
    assert item['componentData']['type']=='Button'
    _,_,w,h=map(int,item['bounds']['bounds'].split()); name='UI32_TOGGLE_'+n
    dd={'key':name,'value':{'version':2,'actions':[action('Mouse Down','Toggle Switch'),action('Enter Pressed','Toggle Switch')],
       'backgroundData':copy.deepcopy(TRANSPARENT),'ignoreMousePresses':False,'disableCoarseDataWheel':False,
       'componentsData':[child('focus','Focus',{'version':1,'backgroundColour':'00000000','outlineColour':'99e3a968','backgroundInset':1.0,'outlineThickness':1.0},f'0 0 {w} {h}',visible='WhenFocussed')]}}
    defs.append(dd);toggle_names.append(n)
    item['componentData']['type']=name
    item['componentData']['data']={'version':1,'handleName':'Data'}
    item['bounds']['acceptsHWFocus']='Yes'
# Clone exact SDK overlay implementation from Origamidi; only appears on double-click/Enter.
defs.append({'key':'knob overlay','value':copy.deepcopy(origdefs['knob overlay'])})
# Keep live art and labels/positions exactly as UI31, fix only active Q-Link highlight bounds to approved sidebar.
t['pageData']['tabs'][0]['qlinkBoundsData']=['1015 173 245 405']*4
# 4-knob physical hardware supports four banks; bind proxies on every bank so no empty bank causes dead knobs.
# RowTopDown order: [13,14,15,16], [9,10,11,12], [5,6,7,8], [1,2,3,4].
for group in ('Screen Mode Q-Links','Program Mode Q-Links'):
    spec=q[group]['map'][0]['Q-Links'] if group=='Screen Mode Q-Links' else q[group]
    for i in range(1,17):
        spec[f'Q-Link {i}']=113+((i-1)%4)
q['Screen Mode Q-Links']['map'][0]['Bank Direction']='RowTopDown'
assert sum(e['componentData']['type'].startswith('UI32_FOCUS_') for e in cs)==39
assert len(toggle_names)==11, toggle_names
assert len(cs)==124
newt=(json.dumps(t,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
newq=(json.dumps(q,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
( WORK/'Yeti Fingers - VST - REminiSCENT/Plugin Skins').mkdir(parents=True,exist_ok=True)
(WORK/TUI).write_bytes(newt);(WORK/QLINKS).write_bytes(newq)
# Source ZIP unchanged samples/images/ARM; only skin JSON members differ.
shutil.copy2(BASE,OUT)
subprocess.run(['zip','-q','-d',str(OUT),TUI,QLINKS],check=True)
subprocess.run(['zip','-q','-X',str(OUT),TUI,QLINKS],cwd=WORK,check=True)
with zipfile.ZipFile(BASE) as za,zipfile.ZipFile(OUT) as zb:
    assert set(za.namelist())==set(zb.namelist());assert len(zb.namelist())==296
    mismatches=[f for f in za.namelist() if za.getinfo(f).CRC!=zb.getinfo(f).CRC or za.getinfo(f).file_size!=zb.getinfo(f).file_size]
    assert set(mismatches)=={TUI,QLINKS},mismatches
    assert zb.testzip() is None
    assert len([f for f in zb.namelist() if f.lower().endswith('.wav')])==254
    print('PASS: source-byte identity except TUI and Q-Links, 254 WAV, binaries unchanged, zip complete.')
print('FOCUS_WRAPPERS',sum(x['key'].startswith('UI32_FOCUS') for x in defs),'TOGGLE_SWITCH',len(toggle_names),'ORIGINAL_COMPONENTS',len(cs))
print('ZIP',OUT,'SIZE',OUT.stat().st_size,'SHA256',hashlib.sha256(OUT.read_bytes()).hexdigest())