#!/usr/bin/env python3
"""Download a curated, UNPROCESSED source WAV selection for one of 13 approved REminiSCENT instruments.
Never touches the active bank, firmware, master, or production DSP.
This is a reproducible research/staging pack, NOT the complete external library.
"""
import hashlib
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile

NAME = sys.argv[1]
OUT = pathlib.Path("dist")
OUT.mkdir(parents=True, exist_ok=True)
ROOT = pathlib.Path(tempfile.mkdtemp(prefix="rem13-"))
VOICE = ROOT / "REminiSCENT_13_FUENTES_CC0" / NAME
VOICE.mkdir(parents=True)
FILES = []
SOURCES = []

GITHUB_SOURCES = {
    "01_violonchelo": ("sfzinstruments/karoryfer-bigcat.cello", "master", [
        ("Samples/sus", 12), ("Samples/pizzcato", 5), ("Samples/staccato", 5)]),
    "02_flauta": ("sgossner/VSCO-2-CE", "master", [
        ("Woodwinds/Flute/susNV", 10), ("Woodwinds/Flute/stac", 5), ("Woodwinds/Flute/expvib", 3)]),
    "06_guitarra_archtop": ("sfzinstruments/karoryfer.shinyguitar", "master", [
        ("Samples/acoustic", 14), ("Samples/electric", 14)]),
    "07_vibrafono": ("sgossner/VCSL", "sfz", [
        ("Idiophones/Struck Idiophones/Vibraphone/Hard Mallets", 10),
        ("Idiophones/Struck Idiophones/Vibraphone/Soft Mallets", 8)]),
    "08_armonica_cromatica": ("sgossner/VCSL", "sfz", [
        ("Aerophones/Free Aerophones/Harmonica-Hohner-Super64/Sustains", 15),
        ("Aerophones/Free Aerophones/Harmonica-Hohner-Super64/Releases", 4)]),
    "09_trombon": ("sgossner/VSCO-2-CE", "master", [
        ("Brass/Tenor Trombone/sus", 12), ("Brass/Tenor Trombone/stac", 6)]),
    "10_corno_frances": ("sgossner/VSCO-2-CE", "master", [
        ("Brass/F Horn/sus", 12), ("Brass/F Horn/stac", 6)]),
    "11_clavecin": ("sgossner/VCSL", "sfz", [
        ("Chordophones/Zithers/Harpsichord, French/Sustains", 15),
        ("Chordophones/Zithers/Harpsichord, French/Releases", 4)]),
    "12_salterio_arco": ("sgossner/VCSL", "sfz", [
        ("Chordophones/Zithers/Psaltery, Bowed and Plucked/LongBow", 12),
        ("Chordophones/Zithers/Psaltery, Bowed and Plucked/Pluck", 6)]),
    "13_vasos_musicales": ("sgossner/VCSL", "sfz", [
        ("Idiophones/Friction Idiophones/Wine Glasses/Sustains", 14),
        ("Idiophones/Friction Idiophones/Wine Glasses/Releases", 4)]),
}
FREEPATS = {
    "03_clarinete": (
        "https://freepats.zenvoid.org/Reed/Clarinet1/Clarinet-SFZ-20190818.tar.xz",
        "https://freepats.zenvoid.org/Reed/clarinet.html"),
    "04_saxo_tenor": (
        "https://freepats.zenvoid.org/Reed/TenorSaxophone/TenorSaxophone-SFZ-20200717.tar.xz",
        "https://freepats.zenvoid.org/Reed/saxophone.html"),
}
META = "05_guitarra_acero"

