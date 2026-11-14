#!/usr/bin/env python3
"""Regression gate: report which author-approved display graphs are linked to host parameters.
Does not mistake numeric text / transparent touch hit rectangles for a responsive graphic.
Run against the full private UI ZIP without publishing audio.
"""
import sys,json,zipfile,collections,re,hashlib,pathlib
z=zipfile.ZipFile(sys.argv[1]); prefix='Yeti Fingers - VST - REminiSCENT/Plugin Skins/'
t=json.loads(z.read(prefix+'TUI.json')); cs=t['pageData']['tabs'][0]['componentDefinition']['componentsData']
visual_types={'Knob','Image','Envelope','Plotter','Slider'}
translucent={'lab10_native_touch_101.png','lab10_touch_hit.png'}
def visual_file(c):
 d=c['componentData']['data'];return d.get('filmStrip') or d.get('image') or d.get('onImage')
def page_of(c):
 patterns=c['bounds'].get('additionalInvalidatingHandles',[])
 for x in patterns:
  m=re.match(r'IndexedEnabling/(\d+)/11/Parameter 112',x)
  if m:return int(m.group(1))
 return None
def param_of(c):
 return [int(m.group(1)) for d in c.get('handle remapping',{}).get('map',[]) if (m:=re.match('Parameter (\\d+)$',d.get('value','')))]
actual=collections.defaultdict(set);evidence=collections.defaultdict(list)
for c in cs:
 d=c['componentData'];p=page_of(c);f=visual_file(c)
 if p is None or d['type'] not in visual_types:continue
 if d['type'] not in ('Envelope','Plotter') and (f in translucent or not f):continue
 if d['type']=='Knob' and d['data'].get('knobType')=='ValueSlider':continue
 params=param_of(c)
 if d['type']=='Envelope':
  for key in ('attackHandle','decayHandle','sustainHandle','releaseHandle'):
   m=re.match(r'Parameter (\d+)$',d['data'].get(key,''))
   if m:params.append(int(m.group(1)))
 if d['type']=='Plotter':
  m=re.match(r'Parameter (\d+)$',d['data'].get('dataHandle',''))
  if m:params.append(int(m.group(1)))
 for param in params:
  actual[p].add(param);evidence[p,param].append(d['name'])
required={
 'Acoustic Blend':(0,[19]),
 'Master Blend Eclipse':(2,[20]),
 'Envelope ADSR':(3,[29,30,31,32]),
 'Resonance 4 params':(5,[38,39,40,41]),
 'Filter 4 params':(6,[42,107,108,43]),
 'Granular 4 params':(8,[44,45,46,47]),
}
report={'ui_version':'UI33','checked':{},'missing':{},'result':'PASS'}
for name,(page,params) in required.items():
 have={str(i):evidence.get((page,i),[]) for i in params if i in actual[page]}
 missing=[i for i in params if i not in actual[page]]
 report['checked'][name]={'page':page,'visual_parameter_evidence':have}
 if missing:report['missing'][name]=missing
if report['missing']:report['result']='BLOCK'
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(report['result']!='PASS')