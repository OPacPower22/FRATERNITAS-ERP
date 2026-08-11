"""
Reparto mensual histórico de Tesorería (enero-mayo 2026), por fondo.

El detalle línea por línea de enero a mayo de 2026 vive únicamente en
el histórico del Tesorero (MOVIMIENTOS 2026.xls, hoja INGRESOS Y
EGRESOS) y no se reimportó recibo por recibo: reconstruirlo
replicaría, mes por mes, el mismo trabajo artesanal de MID-001
(homónimos, prorrateo de egresos, Saco de Beneficencia...) sobre
movimientos que ya no tienen efecto en ninguna obligación viva — el
mismo criterio detrás de ``negocio.services.ajustes_apertura``.

En su lugar se registra, para cada mes y cada fondo, un único
movimiento de ingreso y (si aplica) uno de egreso, tomados tal cual
de la hoja INFORME MENS de MOVIMIENTOS 2026.xls (columnas INGRESO y
EGRESO de cada bloque mensual). Fechados al cierre de cada mes, para
que el Informe Mensual de Resultados Financieros encadene
correctamente el "MES ANT." de cada periodo — incluido mayo, cuyo
propio ingreso/egreso ya no queda mezclado con el arrastre de meses
anteriores (a diferencia de la primera versión de este módulo, que
sólo registraba un saldo único al cierre de mayo).

Es idempotente: cada movimiento queda amarrado a un
``ConceptoContable`` dedicado (clave ``HISTORICO_<FONDO>``) que no se
usa para nada más.
"""

import datetime
from decimal import Decimal

from django.db import transaction

from catalogos.models import ConceptoContable
from tesoreria.models import Movimiento


FUENTE = "MOVIMIENTOS 2026.xls, hoja INFORME MENS, bloque {mes} 2026."

CONCEPTOS = [
    ("HISTORICO_CAPITAS", "Histórico (consolidado) - Cápitas"),
    ("HISTORICO_ANIVERSARIO", "Histórico (consolidado) - Aniversario"),
    ("HISTORICO_SACO_BENEFICENCIA", "Histórico (consolidado) - Saco de Beneficencia"),
    ("HISTORICO_TALLER_BJ", "Histórico (consolidado) - Taller Benito Juárez"),
    ("HISTORICO_OTROS", "Histórico (consolidado) - Otros"),
]

