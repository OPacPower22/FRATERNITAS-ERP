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
