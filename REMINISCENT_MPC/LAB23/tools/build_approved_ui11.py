#!/usr/bin/env python3
"""Rebuild the authorized LAB10 11-screen visual skin for the MPC touch UI.

This is NOT a new design: uses exact approved screenshot sources. Keeps
all existing DSP/plugin binaries intact. No legacy FM1 fondos or Solaris
full-screen opaque overlays. All eleven top navigation buttons remain
native SDK Button widgets bound to UI parameter 112; 4 Q-links use the
existing dynamic proxies (113..116). Source choices and basic page toggles
are native SDK controls. The MPC SDK has one tab containing 11 interactive
touch pages, exactly like the approved LAB10 top navigation.
"""
import json,os,shutil,sys
from pathlib import Path
from PIL import Image,ImageDraw
BASE=Path('/mnt/data')
APP=BASE/'REminiSCENT_LAB24_MPC_ARM32_COMPLETO'/'Yeti Fingers - VST - REminiSCENT'
DEST=BASE/'REminiSCENT_LAB25_MPC_UI11_APPROVED'/'Yeti Fingers - VST - REminiSCENT'
assert APP.exists()
if DEST.exists(): shutil.rmtree(DEST)
shutil.copytree(APP,DEST,copy_function=os.link)
root=DEST/'Plugin Skins'
# Don't mutate the original hardlinked TUI when writing.
original=json.loads((APP/'Plugin Skins'/'TUI.json').read_text())
page=original['pageData']; prior=page['tabs'][0]; before=prior['componentDefinition'];
WIDTH,HEIGHT=1280,628
rescale=HEIGHT/740.0
names=['ACOUSTIC','OSC','BLEND','ENVELOPE','MEMORY','RESONANCE','FILTER','CHARACTER','GRANULAR','MOD','SEND FX']
for i in range(11):
    src=BASE/('REminiSCENT_MOD_TRES_MODULOS_REFERENCIA.png' if i==9 else 'LAB10_UI_%02d.png'%i)
    assert src.exists(),src
    art=Image.open(src).convert('RGB');assert art.size==(1280,800),art.size
    art=art.crop((0,0,1280,740)).resize((WIDTH,HEIGHT),Image.Resampling.LANCZOS)
    # Original screenshot includes fixed numbers in Q-link text. Blank JUST
    # those four values so the SDK renders actual host parameter values.
    d=ImageDraw.Draw(art)
    for yy in (269,385,502,617):
        y=int(yy*rescale)
        rgb=art.getpixel((1207,min(y+7,HEIGHT-1)))
        d.rectangle((1093,y-5,1215,y+23),fill=rgb)
    art.save(root/('lab10_mpc_%02d.png'%i),optimize=True)
# Transparent action hitbox: full screenshot contains exact selected nav state.
Image.new('RGBA',(1,1),(0,0,0,0)).save(root/'lab10_touch_hit.png')

def item(name,typ,data,rect,idx=None,cond=None,focus='Yes',hide='Hide'):
    rem=[] if idx is None else [{'key':'Data','value':'Parameter '+str(idx)}]
    b={'version':2,'acceptsHWFocus':focus,'showWhenDataModelInvalid':hide,'whenVisible':'Always','boundsType':'Absolute','bounds':rect}
    if cond is not None:b['additionalInvalidatingHandles']=[cond]
    return {'version':2,'componentData':{'version':1,'name':name,'type':typ,'data':data},'handle remapping':{'version':1,'map':rem},'bounds':b}

def pagecond(n):return f'IndexedEnabling/{n}/11/Parameter 112'

def value(name,param,rect,cond):
    return item(name,'Knob',{'version':4,'knobType':'ValueSlider',
    'textStyle':{'version':1,'font':{'version':1,'name':'Nexa','style':'Bold','height':20.},
    'colour':'ffffc792','justification':'left verticallyCentred','case':'Original'},
    'dragOrientation':'Vertical','handleName':'Data'},rect,param,cond)

def touch(name,param,rect,cond):
    return item(name,'Knob',{'version':4,'knobType':'RotatingImage',
    'foregroundImage':'lab10_touch_hit.png','backgroundImage':'lab10_touch_hit.png',
    'imageScale':1.0,'dragOrientation':'Vertical','handleName':'Data'},rect,param,cond)

items=[]
for i in range(11):
    items.append(item('APPROVED_LAB10_SCREEN_%02d'%i,'Image',
        {'version':2,'imageType':'Regular','colour':'0','image':'lab10_mpc_%02d.png'%i},
        '0 0 1280 628',None,pagecond(i),focus='No',hide='Show'))
# Button hitboxes for touch navigation (all eleven pages). Preserve exact layout.
for i,n in enumerate(names):
    items.append(item('TOUCH_TAB_'+n.replace(' ','_'),'Button',
        {'version':2,'onImage':'lab10_touch_hit.png','offImage':'lab10_touch_hit.png',
         'buttonId':i,'numButtonsInGroup':11,'handleName':'Data','gestureBehaviour':'Instant'},
        '%d %d 110 37'%(15+113*i,round(83*rescale)),112,focus='Yes'))
# The approved Q-Link sidebar is in the bitmap; its numbers are replaced by
# these direct-edit MPC widgets, correctly backed by dynamic Q-Link proxies.
for k,y in enumerate([269,385,502,617]):
    items.append(value('Q_LINK_%d_EDIT_AND_LIVE_VALUE'%(k+1),113+k,
                       '1093 %d 150 34'%int(y*rescale-4),None))
