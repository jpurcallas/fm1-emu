#!/usr/bin/env python3
"""Static SDK V14 taskq ownership/initialization audit. NO executable patches."""
import subprocess,sys,re
if len(sys.argv)!=4:raise SystemExit("usage: inspect_taskq_init_v24.py sdk.elf PI32_OBJDUMP PI32_NM")
elf,objdump,nm=sys.argv[1:]
dis=subprocess.check_output([objdump,"-d",elf],text=True,errors="replace").splitlines()
names=subprocess.check_output([nm,"-an",elf],text=True).splitlines()
head=[x for x in names if re.search(r"\shead\.792$",x)]
print("BR3_V24_HEAD_SYMBOL",head)
if len(head)!=1:raise SystemExit("head.792 symbol ambiguous")
addr=int(head[0].split()[0],16)
if addr!=0x01c6d21c:raise SystemExit("taskq head moved; do not interpret stale addresses")
keys=[r"head\.792",r"<get_taskq",r"<os_taskq",r"<__os_taskq",
      r"<os_task_create",r"<os_taskq_create",r"<task_create",r"<os_sem",r"<xQueueCreate"]
matches=[]
for i,line in enumerate(dis):
 if any(re.search(k,line,re.I) for k in keys):
  matches.append(i)
print("BR3_V24_TASKQ_REFERENCE_COUNT",len(matches))
def func_label(idx):
 for i in range(idx,-1,-1):
  line=dis[i].strip()
  if line.endswith(":") and not re.match(r"^[0-9a-fA-F]+:",line):
   return line
 return "unknown"
for ix in matches[:95]:
 print("BR3_V24_REFERENCE",repr(dis[ix]),"IN",func_label(ix))
 for line in dis[max(0,ix-4):min(len(dis),ix+6)]:
  print("  ",line)
print("BR3_V24_FUNCTION_DISASSEMBLY_FOCUSED")
for fn in ("os_init","os_start","os_task_create","os_task_create_static","get_taskq",
           "put_taskq","__os_taskq_post","os_taskq_post_type"):
    candidates=[i for i,ln in enumerate(dis) if ln.strip()==fn+":"]
    if len(candidates)!=1:
        print("BR3_V24_FUNCTION_MISSING_OR_AMBIGUOUS",fn,candidates)
        continue
    i=candidates[0]
    j=i+1
    while j<len(dis) and not (dis[j].strip().endswith(":")
                               and not re.match(r"^[0-9a-fA-F]+:",dis[j].strip())):
        j+=1
    print("BR3_V24_FUNCTION_BEGIN",fn,"lines",j-i)
    print("\n".join(dis[i:min(j,i+110)]))
    print("BR3_V24_FUNCTION_END",fn)
print("BR3_V24_RELEVANT_NM_SYMBOLS")
for line in names:
 if re.search(r"taskq|task_create|task_init|os_init|os_start|queue_create|list_init|head\.792",line,re.I):
  print(line)
