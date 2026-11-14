#!/bin/bash
set -Eeuo pipefail
cd "$(dirname "$0")"
python3 compilar_lab20_mac.py
printf '\nPresioná Return para cerrar Terminal.\n'
read -r