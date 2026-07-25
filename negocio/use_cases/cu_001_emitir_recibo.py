"""
Caso de Uso CU-001

Emitir recibo de cuota ordinaria.

Orquesta el proceso completo.
"""

from negocio.services.obligaciones import obtener_obligaciones_pendientes
from negocio.services.aplicacion import proponer_aplicacion_pago
from negocio.services.pagos import registrar_pago
from negocio.services.contabilidad import generar_movimientos
from negocio.services.recibos import emitir_recibo


def ejecutar(
    hermano,
    importe,
    fecha,
    forma_pago,
):
    """
    Ejecuta el caso de uso CU-001.
    """

    obligaciones = obtener_obligaciones_pendientes(
        hermano,
    )

    propuesta = proponer_aplicacion_pago(
        obligaciones,
        importe,
    )

    return propuesta