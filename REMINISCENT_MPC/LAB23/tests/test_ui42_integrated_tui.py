#!/usr/bin/env python3
"""UI42: validate the *active* REminiSCENT TUI (not a provisional generator).

The 24 PNGs are intentionally private and provided by the original author skin,
not committed to the source repository. Use --asset-dir locally to assert them.
"""
from pathlib import Path
import argparse,json,re,hashlib
PAGE_FILES={
4:["lab10_mpc_04.png"],
7:[f"lab10_mpc_07_{x}.png" for x in range(4)],
9:[f"lab10_mpc_09_{x}.png" for x in range(3)],
10:[f"lab10_mpc_10_{x}.png" for x in range(4)]}
GROUPS={
"MEMORY":dict(page=4,x=[461,620,779],w=145,py=289,ph=93,ey=382,eh=45,flags=[5,6,7],sel=117,keys=["FREEZE","REVERSE","TIDE"]),
"CHAR":dict(page=7,x=[50,230,410,590],w=164,py=306,ph=104,ey=410,eh=64,flags=[8,9,10,11],sel=109,keys=["DISTORTION","TAPE","VINYL","CRUSH"]),
"MOD":dict(page=9,x=[48,257,466],w=192,py=304,ph=75,ey=379,eh=56,flags=[16,17,18],sel=111,keys=["LFO1","LFO2","ENV2"]),
"SEND":dict(page=10,x=[50,230,410,590],w=164,py=306,ph=104,ey=410,eh=64,flags=[12,13,14,15],sel=110,keys=["DELAY","REVERB","MOD1","MOD2"]),
}
def verify(path,asset_dir=None):
 t=json.loads(path.read_text())
 assert len(t["pageData"]["tabs"])==1
 components=t["pageData"]["tabs"][0]["componentDefinition"]["componentsData"]
 extra_ui43=sum(c["componentData"]["name"].startswith("UI43_") for c in components)
 assert extra_ui43 in (0,8), f"unexpected UI43 overlay count: {extra_ui43}"
 assert len(components)==146+extra_ui43, f"unexpected number of components: {len(components)}"
 names={c["componentData"]["name"]:c for c in components}
 assert len(names)==len(components), "duplicated component names"
 required_images=set()
 observed_onoff=[]
 observed_edit=[]
 for prefix,g in GROUPS.items():
  for i,key in enumerate(g["keys"]):
   x=g["x"][i];w=g["w"]
   pn=f"MEMORY_{key}" if prefix=="MEMORY" else f"{prefix}_ONOFF_{key}"
   en=f"MEMORY_EDIT_{key}" if prefix=="MEMORY" else f"{prefix}_SELECT_{key}"
   for n,h,id_,group,box,kind in [
      (pn,g["flags"][i],1,1,(x,g["py"],w,g["ph"]),"power"),
      (en,g["sel"],i,len(g["keys"]),(x,g["ey"],w,g["eh"]),"edit")]:
    c=names[n]
    assert c["componentData"]["type"]=="Button",n
    data=c["componentData"]["data"]
    assert data["buttonId"]==id_ and data["numButtonsInGroup"]==group,n
    assert data["gestureBehaviour"]=="Instant"
    assert c["bounds"]["bounds"]==" ".join(str(a) for a in box),n
    assert c["handle remapping"]["map"]==[{"key":"Data","value":f"Parameter {h}"}],n
    assert c["bounds"]["additionalInvalidatingHandles"]==[f"IndexedEnabling/{g['page']}/11/Parameter 112"],n
    for k,image in [("onImage",f"ui40_{w}x{box[3]}_{'power_on' if kind=='power' else 'edit_selected'}.png"),
                    ("offImage",f"ui40_{w}x{box[3]}_{'power_off' if kind=='power' else 'edit_unselected'}.png")]:
     assert data[k]==image,(n,k,data[k])
     required_images.add(image)
    (observed_onoff if kind=="power" else observed_edit).append((n,h))
   assert g["py"]+g["ph"]==g["ey"],f"gap or overlap for {pn}"
 assert len(observed_onoff)==14 and len(observed_edit)==14
 assert len(required_images)==12
 image_component_refs=[c["componentData"]["data"].get("image") for c in components if c["componentData"]["type"]=="Image"]
 for files in PAGE_FILES.values():
  for file in files:
   img="ui40_"+file
   assert image_component_refs.count(img)==1, ("bad page background count",img)
   required_images.add(img)
 assert len(required_images)==24
 # Essential original graphics remain present, not replaced or renamed.
 for name in ["LIVE_ADSR_4_PARAMS_UI31","LIVE_MEMORY_PCM_TRACE_UI31",
              "LIVE_MOD_LFO1_PCM_UI31","LIVE_MOD_LFO2_PCM_UI31","LIVE_MOD_ENV2_ADSR_4_PARAMS_UI31",
              "FILTER_CUTOFF_ORIGINAL_LAB10_REACTIVE"]:
  assert name in names,("missing unaffected graphic",name)
 if asset_dir:
  from PIL import Image
  for file in required_images:
   img=asset_dir/file
   assert img.is_file(),f"missing private asset {file}"
   with Image.open(img) as obj:
    if file.startswith("ui40_lab10_"): assert obj.size==(1280,628),file
    else:
     hit=re.search(r"ui40_(\d+)x(\d+)_",file);assert hit
     assert obj.size==(int(hit.group(1)),int(hit.group(2))),file
 print(f"PASS: UI42 active TUI: {len(observed_onoff)} independent ON/OFF + {len(observed_edit)} EDIT; 12 backgrounds; 12 overlays; original graphics retained; 11 tabs preserved")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--tui",type=Path,required=True)
 p.add_argument("--asset-dir",type=Path);a=p.parse_args();verify(a.tui,a.asset_dir)
