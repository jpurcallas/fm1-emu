#!/usr/bin/env python3
import re,sys,subprocess
nm=subprocess.check_output([sys.argv[2],"-an",sys.argv[1]],text=True)
ob=subprocess.check_output([sys.argv[3],"-d",sys.argv[1]],text=True)
symbols=[]
for l in nm.splitlines():
 m=re.match(r"^([0-9a-fA-F]{8})\s+[A-Za-z]\s+(\S+)$",l)
 if m:symbols.append((int(m[1],16),m[2]))
for target in (0x02018bd2,0x0201eafc,0x0201c1b4,0x02000522):
 nearby=[(hex(a),n) for a,n in symbols if a<=target][-6:]
 tail=[(hex(a),n) for a,n in symbols if a>target][:4]
 print("BR3_V30_OWNER",hex(target),nearby,tail)
 lines=ob.splitlines()
 indexes=[i for i,line in enumerate(lines) if re.match(r"\s*"+format(target,"x")+r":\s+",line)]
 for ix in indexes:print("BR3_V30_OWNER_WINDOW_BEGIN",hex(target),"\\n".join(lines[max(0,ix-18):ix+15]),"BR3_V30_OWNER_WINDOW_END")
