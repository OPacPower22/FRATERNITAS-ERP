"""
Servicios de pagos.
"""

from decimal import Decimal

from negocio.models import Pago


def distribuir_pago(obligacion, importe):
    importe = Decimal(str(importe))
    return {
        "obligacion": obligacion,
        "periodo": getattr(obligacion, "periodo", ""),
        "importe_aplicado": importe,
        "saldo_restante": obligacion.saldo_pendiente - importe,
    }


def registrar_pago(
        hermano,
        importe,
        fecha,
        forma_pago,
        referencia="",
        observaciones="",
):
    """
    Registra el hecho de negocio 'Pago'.

    No aplica obligaciones.
    No genera movimientos.
    No emite recibos.
    """

    pago = Pago.objects.create(
             hermano=hermano,
             fecha=fecha,
             importe=importe,
             forma_pago=forma_pago,
             referencia=referencia,
            observaciones=observaciones,
    )

    return pago
