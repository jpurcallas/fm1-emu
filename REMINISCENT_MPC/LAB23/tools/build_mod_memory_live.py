#!/usr/bin/env python3
"""Rebuild LAB23 MOD and MEMORY graphics from the approved 3-module skin.
Requires Pillow. Source backgrounds 04.png and 09.png are kept unchanged.
Generated filmstrips reflect MIDI/parameter states; MEMORY is a *simulated*
display, not a PCM-bus oscilloscope. MOD WHEEL is explicitly excluded.
Usage: python build_mod_memory_live.py <LAB23/skins>
"""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib, math, random, sys

def generate(root):
    root=Path(root)
    original=Image.open(root/"fondos/09.png").convert("RGBA")
    w,h=607,86
    crop=original.crop((55,395,55+w,395+h))
    def blank():
        im=crop.copy()
        draw=ImageDraw.Draw(im)
        for y in range(9,75):
            diff=2*math.sin(y*.08)
            c=(max(0,6+int(diff)),max(0,26+int(diff)),max(0,29+int(diff)),255)
            draw.line([(6,y),(w-7,y)],fill=c)
        return im
    frames=[]
    for kind in range(5):
        im=blank()
        draw=ImageDraw.Draw(im)
        draw.line([(49,43),(w-48,43)],fill=(110,154,151,110),width=1)
        if kind==4:
            rng=random.Random(0x315634b1)
            levels=[rng.uniform(-.8,.8) for _ in range(10)]
        def value(t):
            if kind==0: return math.sin(2*math.pi*t)
            if kind==1: return 1-4*abs(t-.5)
            if kind==2: return 2*t-1
            if kind==3: return 1 if t<.5 else -1
            return levels[min(int(t*10),9)]
        pts=[(48+round(k*(w-96)/560),43-round(27*value((k/560)%1))) for k in range(561)]
        draw.line(pts,fill=(233,201,159,255),width=3,joint="curve")
        frames.append(im)
    out=Image.new("RGBA",(w,h*5))
    for i,im in enumerate(frames): out.paste(im,(0,i*h))
    out.save(root/"mod_lfo_shape_engine_5.png",optimize=True)
    blank().save(root/"mod_env2_graph_blank.png",optimize=True)

    original=Image.open(root/"fondos/04.png").convert("RGBA")
    w,h=750,88
    base=original.crop((67,446,67+w,446+h))
    signal=[]
    for x in range(w):
        t=x/4.3
        env=.43+.2*math.sin(t*.053+1.4)+.14*math.sin(t*.17+.3)
        v=(math.sin(t*1.02)*.27+math.sin(t*1.85+.4)*.22+
           math.sin(t*3.01+1.2)*.11)*env
        signal.append(v)
    strips=[]
    for frame in range(32):
        im=base.copy()
        draw=ImageDraw.Draw(im,"RGBA")
        draw.rectangle([2,4,w-5,h-12],fill=(3,25,28,255))
        for x in range(20,w-10,36):
            draw.line([(x,5),(x,h-13)],fill=(98,126,119,38),width=1)
        draw.line([(4,39),(w-6,39)],fill=(89,137,139,70),width=1)
        for x in range(8,w-9):
            a=abs(signal[x])*39+1
            draw.line([(x,39-a),(x,39+a)],fill=(98,155,154,68),width=1)
        left=135+int((frame/31)*(w-140-210))
        right=left+210
        draw.rectangle([left,7,right,h-14],fill=(194,157,95,26),
                       outline=(232,184,121,180),width=1)
        for x in range(left+1,right):
            a=abs(signal[x])*39+1
            draw.line([(x,39-a),(x,39+a)],fill=(240,200,144,185),width=1)
        for edge in (left,right):
            draw.line([(edge,7),(edge,h-13)],fill=(245,210,160,255),width=2)
        play=left+round((right-left)*.32)
        draw.line([(play,8),(play,h-13)],fill=(244,214,156,240),width=2)
        strips.append(im)
    out=Image.new("RGBA",(w,h*32))
    for i,im in enumerate(strips):out.paste(im,(0,i*h))
    out.save(root/"memory_position_32.png",optimize=True)
    for name in ("mod_lfo_shape_engine_5.png","mod_env2_graph_blank.png","memory_position_32.png"):
        p=root/name
        print(name,p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit(__doc__)
    generate(sys.argv[1])
