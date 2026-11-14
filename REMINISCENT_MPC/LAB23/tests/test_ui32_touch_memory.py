from pathlib import Path
from collections import Counter
import zipfile,json,hashlib
base=Path('/mnt/data/REminiSCENT_UI31_LAB10_DINAMICA_PREMPC_COMPLETA.zip')
out=Path('/mnt/data/REminiSCENT_UI32_FOCO_QLINKS_ONOFF_MEMORY_CANDIDATO.zip')
with zipfile.ZipFile(base) as a,zipfile.ZipFile(out) as b:
 prefix='Yeti Fingers - VST - REminiSCENT/';t=json.loads(b.read(prefix+'Plugin Skins/TUI.json'));q=json.loads(b.read(prefix+'Plugin Skins/Q-Links.json'))
 c=t['pageData']['tabs'][0]['componentDefinition']['componentsData'];defns=t['pageData']['componentDefinitions']['localComponentDefinitions']
 by_name={x['componentData']['name']:x for x in c}
 assert len(c)==137 and len(defns)==56 and len([n for n in c if n['componentData']['type'].startswith('UI32_FOCUS_')])==39
 assert len([n for n in c if n['componentData']['type'].startswith('UI32_TOGGLE_')])==16
 for key in ('ACOUSTIC_POWER_A','ACOUSTIC_POWER_B','MEMORY_FREEZE','MEMORY_REVERSE','MEMORY_TIDE'):
  assert by_name[key]['componentData']['type'].startswith('UI32_TOGGLE_')
 for d in defns:
  if d['key'].startswith('UI32_TOGGLE_'):
   assert any(a['handler']=='Toggle Switch' and a['onAction']=='Mouse Down' for a in d['value']['actions'])
 for i in range(1,17):
  want=113+(i-1)%4
  assert q['Screen Mode Q-Links']['map'][0]['Q-Links'][f'Q-Link {i}']==want
  assert q['Program Mode Q-Links'][f'Q-Link {i}']==want
 assert q['Screen Mode Q-Links']['map'][0]['Bank Direction']=='RowTopDown'
 assert len([n for n in c if n['componentData']['name'].startswith('APPROVED_LAB10_')])==19
 assert by_name['LIVE_MEMORY_WINDOW_BOUNDS_UI32']['componentData']['data']['handleName']=='Parameter 33'
 assert by_name['LIVE_MEMORY_SELECTED_POSITION_UI32']['componentData']['data']['handleName']=='Parameter 35'
 for i in range(8,19):
  if i in (8,9,10,11,12,13,14,15,16,17,18):
   assert by_name[f'UI32_EFFECT_ENABLED_LED_P{i}']['bounds']['additionalInvalidatingHandles'][1]==f'IndexedEnabling/1/2/Parameter {i}'
 originals=set(a.namelist()); changed=[]
 for x in originals:
  if a.getinfo(x).CRC!=b.getinfo(x).CRC:changed.append(x)
 assert set(changed)=={prefix+'Plugin Skins/TUI.json',prefix+'Plugin Skins/Q-Links.json'}
 assert len(b.namelist())==len(a.namelist())+3
 assert sum(n.endswith('.wav') for n in originals)==254
 assert b.testzip() is None
 print('PASS UI32: 16 real on/off switches, 39 focusable touch drags, 4 Qlink proxies across 4 banks, 11 pages, memory window/position + active LEDs, original art/PCM/DSP unchanged.')
 print('ZIP_SHA256',hashlib.file_digest(open(out,'rb'),'sha256').hexdigest())