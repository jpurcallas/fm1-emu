#!/usr/bin/env python3
"""BIOMECH v27: read-only exact disassembly of verified guest writer PC.
The FWSC remains v19 SHA-pinned. This script does NOT change its code.
"""
import sys,re,subprocess
if len(sys.argv)!=4:raise SystemExit("usage: inspect_taskq_writer_v27.py SDK_ELF OBJDUMP NM")
elf,ob,nm=sys.argv[1:]
pc=0x0201ee7e
syms=[]
for l in subprocess.check_output([nm,"-an",elf],text=True).splitlines():
 m=re.fullmatch(r"([0-9a-fA-F]{8})\s+([A-Za-z])\s+(\S+)",l.strip())
 if m:syms.append((int(m.group(1),16),m.group(2),m.group(3)))
syms.sort()
near=[z for z in syms if z[0]<=pc][-15:]
after=[z for z in syms if z[0]>pc][:10]
print("BR3_V27_ZERO_WRITER_PC",hex(pc))
print("BR3_V27_SYMBOLS_BEFORE",near)
print("BR3_V27_SYMBOLS_AFTER",after)
lines=subprocess.check_output([ob,"-d",elf],text=True,errors="replace").splitlines()
matches=[i for i,l in enumerate(lines) if re.match(r"\s*201ee7e:\s+",l,re.I)]
if len(matches)!=1:raise RuntimeError("zero-writer instruction absent or ambiguous "+str(matches))
i=matches[0]
print("BR3_V27_ZERO_WRITER_WINDOW_BEGIN")
print("\n".join(lines[max(0,i-55):i+55]))
print("BR3_V27_ZERO_WRITER_WINDOW_END")
name=near[-1][2]
print("BR3_V27_OWNER_SYMBOL",name)
for i,l in enumerate(lines):
 if ("<"+name+" :" in l or "<"+name+"+" in l) and "call" in l:
  print("BR3_V27_OWNER_CALLSITE",lines[max(0,i-3):i+5])
