from pathlib import Path
import zipfile,json,hashlib
p=Path('/mnt/data/reminiscent_work/REminiSCENT_UI33_NATIVE_CONTROLS_CANDIDATE.zip')
o=Path('/mnt/data/reminiscent_work/REminiSCENT_UI33_NATIVE_LIVE_CANDIDATE.zip')
root='Yeti Fingers - VST - REminiSCENT/Plugin Skins/'
with zipfile.ZipFile(p) as z:
 t=json.loads(z.read(root+'TUI.json'))
 cs=t['pageData']['tabs'][0]['componentDefinition']['componentsData']
 adjusted=[]
 for c in cs:
  d=c['componentData'];data=d['data']
  if d['type']!='Image' or data.get('imageType')!='FilmStrip':continue
  param=data.get('handleName','');
  if not param.startswith('Parameter '):continue
  d['type']='Knob'
  d['data']={'version':3,'knobType':'FilmStrip','filmStrip':data['image'],'numFrames':data['numFrames'],'invert':False,'dragOrientation':'Horizontal' if ('BLEND' in d['name'] or 'WINDOW' in d['name'] or 'POSITION' in d['name']) else 'Vertical','handleName':'Data'}
  c['handle remapping']={'version':1,'map':[{'key':'Data','value':param}]}
  c['bounds']['acceptsHWFocus']='No' if ('READHEAD' in d['name'] or 'MEMORY' in d['name'] and ('WINDOW' not in d['name'] and 'POSITION' not in d['name'])) else 'Yes'
  adjusted.append(d['name'])
 assert len(adjusted)==10,adjusted
 raw=json.dumps(t,ensure_ascii=False,indent=2).encode()
 with zipfile.ZipFile(o,'w',allowZip64=True) as out:
  for item in z.infolist():out.writestr(item,raw if item.filename==root+'TUI.json' else z.read(item.filename))
with zipfile.ZipFile(o) as z:
 assert z.testzip() is None
 cs=json.loads(z.read(root+'TUI.json'))['pageData']['tabs'][0]['componentDefinition']['componentsData']
 from collections import Counter
 print('PATCH',adjusted)
 print('TYPES',Counter(a['componentData']['type'] for a in cs))
 print('CHECK',o.stat().st_size,hashlib.sha256(o.read_bytes()).hexdigest())