#!/bin/bash
set -u
cd -- "$(dirname -- "$0")" || exit 1
choice=$(/usr/bin/osascript -e 'button returned of (display dialog "¿Qué proyecto querés diagnosticar?" with title "FM1 LIVE LAB · Elegí proyecto" buttons {"Cancelar", "REminiSCENT", "BIOMECH"} default button "BIOMECH")' 2>/dev/null) || exit 0
case "$choice" in
  BIOMECH) project="BIOMECH";;
  REminiSCENT) project="REMINISCENT";;
  *) exit 0;;
esac
root="$HOME/Desktop/FM1_BLACKBOX"
folder="$root/$project"
mkdir -p "$folder"
export FM1_BLACKBOX_DIR="$folder"
export FM1_DIAGNOSTIC_PROFILE="$project"
if [ "$project" = "BIOMECH" ]; then
  export FM1_GROOVE_MEM_TRACE=1
else
  export FM1_NO_JIT=1
fi
fw=$(/usr/bin/osascript -e 'POSIX path of (choose file with prompt "Elegí el firmware .fwsc de '"$project"'")' 2>/dev/null) || exit 0
stamp=$(date +%Y%m%d-%H%M%S)
/usr/bin/shasum -a 256 "$fw" > "$folder/firmware-$stamp.sha256"
echo "PROYECTO: $project"
echo "BLACK BOX: $folder"
echo "BOTONES EN PANTALLA: EXPORTAR JSON · VER ARCHIVOS · GRABAR WAV"
/usr/bin/open "$folder"
./fm1-live --mhz 200 --fwsc "$fw" 2>&1 | /usr/bin/tee "$folder/session-$stamp.log"
echo "Registros: $folder"
/usr/bin/open "$folder"
read -r -p "Presioná Enter para cerrar."
