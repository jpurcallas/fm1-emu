#!/bin/bash
cd -- "$(dirname -- "$0")" || exit 1
if [ "$#" -gt 0 ]; then
  fw="$1"
else
  fw=$(/usr/bin/osascript -e 'POSIX path of (choose file with prompt "Elegí el firmware .fwsc para el emulador")') || exit 0
fi
mkdir -p "$HOME/Desktop/FM1_BLACKBOX"
stamp=$(date +%Y%m%d-%H%M%S)
echo "FM1 LAB · firmware: $fw"
echo "Barra superior: ABRIR FWSC, MHZ, EXPORTAR JSON, GRABAR WAV y VER ARCHIVOS."
echo "Registros en Escritorio / FM1_BLACKBOX."
/usr/bin/shasum -a 256 "$fw" > "$HOME/Desktop/FM1_BLACKBOX/firmware-$stamp.sha256"
./fm1-live --mhz 200 --fwsc "$fw" 2>&1 | /usr/bin/tee "$HOME/Desktop/FM1_BLACKBOX/session-$stamp.log"
echo "Sesión terminada. Los registros están en Escritorio / FM1_BLACKBOX."
read -r -p "Presioná Enter para cerrar."
