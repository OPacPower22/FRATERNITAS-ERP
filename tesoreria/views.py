from decimal import Decimal

from django.shortcuts import render

from miembros.models import Hermano
from negocio.models import Obligacion
from negocio.services.aplicacion import calcular_propuesta


def index(request):
    return render(
        request,
        "core/dashboard.html",
    )


def emitir_recibo(request):

    hermanos = Hermano.objects.filter(
        activo=True,
    ).order_by(
        "apellido_paterno",
        "apellido_materno",
        "nombre",
    )

    hermano = None
    propuesta = None
    obligaciones = []

    if request.method == "POST":

        hermano_id = request.POST.get("hermano")

        if hermano_id:

            hermano = Hermano.objects.get(
                pk=hermano_id,
            )

            obligaciones = Obligacion.objects.filter(
                hermano=hermano,
                estado__in=[
                    "PENDIENTE",
                    "PARCIAL",
                ],
            ).order_by(
                "fecha_vencimiento",
            )

            importe = Decimal(
                request.POST.get(
                    "importe",
                    "0",
                )
            )

            propuesta = calcular_propuesta(
                obligaciones,
                importe,
            )

    return render(
        request,
        "tesoreria/cu001/emitir_recibo.html",
        {
            "hermanos": hermanos,
            "hermano": hermano,
            "hermano_seleccionado": hermano,
            "obligaciones": obligaciones,
            "propuesta": propuesta,
        },
    )