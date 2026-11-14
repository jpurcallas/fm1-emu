#!/usr/bin/env python3
"""UI31: only approved LAB10 rasters and exact Solaris v09; SDK native controls.
No DSP/PCM edits; structural/asset validation is NOT MPC hardware proof.
"""
from pathlib import Path
import json,zipfile,io,hashlib,math,copy,shutil,cv2,numpy as np
from PIL import Image,ImageDraw,ImageFilter
R=Path('/mnt/data/reminiscent_blackbox'); src=R/'REBUILD_CONTROLS_COMPLETE'/'Plugin Skins'
D=R/'UI31_LIVE'/'Plugin Skins';D.mkdir(parents=True,exist_ok=True)
for p in src.iterdir():
 if p.is_file():shutil.copy2(p,D/p.name)
tui=json.loads((D/'TUI.json').read_text()); body=tui['pageData']['tabs'][0]['componentDefinition']; cs=body['componentsData']; assert len(cs)==106
old_imgs=[(c['componentData']['name'],c['componentData']['data']['image']) for c in cs if c['componentData']['name'].startswith('APPROVED_LAB10_')]; assert len(old_imgs)==19
# Only new overlays / approved sprite strips; never change any of 19 original screenshot bytes.

def make_visual(name, kind, data,rect, gates):
 c={'version':2,'componentData':{'version':1,'name':name,'type':kind,'data':data},'handle remapping':{'version':1,'map':[]},'bounds':{'version':2,'acceptsHWFocus':'Yes' if kind=='Envelope' else 'No','showWhenDataModelInvalid':'Hide','whenVisible':'Always','boundsType':'Absolute','bounds':' '.join(map(str,rect)),'additionalInvalidatingHandles':gates}}
 return c
page=lambda n: [f'IndexedEnabling/{n}/11/Parameter 112']
sub=lambda n,p,i,ct:page(n)+[f'IndexedEnabling/{i}/{ct}/Parameter {p}']
film=lambda file,n,host:{'version':2,'imageType':'FilmStrip','colour':'0','image':file,'numFrames':n,'handleName':f'Parameter {host}'}
normal=lambda file:{'version':2,'imageType':'Regular','colour':'0','image':file}
visual=[]
# OSC: redraw waveform only, keeping original LAB10 panel and 8 cards untouched.
# Remove baked SAW path in a narrow clip with telegraphed background, draw original LAB10 wave formula for all 8 shapes.
orig=Image.open(src/'lab10_mpc_01.png').convert('RGB'); x0,y0,w,h=198,246,488,82
b=np.array(orig.crop((x0,y0,x0+w,y0+h)))
hsv=cv2.cvtColor(b,cv2.COLOR_RGB2HSV)
mask=cv2.inRange(hsv,np.array([5,35,110]),np.array([40,210,255]))
mask=cv2.dilate(mask, np.ones((3,3),np.uint8),iterations=1)
clean=cv2.inpaint(b,mask,5,cv2.INPAINT_TELEA)
# exact LAB10 waveValue(t,w) formula
waves=('SINE','TRIANGLE','SAW','SQUARE','PULSE','ORGAN','BRIGHT','HOLLOW')
def wave_val(t,kind):
 phase=(t/(math.pi*2))%1
 return {'SINE':lambda:math.sin(t),'TRIANGLE':lambda:2/math.pi*math.asin(math.sin(t)),'SAW':lambda:2*phase-1,'SQUARE':lambda:1 if phase<.5 else -1,'PULSE':lambda:1 if phase<.27 else -1,'ORGAN':lambda:.63*math.sin(t)+.24*math.sin(t*2)+.13*math.sin(t*3),'BRIGHT':lambda:.53*math.sin(t)+.27*math.sin(t*3)+.2*math.sin(t*5),'HOLLOW':lambda:.7*math.sin(t)+.3*math.sin(t*3)}[kind]()
frames=[]
for wave in waves:
 im=Image.fromarray(clean).convert('RGBA').resize((w*2,h*2),Image.Resampling.BICUBIC)
 dr=ImageDraw.Draw(im)
 pts=[(int((18+i/400*(w-52))*2),int((h/2-wave_val(i/400*math.pi*4, wave)*26)*2)) for i in range(401)]
 dr.line(pts,fill=(246,204,162,255),width=4,joint='curve')
 frames.append(im.resize((w,h),Image.Resampling.LANCZOS))
