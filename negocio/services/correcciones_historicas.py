"""
Correcciones puntuales a la siembra histórica de junio/julio 2026.

``reconstruir_caja_junio_julio_2026`` sólo reconoce dos textos de
concepto de egreso ("CAPITAS GLUM" y "ABONO ANIVERSARIO") y lee el
importe de la columna TOTAL de la hoja INGRESOS Y EGRESOS. La fila
311 de esa hoja ("ALIMENTOS DEL ANIVERSARIO", $9,800.00 cargados a la
columna ANIVERS.) quedó con la columna TOTAL vacía y con un concepto
no reconocido, así que nunca se importó — el egreso real del evento
de aniversario de junio quedó incompleto ($500.00 en vez de
$10,300.00).

Este módulo registra esa corrección puntual, con el mismo criterio
idempotente y auditable que ``ajustes_apertura``.
"""

import datetime
from decimal import Decimal

from django.db import transaction

from catalogos.models import ConceptoContable
from tesoreria.models import Movimiento


FUENTE = (
    "MOVIMIENTOS 2026.xls, hoja INGRESOS Y EGRESOS, fila 311: "
    "'ALIMENTOS DEL ANIVERSARIO', columna ANIVERS. = $9,800.00 "
    "(columna TOTAL vacía en el original, concepto no reconocido "
    "por el importador)."
)

CORRECCIONES = [
    {
        "concepto_nombre": "Aportación Fraternidad",
        "fecha": datetime.date(2026, 6, 30),
        "importe": Decimal("9800.00"),
        "observaciones": (
            "Alimentos del Aniversario (histórico, corrección). " + FUENTE
        ),
    },
]


@transaction.atomic
def aplicar():
    """Registra (o confirma ya registrada) cada corrección puntual."""

    creados = []

    for correccion in CORRECCIONES:
        concepto = ConceptoContable.objects.get(
            nombre=correccion["concepto_nombre"],
        )

        movimiento, creado = Movimiento.objects.get_or_create(
            concepto_contable=concepto,
            tipo="E",
            fecha=correccion["fecha"],
            observaciones=correccion["observaciones"],
            defaults={
                "concepto": concepto.nombre,
                "otros": correccion["importe"],
            },
        )

        creados.append(
            {
                "concepto": concepto.nombre,
                "importe": correccion["importe"],
                "nuevo": creado,
            }
        )

    return creados


def revertir():
    """Elimina únicamente los movimientos de estas correcciones."""

    observaciones = [c["observaciones"] for c in CORRECCIONES]
    movimientos = Movimiento.objects.filter(observaciones__in=observaciones)
    resumen = {"movimientos": movimientos.count()}
    movimientos.delete()

    return resumen
