#!/usr/bin/env python3
"""Stage the exact author-approved BIOMECH V14 UI/MIDI/seq/FX/ALNK adapter.
Only in disposable GH Actions checkout of pinned FM1 Open SDK V14.
Never alter master, original SDK checkout, or BIOMECH 2.
"""
import base64,hashlib,io,pathlib,subprocess,sys,tarfile,shutil
if len(sys.argv)!=3:raise SystemExit("stage_adapter_v04.py ORIGINAL_SDK_COPY BR3_BRANCH_ROOT")
ROOT=pathlib.Path(sys.argv[1]).resolve();REPO=pathlib.Path(sys.argv[2]).resolve()
PAY=REPO/"experiments/biomech-rhythm-3/sdk-v14/overlay-v04-adapter.tar.gz.base64"
blob=base64.b64decode(PAY.read_text().strip(),validate=True)
EXPECTED="7688d7071c1b5c4c8dbe911f2358caf544fa2a9756979f327ef5cc4eed4fa3f7"
actual=hashlib.sha256(blob).hexdigest()
if actual!=EXPECTED:raise SystemExit("BR3 v0.4 adapter integrity FAILED "+actual)
patched=[]
with tarfile.open(fileobj=io.BytesIO(blob),mode="r:gz") as tar:
 for entry in tar.getmembers():
  if not entry.isfile():raise SystemExit("Unexpected adapter member type "+entry.name)
  rel=pathlib.PurePosixPath(entry.name)
  if rel.is_absolute() or ".." in rel.parts:raise SystemExit("Traversal in overlay "+entry.name)
  data=tar.extractfile(entry).read()
  if entry.name.startswith("patches/"):
   if not entry.name.endswith(".patch"):raise SystemExit("bad patch "+entry.name)
   target=entry.name[len("patches/"):-6]
   p=subprocess.run(["patch","--batch","-p1","--forward"],input=data,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   if p.returncode:raise SystemExit("SDK patch failed "+target+"\n"+p.stdout.decode(errors="replace"))
   patched.append(target)
  else:
   dest=ROOT/entry.name
   if dest.exists():raise SystemExit("refusing to overwrite stock file "+entry.name)
   dest.parent.mkdir(parents=True,exist_ok=True)
   dest.write_bytes(data)
   patched.append(entry.name)
# Reuse the exact, versioned six-track CPU0/CPU1 music and blackbox files in
# this same repository. No placeholder DSP, fake panel, or substituted FX.
engine=REPO/"experiments/biomech-rhythm-3/musical-3plus3"
for name in ("biomech.c","biomech.h","biomech_sdk_profile.h","br3_blackbox.c",
             "br3_blackbox.h","br3_cpu1_runtime.c","br3_cpu1_runtime.h",
             "br3_cpu1_entry.S","ram_attr.h"):
 src=engine/name;dest=ROOT/"app/biomech"/name
 if not src.is_file():raise SystemExit("missing BR3 engine "+name)
 shutil.copy2(src,dest)
 patched.append("app/biomech/"+name)
# The C99 DSP unchanged: panel/audio on V14, strict non-ownership probe
# permits full serial playback ONLY in this specifically labelled lab build.
print("BR3_V14_STAGED",len(patched),"paths","adapter_sha256",actual)
for path in patched:print("BR3_V14_STAGE_FILE",path)
