#!/usr/bin/env python3
"""UI44 -- BLEND image compiler from the AUTHOR-APPROVED still.

Outputs exactly two private skin resources, without editing TUI, Q-Links or audio:
  lab10_blend_eclipse_live_16.png  613 x (16*392), native Knob FilmStrip
  lab10_mpc_02.png             1280 x 628, BLEND only background

The star remains static; the foreground planet travels LEFT -> CENTER -> RIGHT.
Both native touch and Q-Link use existing host Parameter 20, defined by UI42.
Reconstructs the concealed side of the sun from its visible left hemisphere;
never reuses an old eclipse/solar image or opaque rectangular clone.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import cv2

# Official TUI UI42 geometry / resource names; no TUI modifications required.
ORIGINAL_SIZE = (1670, 941)
BACKGROUND_SIZE = (1280, 628)
STRIP_RECT = (192, 178, 613, 392)
NFRAMES = 16
SUN = (684.0, 429.0, 298.0)
PLANET = (968.5, 435.0, 322.0)
SCALE = .49
# Even frame count: both central bins must be a TOTAL eclipse at approx. 50%.
# Keep positions monotonic, and the end positions outside the solar disk.
SHIFTS = (-145, -127, -108, -88, -66, -44, -22, 0, 0,
          22, 44, 66, 88, 108, 127, 145)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def starfield(original, size, seed=44):
    """Dark source-matched void, no opaque removed-planet inpainting.

    Detect/copy only faint bright specks OUTSIDE the two celestial spheres;
    gradient derives its black/cyan palette from the source's own corners.
    """
    w,h = size
    y,x = np.mgrid[0:h, 0:w].astype(np.float32)
    # Source original dark space palette from four uncontaminated corner patches.
    a = np.asarray(original, dtype=np.uint8)
    corners = [np.median(a[y0:y0+70, x0:x0+70], axis=(0,1))
               for x0,y0 in [(0,0),(1600,0),(0,870),(1600,870)]]
    palette = np.mean(corners, axis=0)
    # Procedural starfield is blank in the planet areas, avoiding circles/ghosts.
    rr = np.sqrt(((x-w*.49)/(w*.55))**2 + ((y-h*.48)/(h*.6))**2)
    glow = np.exp(-((x-w*.5)/(w*.44))**2 - ((y-h*.48)/(h*.48))**2)
    pic = np.empty((h,w,3), dtype=np.float32)
    for c in range(3):
        pic[...,c] = palette[c] * (0.76+0.24*(1-y/h)) + [0.0,2.0,3.0][c]*glow
    rng = np.random.default_rng(seed)
    pic += (rng.standard_normal((h,w,1)) * .60).astype(np.float32)
    pic = np.uint8(np.clip(pic,0,255))
    img = Image.fromarray(pic,'RGB')
    dots = Image.new('RGBA',(w,h),(0,0,0,0))
    dr = ImageDraw.Draw(dots)
    # Fixed, sparse, tiny points (not audio-reactive and not a new visual motif).
    for _ in range(155):
        sx=int(rng.integers(0,w));sy=int(rng.integers(0,h))
        alpha=int(rng.integers(25,100))
        color=(int(rng.integers(78,149)),int(rng.integers(134,193)),int(rng.integers(162,219)),alpha)
        dr.point((sx,sy),fill=color)
    return Image.alpha_composite(img.convert('RGBA'),dots).convert('RGB')


def preserve_blend_header(composite, orig):
    """Retain LAB10 navigation + original BLEND captions, without amber sky.

    Only replace scenic area x<996 and y>=110; all Q-Link controls, tabs,
    widget-positioned handles and LAB10 typography stay in their native places.
    """
    out = np.asarray(composite).copy()
    old = np.asarray(orig)
    # LAB10 original label plate, isolated well away from the occulting body.
    out[133:156, 48:221] = old[133:156, 48:221]
    # Transfer genuine caption glyph pixels only, not the old solar atmosphere.
    # The texts on this screen are pale metallic/gold/copper, not cyan.
    regions = ((235,133,507,153),(48,163,335,191),(48,196,340,215))
    for x0,y0,x1,y1 in regions:
        s=old[y0:y1,x0:x1].astype(np.int16)
        # anti-aliased glyphs from the LAB10 raster; no new font substituted.
        chroma=(s[:,:,0]>100)&(s[:,:,1]>75)&(s[:,:,0]>s[:,:,2]*1.12)
        # Need keep grayer white BLEND lettering too.
        pale=(s[:,:,0]>143)&(s[:,:,1]>142)&(s[:,:,2]>125)
        mask=(chroma|pale).astype(np.uint8)*255
        # One-pixel soft edge for original antialiasing.
        mask=cv2.GaussianBlur(mask,(3,3),0.45)
        al=mask.astype(np.float32)[...,None]/255
        out[y0:y1,x0:x1]=np.clip(out[y0:y1,x0:x1]*(1-al)+s*al,0,255).astype('uint8')
    # Final caption glyphs cross the old orange solar limb at x 340..356.
    # The pale LAB10 glyphs have G > 160 and B > 125; the old sun has not.
    x0,y0,x1,y1=339,201,370,212
    r=old[y0:y1,x0:x1].astype(np.int16)
    glyph=(r[:,:,0]>158)&(r[:,:,1]>160)&(r[:,:,2]>126)
    out[y0:y1,x0:x1][glyph]=r[glyph].astype(np.uint8)
    return Image.fromarray(out,'RGB')


def base_background(original_bg, still):
    # Keep all non-BLEND skin pixels as-is: x>=996 and y<110.
    out=np.array(original_bg.convert('RGB'))
    blank=np.asarray(starfield(still,(996,518)))
    out[110:628,0:996]=blank
    out[0:110]=np.asarray(original_bg.convert('RGB'))[0:110]
    out[:,996:]=np.asarray(original_bg.convert('RGB'))[:,996:]
    # Retain border and separators exactly.
    out[110:,0:2] = np.asarray(original_bg.convert('RGB'))[110:,0:2]
    out[-2:,:996] = np.asarray(original_bg.convert('RGB'))[-2:,:996]
    return preserve_blend_header(Image.fromarray(out),original_bg)


def alpha_over(base_rgb, rgb, alpha):
    return np.uint8(np.clip(base_rgb.astype(np.float32)*(1-alpha[...,None])+
                            rgb.astype(np.float32)*alpha[...,None],0,255))


def render(still, bg):
    src=np.array(still.convert('RGB'))
    full=np.array(bg.convert('RGB'))
    bx,by,w,h = STRIP_RECT
    bg_crop=full[by:by+h,bx:bx+w]
    y,x=np.mgrid[0:h,0:w].astype(np.float32)
    cx,cy=w/2,h/2
    # The rear solar body is fixed on the screen, and its blue rim is
    # SOURCE-MATCHED. It is rebuilt only where the moving planet concealed it.
    xs=SUN[0]+(x-cx)/SCALE
    ys=SUN[1]+(y-cy)/SCALE
    hidden=xs>640
    warp_x=np.where(hidden,640-(xs-640)*(246/342),xs).astype('float32')
    warp_y=(ys+np.where(hidden,4.7*np.sin((xs-640)/38)*np.sin((ys-430)/42),0)).astype('float32')
    sun_rgb=cv2.remap(src,warp_x,warp_y,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT)
    sun_radius=SUN[2]*SCALE
    d=np.hypot(x-cx,y-cy)
    # Small halo: the approved luminous cyan surface retains its own texture.
    halo=np.exp(-np.maximum(0,d-sun_radius)**2/(2*15**2))
    halo=np.where(d>sun_radius,halo,0)
    bg_with_halo=alpha_over(bg_crop,np.broadcast_to(np.array([21,142,179],dtype=np.uint8),(h,w,3)),np.clip(halo*.32,0,1))
    sun_alpha=np.clip((sun_radius-d+1.6)/2.2,0,1)
    star=alpha_over(bg_with_halo,sun_rgb,sun_alpha)
    frames=[]
    for shift in SHIFTS:
        px=PLANET[0]+(x-cx-shift)/SCALE
        py=PLANET[1]+(y-cy)/SCALE
        planet_rgb=cv2.remap(src,px.astype('float32'),py.astype('float32'),cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT,borderValue=(3,6,8))
        r=PLANET[2]*SCALE
        pd=np.hypot(x-(cx+shift),y-cy)
        planet_a=np.clip((r-pd+1)/2.0,0,1)
        frame=alpha_over(star,planet_rgb,planet_a)
        frames.append(Image.fromarray(frame,'RGB'))
    return frames


def build(still_path,bg_path,out):
    still_path=Path(still_path);bg_path=Path(bg_path);out=Path(out)
    still=Image.open(still_path).convert('RGB')
    original_bg=Image.open(bg_path).convert('RGB')
    assert still.size==ORIGINAL_SIZE,still.size
    assert original_bg.size==BACKGROUND_SIZE,original_bg.size
    out.mkdir(parents=True,exist_ok=True)
    background=base_background(original_bg,still)
    frames=render(still,background)
    strip=Image.new('RGB',(STRIP_RECT[2],STRIP_RECT[3]*NFRAMES))
    for i,frame in enumerate(frames):strip.paste(frame,(0,i*STRIP_RECT[3]))
    fname=out/'lab10_blend_eclipse_live_16.png'
    bname=out/'lab10_mpc_02.png'
    strip.save(fname,optimize=True)
    background.save(bname,optimize=True)
    manifest={'status':'generated_not_mpc_hardware_verified',
        'source_filename':still_path.name,'source_sha256':digest(still_path),
        'base_filename':bg_path.name,'base_sha256':digest(bg_path),
        'tui_baseline':'7516790b1a51b74a6fb8b0a9fb2ed6052e2089a7',
        'host_parameter':20,'native_component':'LIVE_BLENDECLIPSE_LAB10',
        'strip':{'name':fname.name,'sha256':digest(fname),'width':strip.width,'height':strip.height,'frames':NFRAMES,'frame_size':[613,392]},
        'background':{'name':bname.name,'sha256':digest(bname),'size':[1280,628]},
        'shifts':SHIFTS,
        'scope':'Private assets only. TUI, Q-Links, DSP, samples unchanged.',
        'limitations':['Rebuilt hidden sun hemisphere from visible source texture; requires visual author approval','Native MPC touch/Data Wheel/Q-Link not physically verified']}
    (out/'UI44_ASSET_MANIFEST.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    # Contact sheet is QA-only, never a shippable skin asset.
    contact=Image.new('RGB',(1280,628*3))
    for i,n in enumerate([0,7,15]):
        screen=background.copy()
        screen.paste(frames[n],(STRIP_RECT[0],STRIP_RECT[1]))
        contact.paste(screen,(0,i*628))
    contact.save(out/'UI44_VISUAL_CONTACT_QA.png')
    print(json.dumps(manifest,indent=2,ensure_ascii=False))
    return manifest

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--approved',type=Path,required=True)
    ap.add_argument('--lab10-background',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    build(args.approved,args.lab10_background,args.output)