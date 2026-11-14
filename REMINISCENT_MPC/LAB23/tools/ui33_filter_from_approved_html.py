#!/usr/bin/env python3
"""Render FILTER exactly from the author's original LAB10 HTML, 24 host-driven frames.
Uses original CSS/SVG, no self-invented prior artwork; filter ENV/TRACK interaction remains pending.
"""
from pathlib import Path
import io,json,zipfile,hashlib
from playwright.sync_api import sync_playwright
from PIL import Image
src=Path('/mnt/data/reminiscent_work/REminiSCENT_UI33_APPROVED_POINTER_CANDIDATE.zip')
dst=Path('/mnt/data/reminiscent_work/REminiSCENT_UI33_LAB10_FILTER_CUTOFF_CANDIDATE.zip')
HTML=Path('/mnt/data/reminiscent_blackbox/REminiSCENT_UI_LAB_10_INTEGRATION.html').read_text()
root='Yeti Fingers - VST - REminiSCENT/Plugin Skins/'
frames=[]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 page=browser.new_page(viewport={'width':1280,'height':800},device_scale_factor=1)
 page.set_content(HTML)
 page.add_style_tag(content='*{animation:none!important;transition:none!important}body,html,#shell,#stage,#scene{background:transparent!important;box-shadow:none!important;}#art{display:none!important;}')
 page.evaluate("document.getElementById('splash').style.display='none'")
 page.locator('[data-page="6"]').first.click()
 for i in range(24):
  v=round(127*i/23)
  page.evaluate("(v)=>{let p=window.REminiSCENTPresetAPI.getState();p.params.filterCutoff=v;window.REminiSCENTPresetAPI.restoreState(p);document.getElementById('splash').style.display='none'}",v)
  data=page.locator('.filterPanel').screenshot(omit_background=True)
  img=Image.open(io.BytesIO(data)).convert('RGBA').resize((595,231),Image.Resampling.LANCZOS)
  frames.append(img)
 browser.close()
strip=Image.new('RGBA',(595,231*24),(0,0,0,0))
for i,f in enumerate(frames):strip.paste(f,(0,i*231))
mem=io.BytesIO();strip.save(mem,format='PNG',optimize=True)
with zipfile.ZipFile(src) as z:
 tui=json.loads(z.read(root+'TUI.json'))
 cs=tui['pageData']['tabs'][0]['componentDefinition']['componentsData']
 cs.append({'version':2,'componentData':{'version':1,'name':'FILTER_CUTOFF_ORIGINAL_LAB10_REACTIVE','type':'Knob','data':{'version':3,'knobType':'FilmStrip','filmStrip':'lab10_filter_from_approved_html_24.png','numFrames':24,'invert':False,'dragOrientation':'Horizontal','handleName':'Data'}},'handle remapping':{'version':1,'map':[{'key':'Data','value':'Parameter 42'}]},'bounds':{'version':2,'acceptsHWFocus':'Yes','showWhenDataModelInvalid':'Hide','whenVisible':'Always','boundsType':'Absolute','bounds':'49 248 595 231','additionalInvalidatingHandles':['IndexedEnabling/6/11/Parameter 112']}})
 raw=json.dumps(tui,ensure_ascii=False,indent=2).encode()
 with zipfile.ZipFile(dst,'w',allowZip64=True) as out:
  for item in z.infolist():out.writestr(item,raw if item.filename==root+'TUI.json' else z.read(item.filename))
  out.writestr(root+'lab10_filter_from_approved_html_24.png',mem.getvalue(),compress_type=zipfile.ZIP_DEFLATED)
print('FILTER frames=24, size=',strip.size,'sha=',hashlib.sha256(mem.getvalue()).hexdigest(),'ZIP=',dst,'bytes=',dst.stat().st_size)