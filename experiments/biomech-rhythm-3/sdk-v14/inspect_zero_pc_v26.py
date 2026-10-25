#!/usr/bin/env python3
"""Only inspect the exact linked SDK ELF around v26's first zeroing PC."""
import re,subprocess,sys
elf,objdump,nm=sys.argv[1:]
target=0x0201ee7e
symbols=[]
for ln in subprocess.check_output([nm,"-an",elf],text=True).splitlines():
 m=re.match(r"^([0-9a-fA-F]+)\s+([tTwW])\s+(\S+)",ln)
 if m:symbols.append((int(m[1],16),m[3]))
before=[x for x in symbols if x[0]<=target][-8:]
after=[x for x in symbols if x[0]>target][:6]
print("BR3_V26_ZERO_PC_SYMBOLS",before,after)
lines=subprocess.check_output([objdump,"-d",elf],text=True,errors="replace").splitlines()
matches=[i for i,line in enumerate(lines) if re.match(r"^\s*201ee7e:\s+",line,re.I)]
print("BR3_V26_PC_MATCHES",len(matches))
if len(matches)!=1:raise SystemExit("wrong linked ELF")
i=matches[0]
print("BR3_V26_ZERO_PC_WINDOW_BEGIN")
print("\n".join(lines[max(0,i-35):i+32]))
print("BR3_V26_ZERO_PC_WINDOW_END")
