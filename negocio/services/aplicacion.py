from decimal import Decimal

from django.db import transaction

from negocio.domain.propuesta import (
    AplicacionPago,
    PropuestaAplicacion,
)
from negocio.models import AplicacionPago as AplicacionPagoModel


def calcular_propuesta(
    obligaciones,
    importe,
):
    """
    Calcula la propuesta de aplicación de un pago
    utilizando el criterio FIFO.
    """

    disponible = Decimal(str(importe))

    propuesta = PropuestaAplicacion()

    for obligacion in obligaciones:

        if disponible <= 0:
            break

        aplicado = min(
            obligacion.saldo_pendiente,
            disponible,
        )

        propuesta.aplicaciones.append(
            AplicacionPago(
                obligacion=obligacion,
                periodo=obligacion.periodo,
                importe_aplicado=aplicado,
                saldo_restante=(
                    obligacion.saldo_pendiente
                    - aplicado
                ),
            )
        )

        disponible -= aplicado

    propuesta.saldo_a_favor = max(
        disponible,
        Decimal("0.00"),
    )

    return propuesta


@transaction.atomic
def ejecutar_propuesta(
    pago,
    propuesta,
):
    """
    Ejecuta una propuesta de aplicación de pago.
    """

    for aplicacion in propuesta.aplicaciones:

        obligacion = aplicacion.obligacion

        AplicacionPagoModel.objects.create(
            pago=pago,
            obligacion=obligacion,
            importe_aplicado=aplicacion.importe_aplicado,
        )

        obligacion.saldo_pendiente = (
            aplicacion.saldo_restante
        )

        if obligacion.saldo_pendiente == 0:
            obligacion.estado = "LIQUIDADA"
        else:
            obligacion.estado = "PARCIAL"

        obligacion.save()

    return propuesta