strip=Image.new('RGBA',(w,h*8));
for i,im in enumerate(frames):strip.alpha_composite(im,(0,h*i))
strip.save(D/'lab10_osc_wave_live_8.png',optimize=True)
visual.append(make_visual('LIVE_OSC_WAVE_LAB10','Image',film('lab10_osc_wave_live_8.png',8,2),(x0,y0,w,h),page(1)))
# OSC cards: original SAW is baked as selected. Update lamp/bar overlays so the
# eight radio-button selections show their own selected state, not a stuck SAW.
card_x,card_y,card_w,card_h=49,368,779,146
card_source=orig.crop((card_x,card_y,card_x+card_w,card_y+card_h)).convert('RGBA')
led_on=orig.crop((281,374,302,396)).convert('RGBA')
led_off=orig.crop((378,374,399,396)).convert('RGBA')
bar_on=orig.crop((257,484,331,503)).convert('RGBA')
bar_off=orig.crop((354,484,428,503)).convert('RGBA')
selector=Image.new('RGBA',(card_w,card_h*8),(0,0,0,0))
for i in range(8):
 frame=Image.new('RGBA',(card_w,card_h),(0,0,0,0))
 # Eliminate the original fixed SAW indicator from the approved source image.
 frame.alpha_composite(led_off,(281-card_x,374-card_y))
 frame.alpha_composite(bar_off,(257-card_x,484-card_y))
 # Reuse exact SAW-approved glowing LED/bar pixels on the actual selected card.
 if i!=2:
  sx=281+(i-2)*98;bx=257+(i-2)*98
  frame.alpha_composite(led_on,(sx-card_x,374-card_y))
  frame.alpha_composite(bar_on,(bx-card_x,484-card_y))
 else:
  frame.alpha_composite(led_on,(281-card_x,374-card_y))
  frame.alpha_composite(bar_on,(257-card_x,484-card_y))
 selector.alpha_composite(frame,(0,i*card_h))
selector.save(D/'lab10_osc_selection_live_8.png',optimize=True)
visual.append(make_visual('LIVE_OSC_SELECTOR_LAB10','Image',film('lab10_osc_selection_live_8.png',8,2),(card_x,card_y,card_w,card_h),page(1)))
# BLEND: reconstruct eclipse over the ORIGINAL LAB10 sun JPEG & dark planet raster (no new art).
base=Image.open(src/'lab10_mpc_02.png').convert('RGB')
sun=Image.open(R/'imgs_blend.png').convert('RGB');planet=base.crop((281,184,735,555)).convert('RGBA')
# Original planet mapped to 455x371 in screenshot. Preserve proportions and texture with independent transparency.
planet_mask=Image.new('L',planet.size,0);pm=ImageDraw.Draw(planet_mask);pm.ellipse((0,0,planet.width-1,planet.height-1),fill=255)
planet_mask=planet_mask.filter(ImageFilter.GaussianBlur(2.6));planet.putalpha(planet_mask)
# Region only; preserve screenshot outside eclipse. Reconstitute original sun seen behind moving disc.
bx,by,bw,bh=192,178,613,392
baseline=base.crop((bx,by,bx+bw,by+bh)).convert('RGBA')
# Source JPEG is the approved LAB10 celestial background, originally positioned at x~0,y~55.
under=baseline.copy()
under_draw=Image.new('RGBA',(bw,bh));ud=ImageDraw.Draw(under_draw)
# fill only the dark occulting disc with original sun pixels, maintaining existing corona outside.
source=Image.new('RGBA',(bw,bh))
for py in range(bh):
 sy=min(sun.height-1,max(0,int(by+py-55)))
 for px in range(bw):
  sx=min(sun.width-1,max(0,bx+px))
  # minimal render cost: only construct inside disc
  if ((bx+px-508)/223)**2 + ((by+py-368)/187)**2<=1.05:
   rgb=sun.getpixel((sx,sy)); source.putpixel((px,py),(int(rgb[0]*.86),int(rgb[1]*.83),int(rgb[2]*.81),255))
sunmask=Image.new('L',(bw,bh),0);md=ImageDraw.Draw(sunmask);md.ellipse((281-bx,184-by,735-bx,555-by),fill=255)
sunmask=sunmask.filter(ImageFilter.GaussianBlur(8))
under.paste(source,(0,0),sunmask)
blendframes=[]
for i in range(16):
 v=i/15
 frame=under.copy()
 # shift as in the approved LAB10 eclipse, but capped to keep picture readable on MPC touch area
 shift=int(round((v-.5)*490))
 xx=281+shift-bx;yy=184-by
 frame.alpha_composite(planet,(xx,yy))
 blendframes.append(frame)
