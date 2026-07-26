"""
Servicios de emisión de recibos.
"""

from core.services.folios import obtener_siguiente_folio

from documentos.models import Recibo
from negocio.models import AplicacionPago


def emitir_recibo(
    pago,
    usuario,
):
    """
    Genera el recibo oficial de un pago.

    Parámetros
    ----------
    pago : Pago
    usuario : User

    Retorna
    -------
    dict
    """

    # Evita generar dos recibos para el mismo pago
    recibo = Recibo.objects.filter(
        pago=pago,
    ).first()

    if recibo is None:

        folio = obtener_siguiente_folio("REC")

        recibo = Recibo.objects.create(
            pago=pago,
            folio=int(folio.split("-")[-1]),
            emitido_por=usuario,
        )

    aplicaciones = (
        AplicacionPago.objects
        .filter(
            pago=pago,
        )
        .select_related(
            "obligacion",
            "obligacion__concepto",
        )
    )

    return {
        "recibo": recibo,
        "folio": recibo.folio_formateado,
        "fecha": recibo.fecha_emision,
        "hermano": pago.hermano,
        "pago": pago,
        "aplicaciones": aplicaciones,
        "total": pago.importe,
        "estado": recibo.estado,
    }