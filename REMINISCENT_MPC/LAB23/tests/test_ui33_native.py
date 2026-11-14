#!/usr/bin/env python3
"""Verifiable static checks; does not attest MPC hardware or approve overlays."""
import collections,hashlib,json,sys,zipfile
from pathlib import Path
old=Path(sys.argv[1]);new=Path(sys.argv[2]);root='Yeti Fingers - VST - REminiSCENT/Plugin Skins/'
with zipfile.ZipFile(old) as baseline, zipfile.ZipFile(new) as candidate:
    assert candidate.testzip() is None
    oldnames=set(baseline.namelist());newnames=set(candidate.namelist())
    for n in oldnames-{root+'TUI.json'}:
        assert candidate.read(n)==baseline.read(n),n
    ui=json.loads(candidate.read(root+'TUI.json'))
    cs=ui['pageData']['tabs'][0]['componentDefinition']['componentsData']
    types=collections.Counter(c['componentData']['type'] for c in cs)
    assert len(cs)==139,types
    assert set(types)<={'Image','Button','Knob','Slider','Label','Envelope','Plotter'},types
    assert types['Button']==48 and types['Knob']==49 and types['Label']==2
    assert len([x for x in cs if x['componentData']['name'].startswith('APPROVED_LAB10_')])==19
    assert not any('solaris' in x['componentData']['name'].lower() for x in cs)
    assert not any('solaris' in n.lower() for n in newnames)
    assert len([x for x in newnames if x.lower().endswith('.wav')])==254
    assert len([x for x in newnames if x.lower().endswith('.so')])==2
    for c in cs:
        data=c['componentData']; ref=data['data'];typ=data['type'];
        if typ=='Knob':
            assert root+ref['filmStrip'] in newnames,data['name']
            assert c['handle remapping']['map'] and c['handle remapping']['map'][0]['value'].startswith('Parameter '),data['name']
        if typ=='Button':
            assert root+ref['onImage'] in newnames and root+ref['offImage'] in newnames,data['name']
    for id in range(4):
        ptr=next(x for x in cs if x['componentData']['name']==f'QLINK_{id+1}_LAB10_LIVE_POINTER')
        assert ptr['componentData']['type']=='Knob'
        assert ptr['handle remapping']['map'][0]['value']==f'Parameter {113+id}'
    for name in ['ACOUSTIC_POWER_A','ACOUSTIC_POWER_B','MEMORY_FREEZE','MEMORY_REVERSE','MEMORY_TIDE']:
        assert next(x for x in cs if x['componentData']['name']==name)['componentData']['type']=='Button'
    print('PASS: SDK native component families; 55 old pseudo-controls removed; 16 native toggles; Q-Link indicator mappings; original LAB10 rasters, DSP and 254 WAV byte-identical; Solaris absent.')
    print('LIMIT: visual provenance review and real MPC rendering NOT passed.')