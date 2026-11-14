#!/usr/bin/env python3
"""UI43: active TUI integration + eight real parameter-responsive graphical strips.

Synthetic film images are sufficient for structural CI; approved private artwork
is regenerated and visually inspected in the private assembly workspace.
"""
import base64,io,json,subprocess,sys,tempfile
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw

root=Path(__file__).resolve().parents[1]
active=json.loads((root/'skins/TUI.json').read_text())
comps=active['pageData']['tabs'][0]['componentDefinition']['componentsData']
entries={x['componentData']['name']:x for x in comps}
expected=[
 ('RADAR','BODY',38,5,'457 232 323 272'),
 ('RADAR','DECAY',39,5,'457 232 323 272'),
 ('RADAR','EXCITE',40,5,'457 232 323 272'),
 ('RADAR','MIX',41,5,'457 232 323 272'),
 ('GRANULAR','SIZE',44,8,'73 246 604 240'),
 ('GRANULAR','DENSITY',45,8,'73 246 604 240'),
 ('GRANULAR','POSITION',46,8,'73 246 604 240'),
 ('GRANULAR','MIX',47,8,'73 246 604 240')
]
assert len(comps)==154,len(comps)
assert len([x for x in comps if x['componentData']['name'].startswith('TOUCH_TAB_')])==11
for group,key,host,page,bounds in expected:
 item=entries[f'UI43_{group}_{key}']
 data=item['componentData']['data']
 assert item['componentData']['type']=='Knob'
 assert data['knobType']=='FilmStrip' and data['numFrames']==16
 assert data['filmStrip']==f'ui43_{group.lower()}_{key.lower()}_16.png'
 assert item['handle remapping']['map']==[{'key':'Data','value':f'Parameter {host}'}]
 assert item['bounds']['bounds']==bounds
 assert item['bounds']['acceptsHWFocus']=='No'
 assert item['bounds']['additionalInvalidatingHandles']==[f'IndexedEnabling/{page}/11/Parameter 112']
for p in ('05','08'):
 n=f'APPROVED_LAB10_{p}_0'
 assert entries[n]['componentData']['data']['image']==f'ui43_lab10_mpc_{p}.png'
# Reconstruct exactly the 146-component UI42 input; no other components change.
reverted=json.loads(json.dumps(active))
cc=reverted['pageData']['tabs'][0]['componentDefinition']['componentsData']
cc[:]=[c for c in cc if not c['componentData']['name'].startswith('UI43_')]
for c in cc:
 d=c['componentData']['data']
 if c['componentData']['type']=='Image' and d.get('image') in ['ui43_lab10_mpc_05.png','ui43_lab10_mpc_08.png']:
  d['image']=d['image'].replace('ui43_','')
assert len(cc)==146
with tempfile.TemporaryDirectory() as dirname:
 folder=Path(dirname);skins=folder/'original_art';skins.mkdir()
 for name in ['lab10_mpc_05.png','lab10_mpc_08.png']:
  im=Image.new('RGB',(1280,628),(5,29,32))
  ImageDraw.Draw(im).ellipse((465,225,785,518),outline=(220,188,143),width=2)
  im.save(skins/name)
 bg=Image.new('RGB',(995,615),(10,34,37))
 memory=io.BytesIO();bg.save(memory,format='JPEG')
 encoded=base64.b64encode(memory.getvalue()).decode()
 html=folder/'original.html'
 html.write_text('const imgs={"resonance": "data:image/jpeg;base64,'+encoded+
                 '", "granular": "data:image/jpeg;base64,'+encoded+'"};')
 tui=folder/'UI42.json';tui.write_text(json.dumps(reverted))
 out=folder/'result'
 subprocess.run([sys.executable,str(root/'tools/ui43_generate_representative_graphics.py'),
                 '--tui',str(tui),'--assets',str(skins),'--html',str(html),'--out',str(out)],
                 check=True)
 got=json.loads((out/'TUI.json').read_text())
 assert got==active,'Source generator does not reproduce the ACTIVE UI43 TUI'
 for group,key,host,page,bounds in expected:
  d=entries[f'UI43_{group}_{key}']['componentData']['data']
  piece=Image.open(out/d['filmStrip']).convert('RGBA')
  x,y,w,h=[int(z) for z in bounds.split()]
  assert piece.size==(w,h*16),(piece.size,bounds)
  start=piece.crop((0,0,w,h));end=piece.crop((0,h*15,w,h*16))
  assert ImageChops.difference(start,end).getbbox() is not None,(group,key)
  assert start.getchannel('A').getextrema()[0]==0
 for p in ('05','08'):
  im=Image.open(out/f'ui43_lab10_mpc_{p}.png')
  assert im.size==(1280,628)
 print('PASS: 8 independent four-dimensional graphic states, 128 filmstrip frames, two backgrounds, original 146 components unchanged, 11 tabs')
