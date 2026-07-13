"""
Servicios de pagos.
"""

from decimal import Decimal


def distribuir_pago(obligacion, importe):
    importe = Decimal(str(importe))
    return {
        "obligacion": obligacion,
        "periodo": getattr(obligacion, "periodo", ""),
        "importe_aplicado": importe,
        "saldo_restante": obligacion.saldo_pendiente - importe,
    }


def registrar_pago(*args, **kwargs):
    raise NotImplementedError(
        "registrar_pago() será implementado posteriormente."
    )