# Verificado línea por línea contra la hoja INFORME MENS: la cadena
# de "mes_ant" que produce el Informe Mensual al acumular estos
# movimientos coincide, mes a mes, con la columna MES ANT. del
# bloque siguiente (incluido el cierre de mayo → MES ANT. de junio).
DATOS = [
    {
        "mes": "ENERO",
        "fecha": datetime.date(2026, 1, 31),
        "fondos": {
            "HISTORICO_CAPITAS": {"ingreso": Decimal("7475.00"), "egreso": Decimal("5674.00")},
            "HISTORICO_ANIVERSARIO": {"ingreso": Decimal("500.00"), "egreso": Decimal("0.00")},
            "HISTORICO_SACO_BENEFICENCIA": {"ingreso": Decimal("709.00"), "egreso": Decimal("0.00")},
            "HISTORICO_TALLER_BJ": {"ingreso": Decimal("75.00"), "egreso": Decimal("0.00")},
            "HISTORICO_OTROS": {"ingreso": Decimal("128.00"), "egreso": Decimal("0.00")},
        },
    },
    {
        "mes": "FEBRERO",
        "fecha": datetime.date(2026, 2, 28),
        "fondos": {
            "HISTORICO_CAPITAS": {"ingreso": Decimal("9550.00"), "egreso": Decimal("4844.00")},
            "HISTORICO_ANIVERSARIO": {"ingreso": Decimal("1650.00"), "egreso": Decimal("0.00")},
            "HISTORICO_SACO_BENEFICENCIA": {"ingreso": Decimal("440.00"), "egreso": Decimal("0.00")},
            "HISTORICO_TALLER_BJ": {"ingreso": Decimal("450.00"), "egreso": Decimal("0.00")},
            "HISTORICO_OTROS": {"ingreso": Decimal("0.00"), "egreso": Decimal("0.00")},
        },
    },
    {
        "mes": "MARZO",
        "fecha": datetime.date(2026, 3, 31),
        "fondos": {
            "HISTORICO_CAPITAS": {"ingreso": Decimal("17344.50"), "egreso": Decimal("8071.00")},
            "HISTORICO_ANIVERSARIO": {"ingreso": Decimal("7644.00"), "egreso": Decimal("0.00")},
            "HISTORICO_SACO_BENEFICENCIA": {"ingreso": Decimal("533.00"), "egreso": Decimal("0.00")},
            "HISTORICO_TALLER_BJ": {"ingreso": Decimal("375.00"), "egreso": Decimal("0.00")},
            "HISTORICO_OTROS": {"ingreso": Decimal("256.00"), "egreso": Decimal("0.00")},
        },
    },
    {
        "mes": "ABRIL",
        "fecha": datetime.date(2026, 4, 30),
        "fondos": {
            "HISTORICO_CAPITAS": {"ingreso": Decimal("4275.00"), "egreso": Decimal("5014.00")},
            "HISTORICO_ANIVERSARIO": {"ingreso": Decimal("750.00"), "egreso": Decimal("0.00")},
            "HISTORICO_SACO_BENEFICENCIA": {"ingreso": Decimal("1100.00"), "egreso": Decimal("2000.00")},
            "HISTORICO_TALLER_BJ": {"ingreso": Decimal("225.00"), "egreso": Decimal("519.00")},
            "HISTORICO_OTROS": {"ingreso": Decimal("50.00"), "egreso": Decimal("0.00")},
        },
    },
    {
        "mes": "MAYO",
        "fecha": datetime.date(2026, 5, 31),
        "fondos": {
            "HISTORICO_CAPITAS": {"ingreso": Decimal("1995.00"), "egreso": Decimal("3240.00")},
            "HISTORICO_ANIVERSARIO": {"ingreso": Decimal("350.00"), "egreso": Decimal("0.00")},
            "HISTORICO_SACO_BENEFICENCIA": {"ingreso": Decimal("345.00"), "egreso": Decimal("0.00")},
            "HISTORICO_TALLER_BJ": {"ingreso": Decimal("105.00"), "egreso": Decimal("0.00")},
            "HISTORICO_OTROS": {"ingreso": Decimal("0.00"), "egreso": Decimal("0.00")},
        },
    },
]


@transaction.atomic
def aplicar():
    """Registra (o confirma ya registrados) los movimientos mensuales consolidados."""

    conceptos = {}
    for clave, nombre in CONCEPTOS:
        concepto, _ = ConceptoContable.objects.update_or_create(
            clave=clave,
            defaults={"nombre": nombre, "activo": True},
        )
        conceptos[clave] = concepto

    creados = []

    for bloque in DATOS:
        fuente = FUENTE.format(mes=bloque["mes"])

        for clave, importes in bloque["fondos"].items():
            concepto = conceptos[clave]

            for tipo, campo in (("I", "ingreso"), ("E", "egreso")):
                importe = importes[campo]
                if importe <= Decimal("0.00"):
                    continue

                _, nuevo = Movimiento.objects.get_or_create(
                    concepto_contable=concepto,
                    tipo=tipo,
                    fecha=bloque["fecha"],
                    defaults={
                        "concepto": concepto.nombre,
                        "otros": importe,
                        "observaciones": fuente,
                    },
                )

                creados.append(
                    {
                        "mes": bloque["mes"],
                        "concepto": concepto.nombre,
                        "tipo": tipo,
                        "importe": importe,
                        "nuevo": nuevo,
                    }
                )

    return creados


def revertir():
    """Elimina únicamente estos movimientos mensuales consolidados."""

    claves = [clave for clave, _ in CONCEPTOS]
    movimientos = Movimiento.objects.filter(concepto_contable__clave__in=claves)
    resumen = {"movimientos": movimientos.count()}
    movimientos.delete()

    return resumen
