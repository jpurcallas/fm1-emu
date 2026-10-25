#!/usr/bin/env python3
"""BIOMECH3 v17 post-link CPU1 SDK worker hook: only for emulator experiments.

One verified PI32v2 six-byte CALL is replaced, plus one explicitly marked
RAM-data pointer. Refuse ALL changes unless the exact linked ELF satisfies
the worker/call target/return opcode/section/sentinel checks.
Never patch the original SDK source, musical engine, master or FM1 hardware.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import re
import struct
import subprocess
import sys

SENTINEL = 0xB330C017
WORKER = "fm1_r_2c729ca92be9"
ORIGINAL = "fm1_r_e7d3da61dac2"
WRAPPER = "br3_coop_sdk_worker_wrapper"
ORIGINAL_PTR = "br3_coop_original_sdk_worker"

def u16(buf: bytes, offset: int) -> int:
    return struct.unpack_from("<H", buf, offset)[0]

def u32(buf: bytes, offset: int) -> int:
    return struct.unpack_from("<I", buf, offset)[0]

def read_sections(buf: bytes) -> list[dict]:
    if buf[:4] != b"\x7fELF" or buf[4] != 1 or buf[5] != 1:
        raise RuntimeError("expected ELF32 little endian")
    shoff, entsize, count, names_idx = u32(buf, 32), u16(buf, 46), u16(buf, 48), u16(buf, 50)
    if entsize != 40 or count < 3 or names_idx >= count or shoff+count*entsize > len(buf):
        raise RuntimeError("invalid ELF section table")
    sections = []
    for i in range(count):
        parts = struct.unpack_from("<10I",buf,shoff+i*entsize)
        name,type_,flags,addr,offset,size,*_ = parts
        if offset+size > len(buf) and type_ != 8:
            raise RuntimeError("section out of file bounds")
        sections.append(dict(name_idx=name,type=type_,flags=flags,addr=addr,offset=offset,size=size))
    st = sections[names_idx]
    name_bytes=buf[st["offset"]:st["offset"]+st["size"]]
    for s in sections:
        pos=s["name_idx"]
        if pos >= len(name_bytes):
            raise RuntimeError("invalid ELF section name offset")
        s["name"] = name_bytes[pos:name_bytes.find(b"\0",pos)].decode("ascii")
    return sections

def at(sections: list[dict], addr: int, length: int, allowed: tuple[str,...]):
    found=[s for s in sections if s["name"] in allowed and s["type"]==1 and
           s["addr"]<=addr and addr+length<=s["addr"]+s["size"]]
    if len(found)!=1:raise RuntimeError(f"address {addr:#010x} is not uniquely inside {allowed}")
    s=found[0]
    return s["offset"]+addr-s["addr"],s["name"]

def symbol_table(nm: str, elf: Path) -> dict[str,int]:
    out=subprocess.check_output([nm,"-n",str(elf)],text=True)
    names={}
    for line in out.splitlines():
        m=re.fullmatch(r"([0-9a-fA-F]{8})\s+([A-Za-z])\s+(\S+)",line.strip())
        if m:
            name=m.group(3)
            names.setdefault(name,[]).append(int(m.group(1),16))
    required=(WORKER,ORIGINAL,WRAPPER,ORIGINAL_PTR)
    for name in required:
        if len(names.get(name,[]))!=1:
            raise RuntimeError("missing or duplicate symbol "+name)
    return {name:names[name][0] for name in required}

def patch(elf: Path,nm: str) -> None:
    before=elf.read_bytes()
    sections=read_sections(before)
    syms=symbol_table(nm,elf)
    worker,original,wrapper=(syms[x] for x in (WORKER,ORIGINAL,WRAPPER))
    for x in (worker, original, wrapper):
        if x & 1:raise RuntimeError("unaligned PI32 code symbol")
        at(sections,x,2,(".text",))
    matches=[]
    for pc in range(worker, worker+0x40,2):
        try:offset,_=at(sections,pc,8,(".text",))
        except RuntimeError:continue
        if before[offset:offset+2] != b"\x80\xff":continue
        relative=struct.unpack_from("<i",before,offset+2)[0]
        target=(pc+6+relative)&0xffffffff
        if target==original:
            matches.append((pc,offset))
    if len(matches)!=1:
        raise RuntimeError(f"expected ONE SDK-worker direct CALL; found {len(matches)}")
    pc,loc=matches[0]
    if before[loc+6:loc+8] != b"\xf7\x9c":
        raise RuntimeError("SDK worker CALL not followed by original goto -8")
    ptrloc,section=at(sections,syms[ORIGINAL_PTR],4,(".ram0_data",))
    if u32(before,ptrloc)!=SENTINEL:
        raise RuntimeError("SDK worker pointer sentinel missing")
    if original==wrapper or original==0 or wrapper==0 or pc==wrapper:
        raise RuntimeError("invalid original/wrapper target")
    displacement=wrapper-pc-6
    if not -(1<<31)<=displacement < (1<<31):
        raise RuntimeError("wrapper outside 32-bit relative CALL")
    changed=bytearray(before)
    changed[loc:loc+6]=b"\x80\xff"+struct.pack("<i",displacement)
    changed[ptrloc:ptrloc+4]=struct.pack("<I",original)
    assert changed[loc+6:loc+8]==b"\xf7\x9c"
    assert changed[loc+2:loc+6]!=before[loc+2:loc+6]
    # PROOF: all bytes outside exact 6-byte CALL and 4-byte RAM pointer identical.
    changed_offsets=[i for i,(a,b) in enumerate(zip(before,changed)) if a!=b]
    accepted=set(range(loc,loc+6))|set(range(ptrloc,ptrloc+4))
    if not changed_offsets or any(i not in accepted for i in changed_offsets):
        raise RuntimeError("postlink modified bytes outside guarded sites")
    elf.write_bytes(changed)
    verify=elf.read_bytes()
    if verify!=changed:raise RuntimeError("postlink readback mismatch")
    print("BR3_V17_HOOK_VERIFIED",{
      "sdk_worker":hex(worker),"original_sdk_service":hex(original),
      "cpu1_callsite":hex(pc),"old_call":before[loc:loc+6].hex(),
      "new_call":verify[loc:loc+6].hex(),"trampoline":hex(wrapper),
      "sdk_ptr_ram":hex(syms[ORIGINAL_PTR]),"ptr_section":section,
      "modified_byte_count":len(changed_offsets),
      "elf_before_sha256":hashlib.sha256(before).hexdigest(),
      "elf_after_sha256":hashlib.sha256(verify).hexdigest(),
      "status":"SDK-FIRST CALLSITE PATCHED, RUNTIME NOT YET VALIDATED"})
if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("usage: patch_coop_v17.py sdk.elf pi32v2-nm")
    patch(Path(sys.argv[1]),sys.argv[2])
