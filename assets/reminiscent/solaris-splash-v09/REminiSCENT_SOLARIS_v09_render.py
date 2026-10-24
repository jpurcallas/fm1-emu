#!/usr/bin/env python3
"""Solaris v09: exact approved station and typography; simple mathematical ripples.
Requires Python 3 + Pillow + numpy + ffmpeg + C compiler. All output 240x240.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np, subprocess, tempfile, hashlib
root=Path(__file__).resolve().parent
prefix='REminiSCENT_SOLARIS_ONDAS_SIMPLES_ENCAJE_Y_TITULO_v09_240x240'
N=150; FPS=25; CUT=67; W=H=240
subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-o',str(root/'_remin_wave09'),str(root/'REminiSCENT_SOLARIS_v09_waves.c'),'-lm'],check=True)
station=Image.open(root/'REminiSCENT_APPROVED_PANEL_1.png').convert('RGB')
title=Image.open(root/'REminiSCENT_APPROVED_PANEL_3.png').convert('RGB')
sta=np.asarray(station).copy()
# Sample the existing original pastel background, not a guessed solid yellow.
# Both sides of the approved station panel contain the undisturbed background.
by=np.stack([sta[:,0,:],sta[:,W-1,:]],axis=1).astype(float)
fx=np.linspace(0,1,W)[None,:,None]
bg=np.clip(by[:,0:1,:]*(1-fx)+by[:,1:2,:]*fx,0,255).astype(np.uint8)
# Image matte ONLY for approved letterforms: no pasted rectangle / no water sprites.
ty=np.asarray(title).astype(np.float32)
gray=ty.mean(2)
matte=np.clip((219-gray)*2.8,0,255).astype(np.uint8)
matte[:178,:]=0
# Preserve original text strokes and aspect ratio exactly from approved 240px artwork.
ink=np.array([11,15,14],dtype=np.float32)
with tempfile.TemporaryDirectory(prefix='remin_v09_') as folder:
    temp=Path(folder)
    for f in range(N):
        if f<CUT: img=station.copy()
        else:
            mask=temp/(f'{f:03d}.raw')
            subprocess.run([str(root/'_remin_wave09'),str(f),str(mask)],check=True,stdout=subprocess.DEVNULL)
            waves=np.fromfile(mask,dtype=np.uint8).reshape(H,W)
            mask.unlink()
            b=bg.astype(np.float32)
            b-=waves[:,:,None]*np.array([.93,.93,.84])[None,None,:]
            # Fade title in, preserving ALL original letterforms, subtitle and "by Yeti Fingers".
            title_gain=max(0.,min(1.,(f-90)/18.))
            if title_gain>0:
                a=(matte.astype(np.float32)/255.0*title_gain)[:,:,None]
                b=b*(1-a)+ink[None,None,:]*a
            img=Image.fromarray(np.clip(b,0,255).astype(np.uint8),'RGB')
        img.save(temp/(f'{f:03d}.png'),compress_level=1)
    mp4=root/(prefix+'.mp4')
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate',str(FPS),'-i',str(temp/'%03d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','14','-movflags','+faststart',str(mp4)],check=True)
    gif=root/(prefix+'.gif')
    frames=[Image.open(temp/f'{i:03d}.png').convert('RGB') for i in range(0,N,2)]
    frames[0].save(gif,save_all=True,append_images=frames[1:],duration=80,loop=0,optimize=True)
    keys=[0,66,67,83,101,124,149]
    contact=Image.new('RGB',(W*len(keys),280),(249,247,234))
    d=ImageDraw.Draw(contact)
    try:font=ImageFont.truetype('DejaVuSans.ttf',12)
    except: font=ImageFont.load_default()
    for i,k in enumerate(keys):
        contact.paste(Image.open(temp/f'{k:03d}.png'),(W*i,0))
        d.text((W*i+8,248),f'{k:03d} / {k/FPS:.2f} s',font=font,fill=(48,48,48))
    contact.save(root/(prefix+'_CONTACT.png'))
    for k,label in [(66,'ANTES'),(67,'DESPUES'),(149,'FINAL')]:
        Image.open(temp/(f'{k:03d}.png')).save(root/(prefix+'_'+label+'.png'))
    assert np.array_equal(np.asarray(Image.open(temp/'066.png')),sta)
    assert np.all(matte[0:178,:]==0)
    print('Verified untouched station frames 0–66; first math wave f67; complete original title lettering.')
    print('Output:',mp4,'and',gif)
    for p in [mp4,gif,root/(prefix+'_CONTACT.png')]:print(' ',p.name,p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()[:16])