def get(url, target=None, api=False):
    for attempt in range(4):
        try:
            headers = {"User-Agent": "REminiSCENT-CC0-Source-Archiver/1.0"}
            if api:
                headers["Accept"] = "application/vnd.github+json"
                if os.environ.get("GH_TOKEN"):
                    headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=100) as response:
                if target is None:
                    return response.read()
                target.parent.mkdir(parents=True, exist_ok=True)
                with open(target, "wb") as f:
                    shutil.copyfileobj(response, f, length=1024*1024)
                return target
        except Exception as exc:
            print(f"RETRY {attempt+1}/4 {url}: {exc}", flush=True)
            if attempt == 3:
                raise
            time.sleep(2*(attempt+1))

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda:f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def record(dst, source):
    # Source files are unmodified. Check that .wav is actually RIFF/WAVE, not a git-lfs pointer.
    if dst.suffix.lower() == ".wav":
        with open(dst, "rb") as f:
            head = f.read(12)
        if len(head) < 12 or head[:4] not in (b"RIFF",b"RF64") or head[8:12] != b"WAVE":
            raise ValueError(f"Not a real WAV audio file: {dst}, header={head!r}")
    item = {"relative_path": str(dst.relative_to(VOICE)), "bytes": dst.stat().st_size,
            "sha256": sha(dst), "original_source": source}
    FILES.append(item)

