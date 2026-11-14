#!/usr/bin/env python3
"""Add faithfully rendered memory-window and independent on/off status LEDs to UI32. No DSP or samples changed."""
from PIL import Image, ImageDraw, ImageFilter
import pathlib, json, copy, subprocess, shutil, zipfile, hashlib
base=pathlib.Path('/mnt/data/REminiSCENT_UI32_FOCO_DIAL_QLINKS_TOUCH_CANDIDATO.zip')
output=pathlib.Path('/mnt/data/REminiSCENT_UI32_FOCO_QLINKS_ONOFF_MEMORY_CANDIDATO.zip')
work=pathlib.Path('/mnt/data/reminiscent_blackbox/UI32_MEMORY')
prefix='Yeti Fingers - VST - REminiSCENT/'
tuiname=prefix+'Plugin Skins/TUI.json'
skindir=work/prefix/'Plugin Skins'
skindir.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(base) as z:
 t=json.loads(z.read(tuiname)); original_files=set(z.namelist())
cs=t['pageData']['tabs'][0]['componentDefinition']['componentsData']
assert len(cs)==124
# Exact approved LAB10-style thin-gold window overlay, composited atop its already-approved memory waveform.
W,H,N=712,69,64
strip=Image.new('RGBA',(W,H*N),(0,0,0,0))
for i in range(N):
 y=i*H
 # WINDOW parameter controls the span. A musical sample window expands from an 8% minimum to 84% of buffer.
 span=int(W*(0.08+0.76*i/(N-1)))
 x0=(W-span)//2; x1=x0+span
 d=ImageDraw.Draw(strip)
 d.rectangle((x0,y+2,x1,y+H-3),fill=(225,152,72,20),outline=(242,176,102,205),width=2)
 d.line((x0,y+1,x0,y+H-2),fill=(254,192,108,255),width=3)
 d.line((x1,y+1,x1,y+H-2),fill=(254,192,108,255),width=3)
 for dx in (-3,3):
  d.line((x0+dx,y+6,x0+dx,y+17),fill=(254,205,152,160),width=1)
  d.line((x1+dx,y+6,x1+dx,y+17),fill=(254,205,152,160),width=1)
file1=skindir/'lab10_memory_window_dynamic_64.png';strip.save(file1,optimize=True)
# Position cursor rendered independently from WINDOW span. The real playhead already tracks DSP captured segment (Parameter 121).
strip2=Image.new('RGBA',(W,H*N),(0,0,0,0))
for i in range(N):
 y=i*H;x=round(8+(W-16)*i/(N-1));d=ImageDraw.Draw(strip2)
 d.line((x,y+1,x,y+H-3),fill=(255,230,179,180),width=1)
 d.polygon([(x-4,y),(x+4,y),(x,y+6)],fill=(255,211,146,230))
file2=skindir/'lab10_memory_position_dynamic_64.png';strip2.save(file2,optimize=True)
# Active-state accents, independent of the visually selected EDIT card. They illuminate only when the DSP on/off parameter is 1.
light=Image.new('RGBA',(18,18),(0,0,0,0));d=ImageDraw.Draw(light)
d.ellipse((1,1,16,16),fill=(255,177,75,35));d.ellipse((4,4,13,13),fill=(255,187,96,195));d.ellipse((6,6,11,11),fill=(255,236,173,235))
light.save(skindir/'lab10_on_state_glow.png',optimize=True)

def dynamic_img(name,image,bounds,parameter,extra):
 return {'version':2,'componentData':{'version':1,'name':name,'type':'Image','data':{'version':2,'imageType':'FilmStrip','colour':'0','image':image,'numFrames':64,'handleName':f'Parameter {parameter}'}},'handle remapping':{'version':1,'map':[]},'bounds':{'version':2,'acceptsHWFocus':'No','showWhenDataModelInvalid':'Hide','whenVisible':'Always','boundsType':'Absolute','bounds':bounds,'additionalInvalidatingHandles':extra}}
def static_img(name,bounds,parameter,page):
 return {'version':2,'componentData':{'version':1,'name':name,'type':'Image','data':{'version':1,'colour':'0','image':'lab10_on_state_glow.png'}},'handle remapping':{'version':1,'map':[]},'bounds':{'version':2,'acceptsHWFocus':'No','showWhenDataModelInvalid':'Hide','whenVisible':'Always','boundsType':'Absolute','bounds':bounds,'additionalInvalidatingHandles':[f'IndexedEnabling/{page}/11/Parameter 112',f'IndexedEnabling/1/2/Parameter {parameter}']}}
# Place new visual-only images immediately after LIVE_MEMORY_READHEAD and before touch controls, preserving all hit-testing.
idx=next(i for i,x in enumerate(cs) if x['componentData']['name']=='LIVE_MEMORY_READHEAD_UI31')+1
mem=[dynamic_img('LIVE_MEMORY_WINDOW_BOUNDS_UI32','lab10_memory_window_dynamic_64.png','84 455 712 69',33,['IndexedEnabling/4/11/Parameter 112']),dynamic_img('LIVE_MEMORY_SELECTED_POSITION_UI32','lab10_memory_position_dynamic_64.png','84 455 712 69',35,['IndexedEnabling/4/11/Parameter 112'])]
for x in reversed(mem):cs.insert(idx,x)
# LEDs in original approved card positions, including selected-vs-enabled distinction.
lights=[]
for page,vals,xs in [(7,[8,9,10,11],[132,312,492,672]),(9,[16,17,18],[144,353,562]),(10,[12,13,14,15],[132,312,492,672])]:
 for p,x in zip(vals,xs):lights.append(static_img(f'UI32_EFFECT_ENABLED_LED_P{p}',f'{x-9} 243 18 18',p,page))
idx=next(i for i,x in enumerate(cs) if x['componentData']['name']=='TOUCH_TAB_ACOUSTIC')
for x in reversed(lights):cs.insert(idx,x)
assert len(cs)==124+2+11
assert sum(x['componentData']['name'].startswith('UI32_EFFECT_ENABLED') for x in cs)==11
new_json=(json.dumps(t,ensure_ascii=False,indent=2)+'\n').encode()
(skindir/'TUI.json').write_bytes(new_json)
shutil.copy2(base,output)
subprocess.run(['zip','-q','-d',str(output),tuiname],check=True)
subprocess.run(['zip','-q','-X',str(output),tuiname,*[prefix+'Plugin Skins/'+f.name for f in [file1,file2,skindir/'lab10_on_state_glow.png']]],cwd=work,check=True)
with zipfile.ZipFile(base) as a,zipfile.ZipFile(output) as b:
 assert len(b.namelist())==len(a.namelist())+3
 assert set(b.namelist())-set(a.namelist())=={prefix+'Plugin Skins/'+p.name for p in [file1,file2,skindir/'lab10_on_state_glow.png']}
 assert a.read(prefix+'Plugin Skins/Q-Links.json')==b.read(prefix+'Plugin Skins/Q-Links.json')
 assert all(a.getinfo(n).CRC==b.getinfo(n).CRC for n in a.namelist() if n!=tuiname)
 assert b.testzip() is None
 assert len([n for n in b.namelist() if n.endswith('.wav')])==254
print('PASS: 137 components, 13 added images, approved UI31 bases unchanged, 254 WAV, all DSP intact')
print('ZIP',output,'SIZE',output.stat().st_size,'SHA256',hashlib.file_digest(open(output,'rb'),'sha256').hexdigest())