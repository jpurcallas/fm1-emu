#!/bin/bash
# REminiSCENT LAB29: isolate Plotter + Envelope without altering audio/art.
set -euo pipefail
INPUT="${1:-}"
FILENAME='REminiSCENT_UI29_11PANTALLAS_PARAMETROS_SDK_CORREGIDOS.zip'
if [[ -z "$INPUT" ]]; then
  if [[ -f "$HOME/Downloads/$FILENAME" ]]; then
    INPUT="$HOME/Downloads/$FILENAME"
  else
    INPUT="$(/usr/bin/osascript -e 'POSIX path of (choose file with prompt "Selecciona el ZIP original de REminiSCENT LAB29")' 2>/dev/null || true)"
  fi
fi
if [[ ! -f "$INPUT" ]]; then
  echo 'No se encontro el ZIP original LAB29; no se ha modificado nada.'
  read -r -p 'Presiona Enter para cerrar... ' _
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3 no esta disponible en este Mac; no se ha modificado nada.'
  read -r -p 'Presiona Enter para cerrar... ' _
  exit 1
fi
python3 - "$INPUT" "$HOME/Downloads/REminiSCENT_LAB29_DIAGNOSTICO_SIN_PLOTTER_ENVELOPE.zip" <<'PY'
import sys, json, hashlib, zipfile, os, pathlib, tempfile
source, output = map(pathlib.Path, sys.argv[1:])
EXPECTED_SOURCE_SHA = '789dd44b5c88f74d8f94689aa83624dc28740bd5e4f7d069775fe401864eb4ff'
EXPECTED_TUI_SHA = 'ad4c1f0383bd8ad4abd8de38e226f3a0116ba825986deb82a2c2d386259a9884'
EXPECTED_REMOVED = {'LIVE_ADSR_NATIVE_LAB10','LIVE_MOD_ENV2','LIVE_LFO_1_AUDIO_TRACE','LIVE_LFO_2_AUDIO_TRACE','LIVE_MEMORY_WET_AUDIO_WAVE'}
TUI_PATH = 'Yeti Fingers - VST - REminiSCENT/Plugin Skins/TUI.json'
def sha_file(path):
  h=hashlib.sha256()
  with open(path,'rb') as f:
    for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
  return h.hexdigest()
if sha_file(source)!=EXPECTED_SOURCE_SHA:
  sys.exit('ERROR: este no es LAB29 original exacto. No se ha modificado nada.')
with zipfile.ZipFile(source) as z:
  data=json.loads(z.read(TUI_PATH))
  components=data['pageData']['tabs'][0]['componentDefinition']['componentsData']
  gone=[x for x in components if x.get('componentData',{}).get('type') in ('Plotter','Envelope')]
  if len(gone)!=5 or {x['componentData']['name'] for x in gone}!=EXPECTED_REMOVED:
    sys.exit('ERROR: los cinco componentes no coinciden; no se ha modificado nada.')
  data['pageData']['tabs'][0]['componentDefinition']['componentsData']=[x for x in components if x not in gone]
  new_tui=(json.dumps(data,indent=2,ensure_ascii=True)+'\n').encode('utf-8')
  if hashlib.sha256(new_tui).hexdigest()!=EXPECTED_TUI_SHA:
    sys.exit('ERROR: la nueva TUI no coincide con la referencia. No se ha modificado nada.')
  output.parent.mkdir(parents=True,exist_ok=True)
  fd,tmp=tempfile.mkstemp(prefix='.reminiscent_l29_',suffix='.zip',dir=str(output.parent));os.close(fd)
  try:
    with zipfile.ZipFile(tmp,'w',allowZip64=True) as dest:
      for info in z.infolist():
        b=new_tui if info.filename==TUI_PATH else z.read(info.filename)
        dest.writestr(info,b)
    with zipfile.ZipFile(tmp) as chk:
      if len(chk.infolist())!=289 or chk.testzip() is not None:
        raise ValueError('Archivo ZIP incompleto o corrupto')
      if sum(x.filename.lower().endswith('.wav') for x in chk.infolist())!=254:
        raise ValueError('Numero de WAV equivocado')
    os.replace(tmp,output)
  finally:
    if os.path.exists(tmp):os.unlink(tmp)
print('HECHO: '+str(output))
print('254 WAV, arte y binarios ARM conservados; 3 Plotter y 2 Envelope excluidos.')
print('ESTADO: prueba diagnostica; la MPC fisica aun no esta validada.')
PY
if [[ "$(uname -s)" == 'Darwin' ]]; then
  open -R "$HOME/Downloads/REminiSCENT_LAB29_DIAGNOSTICO_SIN_PLOTTER_ENVELOPE.zip" 2>/dev/null || true
fi
read -r -p 'Presiona Enter para cerrar... ' _
