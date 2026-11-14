#!/usr/bin/env python3
"""Render moving ACOUSTIC BLEND bar from LAB10 approved HTML controls, 32 positions.
Overlay covers its old baked track and thumb, preserving LAB10 base image byte-for-byte.
"""
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
import zipfile,json,io,hashlib
src=Path('/mnt/data/reminiscent_work/REminiSCENT_UI33_LAB10_FILTER_CUTOFF_CANDIDATE.zip')
dst=Path('/mnt/data/reminiscent_work/REminiSCENT_UI33_FILTER_ACOUSTIC_BAR_CANDIDATE.zip')
html=Path('/mnt/data/reminiscent_blackbox/REminiSCENT_UI_LAB_10_INTEGRATION.html').read_text()
frames=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 pg=b.new_page(viewport={'width':1280,'height':800})
 pg.set_content(html)
 pg.add_style_tag(content='*{animation:none!important;transition:none!important}body,html,#shell,#stage,#scene{background:transparent!important;box-shadow:none!important;}#art{display:none!important}')
 pg.evaluate("document.getElementById('splash').style.display='none'")
 for i in range(32):
  v=round(127*i/31)
  pg.evaluate("(v)=>{let p=window.REminiSCENTPresetAPI.getState();p.params.acousticBlend=v;window.REminiSCENTPresetAPI.restoreState(p);document.getElementById('splash').style.display='none'}",v)
  frames.append(Image.open(io.BytesIO(pg.locator('.directBlend').first.screenshot(omit_background=True))).convert('RGBA'))
 b.close()
strip=Image.new('RGBA',(530,31*32))
for i,frame in enumerate(frames):strip.paste(frame,(0,31*i))
f='lab10_acoustic_blend_direct_from_html_32.png';buf=io.BytesIO();strip.save(buf,format='PNG',optimize=True)
root='Yeti Fingers - VST - REminiSCENT/Plugin Skins/'
with zipfile.ZipFile(src) as z:
 t=json.loads(z.read(root+'TUI.json'));c=t['pageData']['tabs'][0]['componentDefinition']['componentsData'];
 c.append({'version':2,'componentData':{'version':1,'name':'ACOUSTIC_BLEND_LAB10_LIVE_THUMB','type':'Knob','data':{'version':3,'knobType':'FilmStrip','filmStrip':f,'numFrames':32,'invert':False,'dragOrientation':'Horizontal','handleName':'Data'}},'handle remapping':{'version':1,'map':[{'key':'Data','value':'Parameter 19'}]},'bounds':{'version':2,'acceptsHWFocus':'Yes','showWhenDataModelInvalid':'Hide','whenVisible':'Always','boundsType':'Absolute','bounds':'49 457 530 31','additionalInvalidatingHandles':['IndexedEnabling/0/11/Parameter 112']}})
 raw=json.dumps(t,ensure_ascii=False,indent=2).encode()
 with zipfile.ZipFile(dst,'w',allowZip64=True) as out:
  for info in z.infolist():out.writestr(info,raw if info.filename==root+'TUI.json' else z.read(info.filename))
  out.writestr(root+f,buf.getvalue(),compress_type=zipfile.ZIP_DEFLATED)
print('Done',dst,hashlib.file_digest(open(dst,'rb'),'sha256').hexdigest())