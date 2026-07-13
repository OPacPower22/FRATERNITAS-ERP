from decimal import Decimal

from negocio.domain.propuesta import (
    AplicacionPropuesta,
    PropuestaAplicacion,
)


def proponer_aplicacion_pago(
    obligaciones,
    importe,
):
    """
    Genera una propuesta de aplicación del pago.
    """

    disponible = Decimal(str(importe))

    aplicaciones = []

    for obligacion in obligaciones:

        if disponible <= 0:
            break

        pendiente = obligacion.saldo_pendiente

        aplicado = min(
            disponible,
            pendiente,
        )

        aplicaciones.append(
            AplicacionPropuesta(
                obligacion=obligacion,
                importe=aplicado,
            )
        )

        disponible -= aplicado

    propuesta = PropuestaAplicacion()

    propuesta.importe_recibido = Decimal(str(importe))

    propuesta.saldo_a_favor = disponible

    propuesta.aplicaciones = aplicaciones

    return propuesta