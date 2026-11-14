#!/usr/bin/env python3
"""UI43: regenerate author-approved representative RADAR and DNA layers for MPC.

Four transparent 16-frame native FilmStrips per screen, each driven by the
existing real parameter (no new DSP, no audio analysis). PRIVATE inputs:
UI42 TUI, original LAB10 image assets and approved HTML with source photos.
Never overwrite original LAB10 backgrounds or existing sound files.
"""
import argparse,base64,io,json,math,re
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter

FRAMES=16
RESONANCE=(457,232,323,272)
GRANULAR=(73,246,604,240)
COLORS={"amber":(228,191,145),"sand":(236,204,159),
        "teal":(117,184,181),"pale":(175,211,198),"peach":(212,135,113)}
def rgba(name,opacity=255):
    return (*COLORS[name],int(max(0,min(255,opacity))))
def circle(draw,x,y,r,**k):
    draw.ellipse((x-r,y-r,x+r,y+r),**k)
def photo_from_html(html,name):
    raw=html.read_text()
    m=re.search(r'"'+re.escape(name)+r'"\s*:\s*"data:image/jpeg;base64,([A-Za-z0-9+/=]+)"',raw)
    if not m:raise ValueError("Approved original HTML photo missing: "+name)
    return Image.open(io.BytesIO(base64.b64decode(m.group(1)))).convert("RGB")
def backing(asset,photo,which):
    src=Image.open(asset).convert("RGB")
    assert src.size==(1280,628),asset
    under=Image.new("RGB",src.size,(2,19,21))
    under.paste(photo.resize((995,521),Image.Resampling.BICUBIC),(0,105))
    if which=="radar":
        clean=Image.blend(under,Image.new("RGB",src.size,(5,24,28)),.55)
        mask=Image.new("L",src.size,0)
        ImageDraw.Draw(mask).ellipse((469,238,769,499),fill=255)
        result=Image.composite(clean,src,mask.filter(ImageFilter.GaussianBlur(1.1)))
        extra=Image.new("RGBA",src.size)
        d=ImageDraw.Draw(extra)
        for r,alpha in [(144,100),(116,66),(89,55),(57,49)]:
            d.ellipse((618-r,369-r,618+r,369+r),outline=(190,158,115,alpha))
        d.line((476,369,760,369),fill=(190,158,115,60))
        d.line((618,238,618,499),fill=(190,158,115,60))
        return Image.alpha_composite(result.convert("RGBA"),extra).convert("RGB")
    if which=="granular":
        clean=Image.blend(under,Image.new("RGB",src.size,(3,24,27)),.68)
        mask=Image.new("L",src.size,0)
        ImageDraw.Draw(mask).rectangle((51,231,699,499),fill=255)
        return Image.composite(clean,src,mask.filter(ImageFilter.GaussianBlur(.8)))
    raise ValueError(which)
def bloom(w,h,rect,color,blur=10):
    v=Image.new("RGBA",(w,h))
    ImageDraw.Draw(v).ellipse(rect,fill=color)
    return v.filter(ImageFilter.GaussianBlur(blur))
def radar_layer(kind,v):
    w,h=RESONANCE[2:]
    im=Image.new("RGBA",(w,h))
    d=ImageDraw.Draw(im)
    if kind=="body":
        x=w*(.19+.29*v);y=h*(.51-.24*v)
        im.alpha_composite(bloom(w,h,(x-18,y-18,x+18,y+18),rgba("peach",95)))
        d=ImageDraw.Draw(im)
        d.ellipse((x-15,y-5,x+15,y+5),outline=rgba("sand",220),width=2)
        circle(d,x,y,11,fill=rgba("peach",235),outline=rgba("sand",240),width=2)
        d.ellipse((x-20,y-6,x+20,y+6),outline=rgba("sand",170),width=2)
        circle(d,w*.69,h*(.51+.14*v),3,fill=rgba("sand",245))
    elif kind=="decay":
        cx,cy=w*.47,h*.48
        for i in range(1+int(round(v*4))):
            r=18+i*17+8*v
            circle(d,cx,cy,r,outline=rgba("teal",(35+100*v)/(1+i*.5)),width=2 if v>.5 else 1)
        rad=126
        d.arc((w/2-rad,h/2-rad,w/2+rad,h/2+rad),240,240+60+100*v,fill=rgba("amber",38+93*v),width=2)
    elif kind=="excite":
        x=w*(.54+.18*v);y=h*.19
        im.alpha_composite(bloom(w,h,(x-16,y-16,x+16,y+16),rgba("teal",85+75*v)))
        d=ImageDraw.Draw(im)
        circle(d,x,y,12,fill=rgba("pale",220))
        circle(d,x+5,y-5,12,fill=(4,27,32,255))
        n=3+int(v*4)
        for i in range(n):
            a=i*2*math.pi/n
            xx=w*.7+math.cos(a)*(6+9*v);yy=h*.67+math.sin(a)*(6+9*v)
            d.line([(w*.7,h*.67),(xx,yy)],fill=rgba("sand",120+120*v),width=2)
        circle(d,w*.7,h*.67,4+4*v,fill=rgba("sand",175+70*v))
    elif kind=="mix":
        cx,cy=w*.5,h*.5
        for i,r in enumerate([62,103,133]):
            d.arc((cx-r,cy-r,cx+r,cy+r),190,220+int(v*285),
                  fill=rgba("teal" if i%2 else "amber",20+85*v),width=2)
        circle(d,cx,cy,3+4*v,fill=rgba("sand",40+125*v))
    else:raise ValueError(kind)
    return im
