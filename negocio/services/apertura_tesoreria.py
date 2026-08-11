"""
Saldo de apertura de Tesorería, por fondo.

El detalle de enero a mayo de 2026 vive únicamente en el histórico
del Tesorero (MOVIMIENTOS 2026.xls, hoja INGRESOS Y EGRESOS) y no se
reimportó línea por línea: reconstruirlo replicaría, mes por mes, el
mismo trabajo artesanal de MID-001 (homónimos, prorrateo de egresos,
Saco de Beneficencia...) sobre movimientos que ya no tienen efecto en
ninguna obligación viva — el mismo criterio detrás de
``negocio.services.ajustes_apertura``.

En su lugar se registra un único saldo de apertura por fondo, tomado
tal cual de la hoja INFORME MENS, bloque MAYO 2026, columna SALDO
TOTAL, fechado al cierre de mayo para que alimente correctamente el
"MES ANT." de junio en adelante tanto en el Informe Mensual de
Resultados Financieros como en el saldo de caja del dashboard.

Es idempotente: cada saldo queda amarrado a un ``ConceptoContable``
dedicado (clave ``APERTURA_<FONDO>``) que no se usa para nada más.
"""

import datetime
from decimal import Decimal

from django.db import transaction

from catalogos.models import ConceptoContable
from tesoreria.models import Movimiento


FECHA_CORTE = datetime.date(2026, 5, 31)

FUENTE = (
    "MOVIMIENTOS 2026.xls, hoja INFORME MENS, bloque MAYO 2026, "
    "columna SALDO TOTAL."
)

# Verificado línea por línea contra la hoja INFORME MENS (filas
# 183, 187, 191, 195 y 199): suman exactamente la SUMA TOTAL de mayo
# reportada en esa misma hoja ($26,962.50, fila 202).
SALDOS = [
    {
        "clave": "APERTURA_CAPITAS",
        "nombre": "Saldo de Apertura - Cápitas",
        "importe": Decimal("13796.50"),
    },
    {
        "clave": "APERTURA_ANIVERSARIO",
        "nombre": "Saldo de Apertura - Aniversario",
        "importe": Decimal("10894.00"),
    },
    {
        "clave": "APERTURA_SACO_BENEFICENCIA",
        "nombre": "Saldo de Apertura - Saco de Beneficencia",
        "importe": Decimal("1127.00"),
    },
    {
        "clave": "APERTURA_TALLER_BJ",
        "nombre": "Saldo de Apertura - Taller Benito Juárez",
        "importe": Decimal("711.00"),
    },
    {
        "clave": "APERTURA_OTROS",
        "nombre": "Saldo de Apertura - Otros",
        "importe": Decimal("434.00"),
    },
]


@transaction.atomic
def aplicar():
    """Registra (o confirma ya registrado) el saldo de apertura de cada fondo."""

    creados = []

    for saldo in SALDOS:
        concepto, _ = ConceptoContable.objects.update_or_create(
            clave=saldo["clave"],
            defaults={"nombre": saldo["nombre"], "activo": True},
        )

        movimiento, creado = Movimiento.objects.get_or_create(
            concepto_contable=concepto,
            tipo="I",
            fecha=FECHA_CORTE,
            defaults={
                "concepto": saldo["nombre"],
                "otros": saldo["importe"],
                "observaciones": FUENTE,
            },
        )

        creados.append(
            {
                "concepto": saldo["nombre"],
                "importe": saldo["importe"],
                "nuevo": creado,
            }
        )

    return creados


def revertir():
    """Elimina únicamente los movimientos de apertura."""

    claves = [saldo["clave"] for saldo in SALDOS]
    movimientos = Movimiento.objects.filter(concepto_contable__clave__in=claves)
    resumen = {"movimientos": movimientos.count()}
    movimientos.delete()

    return resumen
