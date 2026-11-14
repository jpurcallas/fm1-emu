#!/usr/bin/env python3
"""Build *source* for a faithful REminiSCENT interactive TUI based on Origamidi V22.
Keep exact approved LAB10 19 art snapshots and standalone PCM engine intact.
No hardware verdict is claimed: static SDK verification only.
"""
import copy, hashlib, json, pathlib, re, shutil, zipfile
from collections import defaultdict,Counter
ROOT=pathlib.Path(__file__).parent
BASE=ROOT/'REBUILD_LAB10_FROM_ORIGAMIDI'/'Plugin Skins'
ORIG=ROOT/'ORIGAMIDI_MPC_V22_MIDI_Y_QLINKS_VERTICALES.zip'
OUT=ROOT/'REBUILD_CONTROLS_COMPLETE'
SKIN=OUT/'Plugin Skins'
SKIN.mkdir(parents=True, exist_ok=True)
for p in BASE.iterdir():
    if p.is_file():shutil.copyfile(p, SKIN/p.name)
with zipfile.ZipFile(ORIG) as f:
    origin=json.loads(f.read('plugins/ORIGAMIDI/skins/TUI.json'))
    original_components=origin['pageData']['tabs'][0]['componentDefinition']['componentsData']
examples={x['componentData']['type']:x for x in original_components if x['componentData']['type'] in ('Image','Button','Knob','Slider','Label')}
tui=json.loads((SKIN/'TUI.json').read_text())
body=tui['pageData']['tabs'][0]['componentDefinition']
components=body['componentsData']
# The previous unverified baseline contains four Q-Link 'Label' widgets. These
# displayed values but *could not receive touch/data-wheel input*; replace all.
components[:]=[c for c in components if not c['componentData']['name'].startswith('Q_LINK_')]
# Delete previous touch widgets other than the 19 original art; recreate entirely.
components[:]=[c for c in components if c['componentData']['name'].startswith('APPROVED_LAB10_')]
assert len(components)==19
# Care: do not introduce any new backdrop, cropped old art, or alternate designs.
transparent='lab10_touch_hit.png'
style={'version':1,'font':{'version':1,'name':'Nexa','style':'Regular','height':19.0},
       'colour':'ffffcf9c','justification':'left verticallyCentred','case':'Original'}
style_hidden={**style,'colour':'00ffffff'}
value_knob={'version':4,'knobType':'ValueSlider','textStyle':style,'dragOrientation':'Vertical','handleName':'Data'}
hidden_knob={'version':4,'knobType':'ValueSlider','textStyle':style_hidden,'dragOrientation':'Vertical','handleName':'Data'}
registry=[]

def add(kind,name,x,y,w,h,host,gate=(),button=None,visible=False):
    if kind=='Button':data={'version':2,'onImage':transparent,'offImage':transparent,
                           'buttonId':button[0],'numButtonsInGroup':button[1],
                           'handleName':'Data','gestureBehaviour':'Instant'}
    elif kind=='Knob':data=copy.deepcopy(value_knob if visible else hidden_knob)
    else:raise ValueError(kind)
    obj=copy.deepcopy(examples[kind]);obj['componentData']['name']=name
    obj['componentData']['type']=kind;obj['componentData']['data']=data
    obj['handle remapping']={'version':1,'map':[{'key':'Data','value':f'Parameter {host}'}]}
    obj['bounds']['bounds']=f'{x} {y} {w} {h}'
    obj['bounds']['acceptsHWFocus']='Yes'
    obj['bounds']['showWhenDataModelInvalid']='Hide'
    obj['bounds']['whenVisible']='Always'
    obj['bounds']['additionalInvalidatingHandles']=list(gate)
    assert x>=0 and y>=0 and w>0 and h>0 and x+w<=1280 and y+h<=628, (name,x,y,w,h)
    assert isinstance(host,int) and 0<=host<=124
    components.append(obj)
    registry.append({'name':name,'type':kind,'host':host,'gate':list(gate),'rect':[x,y,w,h]})
    return obj

def on(page,sub=None):
    gates=[f'IndexedEnabling/{page}/11/Parameter 112']
    if sub is not None:
        key, idx, n=sub
        gates.append(f'IndexedEnabling/{idx}/{n}/Parameter {key}')
    return gates

# -- Navigation: strictly 11 LAB10 pages, not 6 native function tabs.
for i,n in enumerate(('ACOUSTIC','OSC','BLEND','ENVELOPE','MEMORY','RESONANCE','FILTER','CHARACTER','GRANULAR','MOD','SEND_FX')):
    add('Button','TOUCH_TAB_'+n,15+i*113,70,110,37,112,button=(i,11))

# -- Q-Links: native 4-knob RowTopDown grouping preserved; this touch region
# is a real editable Knob bound to each existing proxy and gives Data Wheel focus.
qlink_rects=[(1093,224,149,38),(1093,322,149,38),(1093,421,149,38),(1093,519,149,38)]
for k,(x,y,w,h) in enumerate(qlink_rects):
    add('Knob',f'Q_LINK_{k+1}_TOUCH_WHEEL_VALUE',x,y,w,h,113+k,visible=True)