# Cross-page controls, with source selectors and toggles on their original
# graphic positions. All are bound to existing stable host parameters.
items += [
    touch('ACOUSTIC_ON_A',3,'49 %d 80 53'%round(288*rescale),pagecond(0)),
    touch('ACOUSTIC_ON_B',4,'49 %d 80 53'%round(370*rescale),pagecond(0)),
    value('ACOUSTIC_SOURCE_A',0,'144 %d 435 36'%round(291*rescale),pagecond(0)),
    value('ACOUSTIC_SOURCE_B',1,'144 %d 435 36'%round(370*rescale),pagecond(0)),
    touch('ACOUSTIC_BLEND_BAR',19,'49 %d 529 36'%round(541*rescale),pagecond(0)),
    touch('OSC_WAVE_SELECT',2,'70 %d 700 100'%round(410*rescale),pagecond(1)),
    touch('BLEND_ECLIPSE',20,'250 %d 480 370'%round(246*rescale),pagecond(2)),
    touch('MEMORY_FREEZE',5,'49 %d 155 75'%round(286*rescale),pagecond(4)),
    touch('MEMORY_REVERSE',6,'218 %d 155 75'%round(286*rescale),pagecond(4)),
    touch('MEMORY_TIDE',7,'388 %d 155 75'%round(286*rescale),pagecond(4)),
]
# Main ADSR stage editor, displayed *above* approved stage background.
sourceitems=before['componentsData']
for c in sourceitems:
    nm=c['componentData']['name']
    if nm=='LIVE_ADSR_NATIVE_LAB10':
        cc=json.loads(json.dumps(c));cc['bounds']['bounds']='64 %d 580 158'%round(299*rescale)
        cc['bounds']['additionalInvalidatingHandles']=[pagecond(3)];items.append(cc)
# MOD has exactly THREE approved generators (no wheel).
# Selectors and ON/OFF are native SDK buttons with invisible graphics.
for k,idx in [(0,111),(1,111),(2,111)]:
    items.append(item('MOD_SELECT_'+str(k),'Button',
        {'version':2,'onImage':'lab10_touch_hit.png','offImage':'lab10_touch_hit.png',
         'buttonId':k,'numButtonsInGroup':3,'handleName':'Data','gestureBehaviour':'Instant'},
        '%d %d 192 241'%(48+209*k,round(272*rescale)),idx,pagecond(9)))
# MOD on/off actual source choice is host indices 16..18 (see TUI index map).
for k in range(3):
    # The ON/OFF switch is supplied by the approved module's own bar.
    items.append(touch('MOD_ONOFF_%d'%k,16+k,'%d %d 155 32'%(67+209*k,round(475*rescale)),pagecond(9)))
# Character 4 choices, Send FX 4 choices, related toggles via original art hit zones.
for page_id,selector,base,n,xx in [(7,109,8,4,50),(10,110,12,4,50)]:
    for k in range(n):
        x=xx+180*k
        items.append(item(('CHAR_' if page_id==7 else 'SEND_')+'SELECT_'+str(k),'Button',
            {'version':2,'onImage':'lab10_touch_hit.png','offImage':'lab10_touch_hit.png',
             'buttonId':k,'numButtonsInGroup':4,'handleName':'Data','gestureBehaviour':'Instant'},
            '%d %d 164 210'%(x,round(272*rescale)),selector,pagecond(page_id)))
# Live elements only where their original module artwork has space; no
# full-screen 6-second Solaris playback (it previously covered and froze UI).
# The approved Solaris frames remain in the private package unchanged.
for c in sourceitems:
    nm=c['componentData']['name']
    if nm in ('LIVE_MOD_LFO1_SHAPE','LIVE_MOD_LFO2_SHAPE','LIVE_MOD_ENV2'):
        cc=json.loads(json.dumps(c))
        cc['bounds']['bounds']= '68 %d 590 85'%round(640*rescale)
        cc['bounds']['additionalInvalidatingHandles']=[pagecond(9)]+[x for x in c['bounds'].get('additionalInvalidatingHandles',[]) if '/Parameter 111' in x]
        items.append(cc)
# Build tab root in the existing SDK structure: 11 REAL touch sections,
# each with an authored image and live controls, not the 11 FM1 fondos.
newroot=json.loads(json.dumps(before))
newroot['componentsData']=items
page['tabs'][0]['componentDefinition']=newroot
# The repeated Q-LINKS labels and old FM1 overlay graphics are not reused.
# White/Pink selection live on ACOUSTIC; its original positions at lower-right
# are backed by the same UI-only param index 124, not a new sound engine.
for k in range(2):
    items.append(item('ACOUSTIC_NOISE_'+('WHITE' if k==0 else 'PINK'),'Button',
        {'version':2,'onImage':'noise_white_on.png' if k==0 else 'noise_pink_on.png',
         'offImage':'noise_white_off.png' if k==0 else 'noise_pink_off.png',
         'buttonId':k,'numButtonsInGroup':2,'handleName':'Data','gestureBehaviour':'Instant'},
        '%d %d 98 31'%(660+110*k,round(635*rescale)),124,pagecond(0)))
(root/'TUI.json').write_text(json.dumps(original,indent=2,ensure_ascii=False)+'\n')
# the original Qlink file from the previous correction remains unchanged
print('UILAB10 11 screenshots',len(names),'live components',len(items),'output',root)
