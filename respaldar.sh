#!/usr/bin/env bash
#
# Respaldo de la base de datos. Ejecútelo al terminar cada sesión
# de captura, o programe uno semanal.
#
#   ./respaldar.sh                  guarda en ./respaldos/
#   ./respaldar.sh /media/usb       guarda en la ruta indicada

set -o errexit

DESTINO="${1:-./respaldos}"
mkdir -p "$DESTINO"

MARCA=$(date +%Y-%m-%d_%H%M)
ARCHIVO="${DESTINO}/fraternitas_${MARCA}.sqlite3"

# La copia se hace con sqlite3 para garantizar consistencia aunque
# el servidor esté corriendo. 'cp' puede capturar un estado a medias.
if command -v sqlite3 >/dev/null 2>&1; then
    sqlite3 db.sqlite3 ".backup '${ARCHIVO}'"
else
    cp db.sqlite3 "$ARCHIVO"
fi

gzip -f "$ARCHIVO"

echo "Respaldo creado: ${ARCHIVO}.gz"

# Conserva los últimos 20 y elimina el resto.
ls -1t "${DESTINO}"/fraternitas_*.sqlite3.gz 2>/dev/null \
    | tail -n +21 \
    | xargs -r rm --

echo "Respaldos disponibles:"
ls -1t "${DESTINO}"/fraternitas_*.sqlite3.gz 2>/dev/null | head -5