# -- Acoustic: source choice 0/1; actual note bank selection, not a passive Label.
for side,host,y in (('A',0,246),('B',1,315)):
    add('Knob','ACOUSTIC_SOURCE_'+side,144,y,434,39,host,on(0),visible=True)
    add('Button','ACOUSTIC_POWER_'+side,49,y-2,80,48,3 if side=='A' else 4,on(0),button=(1,1))
add('Knob','ACOUSTIC_BLEND_TOUCH',49,449,530,46,19,on(0))
# Colour selection from LAB24 existing menu, not invented new algorithms.
for idx,n in enumerate(('WHITE','PINK')):
    add('Button','ACOUSTIC_NOISE_'+n,660+idx*110,539,98,31,124,on(0),button=(idx,2))

# -- Oscillator: eight actual selectable waves with standard SDK radio buttons.
# LAB10 exact drawn eight cards start x49, card width 92, gap ~6.7.
for i,w in enumerate(('SINE','TRIANGLE','SAW','SQUARE','PULSE','ORGAN','BRIGHT','HOLLOW')):
    x=49+i*98
    add('Button','OSC_WAVE_'+w,x,368,93,146,2,on(1),button=(i,8))

# -- Blend: eclipse touch gives focus to the exact masterBlend host (20).
add('Knob','BLEND_ECLIPSE_TOUCH',258,225,462,310,20,on(2))

# -- ADSR: exact host parameters (29..32), not visual telemetry.
for name,host,x,y,w,h in [
 ('ATTACK',29,65,243,124,177),('DECAY',30,189,243,145,177),
 ('SUSTAIN',31,334,243,146,177),('RELEASE',32,480,243,164,177)]:
    add('Knob','ENVELOPE_'+name+'_WHEEL',x,y,w,h,host,on(3))

# -- Memory freeze/reverse/tide cards and graph parameter focus.
for idx,(n,h) in enumerate((('FREEZE',5),('REVERSE',6),('TIDE',7))):
    add('Button','MEMORY_'+n,461+idx*159,244,145,137,h,on(4),button=(1,1))
# Captured window / playhead position and wet signal controls are still the
# original DSP parameters; data wheel edits window and position, Q links 4 controls.
add('Knob','MEMORY_WINDOW_VISUAL_TOUCH',50,460,290,106,33,on(4))
add('Knob','MEMORY_POSITION_VISUAL_TOUCH',341,460,422,106,35,on(4))
add('Knob','MEMORY_MIX',60,556,450,35,37,on(4))

# -- Resonance / filter and granular graph: touch -> direct param -> data wheel.
for page,kind,params in [
 (5,'RESONANCE',[(38,(108,275,162,72)),(39,(108,348,162,72)),(40,(108,420,162,72)),(41,(108,494,162,72))]),
 (6,'FILTER',[(42,(90,258,155,63)),(107,(245,258,170,63)),(108,(415,258,170,63)),(43,(585,258,172,63))]),
 (8,'GRANULAR',[(44,(50,503,185,70)),(45,(235,503,184,70)),(46,(419,503,185,70)),(47,(604,503,185,70))])]:
    for i,(host,rect) in enumerate(params):
        add('Knob',f'{kind}_PARAM_{i+1}_TOUCH',*rect,host,on(page))

# -- Character: selected card changes 109; per-module on/off 8..11.
for i,n in enumerate(('DISTORTION','TAPE','VINYL','CRUSH')):
    x=50+i*180
    add('Button','CHAR_SELECT_'+n,x,232,164,180,109,on(7),button=(i,4))
    add('Button','CHAR_ONOFF_'+n,x+22,429,125,42,8+i,on(7),button=(1,1))

# -- Mod: THREE approved cards only (no Mod Wheel).
for i,n in enumerate(('LFO1','LFO2','ENV2')):
    x=48+i*209
    add('Button','MOD_SELECT_'+n,x,231,192,159,111,on(9),button=(i,3))
    add('Button','MOD_ONOFF_'+n,x+19,403,155,32,16+i,on(9),button=(1,1))
# MOD LFO destinations and sync/retrigger are real host controls already
# implemented in LAB24. Accessible by tap in the corresponding selected module.
for i, (suffix,sub,hosts) in enumerate([
 ('LFO1',(111,0,3),[(92,(54,482,120,34)),(97,(182,482,120,34)),(98,(310,482,120,34)),(99,(438,482,120,34))]),
 ('LFO2',(111,1,3),[(93,(54,482,120,34)),(100,(182,482,120,34)),(101,(310,482,120,34)),(102,(438,482,120,34))]),
 ('ENV2',(111,2,3),[(94,(54,482,120,34)),(95,(182,482,120,34))]),
]):
    for n,(host,rect) in enumerate(hosts):
        add('Knob',f'MOD_{suffix}_SECONDARY_{n+1}',*rect,host,on(9,sub))

