#!/usr/bin/env python3
"""UI33: native MPC controls + source text patches. No DSP or sound rewrite."""
import copy,hashlib,io,json,zipfile,pathlib,collections
from PIL import Image,ImageDraw
BASE=pathlib.Path('/mnt/data/reminiscent_work/REminiSCENT_UI32_SIN_ARTE_ANTIGUO.zip')
DEST=pathlib.Path('/mnt/data/reminiscent_work/REminiSCENT_UI33_NATIVE_CONTROLS_CANDIDATE.zip')
ROOT='Yeti Fingers - VST - REminiSCENT/Plugin Skins/'
with zipfile.ZipFile(BASE) as z:
    tui=json.loads(z.read(ROOT+'TUI.json'))
    bg=Image.open(io.BytesIO(z.read(ROOT+'lab10_mpc_00.png'))).convert('RGBA')
    c=tui['pageData']['tabs'][0]['componentDefinition']['componentsData']
    orig_images={x:z.read(x) for x in z.namelist() if x.startswith(ROOT) and x.endswith('.png')}
allowed={'Image','Button','Knob','Slider','Label','Envelope','Plotter'}
new={}
# A one-pixel-transparent hit area extended to 101 frames; real SDK widgets, invisible visual override.
transparent=Image.new('RGBA',(4,404),(0,0,0,0)); buf=io.BytesIO();transparent.save(buf,format='PNG');new['lab10_native_touch_101.png']=buf.getvalue()
# Use SDK's original native, touch-responsive control definitions (no invented types).
replaced=[]
for comp in c:
    data=comp['componentData']; typ=data['type']; n=data['name']
    if not typ.startswith('UI32_'):continue
    if typ.startswith('UI32_TOGGLE_'):
        data['type']='Button'; data['data']={'version':2,'onImage':'lab10_touch_hit.png','offImage':'lab10_touch_hit.png','buttonId':1,'numButtonsInGroup':1,'handleName':'Data','gestureBehaviour':'Instant'}
    else:
        data['type']='Knob'; data['data']={'version':3,'knobType':'FilmStrip','filmStrip':'lab10_native_touch_101.png','numFrames':101,'invert':False,'dragOrientation':'Horizontal' if ('BLEND_TOUCH' in n or 'MEMORY_WINDOW' in n or 'POSITION_VISUAL' in n) else 'Vertical','handleName':'Data'}
    replaced.append(n)
assert len(replaced)==55
# Paint over ONLY pre-rasterized voice names, not frames or entire historical image.
# This overlay carries the original lab10 native greenish panel fill inferred from clean right-hand pixels.
# Same screen coordinates/typography are retained; Voice values are a host-bound native Label.
def voice_patch(y):
    # Original voice fields 144 246 434 40 and 144 314 434 40.
    width,height=404,28
    patch=Image.new('RGBA',(width,height),(0,0,0,0))
    # The untouched inner field's rightmost 15 px has no text; tile its colour/texture through the old lettering.
    # Limit to the text interior; don't paint borders or alter layout artwork.
    source=bg.crop((550,y+5,565,y+5+height))
    for x in range(0,width,15):patch.alpha_composite(source.crop((0,0,min(15,width-x),height)),(x,0))
    out=io.BytesIO();patch.save(out,format='PNG');return out.getvalue()
new['lab10_voice_a_text_clean.png']=voice_patch(246)
new['lab10_voice_b_text_clean.png']=voice_patch(314)

def comp(name,typ,dat,bounds,handle=None,visible=[]):
  x={'version':2,'componentData':{'version':1,'name':name,'type':typ,'data':dat},'handle remapping':{'version':1,'map':([{'key':'Data','value':'Parameter '+str(handle)}] if handle is not None else [])},'bounds':{'version':2,'acceptsHWFocus':'Yes' if typ=='Knob' else 'No','showWhenDataModelInvalid':'Hide','whenVisible':'Always','boundsType':'Absolute','bounds':bounds,'additionalInvalidatingHandles':visible}}
  return x
for index,y in ((0,246),(1,314)):
    # Insert above static BG, below native label and source selector hit target, to avoid swallowing touches.
    zone=['IndexedEnabling/0/11/Parameter 112']
    c.append(comp(f'VOICE_{index}_OLD_TEXT_COVER','Image',{'version':2,'imageType':'Regular','colour':'0','image':('lab10_voice_a_text_clean.png' if index==0 else 'lab10_voice_b_text_clean.png')},f'153 {y+5} 404 28',visible=zone))
    c.append(comp(f'VOICE_{index}_LIVE_HOST_VALUE','Label',{'version':1,'textStyle':{'version':1,'font':{'version':1,'name':'Nexa','style':'Bold','height':13.0},'colour':'fff1dbc1','justification':'verticallyCentred','case':'Original'},'type':'Value','handleName':'Data'},f'159 {y+5} 396 28',handle=index,visible=zone))
# Dynamic Q-Link knobs. APPROVED LAB10 chrome is source; only moving pointer + dark inner disk placed above its baked one.
# The bezel on LAB10 remains untouched, and no earlier artwork enters the archive.
for k,cy in enumerate((223,322,422,522)):
  cx=1050
  frames=[]
  for i in range(101):
    tile=Image.new('RGBA',(50,50),(0,0,0,0));d=ImageDraw.Draw(tile)
    # Inner disk mimics LAB10 centre, leaves original bezel/rim unaffected.
    d.ellipse((6,6,44,44),fill=(11,31,35,255))
    import math
    a=math.radians(-135+270*i/100)
    x1=25+9*math.cos(a);y1=25+9*math.sin(a)
    x2=25+19*math.cos(a);y2=25+19*math.sin(a)
    d.line((x1,y1,x2,y2),fill=(245,196,139,255),width=3)
    frames.append(tile)
  strip=Image.new('RGBA',(50,5050));
  for i,f in enumerate(frames):strip.paste(f,(0,50*i))
  f='lab10_qlink_%d_pointer_101.png'%(k+1);b=io.BytesIO();strip.save(b,format='PNG',optimize=True);new[f]=b.getvalue()
  c.append(comp(f'QLINK_{k+1}_LAB10_LIVE_POINTER','Image',{'version':2,'imageType':'FilmStrip','colour':'0','image':f,'numFrames':101,'handleName':f'Parameter {113+k}'},f'{cx-25} {cy-25} 50 50',visible=[]))
assert all(x['componentData']['type'] in allowed for x in c)
# Preserve original ZIP members bytewise except exact TUI, add only UI-derived assets.
outdata=json.dumps(tui,ensure_ascii=False,indent=2).encode()
with zipfile.ZipFile(BASE) as src,zipfile.ZipFile(DEST,'w',allowZip64=True) as out:
 for info in src.infolist():
    b=outdata if info.filename==ROOT+'TUI.json' else src.read(info.filename)
    out.writestr(info,b)
 for name,b in new.items():out.writestr(ROOT+name,b,compress_type=zipfile.ZIP_DEFLATED)
with zipfile.ZipFile(DEST) as z:
 assert z.testzip() is None
 assert len([x for x in z.namelist() if x.endswith('.wav')])==254
 assert len([x for x in z.namelist() if x.endswith('.so')])==2
 print('ZIP',DEST,'bytes',DEST.stat().st_size,'sha256',hashlib.sha256(DEST.read_bytes()).hexdigest())
 print('components',len(c),'replaced',len(replaced),'new assets',list(new))