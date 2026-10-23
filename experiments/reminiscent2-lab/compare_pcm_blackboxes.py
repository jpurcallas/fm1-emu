#!/usr/bin/env python3
"""BIOMECH 2 audible control vs REminiSCENT 2 silent target.
Use the JSON exported by experimental emulator branch with audioOutput.
Does not infer physical speaker output, and does not guess missing fields.
"""
import json,sys
from pathlib import Path
def describe(p):
    d=json.loads(Path(p).read_text(encoding='utf-8'))
    a=d.get('audioOutput')
    f=d.get('firmware',{})
    if isinstance(f,dict): name=f.get('name') or f.get('id')
    else:name=f
    result={'file':str(p),'firmware':name or d.get('candidate'),
            'MHz':f.get('mhz') if isinstance(f,dict) else d.get('clockMHz'),
            'halted':(d.get('cpu') or d.get('emulator') or {}).get('halted')}
    if not a or not a.get('enabled'):
        result['host_audio']='NOT RECORDED: use instrumented emulator branch'
        return result
    for key in ('quanta','requestedFrames','renderedFrames','shortQuanta',
        'nonzeroFrames','nonzeroQuanta','silentQuanta','outputPeak',
        'firstNonzeroGuestMs','lastNonzeroGuestMs','wallLateQuanta','worstWorkletMs'):
        result[key]=a.get(key)
    return result
if __name__=='__main__':
    if len(sys.argv)!=3:
        raise SystemExit('usage: python compare_pcm_blackboxes.py BIOMECH_BLACKBOX.json REMINISCENT_BLACKBOX.json')
    reports=[describe(x) for x in sys.argv[1:]]
    print(json.dumps({'control':reports[0],'target':reports[1]},indent=2,ensure_ascii=False))
    a,b=reports
    if 'nonzeroFrames' in a and 'nonzeroFrames' in b:
        if a['nonzeroFrames'] and not b['nonzeroFrames']:
            print('DIFFERENCE: audible control has worklet signal, target has none.')
        elif a['nonzeroFrames'] and b['nonzeroFrames']:
            print('BOTH have PCM at AudioWorklet output; inspect continuity, levels and browser wall time.')
        else:print('NO conclusion: control lacks worklet signal or signal not recorded.')
