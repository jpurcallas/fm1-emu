#!/usr/bin/env python3
"""Reproduce author's exact FM1 Open V14 SDK baseline in native JieLi PI32.
This script links STOCK SDK without any BIOMECH3 DSP: an integration prerequisite,
NOT a musical candidate, not intended for flashing. No changes to vendor SDK.
"""
import hashlib,json,os,pathlib,re,subprocess,sys
if len(sys.argv)!=4: raise SystemExit("build_v14_base.py PINNED_SDK_ROOT TOOLCHAIN_ROOT OUTPUT_ROOT")
ROOT=pathlib.Path(sys.argv[1]).resolve()
TOOL=pathlib.Path(sys.argv[2]).resolve()
BUILD=pathlib.Path(sys.argv[3]).resolve()
SDK=ROOT/"sdk";APP=ROOT/"app";BIN=TOOL/"pi32v2/bin"
BR3_LINK=os.getenv("BR3_LINK_ENGINE","0")=="1"
BR3_SRC=pathlib.Path(__file__).resolve().parents[1]/"musical-3plus3"
BUILD.mkdir(parents=True,exist_ok=True)
OBJ=BUILD/"obj";OBJ.mkdir(exist_ok=True)
GEN=BUILD/"generated";GEN.mkdir(exist_ok=True)
LOG=(BUILD/"build.log").open("w")
def note(s):
 print(s,flush=True);LOG.write(s+"\n");LOG.flush()
def run(argv):
 argv=[str(x) for x in argv]
 p=subprocess.run(argv,cwd=BUILD,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors="replace")
 LOG.write(p.stdout);LOG.flush()
 if p.returncode:
  note("COMMAND_FAILED "+str(p.returncode)+" "+repr(argv[:5]))
  note(p.stdout[-5000:])
  raise RuntimeError("failed "+argv[0])
 return p.stdout
# The user-provided 19 Oct V14 was verified against pinned upstream Git SHA.
PINNED_SHA256={
 "sdk/Build.ps1":"6375b93b57498330895d6b25052f4318c10224d3665d79a5cac4365da1cd844b",
 "sdk/lib/libfm1_engine.a":"cf94df1316d57390499db121ccd9b0375e570160441fc77ae29111fe431725d5",
 "sdk/lib/libc.a":"fcea6ec66162a5173db4626f4c98d63c2873c80ac48c849efbe0fd223fe94a58",
 "sdk/config/linker.ld.in":"f9861aafebf6913ce70bea74e7448769a8def498e1a0bf981281cfd94a3e9b3f",
 "sdk/manifest.json":"23d4354d134675b3d9e0ed92ec53459cf61a1e01c021481c71782dd30b94ba3b"
}
for rel,expected in PINNED_SHA256.items():
 actual=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
 if actual!=expected:raise SystemExit("WRONG V14 REVISION "+rel+": "+actual+" != "+expected)
data=json.loads((SDK/"manifest.json").read_text())
assert data["abi"]==131072
for rel,expected in data["files"].items():
 path=ROOT/rel
 if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
  raise SystemExit("V14 FILE INTEGRITY FAILURE "+rel)
note("FM1 OPEN V14 SDK AUTHOR COPY VERIFIED "+str(len(data["files"]))+" manifest entries")
flags=["-target","pi32v2","-integrated-as","-mcpu=r3","-mfprev1","-Wuninitialized",
 "-Wno-invalid-noreturn","-fno-common","-flto","-fallow-pointer-null",
 "-fprefer-gnu-section","-femulated-tls","-Wno-shift-negative-value",
 "-Wframe-larger-than=2560","-fms-extensions","-fno-unwind-tables",
 "-ffunction-sections","-fdata-sections","-fmessage-length=0",
 "-cl-single-precision-constant","-mllvm","-pi32v2-large-program=true",
 "-D__GCC_PI32V2__","-O2","-I"+str(TOOL/"pi32v2/include")]
for d in ["sdk/include","sdk/include/libc","app/synth","sdk/config","app","app/board"]:
 flags.extend(["-I"+str(ROOT/d)])
sources=sorted(p for p in APP.rglob("*")
 if p.suffix in (".c",".S") and not p.is_relative_to(APP/"synth"))
note("APP SOURCES "+str(len(sources)))
objs=[]
for i,path in enumerate(sources):
 rel=path.relative_to(ROOT).as_posix()
 opts=list(flags)
 if rel in ("app/screen.c","app/transfer.c","app/midi_router.c"):opts.append("-fno-lto")
 if rel=="app/board/panel.c":opts+=["-fno-lto","-fno-pic"]
 opts+=["-fwrapv","-fno-fast-math","-ffp-contract=off"]
 if rel in ("app/project.c","app/transfer.c","app/samples.c","app/screen.c","app/presets.c","app/midi_router.c","app/fm_factory.c","app/fm_library.c"):
  opts.append("-Oz")
 if rel=="app/screen.c":opts.append("-fno-inline-functions")
 out=OBJ/(f"{i:02d}_"+re.sub("[^a-zA-Z0-9._-]","_",rel)+".o")
 note("Compile "+rel)
 run([BIN/"clang",*opts,"-c",path,"-o",out]);objs.append(out)
