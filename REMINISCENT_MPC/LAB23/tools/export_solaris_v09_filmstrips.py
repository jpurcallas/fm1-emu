#!/usr/bin/env python3
"""Produce exact Solaris v09 approved frames for MPC SDK FilmStrip.

Usage: python export_solaris_v09_filmstrips.py <approved-v09-240x240.mp4> <skins>
The approved reference is in GitHub PR #30 and the author's private Library.
Requires Pillow and ffmpeg. Do not replace/re-draw the v09 artwork.
6 x 25 frames are used instead of an unsupported 36000-pixel-high texture.
Do not commit the generated PNGs to the public repo; they belong to the private skin.
"""
from pathlib import Path
from PIL import Image, ImageDraw
from tempfile import TemporaryDirectory
import subprocess
import sys

def export(movie, skins):
    movie=Path(movie); skins=Path(skins)
    skins.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory() as tmpdir:
        folder=Path(tmpdir)
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
            '-i',str(movie),'-vsync','0',str(folder/'frame_%03d.png')],check=True)
        frames=sorted(folder.glob('frame_*.png'))
        if len(frames)!=150: raise ValueError('Solaris v09 requires exactly 150 frames')
        for group in range(6):
            strip=Image.new('RGB',(240,6000))
            for f in range(25):
                frame=Image.open(frames[group*25+f]).convert('RGB')
                if frame.size!=(240,240):raise ValueError('Approved source is 240x240')
                strip.paste(frame,(0,240*f))
            strip.save(skins/f'solaris_v09_{group:02d}.png',compress_level=8)
        bg=Image.open(frames[0]).convert('RGB').getpixel((0,0))
        Image.new('RGB',(1280,628),bg).save(skins/'solaris_v09_plate.png',compress_level=9)
    # The actual MEMORY playback position is fed by read-only SDK parameter 121.
    w,h=750,88
    strip=Image.new('RGBA',(w,h*32))
    for k in range(32):
        frame=Image.new('RGBA',(w,h))
        paint=ImageDraw.Draw(frame,'RGBA')
        x=round(12+k*(w-26)/31)
        paint.line([(x,4),(x,h-6)],fill=(250,215,164,240),width=2)
        paint.polygon([(x-5,4),(x+5,4),(x,14)],fill=(250,215,164,250))
        strip.paste(frame,(0,k*h))
    strip.save(skins/'memory_playhead_live_32.png',compress_level=9)

if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit(__doc__)
    export(sys.argv[1],sys.argv[2])
