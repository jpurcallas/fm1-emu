#!/usr/bin/env python3
"""REminiSCENT LAB20: reutiliza Zig de ayer; compila con el SDK oficial para MPC One+ ARM32.
No toca la MPC ni repositorios. Requiere las 254 muestras PCM reales para producir paquete completo.
"""
from pathlib import Path
import hashlib, os, platform, shutil, subprocess, sys, tarfile, zipfile, time

ROOT=Path(__file__).resolve().parent
SDK=ROOT/'mpc-plugin-builder-sdk-main'
PROJECT=SDK/'plugins'/'REminiSCENT_MPC_LAB20'
CONTENT=PROJECT/'Content'
INDEX=CONTENT/'bank.tsv'
OUT=ROOT/'SALIDA_MPC'
OUT.mkdir(exist_ok=True)
LOG=ROOT/'REGISTROS'
LOG.mkdir(exist_ok=True)
EXPECTED_ZIG='75f1bc7a1e9852f17ec9a0c1895f767c4ec56d46bc8a834920eece1d0359dd8d'
ZIG_NAME='zig-aarch64-macos-0.17.1.tar.xz'


def sha256file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def die(message):
    print('\nERROR:',message,'\nLos archivos anteriores no fueron modificados.');sys.exit(1)

def run(cmd,cwd=None,log=None):
    print('\n$',' '.join(map(str,cmd)),flush=True)
    if log:
        with open(log,'a',encoding='utf-8') as f:
            proc=subprocess.Popen(list(map(str,cmd)),cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors='replace')
            for line in proc.stdout:
                print(line,end='',flush=True);f.write(line)
            return proc.wait()
    return subprocess.run(list(map(str,cmd)),cwd=cwd).returncode

def list_parents():
    roots=[ROOT,ROOT.parent,Path.home()/'Downloads',Path.home()/'Desktop',Path.home()/'Documents']
    return [p for p in roots if p.exists()]

def find_with_name(filename,maxdepth=4):
    for base in list_parents():
        for here,dirs,files in os.walk(base):
            depth=len(Path(here).relative_to(base).parts)
            dirs[:]=[d for d in dirs if not d.startswith('.') and d not in {'node_modules','Library','Applications','__pycache__','.git'}]
            if filename in files:yield Path(here)/filename
            if depth>=maxdepth:dirs[:]=[]

def verify_zig(path):
    if not path or not path.exists():return False
    cmd=[str(path),'version']
    if path.name=='python' or path.name.startswith('python3'):cmd=[str(path),'-m','ziglang','version']
    try:
        s=subprocess.check_output(cmd,stderr=subprocess.DEVNULL,text=True,timeout=10).strip()
        print('Zig disponible:',s,'en',path)
        return s.startswith('0.17.')
    except Exception:return False

def from_offline_backup(zipfile_path):
    target=ROOT/'DEPENDENCIAS_ORIGINALES'/ZIG_NAME
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.is_file():
        print('Recuperando Zig de',zipfile_path)
        with zipfile.ZipFile(zipfile_path) as z:
            matches=[x for x in z.namelist() if x.endswith('/'+ZIG_NAME) or x==ZIG_NAME]
            if not matches: return None
            with z.open(matches[0]) as src, target.open('wb') as dst:shutil.copyfileobj(src,dst)
    h=sha256file(target)
    if h!=EXPECTED_ZIG:die('Zig de respaldo no coincide con SHA-256 oficial')
    print('SHA256 de Zig: OK')
    dest=ROOT/'COMPILADOR_ZIG_MAC'
    zig=dest/'zig-aarch64-macos-0.17.1'/'zig'
    if not zig.exists():
        dest.mkdir(parents=True,exist_ok=True)
        with tarfile.open(target,'r:xz') as tar:
            for member in tar.getmembers():
                resolved=(dest/member.name).resolve()
                if not str(resolved).startswith(str(dest.resolve())+os.sep):die('Ruta insegura en archivo Zig')
            tar.extractall(dest)
        zig.chmod(zig.stat().st_mode|0o111)
    return zig

