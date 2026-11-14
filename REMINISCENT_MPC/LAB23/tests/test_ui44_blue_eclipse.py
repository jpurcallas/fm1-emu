#!/usr/bin/env python3
"""UI44 structural/visual regression and official SDK Knob FilmStrip contract.

Run with original approved still and LAB10 background, not historical animated strips.
TUI and Q-Links are READ-ONLY; no audio assets are opened or modified.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import tempfile

import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'tools'))
try:
    import ui44_build_blue_eclipse as b
except ImportError:
    sys.path.insert(0,str(HERE))
    import ui44_build_blue_eclipse as b


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inspect_tui(tui, qlinks):
    """Follows official Akai docs/ui-reference.md, §§6.4/7/8, SDK febd2ca5."""
    t=json.loads(Path(tui).read_text())
    comps=t['pageData']['tabs'][0]['componentDefinition']['componentsData']
    byname={c['componentData']['name']:c for c in comps}
    eclipse=byname['LIVE_BLENDECLIPSE_LAB10']
    d=eclipse['componentData']['data']
    assert eclipse['componentData']['type']=='Knob'
    assert d['version']==3 and d['knobType']=='FilmStrip'
    assert d['filmStrip']=='lab10_blend_eclipse_live_16.png'
    assert d['numFrames']==16 and d['invert'] is False
    assert d['dragOrientation']=='Horizontal' and d['handleName']=='Data'
    assert eclipse['handle remapping']['map']==[{'key':'Data','value':'Parameter 20'}]
    assert eclipse['bounds']['bounds']=='192 178 613 392'
    assert eclipse['bounds']['acceptsHWFocus']=='Yes'
    assert 'IndexedEnabling/2/11/Parameter 112' in eclipse['bounds']['additionalInvalidatingHandles']
    touch=byname['BLEND_ECLIPSE_TOUCH']
    assert touch['handle remapping']['map']==[{'key':'Data','value':'Parameter 20'}]
    assert touch['bounds']['acceptsHWFocus']=='Yes'
    assert touch['componentData']['type'].startswith('LAB10_SDK_FOCUS_')
    bg=byname['APPROVED_LAB10_02_0']
    assert bg['componentData']['data']['image']=='lab10_mpc_02.png'
    assert bg['bounds']['bounds']=='0 0 1280 628'
    assert len(t['pageData']['tabs'])==1
    q=json.loads(Path(qlinks).read_text())
    assert q['Screen Mode Q-Links']['map'][0]['Q-Links']['Q-Link 1']==113
    assert q['Program Mode Q-Links']['Q-Link 1']==113
    print('PASS SDK native Knob FilmStrip / touch remaps MASTER BLEND Parameter 20; Q-Link 1 proxy 113')
    print('NOTE: C++ UI41 qLinkTarget(page BLEND=2, slot=0) must resolve field 24 -> host Parameter 20, physical MPC test pending')


def test_assets(approved, lab10, assets):
    approved,lab10,assets=Path(approved),Path(lab10),Path(assets)
    source=Image.open(approved)
    old=Image.open(lab10).convert('RGB')
    strip=Image.open(assets/'lab10_blend_eclipse_live_16.png').convert('RGB')
    background=Image.open(assets/'lab10_mpc_02.png').convert('RGB')
    m=json.loads((assets/'UI44_ASSET_MANIFEST.json').read_text())
    assert source.size==b.ORIGINAL_SIZE
    assert strip.size==(613,392*16)
    assert background.size==(1280,628)
    assert strip.height<=8192, 'filmstrip exceeds existing UI31 size gate'
    assert m['source_sha256']==sha(approved.read_bytes())
    assert m['base_sha256']==sha(lab10.read_bytes())
    assert m['strip']['sha256']==sha((assets/'lab10_blend_eclipse_live_16.png').read_bytes())
    assert m['background']['sha256']==sha((assets/'lab10_mpc_02.png').read_bytes())
    assert tuple(m['shifts'])==b.SHIFTS
    assert all(a<=v for a,v in zip(b.SHIFTS,b.SHIFTS[1:]))
    assert b.SHIFTS[7]==b.SHIFTS[8]==0
    assert b.SHIFTS[0]<0 and b.SHIFTS[-1]>0
    bb=np.array(background);oldarray=np.array(old)
    assert np.array_equal(bb[:110],oldarray[:110]),'Original tabs replaced'
    assert np.array_equal(bb[:,996:],oldarray[:,996:]),'Original Q-Link panel replaced'
    assert np.array_equal(bb[-2:,:996],oldarray[-2:,:996]),'Original outer border replaced'
    assert np.max(bb[225:570,250:800])<255
    frames=np.array(strip).reshape(16,392,613,3)
    assert np.array_equal(frames[7],frames[8]),'at 50% two filmstrip bins must be same total eclipse'
    assert all(not np.array_equal(frames[i],frames[i+1]) for i in range(15) if i!=7)
    for i,dx in enumerate(b.SHIFTS):
        # Planet centre must carry the identical source pixel while it moves.
        rgb=frames[i,196,int(613/2+dx)]
        expected=np.asarray(source)[int(b.PLANET[1]),int(b.PLANET[0])]
        assert np.max(abs(rgb.astype(int)-expected.astype(int)))<10,(i,rgb,expected)
        # Image bounds must not cut a rectangular edge across the celestial sphere.
        assert np.max(abs(frames[i,:,0].astype(int)-bb[178:570,192].astype(int)))<3,(i,'left seam')
        assert np.max(abs(frames[i,:,-1].astype(int)-bb[178:570,804].astype(int)))<3,(i,'right seam')
    # At central frames, planet centre is dark and the cyan rim is visible.
    assert np.mean(frames[7,180:205,295:318])<110
    assert np.mean(frames[0,180:205,450:465,2])>np.mean(frames[0,180:205,450:465,0]),'sun not blue'
    # Four corners of visual frame should remain dark, not rectangular patches.
    assert np.max(np.mean(frames[:,-12:,:12],axis=(1,2,3)))<30
    print('PASS 16 frames 613×392, strip 613×6272, authored source digest, centre eclipse, smooth independent planet movement')
    print('PASS no left/right hard vertical clipping, black space without ghosts, original tabs/Q-Link panel/border pixel-perfect')


def test_determinism(approved,lab10,assets):
    with tempfile.TemporaryDirectory() as tmp:
        b.build(approved,lab10,tmp)
        for fname in ['lab10_blend_eclipse_live_16.png','lab10_mpc_02.png']:
            assert sha((Path(tmp)/fname).read_bytes())==sha((Path(assets)/fname).read_bytes()),fname
    print('PASS deterministic repeatable bitwise compilation')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--approved',type=Path)
    ap.add_argument('--lab10-background',type=Path)
    ap.add_argument('--asset-dir',type=Path)
    ap.add_argument('--tui',type=Path)
    ap.add_argument('--qlinks',type=Path)
    ap.add_argument('--no-rebuild',action='store_true')
    args=ap.parse_args()
    if args.tui and args.qlinks:
        inspect_tui(args.tui,args.qlinks)
    elif args.tui or args.qlinks:
        ap.error('--tui and --qlinks must be supplied together')
    if args.asset_dir or args.approved or args.lab10_background:
        if not all([args.asset_dir,args.approved,args.lab10_background]):
            ap.error('private asset tests require --approved, --lab10-background, --asset-dir')
        test_assets(args.approved,args.lab10_background,args.asset_dir)
        if not args.no_rebuild:test_determinism(args.approved,args.lab10_background,args.asset_dir)
    elif not args.tui:
        ap.error('supply --tui/--qlinks for CI or private asset test arguments')

if __name__=='__main__':main()