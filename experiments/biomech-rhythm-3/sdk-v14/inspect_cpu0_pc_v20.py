#!/usr/bin/env python3
"""Read-only disassembly of the exact v19 SHA-pinned ELF at stalled CPU0 PC.
No firmware/SDK edits. Print surrounding instructions, containing ELF symbols.
"""
from pathlib import Path
import re
import subprocess
import sys
if len(sys.argv)!=4:
    raise SystemExit("usage: inspect_cpu0_pc_v20.py ELF PI32_OBJDUMP PI32_NM")
elf, objdump, nm=map(str,sys.argv[1:])
target=0x0202b378
syms=[]
for ln in subprocess.check_output([nm,"-an",elf],text=True).splitlines():
    m=re.match(r"^([0-9a-fA-F]{8})\s+([tTwW])\s+(.+)$",ln.strip())
    if m:syms.append((int(m[1],16),m[2],m[3]))
syms.sort()
near=[x for x in syms if x[0]<=target][-12:]
following=[x for x in syms if x[0]>target][:6]
print("BR3_V20_STALLED_PC",hex(target))
print("BR3_V20_NEAREST_TEXT_SYMBOLS_BEFORE",near)
print("BR3_V20_NEAREST_TEXT_SYMBOLS_AFTER",following)
text=subprocess.check_output([objdump,"-d",elf],text=True,errors="replace")
lines=text.splitlines()
at=[i for i,l in enumerate(lines) if re.match(r"^\s*202b378:\s+",l,re.I)]
print("BR3_V20_OBJDUMP_TARGET_COUNT",len(at))
if len(at)!=1:raise RuntimeError("Stalled CPU0 PC missing or duplicate in linked disassembly")
i=at[0]
print("BR3_V20_INSTRUCTION_WINDOW_BEGIN")
print("\n".join(lines[max(0,i-35):min(len(lines),i+36)]))
print("BR3_V20_INSTRUCTION_WINDOW_END")