def resolve_zig():
    probes=[]
    env=os.environ.get('ZIG','').strip()
    if env:probes.append(Path(env).expanduser())
    z=shutil.which('zig')
    if z:probes.append(Path(z))
    z=SDK/'.sdk-tools'/'zigenv'/'bin'/'python'
    if z.exists():probes.append(z)
    probes.append(ROOT/'COMPILADOR_ZIG_MAC'/'zig-aarch64-macos-0.17.1'/'zig')
    for r in list_parents():
        probes.extend([r/'COMPILADOR_ZIG_MAC'/'zig-aarch64-macos-0.17.1'/'zig',r/'REminiSCENT_MPC_KIT_DESCARGA_TOTAL_MAC_M4'/'COMPILADOR_ZIG_MAC'/'zig-aarch64-macos-0.17.1'/'zig'])
    for p in probes:
        if verify_zig(p):return p
    # Fully offline self-contained delivery: Mac Zig archive is bundled.
    if (ROOT/'DEPENDENCIAS_ORIGINALES'/ZIG_NAME).is_file():
        zig=from_offline_backup(Path('__embedded_zig_archive__'))
        if verify_zig(zig):return zig
    backups=list(find_with_name('REminiSCENT_MPC_RESPALDO_DESARROLLO_MAC_OFFLINE.zip'))
    backups+=list(find_with_name('REminiSCENT_MPC_KIT_UNICO_DESCARGA_Y_COMPILACION_MAC_ARM32.zip'))
    for b in backups:
        try:
            zig=from_offline_backup(b)
            if verify_zig(zig):return zig
        except Exception as e:print('Respaldo no utilizable',b,str(e))
    print('\nNo se encontró Zig. Pegá la ruta de tu ZIP de respaldo de ayer (arrastralo aquí) y presioná Return.')
    p=input('Ruta del respaldo, o ENTER para cancelar: ').strip().strip('"\'')
    if p and Path(p).expanduser().is_file():
        zig=from_offline_backup(Path(p).expanduser())
        if verify_zig(zig):return zig
    die('Falta Zig 0.17.1. Conservá el respaldo de ayer. No se instaló nada.')

def bank_rows():
    rows=[]
    for line in INDEX.read_text().splitlines():
        chunks=line.split()
        if len(chunks)>=3 and chunks[0].isdigit():rows.append(chunks[2])
    if len(rows)!=254:die('bank.tsv no contiene 254 archivos válidos: '+str(len(rows)))
    return rows

def find_bank(rows):
    candidates=[CONTENT/'samples']
    for root in list_parents():
        candidates.extend([root/'REminiSCENT_LAB19_27_ACOUSTIC_PCM_MAC'/'samples',root/'REminiSCENT_LAB19_27_ACOUSTIC_PCM_MAC'/'REminiSCENT_LAB19_27_ACOUSTIC_PCM_MAC'/'samples',root/'samples'])
    def matches(p):return p.is_dir() and all((p.parent/rel).is_file() for rel in rows)
    for cand in candidates:
        if matches(cand):return cand
    print('\nNo encuentro las 254 muestras LAB19 en tu Mac.')
    print('Si tenés la carpeta LAB19/samples, arrastrala aquí y presioná Return; si no, ENTER.')
    p=input('Carpeta samples: ').strip().strip('"\'')
    cand=Path(p).expanduser() if p else None
    if cand and matches(cand):return cand
    return None

def make_samples_local(source,rows):
    target=CONTENT/'samples'
    if target.exists() and target.is_symlink():target.unlink()
    if target.is_dir() and target.resolve()!=source.resolve():
        # Never overwrite a folder of bank data without inspecting it
        if all((target.parent/rel).is_file() for rel in rows):return target
        die('Hay una carpeta Content/samples incompleta. No se reemplazó automáticamente.')
    if target==source:return target
    target.mkdir(parents=True,exist_ok=True)
    for i,rel in enumerate(rows,1):
        src=source.parent/rel
        dst=CONTENT/rel
        dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.is_file() and dst.stat().st_size==src.stat().st_size:continue
        try:os.link(src,dst)  # Hardlink: sin duplicar almacenamiento cuando comparten volumen
        except OSError:shutil.copy2(src,dst)
        if i%50==0:print('Muestras enlazadas/copias:',i,'/254')
    return target

