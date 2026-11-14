#!/usr/bin/env python3
"""Regression guard: a fresh REminiSCENT instance starts as acoustic A, dry."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
contract=(root/"src/ui07_contract_generated.hpp").read_text()
engine=(root/"src/engine.hpp").read_text()
plugin=(root/"src/REminiSCENTMPC.cpp").read_text()
def field(name):
    m=re.search(r'\{"'+re.escape(name)+r'","(?:bool|int|choice)",[^\n]*?\}',contract)
    if not m: raise AssertionError("Field absent: "+name)
    pieces=re.match(r'\{"[^"]+","[^"]+",([^,]+),([^,]+),([^,]+),',m.group(0))
    if not pieces: raise AssertionError("Field malformed: "+name)
    return float(pieces.group(3))
required={
 "a":0, "onA":1, "onB":0, "params.acousticBlend":0,
 "params.masterBlend":0,"params.oscLevel":0,"params.memoryMix":0,
 "params.resoMix":0,"params.filterMix":0,"params.grainMix":0,
 "params.acousticNoise":0,
 "freeze":0,"reverse":0,"tide":0,
 "characterOn.distortion":0,"characterOn.tape":0,
 "characterOn.vinyl":0,"characterOn.crush":0,
 "sendOn.delay":0,"sendOn.reverb":0,"sendOn.mod1":0,"sendOn.mod2":0,
 "modOn.lfo1":0,"modOn.lfo2":0,"modOn.env2":0,
}
for name,expected in required.items():
    actual=field(name)
    assert actual==expected, f"{name}: expected {expected}, got {actual}"
assert "bool acousticA=true,acousticB=false,oscOn=false;" in engine
assert "float acousticBlend=0.f, masterBlend=0.f, oscLevel=0.f;" in engine
assert "e.setParameter(rem::ParameterId::OscOn,(v[28]>0.f)?1.f:0.f);" in plugin
assert 'e.setParameter(rem::ParameterId::LowPassOn,(v[51]/127.f)>0.f?1.f:0.f);' in plugin
assert "p.grainMix=(v[55]/127.f);" in plugin
assert "p.resoMix=(v[47]/127.f);" in plugin
# Default changes must NOT be reapplied on prepare/reset; saved project state wins.
for fn in ("void prepare(", "void reset("):
    idx=plugin.find(fn); assert idx>=0
    body=plugin[idx:idx+800]
    assert "onB" not in body and "masterBlend" not in body
print("PASS acoustic-only start: 26 default checks, OSC gate and state restoration guard")
