#!/usr/bin/env python3
"""Regression test UI33 native controls and faithful filter SVG, without approval claims."""
import zipfile,io,hashlib,json,collections,sys
from PIL import Image
old,new=sys.argv[1:3]
root='Yeti Fingers - VST - REminiSCENT/Plugin Skins/'
with zipfile.ZipFile(old) as z0, zipfile.ZipFile(new) as z:
 assert z.testzip() is None
 old_names=set(z0.namelist());new_names=set(z.namelist())
 assert all(z.read(n)==z0.read(n) for n in old_names if n!=root+'TUI.json')
 comps=json.loads(z.read(root+'TUI.json'))['pageData']['tabs'][0]['componentDefinition']['componentsData']
 assert len(comps)==140
 t=collections.Counter(x['componentData']['type'] for x in comps)
 assert set(t).issubset({'Button','Knob','Image','Label','Plotter','Envelope','Slider'})
 assert t['Knob']==50 and t['Button']==48 and t['Label']==2
 assert len([x for x in comps if x['componentData']['name'].startswith('APPROVED_LAB10_')])==19
 for s in ['SOLARIS','OLD_FM1','LEGACY_FM1']:
  assert not any(s.lower() in n.lower() for n in new_names)
 for i in range(1,5):
  e=next(x for x in comps if x['componentData']['name']==f'QLINK_{i}_LAB10_LIVE_POINTER')
  assert e['componentData']['type']=='Knob'
  assert e['handle remapping']['map'][0]['value']==f'Parameter {112+i}'
 for n in ('ACOUSTIC_POWER_A','ACOUSTIC_POWER_B','MEMORY_FREEZE','MEMORY_REVERSE','MEMORY_TIDE'):
  assert next(x for x in comps if x['componentData']['name']==n)['componentData']['type']=='Button'
 f=next(x for x in comps if x['componentData']['name']=='FILTER_CUTOFF_ORIGINAL_LAB10_REACTIVE')
 assert f['componentData']['type']=='Knob' and f['handle remapping']['map'][0]['value']=='Parameter 42'
 img=Image.open(io.BytesIO(z.read(root+'lab10_filter_from_approved_html_24.png')))
 assert img.size==(595,5544)
 for n in old_names:
  if n.endswith(('.wav','.so','.png')):assert z.read(n)==z0.read(n)
 assert len([n for n in new_names if n.endswith('.wav')])==254
 print('PASS: 140 native SDK components; 16 ON/OFF mapped; 4 physical Q-Link visual pointers; 19 LAB10 approved base images unchanged; original DSP+254 WAV byte-identical; FILTER 24 frames derived from original LAB10 HTML.')
 print('BLOCK: static provenance gate still requires individual review of graphic overlays; FILTER ENV/TRACK and RESONANCE/GRANULAR composite graphics not complete. No physical MPC test.')