blendstrip=Image.new('RGBA',(bw,bh*16));
for i,im in enumerate(blendframes):blendstrip.alpha_composite(im,(0,i*bh))
blendstrip.save(D/'lab10_blend_eclipse_live_16.png',optimize=True)
visual.append(make_visual('LIVE_BLENDECLIPSE_LAB10','Image',film('lab10_blend_eclipse_live_16.png',16,20),(bx,by,bw,bh),page(2)))
# ADSR: remove baked fixed curve only from original LAB10 window; SDK 4-handle native ADSR remains editable.
x,y,w,h=50,271,591,185
panel=Image.open(src/'lab10_mpc_03.png').convert('RGB').crop((x,y,x+w,y+h))
a=np.array(panel)
# Remove warm line/node strokes only, protecting border and caption bars.
hsv=cv2.cvtColor(a,cv2.COLOR_RGB2HSV);mask=cv2.inRange(hsv,np.array([5,35,103]),np.array([40,200,255]));mask[:9]=0;mask[-20:]=0;mask[:,:12]=0;mask[:,-12:]=0
mask=cv2.dilate(mask,np.ones((3,3),np.uint8),iterations=1)
flat=cv2.inpaint(a,mask,7,cv2.INPAINT_TELEA)
Image.fromarray(flat).save(D/'lab10_adsr_clean_panel.png',optimize=True)
visual.append(make_visual('LIVE_ADSR_CLEAN_PANEL','Image',normal('lab10_adsr_clean_panel.png'),(x,y,w,h),page(3)))
# Original validated 4-stage envelope schema, using actual ARM host parameters, no static curve.
with zipfile.ZipFile(R/'REminiSCENT_UI29_11PANTALLAS_PARAMETROS_SDK_CORREGIDOS.zip') as z:
 old=json.loads(z.read('Yeti Fingers - VST - REminiSCENT/Plugin Skins/TUI.json'))
old_vis=old['pageData']['tabs'][0]['componentDefinition']['componentsData']
adsr=copy.deepcopy(next(v for v in old_vis if v['componentData']['name']=='LIVE_ADSR_NATIVE_LAB10'))
adsr['bounds']['bounds']='64 276 565 149'; adsr['bounds']['additionalInvalidatingHandles']=page(3)
adsr['componentData']['name']='LIVE_ADSR_4_PARAMS_UI31';visual.append(adsr)
# MEMORY: preserve LAB10 panel, erase old fake wave, layer REAL MEMORY DSP waveform and playhead signal.
x,y,w,h=84,455,712,69
base_m=np.array(Image.open(src/'lab10_mpc_04.png').convert('RGB').crop((x,y,x+w,y+h)))
hsv=cv2.cvtColor(base_m,cv2.COLOR_RGB2HSV)
# clear traces in memory waveform area but preserve panel grid/crosshair.
mask=cv2.inRange(hsv,np.array([4,23,65]),np.array([44,180,255]));mask[:2]=0;mask[-4:]=0;mask=cv2.dilate(mask,np.ones((2,2),np.uint8),iterations=1)
cleared=cv2.inpaint(base_m,mask,4,cv2.INPAINT_TELEA)
Image.fromarray(cleared).save(D/'lab10_memory_clean_panel.png',optimize=True)
visual.append(make_visual('LIVE_MEMORY_CLEAN_PANEL','Image',normal('lab10_memory_clean_panel.png'),(x,y,w,h),page(4)))
memplot=copy.deepcopy(next(v for v in old_vis if v['componentData']['name']=='LIVE_MEMORY_WET_AUDIO_WAVE'))
memplot['componentData']['name']='LIVE_MEMORY_PCM_TRACE_UI31';memplot['componentData']['data']['backgroundColour']='00000000'; memplot['componentData']['data']['dataHandle']='Parameter 120'
memplot['componentData']['data']['historyTime']=2; memplot['bounds']['bounds']=f'{x} {y+6} {w} 54'; memplot['bounds']['additionalInvalidatingHandles']=page(4)
visual.append(memplot)
# Real live playhead 32-frame strip with the original LAB10 gold cursor, over actual PCM waveform.
play=Image.new('RGBA',(w,h*32),(0,0,0,0))
for i in range(32):
 frame=Image.new('RGBA',(w,h)); dr=ImageDraw.Draw(frame);xx=10+round((w-20)*i/31)
 dr.line((xx,2,xx,h-3),fill=(247,211,161,220),width=2);dr.polygon([(xx-4,3),(xx+4,3),(xx,8)],fill=(247,211,161,255))
 play.alpha_composite(frame,(0,i*h))