def verify_approved_skin(project, output=False):
    skin=(project/'build'/'Yeti Fingers - VST - REminiSCENT MPC LAB20'/'Plugin Skins') if output else (project/'skins')
    tui=skin/'TUI.json'; q=skin/'Q-Links.json'
    if not (tui.is_file() and q.is_file()):die('FALTA SKIN APROBADA; no se permite compilar paquete genérico')
    j=json.loads(tui.read_text(encoding='utf-8'))
    tabs=j['pageData']['tabs']; widgets=tabs[0]['componentDefinition']['componentsData']
    names={v['componentData']['name'] for v in widgets}
    for i,name in enumerate(['ACOUSTIC','OSC','BLEND','ENVELOPE','MEMORY','RESONANCE','FILTER','CHARACTER','GRANULAR','MOD','SEND FX']):
        if f'TAB_{name}' not in names or f'original_art_{name}' not in names or not (skin/'fondos'/f'{i:02}.png').is_file():
            die('Skin incompleta (página '+name+'); NO generar plugin genérico')
        if not (skin/f'nav_{i:02}_on.png').is_file() or not (skin/f'nav_{i:02}_off.png').is_file():
            die('Skin incompleta (pestaña '+name+')')
    if not (('BLEND_ECLIPSE_FOCUS_MASTER_BLEND' in names) and all(f'Q{k}_knob' in names for k in range(1,5))):
        die('Falta foco táctil eclipse o controles Q-Link de la interfaz aprobada')
    mapping=json.loads(q.read_text(encoding='utf-8'))
    if len(mapping.get('Screen Mode Q-Links',{}).get('map',[]))<1:
        die('Falta mapa Q-Link')
    print('SKIN ARTÍSTICA: 11 páginas, pestañas, eclipse táctil y 4 Q-Links presentes'+(' (paquete)' if output else ' (proyecto)'))

def main():
    print('REminiSCENT MPC LAB20 — compilación en Mac / ARM32 — sin instalar ni modificar Bridge16')
    if sys.platform!='darwin' or platform.machine()!='arm64':die('Este lanzador usa macOS Apple Silicon')
    if not (SDK/'tools'/'build.py').is_file():die('Falta el SDK. Extraé el kit completo')
    verify_approved_skin(PROJECT)
    rows=bank_rows()
    samples=find_bank(rows)
    if samples:
        samples=make_samples_local(samples,rows)
        print('Banco completo localizado:',samples)
    else:
        print('AVISO: banco de 254 muestras NO DISPONIBLE. Solo se verificará compilación; NO SE CREARÁ UN PAQUETE PARA INSTALAR.')
    zig=resolve_zig()
    log=LOG/('build_lab20_'+time.strftime('%Y%m%d_%H%M%S')+'.log')
    cmd=[sys.executable,'tools/build.py','plugins/REminiSCENT_MPC_LAB20','--target','all','--no-ui','--zig',str(zig)]
    if run(cmd,cwd=SDK,log=log)!=0:die('Falló la compilación ARM32/ARM64. Registro: '+str(log))
    built=PROJECT/'build'/'Yeti Fingers - VST - REminiSCENT MPC LAB20'
    if not built.exists():
        dirs=list((PROJECT/'build').glob('*'))
        die('No está la carpeta esperada; se generaron: '+str(dirs))
    verify_approved_skin(PROJECT,output=True)
    import struct
    b=(built/'VST'/'reminiscent-mpc-lab20-arm32.so').read_bytes()[:20]
    if len(b)<20 or b[:4]!=b'\x7fELF' or b[4]!=1 or struct.unpack_from('<H',b,18)[0]!=40:
        die('El binario no es ARM32 ELF válido')
    print('\nCOMPILACIÓN ARM32 VERIFICADA: ELF 32 bits ARM')
    if not samples:
        print('\nSOLO CODIGO COMPILADO, SIN BANCO PCM. NO INSTALAR EN MPC.')
        print('Registro:',log)
        return
    if len([p for p in (built/'Content'/'samples').rglob('*.wav') if p.is_file()])!=254:
        die('Salida incompleta: no copió 254 WAV. No se empaqueta.')
    outzip=OUT/'REminiSCENT_MPC_LAB20_ARM32_CON_27_VOCES.zip'
    with zipfile.ZipFile(outzip,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for p in built.rglob('*'):
            if p.is_file():z.write(p,'VST2 Plugins/'+built.name+'/'+str(p.relative_to(built)))
    print('\nPAQUETE PARA INSTALACIÓN MANUAL:',outzip)
    print('SHA256:',sha256file(outzip))
    print('Registro:',log)
    print('EXPERIMENTAL. No probada aún en la MPC física. Guardá proyectos antes de probar. Skin artística presente; interacción pendiente de prueba física en MPC.')

if __name__=='__main__':
    try:main()
    except (KeyboardInterrupt,EOFError):print('\nCancelado por el usuario. Sin instalación en MPC.');sys.exit(130)