def github_dir(repo, ref, dirname):
    api = "https://api.github.com/repos/" + repo + "/contents/" + urllib.parse.quote(dirname, safe="/") + "?ref=" + ref
    data = json.loads(get(api, api=True).decode("utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"GitHub source folder unavailable: {repo} {dirname}: {data}")
    wavs = [v for v in data if v.get("type") == "file" and v.get("name","").lower().endswith(".wav")]
    for d in data:
        if d.get("type") == "dir":
            wavs.extend(github_dir(repo, ref, d["path"]))
    return wavs

def evenly_pick(wavs, n):
    wavs = sorted(wavs, key=lambda x:x["path"].lower())
    if not wavs:
        raise ValueError("Empty WAV source path")
    if len(wavs) <= n:
        return wavs
    ix = sorted(set(round(i * (len(wavs)-1) / (n-1)) for i in range(n)))
    return [wavs[i] for i in ix]

def from_github():
    repo, ref, subdirs = GITHUB_SOURCES[NAME]
    SOURCES.append({"repository": f"https://github.com/{repo}", "ref": ref, "license": "CC0-1.0"})
    for dirname, count in subdirs:
        wavs = github_dir(repo, ref, dirname)
        # Skip archtop release noises for pitched playable selection, but retain dry mic and pickup.
        if NAME == "06_guitarra_archtop":
            wavs = [w for w in wavs if "_release_" not in w["name"].lower()]
        selected = evenly_pick(wavs, count)
        print(f"{NAME} {dirname}: {len(wavs)} source WAVs; selecting {len(selected)}", flush=True)
        for entry in selected:
            source_url = entry["download_url"]
            rel = pathlib.PurePosixPath(entry["path"])
            dst = VOICE / "WAV_ORIGINALES" / rel
            get(source_url, dst)
            record(dst, source_url)

def from_freepats():
    url, site = FREEPATS[NAME]
    SOURCES.append({"download_url":url, "website":site,"license":"CC0-1.0"})
    archive = ROOT / "upstream.tar.xz"
    get(url, archive)
    print(f"{NAME} compressed source archive: {archive.stat().st_size} bytes",flush=True)
    with tarfile.open(archive, "r:xz") as tf:
        for member in tf:
            if not member.isfile():
                continue
            n = pathlib.PurePosixPath(member.name)
            if ".." in n.parts or n.is_absolute():
                raise ValueError(f"Unsafe tar member: {n}")
            if n.suffix.lower() not in (".wav", ".sfz", ".txt", ".md", ".license"):
                continue
            src = tf.extractfile(member)
            if src is None: continue
            dst = VOICE / "ARCHIVO_ORIGINAL_EXTRAIDO" / n
            dst.parent.mkdir(parents=True, exist_ok=True)
            with open(dst,"wb") as f:
                shutil.copyfileobj(src,f)
            record(dst, url+"#"+str(n))

def from_meta():
    tag = "meta-steel-guitar-v1.0.0"
    filename = "meta-open-sound-meta-steel-guitar-wav.zip"
    url = f"https://github.com/facebookincubator/Meta-open-sound/releases/download/{tag}/{filename}"
    SOURCES.append({"download_url":url,"license":"CC0-1.0","version":tag})
    source_archive = ROOT / filename
    print("Retrieving 24-bit / 48 kHz source WAV library (large temporary upstream download)",flush=True)
    subprocess.run(["gh","release","download",tag,"--repo","facebookincubator/Meta-open-sound",
                    "--pattern",filename,"--dir",str(ROOT),"--clobber"],
                   check=True, timeout=1200)
    if source_archive.stat().st_size < 100_000_000:
        raise ValueError("Meta original WAV ZIP suspiciously small")
    with zipfile.ZipFile(source_archive,"r") as z:
        names=sorted([n for n in z.namelist() if n.lower().endswith(".wav") and not n.startswith("__MACOSX/")])
        print(f"Meta steel guitar WAVs in source: {len(names)}",flush=True)
        if len(names) < 300:
            raise ValueError("Original steel-guitar library is incomplete")
        # Across whole original library select 24 unmodified, full-quality notes.
        chosen=evenly_pick([{"path":n} for n in names],24)
        for item in chosen:
            n=item["path"]
            rel=pathlib.PurePosixPath(n)
            if ".." in rel.parts:
                raise ValueError("Unsafe zip path")
            dst=VOICE/"WAV_ORIGINALES"/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            with z.open(n) as fi, open(dst,"wb") as fo:
                shutil.copyfileobj(fi,fo)
            record(dst,url+"#"+n)
        # Bring the unmodified mapping and license if present; the mapping may reference samples not selected.
        for n in z.namelist():
            if pathlib.PurePosixPath(n).name.lower() in ("license","license.txt","readme.md"):
                if z.getinfo(n).file_size < 500_000:
                    dst=VOICE/"UPSTREAM_DOCUMENTATION"/pathlib.PurePosixPath(n).name
                    dst.parent.mkdir(parents=True,exist_ok=True)
                    dst.write_bytes(z.read(n))
                    record(dst,url+"#"+n)

if NAME in GITHUB_SOURCES:
    from_github()
elif NAME in FREEPATS:
    from_freepats()
elif NAME == META:
    from_meta()
else:
    raise SystemExit("Unknown approved instrument: "+NAME)

wavs=[f for f in FILES if f["relative_path"].lower().endswith(".wav")]
if len(wavs)<4:
    raise ValueError(f"Too few WAVs for {NAME}: {len(wavs)}")
manifest={
 "instrument_id":NAME,
 "purpose":"REminiSCENT authorized 13 new acoustic sources",
 "status":"ORIGINAL_SOURCE_SELECTION_NOT_YET_IN_FM1_BANK",
 "complete_upstream_library": NAME in FREEPATS,
 "source_license":"CC0-1.0 (source websites; verify attached upstream licensing before publication)",
 "source_libraries":SOURCES,
 "file_count":len(FILES),"wav_count":len(wavs),
 "total_uncompressed_bytes":sum(f["bytes"] for f in FILES),
 "files":FILES,
}
(VOICE/"MANIFIESTO_SHA256.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
(VOICE/"LEEME.txt").write_text(
    "REminiSCENT - fuente acustica: "+NAME+"\n\n"
    "Grabaciones originales descargadas; NO normalizadas, NO reafinadas, NO ADPCM.\n"
    "NO es un banco FM-1 ni un firmware. NO modificar la version audible vigente.\n"
    "Este paquete es una SELECCION parcial de notas WAV, excepto FreePats\n"
    "que incluye su archivo SFZ/WAV original completo. Se conserva la procedencia\n"
    "de cada archivo y el SHA256 en MANIFIESTO_SHA256.json.\n"
    "Pueden faltar notas referenciadas en SFZ originales de otras fuentes.\n"
    "Las fuentes declararon licencia CC0; ver enlaces en MANIFIESTO_SHA256.json.\n",
    encoding="utf-8"
)
out=OUT/(NAME+".zip")
with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=5,allowZip64=True) as z:
    for path in sorted(VOICE.rglob("*")):
        if path.is_file():
            z.write(path,arcname=str(path.relative_to(ROOT)))
with zipfile.ZipFile(out) as z:
    if z.testzip() is not None:
        raise ValueError("ZIP integrity failed")
print("SUCCESS", NAME, "WAV",len(wavs),"ZIP_BYTES",out.stat().st_size,
      "ZIP_SHA256",sha(out), flush=True)
