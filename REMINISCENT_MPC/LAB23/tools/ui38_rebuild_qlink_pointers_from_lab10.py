#!/usr/bin/env python3
"""Regenerate Q-Link animation using ORIGINAL LAB10 knob pixels, neutralizing each baked-in needle.
Precisely scoped to knob inner disks. No changes to LAB10 backgrounds or DSP.
"""
import argparse, io, json, zipfile, math
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw

def make_pointers(bg:Image.Image):
    out={}
    for k,cy in enumerate((223,322,422,522)):
        cx=1050
        rgb=np.array(bg.crop((cx-25,cy-25,cx+25,cy+25)).convert('RGB'))
        h,w=rgb.shape[:2]
        yy,xx=np.indices((h,w)); radius=np.hypot(xx-25,yy-25)
        # Needle differs for every Q-Link in the approved background: mask its *actual* orientation.
        # Restrict colour removal to inner disk (the outside 18.5px ring stays source-authentic).
        luma=rgb.astype(np.float32).mean(axis=2)
        mask=((luma>97)&(radius<22.0)).astype(np.uint8)*255
        mask=cv2.dilate(mask,np.ones((5,5),np.uint8),iterations=2)
        mask=np.where(radius<23.0,mask,0).astype('uint8')
        clean=cv2.inpaint(rgb,mask,5,cv2.INPAINT_TELEA)
        # Interior of the approved knob is a smooth dark radial gradient. Rebuild
        # *only* this interior from robust source pixels, excluding all baked
        # needle orientations; the decorative ring and panel remain untouched.
        core=clean.astype(np.float32)
        inner=(radius<22.0)
        # Use original LAB10's surrounding neutral dark pixels to model a very
        # subtle spherical gradient. Avoid the sampled needle completely.
        for rr in range(23):
            sel=(radius>=rr)&(radius<rr+1)&(luma<95)
            if np.any(sel):
                vals=np.median(rgb[sel].astype(np.float32),axis=0)
            else:
                vals=np.array([19.,35.,38.],dtype=np.float32)
            core[(radius>=rr)&(radius<rr+1)&inner]=vals
        # Smooth only the dark interior. Original gold ring / bezel pixels are
        # preserved verbatim, with a two-pixel soft transition at the seam.
        smooth=cv2.GaussianBlur(core,(7,7),1.1)
        weight=np.clip((23.2-radius)/2.0,0,1).astype(np.float32)[:,:,None]
        clean=np.uint8(np.clip(rgb.astype(np.float32)*(1-weight)+smooth*weight,0,255))
        originals=Image.fromarray(clean,'RGB').convert('RGBA')
        alpha=Image.new('L',(200,200),0);d=ImageDraw.Draw(alpha)
        d.ellipse((12,12,188,188),fill=255)
        originals.putalpha(alpha.resize((50,50),Image.Resampling.LANCZOS))
        strip=Image.new('RGBA',(50,5050))
        for i in range(101):
            canvas=originals.copy()
            needle=Image.new('RGBA',(200,200),(0,0,0,0)); dr=ImageDraw.Draw(needle)
            angle=math.radians(-135.+270.*i/100)
            x0=100+16*math.sin(angle);y0=100-16*math.cos(angle)
            x1=100+63*math.sin(angle);y1=100-63*math.cos(angle)
            dr.line((x0,y0,x1,y1),fill=(245,208,158,255),width=14)
            needle=needle.resize((50,50),Image.Resampling.LANCZOS)
            canvas.alpha_composite(needle)
            strip.paste(canvas,(0,50*i))
        out[f'lab10_qlink_{k+1}_pointer_101.png']=strip
    return out

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('base_zip');parser.add_argument('output_folder');args=parser.parse_args()
    with zipfile.ZipFile(args.base_zip) as z:
        root='Yeti Fingers - VST - REminiSCENT/Plugin Skins/'
        bg=Image.open(io.BytesIO(z.read(root+'lab10_mpc_00.png')))
    dest=Path(args.output_folder);dest.mkdir(parents=True,exist_ok=True)
    for name,sheet in make_pointers(bg).items():sheet.save(dest/name,optimize=True)
    print('Generated',len(list(dest.glob('lab10_qlink_*_pointer_101.png'))),'approved-LAB10-derived 101 frame strips')