#!/usr/bin/env python3
"""Relocate only the 7.1 KiB UI/audio snapshot to SDK cache RAM, preserving DSP and all parameters.
Refuse the patch if the exact declaration or build memory budget differs.
Emulator experiment ONLY. Never alias unrelated SDK buffers.
"""
from pathlib import Path
import re,sys
if len(sys.argv)!=2: raise SystemExit("usage: reclaim_snapshot_cache_v12.py SDK_ROOT")
p=Path(sys.argv[1])/"app/biomech/biomech_sdk_port.c"
s=p.read_text()
lines=s.splitlines(keepends=True)
found=[]
for i,line in enumerate(lines):
 if re.search(r'\bstatic\b.*\bsnapshot\b',line) and re.search(r'\bBRSDK_STATIC\b',line) and ';' in line:
  found.append(i)
if len(found)!=1:
 raise SystemExit(f"SNAPSHOT_RELOCATION_REFUSED: expected one static snapshot declaration, found {len(found)}; inspect source before modifying")
i=found[0];line=lines[i]
match=re.search(r'\bBRSDK_STATIC\b',line)
assert match
lines[i]=line[:match.start()]+'__attribute__((section(".memp_memory_x"),aligned(32)))'+line[match.end():]
p.write_text("".join(lines))
print("BR3_V12_MOVED_ONLY_SNAPSHOT_TO_CACHE",line.strip())