version=(ROOT/"app/version.h").read_text()
product=re.search(r'^#define FM1_UPDATE_PRODUCT "(FM-1_8\d{6})"',version,re.M)
assert product
identity=hashlib.sha256(("br3-v14-pinned-base-no-dsp\n"+str(len(sources))).encode()).digest()
identitycode='#include "layout.h"\nconst struct fm1_firmware_layout fm1_layout={536576U,7U};\n'
identitycode+='const unsigned char fm1_build_id[32]={'+','.join(hex(i) for i in identity)+'};\n'
identitycode+='const unsigned char fm1_update_identity[27]="'+product.group(1)+'";\n'
(GEN/"build_identity.c").write_text(identitycode)
run([BIN/"clang",*flags,"-c",GEN/"build_identity.c","-o",OBJ/"build_identity.o"])
objs.append(OBJ/"build_identity.o")
if BR3_LINK:
 note("LINK EXPERIMENT: COMPILE REAL BR3 SIX-TRACK DSP + PRIVATE CPU1, NO UI OR DMA YET")
 for name in ("biomech.c","br3_blackbox.c","br3_cpu1_runtime.c","br3_cpu1_entry.S"):
  source=BR3_SRC/name
  out=OBJ/("br3_"+name.replace(".","_")+".o")
  args=list(flags)+["-I"+str(BR3_SRC),"-DBR3_DUAL_CORE","-DBR3_PI32V2","-DBR3_ACTIVE_SLOTS_LAB",
                    "-fwrapv","-fno-fast-math","-ffp-contract=off"]
  run([BIN/"clang",*args,"-c",source,"-o",out])
  objs.append(out)

ld=(SDK/"config/linker.ld.in").read_text()
ld=ld.replace("@SBC_DECODER@","sbc_decoder\n").replace("@ACL_TX_EXTRA@"," + 1024").replace("@ACL_RX_EXTRA@"," + 4096")
(GEN/"linker").write_text(ld)
link=[BIN/"ld","--plugin",BIN/"LLVMgold.so","-o","sdk.elf",*objs,"-flto",
 "--plugin-opt=-pi32v2-always-use-itblock=false","--plugin-opt=-enable-ipra=true",
 "--plugin-opt=-pi32v2-merge-max-offset=4096","--plugin-opt=-pi32v2-enable-simd=true",
 "--plugin-opt=mcpu=r3","--plugin-opt=-global-merge-on-const","--plugin-opt=-inline-threshold=5",
 "--plugin-opt=-inline-max-allocated-size=32",
 "--plugin-opt=-inline-normal-into-special-section=true",
 "--plugin-opt=-dont-used-symbol-list=malloc,free,sprintf,printf,puts,putchar",
 "--plugin-opt=-pi32v2-enable-rep-memop","--plugin-opt=-emulated-tls",
 "--sort-common","--plugin-opt=-pi32v2-large-program=true",
 "--plugin-opt=-pi32v2-csync-before-rti","--start-group","--whole-archive",
 SDK/"lib/libfm1_engine.a","--no-whole-archive",SDK/"lib/libc.a",
 SDK/"lib/libcompiler_rt.a",TOOL/"pi32v2/lib/r3/libm.a","--end-group",
 "--gc-sections","-Tgenerated/linker","-M=sdk.map",
 "--undefined=connectivity_wl82_bluetooth_start",
 "--undefined=audio_app_bluetooth_open",
 "--undefined=bt_get_local_name","--undefined=bt_get_mac_addr"]
if BR3_LINK:
 # Force both music and CPU1 work symbols to be retained. Otherwise
 # --gc-sections could fake a successful integration by dropping all BR3.
 link+=["--undefined=br_render","--undefined=br3_cpu1_start",
        "--undefined=br3_cpu1_main","--undefined=br3_blackbox"]
note("LINK STOCK V14 + REAL BR3 OBJECTS" if BR3_LINK else "LINK ORIGINAL SDK ONLY")
run(link)
run([BIN/"nm","-n","sdk.elf"])
if BR3_LINK:
 out=run([BIN/"nm","-n","sdk.elf"])
 for symbol in ("br_render","br3_cpu1_start","br3_cpu1_main","br3_blackbox"):
  if not any(line.strip().endswith(" "+symbol) for line in out.splitlines()):
   raise RuntimeError("BR3 symbol lost in SDK link: "+symbol)
 note("BR3 V14 REAL DSP + CPU1 OBJECT LINKED; GUI/DMA HANDOFF NOT YET ATTACHED")
else:
 note("LINK VERIFIED STOCK SDK ORIGINAL NO BIOMECH 3 FWSC")
LOG.close()
