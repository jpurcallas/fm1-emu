#!/usr/bin/env python3
"""UI40: functional 3-zone bars for the author's approved REminiSCENT MPC art.

Inputs: UI39 TUI.json and matching unmodified approved LAB10 1280x628 PNGs.
Outputs: new TUI + additive PNGs; NEVER overwrite original LAB10 backgrounds.
The palette and chrome are derived from the currently used skin, not old designs.
No DSP, parameters, bank, presets, or sound files are modified.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PAGE_FILES = {
    4: ['lab10_mpc_04.png'],
    7: [f'lab10_mpc_07_{k}.png' for k in range(4)],
    9: [f'lab10_mpc_09_{k}.png' for k in range(3)],
    10: [f'lab10_mpc_10_{k}.png' for k in range(4)],
}
GROUPS = {
    'MEMORY': dict(page=4,x=[461,620,779],width=145, p_y=289,p_h=93,e_y=382,e_h=45,flags=[5,6,7],sel=117,keys=['FREEZE','REVERSE','TIDE']),
    'CHAR': dict(page=7,x=[50,230,410,590],width=164,p_y=306,p_h=104,e_y=410,e_h=64,flags=[8,9,10,11],sel=109,keys=['DISTORTION','TAPE','VINYL','CRUSH']),
    'MOD': dict(page=9,x=[48,257,466],width=192,p_y=304,p_h=75,e_y=379,e_h=56,flags=[16,17,18],sel=111,keys=['LFO1','LFO2','ENV2']),
    'SEND': dict(page=10,x=[50,230,410,590],width=164,p_y=306,p_h=104,e_y=410,e_h=64,flags=[12,13,14,15],sel=110,keys=['DELAY','REVERB','MOD1','MOD2']),
}
INK=(215,184,137)
INK_BRIGHT=(250,220,165)
INK_DARK=(105,115,110)

def font(size,bold=False):
    name='/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf'
    try:return ImageFont.truetype(name,size)
    except OSError:return ImageFont.load_default()

def label_center(draw,xy,value,face,color):
    x,y=xy
    bb=draw.textbbox((0,0),value,font=face)
    draw.text((round(x-(bb[2]-bb[0])/2),round(y-(bb[3]-bb[1])/2)-bb[1]),value,font=face,fill=color)

def power_image(w,h,on):
    im=Image.new('RGBA',(w,h),(0,0,0,0))
    d=ImageDraw.Draw(im)
    color=INK_BRIGHT if on else INK_DARK
    cx=w//2;cy=round(h*.36);rad=max(10,min(w,h)//5)
    if on:
        halo=Image.new('RGBA',(w,h),(0,0,0,0));hd=ImageDraw.Draw(halo)
        hd.arc((cx-rad,cy-rad,cx+rad,cy+rad),45,315,fill=(*INK,180),width=6)
        hd.line((cx,cy-rad-2,cx,cy+1),fill=(*INK,150),width=6)
        im.alpha_composite(halo.filter(ImageFilter.GaussianBlur(5)))
    d.arc((cx-rad,cy-rad,cx+rad,cy+rad),46,314,fill=(*color,255),width=3)
    d.line((cx,cy-rad-4,cx,cy+2),fill=(*color,255),width=3)
    label_center(d,(cx,round(h*.78)),'ON/OFF',font(max(11,min(15,h//6)),True),(*color,255))
    return im

def edit_image(w,h,selected):
    im=Image.new('RGBA',(w,h),(0,0,0,0));d=ImageDraw.Draw(im)
    color=INK_BRIGHT if selected else INK_DARK
    x=w//2;y=max(9,round(h*.33));gap=max(5,min(9,h//7))
    for j,shift in enumerate((3,-6,5)):
        yy=y+(j-1)*gap
        d.line((x-15,yy,x+15,yy),fill=(*color,230),width=2)
        xx=x+shift
        d.rectangle((xx-3,yy-4,xx+3,yy+4),fill=(*color,255))
    label_center(d,(x,round(h*.74)),'EDIT',font(max(11,min(16,h//4)),True),(*color,255))
    if selected:d.line((12,h-3,w-12,h-3),fill=(*INK,180),width=2)
    return im

def draw_backing(src,configs):
    im=src.convert('RGBA')
    d=ImageDraw.Draw(im,'RGBA')
    # Existing frames, titles, lamps, rivets and all outside art remain untouched.
    # Replace ONLY the old internal icon/power/selector surfaces in the bars.
    for g in configs:
        x,w=g['x'],g['width'];y0=g['p_y'];y1=g['e_y']+g['e_h']
        for y in range(y0,y1):
            f=(y-y0)/max(1,y1-y0)
            d.line((x+7,y,x+w-7,y),fill=(11+round(4*f),32+round(2*f),34+round(2*f),255),width=1)
        for yy,color in [(y0,(104,89,67,255)),(y0+1,(1,10,13,255)),(g['e_y']-1,(1,10,13,255)),(g['e_y'],(105,93,71,255))]:
            d.line((x+6,yy,x+w-6,yy),fill=color,width=1)
    return im.convert('RGB')

def button(name,handle,button_id,group,bounds,page,kind):
    x,y,w,h=bounds
    if kind=='power':
        name_on=f'ui40_{w}x{h}_power_on.png';name_off=f'ui40_{w}x{h}_power_off.png'
    else:
        name_on=f'ui40_{w}x{h}_edit_selected.png';name_off=f'ui40_{w}x{h}_edit_unselected.png'
    return dict(version=2,componentData=dict(version=1,name=name,type='Button',
        data=dict(version=2,onImage=name_on,offImage=name_off,buttonId=button_id,
                  numButtonsInGroup=group,handleName='Data',gestureBehaviour='Instant')),
        **{'handle remapping':dict(version=1,map=[dict(key='Data',value=f'Parameter {handle}')])},
        bounds=dict(version=2,acceptsHWFocus='Yes',showWhenDataModelInvalid='Hide',
                    whenVisible='Always',boundsType='Absolute',bounds=f'{x} {y} {w} {h}',
                    additionalInvalidatingHandles=[f'IndexedEnabling/{page}/11/Parameter 112']))

def generate(tui,assets,destination):
    destination.mkdir(parents=True,exist_ok=True)
    obj=json.loads(tui.read_text())
    components=obj['pageData']['tabs'][0]['componentDefinition']['componentsData']
    byname={c['componentData']['name']:c for c in components}
    generated=[]
    for prefix,g in GROUPS.items():
        for i,key in enumerate(g['keys']):
            x,w=g['x'][i],g['width']
            pn=f'{prefix}_ONOFF_{key}' if prefix!='MEMORY' else f'MEMORY_{key}'
            en=f'{prefix}_SELECT_{key}' if prefix!='MEMORY' else f'MEMORY_EDIT_{key}'
            pb=(x,g['p_y'],w,g['p_h']);eb=(x,g['e_y'],w,g['e_h'])
            if pn not in byname:raise AssertionError(f'Missing historic ON/OFF: {pn}')
            idx=components.index(byname[pn])
            components[idx]=button(pn,g['flags'][i],1,1,pb,g['page'],'power')
            if prefix=='MEMORY':
                components.insert(idx+1,button(en,g['sel'],i,len(g['keys']),eb,g['page'],'edit'))
            else:
                if en not in byname:raise AssertionError(f'Missing historic EDIT: {en}')
                idx=components.index(byname[en])
                components[idx]=button(en,g['sel'],i,len(g['keys']),eb,g['page'],'edit')
            for typ,rect in [('power',pb),('edit',eb)]:
                _,_,ww,hh=rect
                if typ=='power':
                    pairs=[('power_on',power_image(ww,hh,True)),('power_off',power_image(ww,hh,False))]
                else:
                    pairs=[('edit_selected',edit_image(ww,hh,True)),('edit_unselected',edit_image(ww,hh,False))]
                for suffix,img in pairs:
                    dst=destination/f'ui40_{ww}x{hh}_{suffix}.png'
                    if not dst.exists():img.save(dst);generated.append(dst.name)
        for name in PAGE_FILES[g['page']]:
            src=assets/name
            if not src.is_file():raise FileNotFoundError(src)
            image=Image.open(src)
            if image.size!=(1280,628):raise AssertionError(f'Unexpected size {src}: {image.size}')
            areas=[dict(x=x,width=g['width'],p_y=g['p_y'],e_y=g['e_y'],e_h=g['e_h']) for x in g['x']]
            result=draw_backing(image,areas)
            dst=destination/('ui40_'+name);result.save(dst,optimize=True);generated.append(dst.name)
    replace={n for files in PAGE_FILES.values() for n in files}
    replacements=0
    for c in components:
        data=c['componentData'].get('data',{})
        if c['componentData']['type']=='Image' and data.get('image') in replace:
            data['image']='ui40_'+data['image'];replacements+=1
    if replacements!=sum(map(len,PAGE_FILES.values())):raise AssertionError(f'Expected 12 page variants, got {replacements}')
    # Historic host indices are preserved; three new controls refer to existing
    # Parameter 117 (ui.selectedMemory), with no appended host parameters.
    for prefix,g in GROUPS.items():
        for i,key in enumerate(g['keys']):
            pn=f'{prefix}_ONOFF_{key}' if prefix!='MEMORY' else f'MEMORY_{key}'
            en=f'{prefix}_SELECT_{key}' if prefix!='MEMORY' else f'MEMORY_EDIT_{key}'
            for name,idx in [(pn,g['flags'][i]),(en,g['sel'])]:
                c=next(c for c in components if c['componentData']['name']==name)
                assert c['handle remapping']['map'][0]['value']==f'Parameter {idx}'
    out=destination/'TUI.json'
    out.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    manifest={}
    for name in generated+['TUI.json']:
        data=(destination/name).read_bytes()
        manifest[name]=dict(size=len(data),sha256=hashlib.sha256(data).hexdigest())
    (destination/'UI40_ASSETS_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--tui',type=Path,required=True)
    parser.add_argument('--assets',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    manifest=generate(args.tui,args.assets,args.out)
    print(f'UI40: {len(manifest)} files, {sum(v["size"] for v in manifest.values())} bytes; original source untouched')

if __name__=='__main__':main()
