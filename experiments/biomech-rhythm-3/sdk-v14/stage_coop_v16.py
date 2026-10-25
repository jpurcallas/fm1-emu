#!/usr/bin/env python3
"""Wire experimental cooperative bridge into staged V14 application.
This does NOT patch the SDK worker or claim CPU1 ownership.
Strict anchors prevent unknown firmware changes.
"""
from pathlib import Path
import sys
if len(sys.argv)!=2: raise SystemExit("usage: stage_coop_v16.py SDK_ROOT")
p=Path(sys.argv[1])/"app/biomech/biomech_sdk_port.c"
s=p.read_text()
marker='#include "biomech_sdk_port.h"'
assert s.count(marker)==1
s=s.replace(marker,marker+'\nextern void br3_coop_init(void);\nextern void br3_coop_attach_if_alive(void);',1)
marker='    br_fm1_runtime_init(&runtime,&effects);'
assert s.count(marker)==1
s=s.replace(marker,marker+'\n    br3_coop_init(); /* only initializes mailbox; does not reset CPU1 */',1)
marker='int BR_RAMCODE biomech_sdk_audio(int32_t *out,unsigned frames){'
assert s.count(marker)==1
s=s.replace(marker,marker+'\n    br3_coop_attach_if_alive(); /* inert until audited SDK worker handshake */',1)
p.write_text(s)
print("BR3_V16_STAGED_COOP_NO_CPU1_WORKER_HOOK",p)
