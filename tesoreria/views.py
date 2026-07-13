from decimal import Decimal

from django.shortcuts import render

from negocio.services.aplicacion import calcular_propuesta


class ObligacionDummy:
    """
    Temporal.
    Será sustituido por el modelo Obligacion.
    """

    def __init__(self, periodo, saldo):
        self.periodo = periodo
        self.saldo_pendiente = Decimal(str(saldo))


def index(request):
    return render(
        request,
        "core/dashboard.html",
    )


def emitir_recibo(request):

    propuesta = None

    if request.method == "POST":

        importe = Decimal(
            request.POST.get(
                "importe",
                "0",
            )
        )

        obligaciones = [
            ObligacionDummy("Julio 2026", 280),
            ObligacionDummy("Agosto 2026", 280),
            ObligacionDummy("Septiembre 2026", 280),
        ]

        propuesta = calcular_propuesta(
            obligaciones,
            importe,
        )

    return render(
        request,
        "tesoreria/cu001/emitir_recibo.html",
        {
            "propuesta": propuesta,
        },
    )