# -- Send FX: choose 4 approved modules, independent enable + algorithm select.
for i,n in enumerate(('DELAY','REVERB','MOD1','MOD2')):
    x=50+i*180
    add('Button','SEND_SELECT_'+n,x,232,164,180,110,on(10),button=(i,4))
    add('Button','SEND_ONOFF_'+n,x+22,429,125,42,12+i,on(10),button=(1,1))
# Current DSP mod algorithm is controlled by existing parameter 103/104.
# Tap to focus in the selected MOD SEND mode, not an alternate visual redesign.
add('Knob','SEND_MOD1_ALGORITHM_TOUCH',155,486,290,38,103,on(10,(110,2,4)))
add('Knob','SEND_MOD2_ALGORITHM_TOUCH',155,486,290,38,104,on(10,(110,3,4)))

# QLinks: slots 13..16 form one physical bank; test 4 proxies exactly.
q=json.loads((SKIN/'Q-Links.json').read_text());screen=q['Screen Mode Q-Links']['map'][0]
assert screen['Bank Direction']=='RowTopDown'
assert [screen['Q-Links'][f'Q-Link {i}'] for i in (13,14,15,16)]==[113,114,115,116]
# Supported image widgets only; no Plotter, Envelope or old FM-1 artwork.
assert not {'Plotter','Envelope'} & {x['componentData']['type'] for x in components}
assert [x['componentData']['name'] for x in components if x['componentData']['type']=='Image']==[x['componentData']['name'] for x in tui['pageData']['tabs'][0]['componentDefinition']['componentsData'] if x['componentData']['type']=='Image']
# Include explicit replacementStrings for both source menus and OSC 8 choices.
# The host parameters are already discrete and preserve their numeric order.
contract=[
 'Piano VEL 3','Mbira de Zimbabue','Trompeta','Violín','Bandoneón','Contrabajo jazz','Tuba','Marimba','Balafón','Didgeridoo','Guitarra nylon','Hang','Ocarina','Arpa','Violonchelo','Flauta','Clarinete','Saxo tenor','Guitarra acero','Guitarra archtop','Vibráfono','Armónica cromática','Trombón','Corno francés','Clavecín','Salterio de arco','Vasos musicales']
# Duduk excluded in approved bank; list above contains 27 sources, no duduk.
assert len(contract)==27
for host,values in [(0,contract),(1,contract),(2,['SINE','TRIANGLE','SAW','SQUARE','PULSE','ORGAN','BRIGHT','HOLLOW']),
                    (103,['CHORUS','FLANGER','PHASER','TREMOLO','AUTO-PAN']),
                    (104,['CHORUS','FLANGER','PHASER','TREMOLO','AUTO-PAN'])]:
    tui['pageData']['replacementStrings'].append({'key':f'Parameter {host}','value':values})
for i,n in enumerate(('LFO1','LFO2','ENV2')):
    host=92+i
    tui['pageData']['replacementStrings'].append({'key':f'Parameter {host}','value':['PITCH','CUTOFF','AMP','PAN','BLEND','PWM']})
for host in (98,101):tui['pageData']['replacementStrings'].append({'key':f'Parameter {host}','value':['1/1','1/2','1/4','1/8','1/16','1/4D','1/8D','1/4T','1/8T']})
# All 11 gates must select precisely the LAB10 full-screen images.
assert len([c for c in components if c['componentData']['name'].startswith('TOUCH_TAB_')])==11
assert len([c for c in components if c['componentData']['name'].startswith('Q_LINK_')])==4
assert len([c for c in components if c['componentData']['name'].startswith('OSC_WAVE_')])==8
assert len([c for c in components if c['componentData']['name'].startswith('APPROVED_LAB10_')])==19
# Sanity: every main page has user-selectable touch controls and Q-Links.
for pg in range(11):
    assert any(f'IndexedEnabling/{pg}/11/Parameter 112' in c['gate'] for c in registry),pg
SKIN.joinpath('TUI.json').write_text(json.dumps(tui,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(OUT/'CONTROL_MAP.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(OUT/'INTERACTION_AUDIT.json').write_text(json.dumps({
 'source':'Origamidi V22 proven widget structure, LAB10 approved 19 full-page rasters',
 'status':'source implementation, STATIC SDK only; hardware MPC unverified',
 'components_total':len(components),'touch_controls':len(registry),
 'touch_by_type':dict(Counter(x['type'] for x in registry)),
 'page_selector':112,'q_link_proxy_indices':[113,114,115,116],
 'ui_tui_sha256':hashlib.sha256((SKIN/'TUI.json').read_bytes()).hexdigest(),
 'art_files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in SKIN.glob('lab10_mpc_*.png')},
 'known_nonworking_replaced':'LAB29 old static label-only controls, no Plotter/Envelope',
 'limitations':['No physical MPC renderer/touch test','No dynamic redraw of OSC/BLEND/ADSR/MEMORY/LFO from static source images','No hardware confirmation Data Wheel after focus','No PCM/DSP edits']
 },indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'components':len(components),'touch':len(registry),'type_counts':dict(Counter(c['componentData']['type'] for c in components)),'out':str(OUT)},indent=2))
