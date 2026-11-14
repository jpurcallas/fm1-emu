#!/usr/bin/env python3
from pathlib import Path
import json,copy
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
B=Path('/mnt/data')
R=B/'REminiSCENT_LAB25_MPC_UI11_APPROVED'/'Yeti Fingers - VST - REminiSCENT'/'Plugin Skins'
J=json.loads((R/'TUI.json').read_text());A=J['pageData']['tabs'][0]['componentDefinition']['componentsData']
sc=628/740
selected={7:('selectedChar',['distortion','tape','vinyl','crush'],109),9:('selectedMod',['lfo1','lfo2','env2'],111),10:('selectedSend',['delay','reverb','mod1','mod2'],110)}
source=(B/'REminiSCENT_UI_MPC_REFERENCIA_11_SIN_MODWHEEL.html').read_text()
with sync_playwright() as pl:
 b=pl.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1280,'height':800},device_scale_factor=1)
 page.set_content(source)
 page.get_by_text('SALTAR INTRO').click()
 for pg,(key,opts,param) in selected.items():
  for index,val in enumerate(opts):
   page.evaluate('(a)=>{state.page=a.pg;state[a.key]=a.val;render();}',{'pg':pg,'key':key,'val':val})
   shot=page.screenshot()
   from io import BytesIO
   im=Image.open(BytesIO(shot)).convert('RGB')
   im=im.crop((0,0,1280,740)).resize((1280,628),Image.Resampling.LANCZOS)
   d=ImageDraw.Draw(im)
   for yy in (269,385,502,617):
    y=int(yy*sc); rgb=im.getpixel((1207,min(y+7,627)))
    d.rectangle((1093,y-5,1215,y+23),fill=rgb)
   im.save(R/f'lab10_mpc_{pg:02d}_{index}.png',optimize=True)
 b.close()
# Replace the 3 single-page static images with choices bound to host selector.
for pg,(key,opts,param) in selected.items():
 i=next(i for i,x in enumerate(A) if x['componentData']['name']==f'APPROVED_LAB10_SCREEN_{pg:02d}')
 old=A.pop(i)
 replacements=[]
 for k,_ in enumerate(opts):
  c=copy.deepcopy(old)
  c['componentData']['name']=f'APPROVED_LAB10_SCREEN_{pg:02d}_STATE_{k}'
  c['componentData']['data']['image']=f'lab10_mpc_{pg:02d}_{k}.png'
  c['bounds']['additionalInvalidatingHandles'].append(f'IndexedEnabling/{k}/{len(opts)}/Parameter {param}')
  replacements.append(c)
 A[i:i]=replacements
# A native transparent Button is touch-selectable and changes bool *instantly*
# as opposed to the older invisible rotary knob (which required a drag).
PNG='lab10_touch_hit.png'
def button(name,param,bounds,group=1,id=1,vis=None,on=PNG,off=PNG):
 bb={'version':2,'acceptsHWFocus':'Yes','showWhenDataModelInvalid':'Hide','whenVisible':'Always','boundsType':'Absolute','bounds':bounds}
 if vis:bb['additionalInvalidatingHandles']=[vis]
 return {'version':2,'componentData':{'version':1,'name':name,'type':'Button','data':{'version':2,'onImage':on,'offImage':off,'buttonId':id,'numButtonsInGroup':group,'handleName':'Data','gestureBehaviour':'Instant'}},'handle remapping':{'version':1,'map':[{'key':'Data','value':f'Parameter {param}'}]},'bounds':bb}
for i,x in enumerate(A):
 if x['componentData']['name'] in ('ACOUSTIC_ON_A','ACOUSTIC_ON_B','MEMORY_FREEZE','MEMORY_REVERSE','MEMORY_TIDE') or x['componentData']['name'].startswith('MOD_ONOFF_'):
  p=x['handle remapping']['map'][0]['value'].split()[-1]
  A[i]=button(x['componentData']['name'],int(p),x['bounds']['bounds'],vis=x['bounds']['additionalInvalidatingHandles'][0])
# Add all 4 CHARACTER and all 4 SEND FX on/off toggles, independently bound.
for pg,start in [(7,8),(10,12)]:
 for k in range(4):
  x=50+180*k
  A.append(button(f"{'CHAR' if pg==7 else 'SEND'}_ONOFF_{k}",start+k,f'{x+22} {round(505*sc)} 125 42',vis=f'IndexedEnabling/{pg}/11/Parameter 112'))
# Existing oscillator wave selector, sections and effects remain direct edit controls.
# Ensure no full-screen autoplay/opaque Solaris plate entered the root tree.
assert all('SOLARIS' not in x['componentData']['name'] for x in A)
assert all('fondos/' not in str(x['componentData']['data']) for x in A)
(R/'TUI.json').write_text(json.dumps(J,indent=2,ensure_ascii=False)+'\n')
print('LIVE LAB10 UI: 11 sections, 11 choice variants,',len(A),'SDK widgets')
