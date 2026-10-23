#!/usr/bin/env python3
"""External passive reader of REminiSCENT 2 LAB trace RAM snapshots.
Does not run or call target firmware. Can scan raw RAM after a freeze.
HOST TESTS use synthetic PC/SP, not real PI32v2 exception state.
"""
import argparse
import json
import struct
from pathlib import Path

MAGIC = 0x52325442
EVENTS = ['?', 'BOOT0','C1_ENTRY','C1_ALIVE','JOB_ISSUE','JOB_BEGIN',
          'JOB_END','JOB_JOIN','DMA_COPY','LAST_GOOD','BAD_MAILBOX','TIMEOUT',
          'FAULT','PC_GUARD','PARKED','REBOOT','DMA_LATE']
FMT = '<16I'
FIELDS = ['commit','cycle','block','job','event','pc','sp','wait_ticks',
          'dma_half','dma_deadline','dma_copy_tick','audio_late',
          'last_valid_block','fault_reason','payload_crc','extra']

def rol7(x):
    return ((x << 7) | (x >> 25)) & 0xFFFFFFFF

def record_crc(v):
    h = 0xA72D19E5
    for k in FIELDS[1:14] + ['extra']:
        h = rol7(h) ^ v[k]
    return h

def parse(buf):
    marker = struct.pack('<I', MAGIC)
    base = buf.find(marker)
    if base < 0:
        raise ValueError('R2TB marker not found in memory snapshot')
    if base + 128 > len(buf):
        raise ValueError('R2TB header truncated')
    magic, schema, nbytes, enabled = struct.unpack_from('<4I',buf,base)
    if magic != MAGIC or schema != 1:
        raise ValueError('unsupported or damaged trace header')
    if nbytes < 128 or base+nbytes > len(buf):
        raise ValueError('trace incomplete or memory window too short')
    firmware = bytes(buf[base+16:base+48]).split(b'\0')[0].decode('ascii','replace')
    sha = bytes(buf[base+48:base+113]).split(b'\0')[0].decode('ascii','replace')
    ringbytes = (nbytes-128)//2
    slots = (ringbytes-64)//64
    if slots < 1 or slots > 1024 or 128+2*(64+64*slots) != nbytes:
        raise ValueError('trace size not compatible with two 64-byte rings')
    cores = []
    for core in range(2):
        offset = base + 128 + core*ringbytes
        head,overflow = struct.unpack_from('<II',buf,offset)
        if head>1_000_000_000:
            raise ValueError('implausible head counter')
        start = max(0,head-slots)
        events=[]; incomplete=0;badcrc=0
        for pos in range(start,head):
            data=struct.unpack_from(FMT,buf,offset+64+(pos%slots)*64)
            r=dict(zip(FIELDS,data))
            if r['commit']!=2*(pos+1):
                incomplete+=1
                continue
            if r['payload_crc']!=record_crc(r):
                badcrc+=1
                continue
            r['event_name']=EVENTS[r['event']] if r['event']<len(EVENTS) else 'UNKNOWN'
            events.append(r)
        cores.append({'core':core,'head':head,'overflow':overflow,
                      'incomplete':incomplete,'bad_crc':badcrc,'events':events})
    return {'firmware':firmware,'build_sha256':sha,'schema':schema,
            'memory_offset':base,'recorder_bytes':nbytes,'enabled':enabled,'cores':cores}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('snapshot',type=Path,help='raw RAM snapshot (emulator or host fixture)')
    ap.add_argument('--output',type=Path,help='JSON output path')
    a=ap.parse_args()
    result=parse(a.snapshot.read_bytes())
    s=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if a.output:a.output.write_text(s)
    else:print(s,end='')
