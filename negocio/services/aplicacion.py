"""
Motor de aplicación de pagos.
"""


def proponer_aplicacion_pago(
    obligaciones,
    importe,
):
    """
    Genera una propuesta de aplicación del pago.

    Parámetros
    ----------
    obligaciones : iterable
        Obligaciones pendientes ordenadas
        por antigüedad.

    importe : Decimal | float

    Retorna
    -------
    dict
    """

    disponible = importe

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
            {
                "obligacion": obligacion,
                "importe": aplicado,
            }
        )

        disponible -= aplicado

    return {
        "aplicaciones": aplicaciones,
        "saldo_a_favor": disponible,
    }