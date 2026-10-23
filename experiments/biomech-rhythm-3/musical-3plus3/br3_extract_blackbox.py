#!/usr/bin/env python3
"""Extract BR3 fixed native blackbox from fm1-emu JSON RAM snapshot.
No OCR and no dependency on unverified symbol addresses.
"""
import argparse, base64, json, struct, pathlib
p=argparse.ArgumentParser()
p.add_argument('blackbox_json',type=pathlib.Path)
a=p.parse_args()
data=json.loads(a.blackbox_json.read_text())
raw=data.get('ram_base64') or data.get('ram') or data.get('memory_base64')
if raw is None:
    raise SystemExit('No RAM base64 field. Export the complete emulator BLACK BOX.')
if isinstance(raw,dict):raw=raw.get('base64')
ram=base64.b64decode(raw)
needle=b'BR3BBX01'
off=ram.find(needle)
if off<0:raise SystemExit('No BR3BBX01 marker; this is not a BIOMECH3 direct CPU1 build.')
fields='schema build_tag events_written0 events_written1 head0 head1 jobs_sent jobs_done jobs_bad job_timeouts fallback_count dma_ok dma_missed cpu0_last_stage cpu1_last_stage cpu0_last_pc cpu1_last_pc last_job last_tick last_wait_ticks max_wait_ticks last_error'.split()
values=struct.unpack_from('<'+len(fields)*'I',ram,off+8)
result=dict(zip(fields,values))
result['ram_offset']=off
result['events']=[]
base=off+8+4*len(fields)
for core_id in range(2):
    for i in range(32):
        tick,seq,core,stage,arg0,arg1=struct.unpack_from('<6I',ram,base+(core_id*32+i)*24)
        if stage:result['events'].append(dict(tick=tick,seq=seq,core=core,stage=stage,arg0=arg0,arg1=arg1))
result['events'].sort(key=lambda x:(x['tick'],x['core']))
print(json.dumps(result,indent=2))
