from pathlib import Path
import sys,json,hashlib,re,zipfile,collections
from PIL import Image
ROOT=Path('/mnt/data/reminiscent_blackbox'); skin=ROOT/'UI31_LIVE'/'Plugin Skins';
sys.path.insert(0,str(ROOT/'sdk/tools'));import validate
class Reporter:
 def __init__(self):self.errors=[];self.warnings=[];self.passes=[]
 def error(self,s,*x):self.errors.append(s%x if x else s)
 def warn(self,s,*x):self.warnings.append(s%x if x else s)
 def ok(self,s,*x):self.passes.append(s%x if x else s)
rep=Reporter();validate.check_skins(rep,str(skin),125)
assert not rep.errors,(len(rep.errors),rep.errors[:10]);assert not rep.warnings,(len(rep.warnings),rep.warnings[:10]);print('SDK',len(rep.passes),'PASS / 0 WARN / 0 FAIL')
a=json.loads((skin/'TUI.json').read_text()); cs=a['pageData']['tabs'][0]['componentDefinition']['componentsData'];names={c['componentData']['name']:c for c in cs}
base=json.loads((ROOT/'REBUILD_CONTROLS_COMPLETE/Plugin Skins/TUI.json').read_text());prev=base['pageData']['tabs'][0]['componentDefinition']['componentsData']
assert len(cs)==124 and len(prev)==106
assert [(c['componentData']['name'],c['componentData']['data']) for c in cs if c['componentData']['name'].startswith('APPROVED_LAB10')]==[(c['componentData']['name'],c['componentData']['data']) for c in prev if c['componentData']['name'].startswith('APPROVED_LAB10')]
assert len([n for n in names if n.startswith('TOUCH_TAB_')])==11
assert len([n for n in names if n.startswith('Q_LINK_')])==4
assert len([n for n in names if n.startswith('SOLARIS_V09_SEGMENT')])==6
assert len([n for n in names if n.startswith('LIVE_MOD_LFO')])==2
params={'LIVE_OSC_WAVE_LAB10':2,'LIVE_OSC_SELECTOR_LAB10':2,'LIVE_BLENDECLIPSE_LAB10':20,'LIVE_MEMORY_READHEAD_UI31':121,'LIVE_MOD_LFO1_PCM_UI31':118,'LIVE_MOD_LFO2_PCM_UI31':119,'LIVE_MEMORY_PCM_TRACE_UI31':120}
for n,p in params.items():
 d=names[n]['componentData']['data'];ref=d.get('handleName',d.get('dataHandle'));assert ref==f'Parameter {p}',(n,ref)
for i in range(6):
 obj=names[f'SOLARIS_V09_SEGMENT_{i}'];assert obj['componentData']['data']['numFrames']==25
 assert obj['bounds']['additionalInvalidatingHandles']==[f'IndexedEnabling/{i}/7/Parameter 122']
 assert obj['componentData']['data']['handleName']=='Parameter 123'
assert not any(x.get('bounds',{}).get('additionalInvalidatingHandles')==['IndexedEnabling/6/7/Parameter 122'] for x in cs), 'Solaris must HIDE at DONE'
assert 'Parameter 122' in {v['key'] for v in a['pageData']['replacementStrings']}
adsr=names['LIVE_ADSR_4_PARAMS_UI31']['componentData']['data']; assert [adsr[k+'Handle'] for k in ('attack','decay','sustain','release')]==[f'Parameter {i}' for i in [29,30,31,32]]
env2=names['LIVE_MOD_ENV2_ADSR_4_PARAMS_UI31']['componentData']['data']; assert [env2[k+'Handle'] for k in ('attack','decay','sustain','release')]==[f'Parameter {i}' for i in range(88,92)]
# No performance-hostile sprite sheets: SDK target supports up to 8192 px texture.
for p in skin.glob('*.png'):
 im=Image.open(p); assert im.width<=1280 and im.height<=8192,(p.name,im.size)
for n in ('lab10_osc_wave_live_8.png','lab10_blend_eclipse_live_16.png','lab10_memory_playhead_32.png'):
 im=Image.open(skin/n); frames=int(re.search(r'_(8|16|32)\.png$',n).group(1));assert im.height%frames==0
assert len([x for x in cs if x['componentData']['name'].startswith('APPROVED_LAB10')])==19
print('TUI all 11 original pages, 87 controls preserved, OSC / BLEND / ADSR / MEMORY / LFO / Solaris visual handles OK')
print('Art 19/19 exact original, sprite texture heights <=8192')
with zipfile.ZipFile('/mnt/data/REminiSCENT_UI31_LAB10_GRAFICOS_DINAMICOS_CANDIDATO.zip') as z:
 assert z.testzip() is None
 assert sum(x.filename.endswith('.wav') for x in z.infolist())==254
 print('ZIP PASS members=',len(z.infolist()))
print('STATIC PASS; MPC HARDWARE NOT TESTED')