#!/usr/bin/env python3
"""Use only LAB10 original knob pixels: erase baked needle and rotate exact sourced needle."""
import zipfile,json,io,math,hashlib
from PIL import Image,ImageFilter,ImageDraw
import numpy as np,cv2
from pathlib import Path
SOURCE=Path('/mnt/data/reminiscent_work/REminiSCENT_UI33_NATIVE_LIVE_CANDIDATE.zip')
DEST=Path('/mnt/data/reminiscent_work/REminiSCENT_UI33_APPROVED_POINTER_CANDIDATE.zip')
root='Yeti Fingers - VST - REminiSCENT/Plugin Skins/'
with zipfile.ZipFile(SOURCE) as z:
 b=Image.open(io.BytesIO(z.read(root+'lab10_mpc_00.png'))).convert('RGBA')
 new={}
 for k,cy in enumerate((223,322,422,522)):
  cx=1050
  # Use each original knob exactly (their default lines differ).
  arr=np.array(b.crop((cx-25,cy-25,cx+25,cy+25)).convert('RGB'))
  # Work on center needle, leaving original ring and metallic texture intact.
  mask=np.zeros((50,50),dtype=np.uint8)
  # mask needle in inner disk; avoid any ring pixels
  cv2.line(mask,(25,24),(25,8),255,5)
  # Use Telea on the baked pointer region, preserving approved dark gradient.
  clean=cv2.inpaint(arr,mask,5,cv2.INPAINT_TELEA)
  originals=Image.fromarray(clean,'RGB').convert('RGBA')
  # Transparent anti-aliased mask only over circular inner disk.
  a=Image.new('L',(200,200),0);dr=ImageDraw.Draw(a)
  dr.ellipse((20,20,180,180),fill=255)
  a=a.resize((50,50),Image.Resampling.LANCZOS)
  originals.putalpha(a)
  strip=Image.new('RGBA',(50,5050))
  for i in range(101):
   frame=originals.copy()
   needle=Image.new('RGBA',(200,200),(0,0,0,0))
   d=ImageDraw.Draw(needle)
   # Source needle tint sampled from approved LAB10 raster; top vertical at 50%.
   source_col=tuple(arr[12,25]);
   # LAB10 original pointer length and line thickness, oversampling for fidelity.
   ang=math.radians(-135+270*i/100)
   x0=100+20*math.sin(ang);y0=100-20*math.cos(ang)
   x1=100+55*math.sin(ang);y1=100-55*math.cos(ang)
   d.line((x0,y0,x1,y1),fill=(*source_col,255),width=12)
   needle=needle.resize((50,50),Image.Resampling.LANCZOS)
   frame.alpha_composite(needle)
   strip.paste(frame,(0,50*i))
  n=f'lab10_qlink_{k+1}_pointer_101.png';bio=io.BytesIO();strip.save(bio,format='PNG',optimize=True);new[n]=bio.getvalue()
 with zipfile.ZipFile(DEST,'w',allowZip64=True) as out:
  for item in z.infolist():
   if item.filename.startswith(root) and item.filename[len(root):] in new:
    dat=new[item.filename[len(root):]]
   else:dat=z.read(item.filename)
   out.writestr(item,dat)
 print('Knobs from LAB10 originals; kept all source ZIP files except four regenerated pointers')
 print('new sizes:',[(x,len(y)) for x,y in new.items()])
 print('sha256:',hashlib.sha256(DEST.read_bytes()).hexdigest())