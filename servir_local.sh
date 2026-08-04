#!/usr/bin/env bash
#
# Arranca FRATERNITAS-ERP en la red local para trabajar desde el iPad.
#
#   ./servir_local.sh          arranca en el puerto 8000
#   ./servir_local.sh 9000     arranca en otro puerto
#
# Detecta la IP de la máquina, la agrega a ALLOWED_HOSTS y muestra la
# dirección —y un código QR— para abrirla desde la tableta.

set -o errexit

PUERTO="${1:-8000}"

# --- IP de la red local -----------------------------------------------
IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}')

if [ -z "$IP" ]; then
    IP=$(hostname -I | awk '{print $1}')
fi

if [ -z "$IP" ]; then
    echo "No se pudo determinar la IP local. ¿Está conectado a la red?"
    exit 1
fi

URL="http://${IP}:${PUERTO}/tesoreria/"

# --- Configuración del entorno ----------------------------------------
export ALLOWED_HOSTS="127.0.0.1,localhost,${IP}"
export DEBUG="${DEBUG:-False}"

# Recolecta estáticos si WhiteNoise los sirve desde staticfiles/
python manage.py collectstatic --no-input >/dev/null 2>&1 || true

python manage.py migrate --no-input

# --- Aviso -------------------------------------------------------------
echo
echo "════════════════════════════════════════════════════════════"
echo "  FRATERNITAS-ERP · Tesorería"
echo "════════════════════════════════════════════════════════════"
echo
echo "  Desde el iPad, abra:"
echo
echo "      ${URL}"
echo

python - "$URL" <<'PY' 2>/dev/null || true
import sys
try:
    import qrcode
    codigo = qrcode.QRCode(border=1)
    codigo.add_data(sys.argv[1])
    codigo.make(fit=True)
    codigo.print_ascii(invert=True)
except Exception:
    pass
PY

echo "  Ambos equipos deben estar en la misma red."
echo "  Para detener el servidor: Ctrl+C"
echo "════════════════════════════════════════════════════════════"
echo

# --- Servidor ----------------------------------------------------------
if python -c "import waitress" 2>/dev/null; then
    exec waitress-serve \
        --listen="0.0.0.0:${PUERTO}" \
        --threads=4 \
        config.wsgi:application
else
    echo "waitress no está instalado; se usa gunicorn."
    exec gunicorn config.wsgi:application \
        --bind "0.0.0.0:${PUERTO}" \
        --workers 2 \
        --timeout 60
fi
