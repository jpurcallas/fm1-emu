#!/usr/bin/env python3
"""Read-only native PI32v2 stock-vs-BR3 fifth os_task_create entry owner."""
import pathlib,re,subprocess,sys
binpath=pathlib.Path(sys.argv[1])
nmcmd=sys.argv[2]; objcmd=sys.argv[3]
data=subprocess.check_output([nmcmd,"-an",str(binpath)],text=True)
dis=subprocess.check_output([objcmd,"-d",str(binpath)],text=True)
syms=[]
for l in data.splitlines():
 m=re.match(r"^([a-fA-F0-9]{8})\s+\w\s+(\S+)$",l)
 if m:syms.append((int(m.group(1),16),m.group(2)))
def closest(address):
 before=[(hex(a),n) for a,n in syms if a<=address]
 after=[(hex(a),n) for a,n in syms if a>address]
 return {"previous":before[-6:],"next":after[:5]}
print("BR3_V37_IDENTITY",binpath)
lines=dis.splitlines()
for t in [0x0201c56a,0x02017aac,0x0200744a,0x02018bb2,0x02018c2e]:
 print("BR3_V37_TARGET",hex(t),closest(t))
 for i,l in enumerate(lines):
  m=re.match(r"\s*([a-fA-F0-9]+):",l)
  if m and abs(int(m.group(1),16)-t)<=4:
   print("BR3_V37_AROUND",hex(t),"\\n".join(lines[max(i-22,0):i+20]))
tasksyms=[(hex(a),n) for a,n in syms if "task" in n.lower() or "uart" in n.lower() or "midi" in n.lower() or "control" in n.lower()]
print("BR3_V37_TASK_SYMBOLS",tasksyms[:120])
for i,l in enumerate(lines):
 if "call" in l and ("<os_task_create " in l or "<fm1_control_request " in l):
  print("BR3_V37_TASK_CALLSITE",l.strip()," owner",closest(int(re.match(r"\s*([a-fA-F0-9]+):",l).group(1),16))["previous"][-2:])
