#!/usr/bin/env bash
# Script de construcción para Render.
# Se ejecuta en cada despliegue, antes de arrancar el servidor.

set -o errexit   # aborta el despliegue si cualquier paso falla

echo "==> Instalando dependencias"
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Recolectando archivos estáticos"
python manage.py collectstatic --no-input

echo "==> Aplicando migraciones"
python manage.py migrate --no-input

echo "==> Sincronizando el Documento Maestro Institucional"
python manage.py sincronizar_dmi || echo "MID omitido (sin cambios o archivo ausente)"

echo "==> Creando el usuario administrador si no existe"
python manage.py crear_superusuario

echo "==> Construcción terminada"
