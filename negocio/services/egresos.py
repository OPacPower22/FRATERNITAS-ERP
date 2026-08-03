from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum

from tesoreria.models import Movimiento

CENTAVOS = Decimal("0.01")


def obtener_saldos():
    """
    Obtiene el saldo disponible por concepto institucional.
    """

    ingresos = (
        Movimiento.objects
        .filter(
            tipo="I",
            concepto_contable__isnull=False,
        )
        .values(
            "concepto_contable",
            "concepto_contable__nombre",
        )
        .annotate(
            ingresos=Sum("total"),
        )
    )

    egresos = (
        Movimiento.objects
        .filter(
            tipo="E",
            concepto_contable__isnull=False,
        )
        .values(
            "concepto_contable",
        )
        .annotate(
            egresos=Sum("total"),
        )
    )

    egresos_dict = {
        item["concepto_contable"]: item["egresos"]
        for item in egresos
    }

    resultado = []

    for ingreso in ingresos:

        total_ingresos = (
            ingreso["ingresos"] or Decimal("0.00")
        ).quantize(
            CENTAVOS,
            rounding=ROUND_HALF_UP,
        )

        total_egresos = (
            egresos_dict.get(
                ingreso["concepto_contable"],
                Decimal("0.00"),
            )
        ).quantize(
            CENTAVOS,
            rounding=ROUND_HALF_UP,
        )

        saldo = (
           total_ingresos - total_egresos
        ).quantize(
            CENTAVOS,
            rounding=ROUND_HALF_UP,
        )

        resultado.append(
            {
                "concepto_id": ingreso["concepto_contable"],
                "concepto": ingreso["concepto_contable__nombre"],
                "ingresos": total_ingresos,
                "egresos": total_egresos,
                "saldo": saldo,
            }
        )

    return resultado


GRUPOS_INSTITUCIONALES = ("GLUM", "INSTITUCIONAL", "GRAN_LOGIA")


def obtener_grupos_por_concepto():
    """
    Mapea cada concepto destino con su grupo de distribución.

    El grupo proviene de ``DistribucionCapita.grupo``, no de una
    lista fija de nombres en la plantilla.
    """

    from catalogos.models import DistribucionCapita

    mapa = {}

    for distribucion in DistribucionCapita.objects.filter(activa=True):
        mapa[distribucion.concepto_destino_id] = (
            distribucion.grupo or "LOCAL"
        ).strip().upper()

    return mapa


def obtener_saldos_agrupados():
    """
    Devuelve los saldos por cubrir separados en institucionales
    (Gran Logia) y locales, con sus totales.

    Estructura:
        {
            "institucionales": {"conceptos": [...], "total": Decimal},
            "locales":         {"conceptos": [...], "total": Decimal},
            "total_general":   Decimal,
        }
    """

    mapa = obtener_grupos_por_concepto()

    institucionales = []
    locales = []

    for saldo in obtener_saldos():

        grupo = mapa.get(saldo["concepto_id"], "LOCAL")
        saldo["grupo"] = grupo

        if grupo in GRUPOS_INSTITUCIONALES:
            institucionales.append(saldo)
        else:
            locales.append(saldo)

    def _total(coleccion):
        return sum(
            (item["saldo"] for item in coleccion),
            Decimal("0.00"),
        )

    total_institucional = _total(institucionales)
    total_local = _total(locales)

    return {
        "institucionales": {
            "conceptos": institucionales,
            "total": total_institucional,
        },
        "locales": {
            "conceptos": locales,
            "total": total_local,
        },
        "total_general": total_institucional + total_local,
    }
