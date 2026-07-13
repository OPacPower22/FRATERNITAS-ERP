from decimal import Decimal

from negocio.domain.propuesta import PropuestaAplicacion
from negocio.services.pagos import distribuir_pago


def calcular_propuesta(obligaciones, importe):
    """
    Genera una propuesta de aplicación del pago.

    Parámetros
    ----------
    obligaciones : iterable
        Objetos con atributo saldo_pendiente.
    importe : Decimal | int | float

    Retorna
    -------
    PropuestaAplicacion
    """
    disponible = Decimal(str(importe))
    aplicaciones = []

    for obligacion in obligaciones:
        if disponible <= 0:
            break

        saldo = obligacion.saldo_pendiente
        aplicado = min(saldo, disponible)

        aplicaciones.append(
            distribuir_pago(
                obligacion=obligacion,
                importe=aplicado,
            )
        )

        disponible -= aplicado

    propuesta = PropuestaAplicacion(
        aplicaciones=aplicaciones,
        saldo_a_favor=max(disponible, Decimal("0.00")),
    )

    return propuesta
