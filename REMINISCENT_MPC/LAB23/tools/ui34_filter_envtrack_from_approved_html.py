#!/usr/bin/env python3
"""UI34: faithful FILTER ghost response: HTML LAB10 equation, no new artwork.
Main curve from original HTML, dashed ENV+TRACK overlay controlled by derived host parameter 125.
Does not alter any 19 base backgrounds, sound, or other GUI widgets.
"""
import io,math,json,zipfile,hashlib,pathlib,copy
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw
D=pathlib.Path('/mnt/data/reminiscent_work')
original=D/'UI33_NATIVE_FILTER_ACOUSTIC_PRIVATE_BLOCKED.zip'
output=D/'REminiSCENT_UI34_FILTER_ENVTRACK_PRIVATE_CANDIDATE.zip'
html=pathlib.Path('/mnt/data/reminiscent_blackbox/REminiSCENT_UI_LAB_10_INTEGRATION.html').read_text()
root='Yeti Fingers - VST - REminiSCENT/Plugin Skins/'
with zipfile.ZipFile(original) as zz:
 t=json.loads(zz.read(root+'TUI.json'))
 cs=t['pageData']['tabs'][0]['componentDefinition']['componentsData']
 main=next(c for c in cs if c['componentData']['name']=='FILTER_CUTOFF_ORIGINAL_LAB10_REACTIVE')
 assert main['componentData']['data']['filmStrip']=='lab10_filter_from_approved_html_24.png'
main_frames=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 page=b.new_page(viewport={'width':1280,'height':800},device_scale_factor=1)
 page.set_content(html)
 page.add_style_tag(content='*{animation:none!important;transition:none!important}body,html,#shell,#stage,#scene{background:transparent!important;box-shadow:none!important;}#art{display:none!important;} .filterPanel .responseGraph > path:first-of-type{visibility:hidden!important}')
 page.evaluate("document.getElementById('splash').style.display='none'")
 page.locator('[data-page="6"]').first.click()
 for i in range(24):
  v=round(127*i/23)
  page.evaluate("(v)=>{let p=window.REminiSCENTPresetAPI.getState();p.params.filterCutoff=v;p.params.filterEnv=64;p.params.filterTrack=64;window.REminiSCENTPresetAPI.restoreState(p);document.getElementById('splash').style.display='none'}",v)
  im=Image.open(io.BytesIO(page.locator('.filterPanel').screenshot(omit_background=True))).convert('RGBA').resize((595,231),Image.Resampling.LANCZOS)
  main_frames.append(im)
 b.close()
main_strip=Image.new('RGBA',(595,231*len(main_frames)),(0,0,0,0))
for idx,im in enumerate(main_frames):main_strip.paste(im,(0,231*idx))
memb=io.BytesIO();main_strip.save(memb,format='PNG',optimize=True)
# Exact LAB10 filterPath curve formula (filterMix default is 127); no new design.
W,H=595,231
mod_strip=Image.new('RGBA',(W,H*64),(0,0,0,0))
for fi in range(64):
 cutoff=127*fi/63
 center=20*1000**(cutoff/127)
 pts=[]
 for i in range(271):
  freq=20*1000**(i/270)
  response=1/math.sqrt(1+(freq/center)**4)
  x=(22+i/270*535)*W/580
  y=(16+(1-response)*168)*H/225
  pts.append((x,y))
 frame=Image.new('RGBA',(W,H),(0,0,0,0))
 draw=ImageDraw.Draw(frame)
 # LAB10 ghost: stroke #77aba6, 2px, dashed 5/8, alpha .72
 from math import hypot
 cur=0.;drawing=True;pattern=(5.0,8.0)
 for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
  span=hypot(x1-x0,y1-y0)
  if span<1e-12:continue
  distance=0.
  while distance<span:
   limit=pattern[0 if drawing else 1]-cur
   step=min(limit,span-distance)
   if drawing:
    a=distance/span;b=(distance+step)/span
    draw.line([(x0+(x1-x0)*a,y0+(y1-y0)*a),(x0+(x1-x0)*b,y0+(y1-y0)*b)],fill=(119,171,166,184),width=2)
   distance+=step;cur+=step
   if cur>=pattern[0 if drawing else 1]-1e-6:
    cur=0;drawing=not drawing
 mod_strip.paste(frame,(0,fi*H))
# 64 frames as 2 x 32-frame strips to comply with 8192px vertical texture limit.
strips=[]
for group in range(2):
 piece=mod_strip.crop((0,group*32*H,W,(group+1)*32*H))
 assert piece.height==7392 and piece.height<=8192
 buf=io.BytesIO();piece.save(buf,format='PNG',optimize=True)
 name=f'lab10_filter_envtrack_from_html_32_{group}.png'
 pathlib.Path('/mnt/data/reminiscent_work/'+name).write_bytes(buf.getvalue())
 strips.append((name,buf.getvalue()))
cs_before=len(cs)
for group,(name,blob) in enumerate(strips):
 vis={'version':2,'componentData':{'version':1,'name':f'FILTER_ENV_KEY_ORIGINAL_LAB10_REACTIVE_{group}','type':'Knob','data':{'version':3,'knobType':'FilmStrip','filmStrip':name,'numFrames':32,'invert':False,'dragOrientation':'Horizontal','handleName':'Data'}},'handle remapping':{'version':1,'map':[{'key':'Data','value':'Parameter 126'}]},'bounds':{'version':2,'acceptsHWFocus':'No','showWhenDataModelInvalid':'Hide','whenVisible':'Always','boundsType':'Absolute','bounds':'49 248 595 231','additionalInvalidatingHandles':['IndexedEnabling/6/11/Parameter 112',f'IndexedEnabling/{group}/2/Parameter 127']}}
 cs.append(vis)

content=json.dumps(t,ensure_ascii=False,indent=2).encode()
assert len(cs)==cs_before+2 and all(x['componentData']['name'].startswith('FILTER_ENV_KEY_ORIGINAL_LAB10_REACTIVE_') for x in cs[-2:])
pathlib.Path('/mnt/data/reminiscent_work/UI34_FILTER_TUI.json').write_bytes(content)
pathlib.Path('/mnt/data/reminiscent_work/lab10_filter_from_approved_html_24_UI34.png').write_bytes(memb.getvalue())
print('UI34 asset stage',len(cs),'components, 24 main frames, 64 ghost frames',sum(len(x[1]) for x in strips),'two ghost PNG bytes')