def granular_layer(kind,v):
    w,h=GRANULAR[2:]
    im=Image.new("RGBA",(w,h))
    d=ImageDraw.Draw(im)
    def xy(x,y):return (x*w/600,y*h/290)
    if kind=="density":
        n=11+int(round(v*18))
        freq=math.pi*(2.6+v*2.2)
        upper=[];lower=[]
        for i in range(n):
            q=i/(n-1);x=15+q*515;delta=math.sin(q*freq)*62
            a=xy(x,147+delta);b=xy(x,147-delta)
            d.line([a,b],fill=rgba("teal",90))
            circle(d,*a,2.5,fill=rgba("sand",230))
            circle(d,*b,2.5,fill=rgba("teal",230))
            if i%3==0:
                xx,yy=xy(x+(.1+v)*34,147+delta-11-v*27)
                circle(d,xx,yy,1.5+2*v,fill=rgba("peach",155))
            upper.append(a);lower.append(b)
        d.line(upper,fill=rgba("sand",160),width=2)
        d.line(lower,fill=rgba("teal",185),width=2)
    elif kind=="size":
        for i in range(13):
            q=i/12;x=15+515*q;offset=math.sin(q*math.pi*3.6)*61
            for y,c in [(147+offset,"sand"),(147-offset,"teal")]:
                xx,yy=xy(x,y)
                circle(d,xx,yy,1.3+5*v,fill=rgba(c,80+140*v))
    elif kind=="position":
        x,_=xy(15+v*515,0)
        im.alpha_composite(bloom(w,h,(x-9,28,x+9,h-26),rgba("teal",45),11))
        d=ImageDraw.Draw(im)
        d.line([(x,30),(x,h-31)],fill=rgba("pale",90),width=2)
        d.polygon([(x-5,26),(x+5,26),(x,31)],fill=rgba("sand",160))
    elif kind=="mix":
        for sign,col in [(1,"sand"),(-1,"teal")]:
            pts=[]
            for i in range(80):
                q=i/79;pts.append(xy(15+q*515,147+sign*math.sin(q*math.pi*3.8)*(47+30*v)))
            d.line(pts,fill=rgba(col,45+155*v),width=1 if v<.15 else 2)
    else:raise ValueError(kind)
    return im
def strip(layer,name):
    frames=[layer(name,i/(FRAMES-1)) for i in range(FRAMES)]
    w,h=frames[0].size
    out=Image.new("RGBA",(w,FRAMES*h))
    for i,frame in enumerate(frames):out.alpha_composite(frame,(0,i*h))
    return out
def widget(name,param,img,bounds,page):
    x,y,w,h=bounds
    return {"version":2,
      "componentData":{"version":1,"name":name,"type":"Knob","data":{
        "version":3,"knobType":"FilmStrip","filmStrip":img,"numFrames":FRAMES,
        "invert":False,"dragOrientation":"Horizontal","handleName":"Data"}},
      "handle remapping":{"version":1,"map":[{"key":"Data","value":f"Parameter {param}"}]},
      "bounds":{"version":2,"acceptsHWFocus":"No","showWhenDataModelInvalid":"Hide",
        "whenVisible":"Always","boundsType":"Absolute","bounds":f"{x} {y} {w} {h}",
        "additionalInvalidatingHandles":[f"IndexedEnabling/{page}/11/Parameter 112"]}}
def integrate(tui,assets,html,out):
    out.mkdir(parents=True,exist_ok=True)
    skin=json.loads(tui.read_text())
    comps=skin["pageData"]["tabs"][0]["componentDefinition"]["componentsData"]
    if any(x["componentData"]["name"].startswith("UI43_") for x in comps):
        raise ValueError("UI43 already applied; refusing to duplicate")
    groups=[
     ("radar",5,[38,39,40,41],["body","decay","excite","mix"],RESONANCE,"lab10_mpc_05.png","resonance"),
     ("granular",8,[44,45,46,47],["size","density","position","mix"],GRANULAR,"lab10_mpc_08.png","granular")]
    for name,page,params,keys,bounds,asset,photo in groups:
        clean=backing(assets/asset,photo_from_html(html,photo),name)
        clean.save(out/("ui43_"+asset),optimize=True)
        matches=[c for c in comps if c["componentData"]["type"]=="Image" and c["componentData"]["data"].get("image")==asset]
        if len(matches)!=1:raise ValueError(f"Unexpected existing background count {asset}:{len(matches)}")
        matches[0]["componentData"]["data"]["image"]="ui43_"+asset
        touch="RESONANCE" if name=="radar" else "GRANULAR"
        idx=next((i for i,c in enumerate(comps) if c["componentData"]["name"].startswith(touch+"_PARAM_")),None)
        if idx is None:raise ValueError("Approved touch/Q-Link controls missing "+touch)
        layers=[]
        for key,param in zip(keys,params):
            filename=f"ui43_{name}_{key}_{FRAMES}.png"
            strip(radar_layer if name=="radar" else granular_layer,key).save(out/filename,optimize=True,compress_level=9)
            layers.append(widget(f"UI43_{name.upper()}_{key.upper()}",param,filename,bounds,page))
        comps[idx:idx]=layers
    assert len(comps)==154
    (out/"TUI.json").write_text(json.dumps(skin,ensure_ascii=False,indent=2)+"\n")
    print("UI43 generated: 2 backgrounds, 8 independently bound 16-frame RGBA filmstrips, 154 widgets")
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    for arg in ["tui","assets","html","out"]:ap.add_argument("--"+arg,required=True,type=Path)
    args=ap.parse_args()
    integrate(args.tui,args.assets,args.html,args.out)
