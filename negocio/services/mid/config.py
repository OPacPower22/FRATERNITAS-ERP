"""
Configuración del Motor Institucional de Datos (MID)
"""

from pathlib import Path

from django.conf import settings


DMI = (
    Path(settings.BASE_DIR)
    / "importaciones"
    / "tesoreria"
    / "TESORERIA_MOVIMIENTOS_2026.xlsx"
)

HOJAS = {
    "catalogos": "CATALOGOS_MAESTROS",
    "miembros": "MIEMBROS",
    "parametros": "PARAMETROS",
    "tarifas": "TARIFAS_OBLIGACIONES",
    "distribucion": "DISTRIBUCION_CAPITA",
}
