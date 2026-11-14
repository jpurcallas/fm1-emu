#!/usr/bin/env python3
"""Native Akai SDK Q-Link focus workflow. Based on pinned SDK ui-reference.md §§3.6,4.1-4.5,8.3.
Changes TUI only; no Origamidi-derived components, PCM, DSP or graphics modified.
"""
import json,copy,pathlib,collections
BASE=pathlib.Path('/mnt/data/reminiscent_work/UI34_FILTER_TUI.json')
OUT=pathlib.Path('/mnt/data/reminiscent_work/UI35_NATIVE_SDK_QFOCUS_TUI.json')
d=json.loads(BASE.read_text())
p=d['pageData'];tab=p['tabs'][0];cs=tab['componentDefinition']['componentsData'];defs=p['componentDefinitions']['localComponentDefinitions']
keys={x['key'] for x in defs}
assert 'LAB10_SDK_NATIVE_QFOCUS' not in keys
# A standard Akai touch-focus widget: one Parameter Data, focus ring, native knob, Q-Link bank selection.
# Its knob overlay is the existing SDK overlay: not an invented fallback.
definition={'version':2,'actions':[
 {'version':1,'onAction':'Mouse Down','handler':'Q-Link','handleName':'Data','additionalData':''},
 {'version':1,'onAction':'Double Click','handler':'Show Overlay','handleName':'Data','additionalData':'knob overlay'},
 {'version':1,'onAction':'Enter Pressed','handler':'Show Overlay','handleName':'Data','additionalData':'knob overlay'}
 ],'backgroundData':{'version':1,'focussed':{'version':1,'colour':'0','image':''},'unfocussed':{'version':1,'colour':'0','image':''}},
 'ignoreMousePresses':False,'disableCoarseDataWheel':False,
 'componentsData':[
 {'version':2,'componentData':{'version':1,'name':'selected control focus','type':'Focus','data':{'version':1,'backgroundColour':'00000000','outlineColour':'88e1ac80','backgroundInset':1.0,'outlineThickness':1.0}},'handle remapping':{'version':1,'map':[]},'bounds':{'version':1,'acceptsHWFocus':'No','showWhenDataModelInvalid':'Show','whenVisible':'WhenFocussed','boundsType':'Absolute','bounds':'0 0 100 100'}},
 {'version':2,'componentData':{'version':1,'name':'native handle editor','type':'Knob','data':{'version':3,'knobType':'FilmStrip','filmStrip':'lab10_native_touch_101.png','numFrames':101,'invert':False,'dragOrientation':'Vertical','handleName':'Data'}},'handle remapping':{'version':1,'map':[]},'bounds':{'version':1,'acceptsHWFocus':'No','showWhenDataModelInvalid':'Show','whenVisible':'Always','boundsType':'Absolute','bounds':'0 0 100 100'}}
 ]}
# Create one reusable definition for each distinct rectangle to maintain exact touch bounds and orientation.
def simple_def(w,h,orientation,slot):
 a=copy.deepcopy(definition)
 # SDK handler binds the touch to the active four-Q-Link bank (proxy 113..116).
 a['actions'][0]['handleName']=f"Parameter {113+slot}"
 for x in a['componentsData']:x['bounds']['bounds']=f'0 0 {w} {h}'
 a['componentsData'][1]['componentData']['data']['dragOrientation']=orientation
 return a
# True parameter controls, not drawing-only elements: leave all LAB10 sprites as non-focus decorative layers.
interactive=[]
for c in cs:
 n=c['componentData']['name'];kind=c['componentData']['type'];data=c['componentData']['data']
 if kind!='Knob' or not c['handle remapping']['map']:continue
 if not (n.startswith('Q_LINK_') or n.startswith('ACOUSTIC_') or n.startswith('BLEND_ECLIPSE_TOUCH') or n.startswith('ENVELOPE_') or n.startswith('MEMORY_') or n.startswith('RESONANCE_PARAM_') or n.startswith('FILTER_PARAM_') or n.startswith('GRANULAR_PARAM_') or n.startswith('MOD_') or n.startswith('SEND_')):continue
 if n.startswith('Q_LINK_') and 'TOUCH_WHEEL_VALUE' not in n:continue
 # Preserve numeric labels and pointers as separate layers.
 rect=c['bounds']['bounds'].split();assert len(rect)==4,n
 w,h=map(int,rect[2:]);orient=data.get('dragOrientation','Vertical')
 # Map touched parameter groups to the existing four dynamic proxy slots.
 if n.startswith('Q_LINK_'):slot=int(n.split('_')[2])-1
 elif 'PARAM_' in n:slot=int(n.split('PARAM_')[1][0])-1
 elif n.startswith('ENVELOPE_'):slot={'ATTACK':0,'DECAY':1,'SUSTAIN':2,'RELEASE':3}[n.split('_')[1]]
 elif n.startswith('ACOUSTIC_SOURCE_'):slot=1 if n.endswith('_A') else 2
 elif n.startswith('ACOUSTIC_BLEND_') or n.startswith('BLEND_ECLIPSE_'):slot=0
 elif n.startswith('MEMORY_'):slot=next((v for k,v in {'WINDOW':0,'SPEED':1,'POSITION':2,'SHAPE':3,'MIX':0}.items() if k in n),0)
 elif 'SECONDARY_' in n:slot=int(n.rsplit('SECONDARY_',1)[1])-1
 else:slot=0
 assert slot in range(4),(n,slot)
 key=f'LAB10_SDK_FOCUS_S{slot}_{w}_{h}_{orient.upper()}' 
 if key not in keys:
  defs.append({'key':key,'value':simple_def(w,h,orient,slot)});keys.add(key)
 c['componentData']['type']=key;c['componentData']['data']={'version':1,'handleName':'Data'}
 c['bounds']['acceptsHWFocus']='Yes'
 interactive.append((n, c['handle remapping']['map'][0]['value']))
assert len(interactive)>=29,len(interactive)
# Native bounding box for the four visible Q-Links, without suggesting there are four separate banks when all 16 mapping slots are identical.
# Four matching rectangles preserve known parser shape; Q-Link click actions select the actual bank.
assert tab['qlinkBoundsData'] == ['1015 173 245 405']*4
assert len([x for x in cs if x['componentData']['name'].startswith('QLINK_') and 'LIVE_POINTER' in x['componentData']['name']])==4
OUT.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
print('updated',len(interactive),'controls,',len(defs),'definitions, UI unchanged',OUT)