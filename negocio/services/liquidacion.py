"""
Servicios de liquidación de obligaciones.

Convierte una propuesta de aplicación en registros definitivos.
"""

from decimal import Decimal

from django.db import transaction

from negocio.models import AplicacionPago


@transaction.atomic
def aplicar_propuesta(
    pago,
    propuesta,
):
    """
    Persiste una propuesta de aplicación.

    Parameters
    ----------
    pago : Pago
    propuesta : PropuestaAplicacion

    Returns
    -------
    list[AplicacionPago]
    """

    aplicaciones = []

    for item in propuesta.aplicaciones:

        obligacion = item["obligacion"]
        importe = Decimal(str(item["importe_aplicado"]))

        aplicacion = AplicacionPago.objects.create(
            pago=pago,
            obligacion=obligacion,
            importe_aplicado=importe,
        )

        obligacion.saldo_pendiente -= importe

        if obligacion.saldo_pendiente <= 0:
            obligacion.saldo_pendiente = Decimal("0.00")
            obligacion.estado = "LIQUIDADA"

        elif obligacion.saldo_pendiente < obligacion.importe:
            obligacion.estado = "PARCIAL"

        else:
            obligacion.estado = "PENDIENTE"

        obligacion.save(
            update_fields=[
                "saldo_pendiente",
                "estado",
            ]
        )

        aplicaciones.append(aplicacion)

    return aplicaciones
