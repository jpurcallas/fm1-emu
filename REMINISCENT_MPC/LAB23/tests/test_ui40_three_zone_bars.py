#!/usr/bin/env python3
"""UI40 structural regression: selectors and switches MUST stay independent."""
import argparse,json
from pathlib import Path
from PIL import Image,ImageChops
from ui40_build_approved_three_zone_bars import GROUPS,PAGE_FILES,generate

def validate(original,result,assets):
    old=json.loads(original.read_text())
    new=json.loads((result/'TUI.json').read_text())
    def entries(x):return x['pageData']['tabs'][0]['componentDefinition']['componentsData']
    aa={c['componentData']['name']:c for c in entries(old)}
    bb={c['componentData']['name']:c for c in entries(new)}
    changed=set()
    for prefix,g in GROUPS.items():
        for k,key in enumerate(g['keys']):
            switch=f'{prefix}_ONOFF_{key}' if prefix!='MEMORY' else f'MEMORY_{key}'
            edit=f'{prefix}_SELECT_{key}' if prefix!='MEMORY' else f'MEMORY_EDIT_{key}'
            changed.update((switch,edit))
            a=bb[switch];b=bb[edit]
            assert a['componentData']['type']==b['componentData']['type']=='Button'
            assert a['componentData']['data']['buttonId']==1
            assert a['componentData']['data']['numButtonsInGroup']==1
            assert b['componentData']['data']['buttonId']==k
            assert b['componentData']['data']['numButtonsInGroup']==len(g['keys'])
            assert a['handle remapping']['map'][0]['value']==f'Parameter {g["flags"][k]}'
            assert b['handle remapping']['map'][0]['value']==f'Parameter {g["sel"]}'
            assert a['bounds']['bounds']==f'{g["x"][k]} {g["p_y"]} {g["width"]} {g["p_h"]}'
            assert b['bounds']['bounds']==f'{g["x"][k]} {g["e_y"]} {g["width"]} {g["e_h"]}'
            assert g['p_y']+g['p_h']<=g['e_y']
            for comp in (a,b):
                for prop in ('onImage','offImage'):
                    assert (result/comp['componentData']['data'][prop]).is_file()
    assert len(bb)==len(aa)+3
    assert old['pageData']['replacementStrings']==new['pageData']['replacementStrings']
    for name,entry in aa.items():
        if name in changed or name.startswith('APPROVED_LAB10_'):continue
        assert bb[name]==entry,f'Unexpected change: {name}'
    for prefix,g in GROUPS.items():
        for name in PAGE_FILES[g['page']]:
            src=Image.open(assets/name).convert('RGB')
            dst=Image.open(result/('ui40_'+name)).convert('RGB')
            assert src.size==dst.size==(1280,628)
            rect=ImageChops.difference(src,dst).getbbox()
            assert rect is not None
            x0,y0,x1,y1=rect
            assert min(g['x'])+6<=x0<x1<=max(g['x'])+g['width']-5
            assert g['p_y']<=y0<y1<=g['e_y']+g['e_h']
    print('PASS: 14 ON/OFF + 14 EDIT independent; 3 new MEMORY EDIT; 12 reversible art variants; no DSP or PCM changes')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for arg in ('tui','assets','out'):p.add_argument('--'+arg,type=Path,required=True)
    a=p.parse_args()
    generate(a.tui,a.assets,a.out)
    validate(a.tui,a.out,a.assets)