play.save(D/'lab10_memory_playhead_32.png',optimize=True)
visual.append(make_visual('LIVE_MEMORY_READHEAD_UI31','Image',film('lab10_memory_playhead_32.png',32,121),(x,y,w,h),page(4)))
# MOD LFO1/LFO2: original LAB29 plots of live motor signals, behind static LAB10 controls.
for n,where,source in [('LFO1',0,118),('LFO2',1,119)]:
 t=copy.deepcopy(next(v for v in old_vis if v['componentData']['name']==f'LIVE_LFO_{1+where}_AUDIO_TRACE'))
 t['componentData']['name']='LIVE_MOD_'+n+'_PCM_UI31';t['componentData']['data']['dataHandle']=f'Parameter {source}'
 t['componentData']['data']['backgroundColour']='00000000';t['bounds']['bounds']='94 543 516 77'
 t['bounds']['additionalInvalidatingHandles']=sub(9,111,where,3)
 visual.append(t)
# MOD ENV2 has its OWN REAL DSP envelope fields 96..99 = host parameters 88..91.
# Restore an independent four-stage moving envelope, gated to the approved third MOD card.
x,y,w,h=94,511,534,112
base_env2=np.array(Image.open(src/'lab10_mpc_09_2.png').convert('RGB').crop((x,y,x+w,y+h)))
hsv=cv2.cvtColor(base_env2,cv2.COLOR_RGB2HSV)
mask=cv2.inRange(hsv,np.array([5,35,105]),np.array([40,200,255]));mask[:3]=0;mask[-7:]=0;mask[:,:10]=0;mask[:,-8:]=0
mask=cv2.dilate(mask,np.ones((3,3),np.uint8),iterations=1)
clean=cv2.inpaint(base_env2,mask,5,cv2.INPAINT_TELEA)
Image.fromarray(clean).save(D/'lab10_mod_env2_clean_panel.png',optimize=True)
visual.append(make_visual('LIVE_MOD_ENV2_CLEAN_PANEL','Image',normal('lab10_mod_env2_clean_panel.png'),(x,y,w,h),sub(9,111,2,3)))
env2=copy.deepcopy(adsr);env2['componentData']['name']='LIVE_MOD_ENV2_ADSR_4_PARAMS_UI31'
for field,host in [('attack',88),('decay',89),('sustain',90),('release',91)]:env2['componentData']['data'][field+'Handle']=f'Parameter {host}'
env2['bounds']['bounds']='101 515 520 101';env2['bounds']['additionalInvalidatingHandles']=sub(9,111,2,3)
visual.append(env2)
# Solaris v09, the approved 240x240 art. 6 segments x25 frames, gated by engine startup parameter 122;
# UI draws nothing after param 122=6. No opaque fallback / no whole-screen obstruction.
with zipfile.ZipFile(R/'REminiSCENT_LAB24_58_PNG_WHITE_PINK_PRIVADO.zip') as z:
 for i in range(6):
  filename=f'solaris_v09_{i:02}.png'; raw=z.read('skins/'+filename)
  im=Image.open(io.BytesIO(raw));assert im.size==(240,6000),(filename,im.size)
  (D/filename).write_bytes(raw)
  visual.append(make_visual('SOLARIS_V09_SEGMENT_'+str(i),'Image',film(filename,25,123),(482,195,316,316),[f'IndexedEnabling/{i}/7/Parameter 122']))
if not any(x['key']=='Parameter 122' for x in tui['pageData']['replacementStrings']):
 tui['pageData']['replacementStrings'].append({'key':'Parameter 122','value':['0','1','2','3','4','5','DONE']})
# Retain 19 approved screenshot rasters as first components. Visuals draw above the original image,
# while the 87 touch controls stay on top to receive focus and Q-Link movement.
cs[19:19]=visual
assert cs[0]['componentData']['name'].startswith('APPROVED_LAB10_')
assert len([x for x in cs if x['componentData']['name'].startswith('APPROVED_LAB10_')])==19
assert len([x for x in cs if x['componentData']['name'].startswith('Q_LINK_')])==4
assert len(cs)==106+len(visual)
(D/'TUI.json').write_text(json.dumps(tui,indent=2,ensure_ascii=False)+'\n')
assets={p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'size':Image.open(p).size} for p in D.glob('*.png')}
report={'parent':'UI30 PR32 source; binary LAB29 254 WAV, DSP unchanged','status':'UI source + skin, static validation; MPC physical not verified','modules':11,'approved_backgrounds_sha256':{name:assets[name]['sha256'] for _,name in old_imgs},'added_visuals':len(visual),'components_total':len(cs),'assets':assets,'wav':254,'limitations':['Native Envelope/Plotter renderer must be tested on actual MPC','Solaris auto-hide depends on audio engine host 122 advancing to 6','MOD ENV2 4 real host ADSR handles 88..91 structurally bound; actual MPC render untested']}
(R/'UI31_LIVE'/'REPORT.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('assets','approved_backgrounds_sha256')}))