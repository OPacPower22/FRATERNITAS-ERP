"""
CU-002 - Cobro Integral

Orquesta el proceso completo de cobro.
"""

from negocio.domain.cobro_resultado import CobroResultado

from negocio.services.obligaciones import (
    obtener_obligaciones_pendientes,
)

from negocio.services.aplicacion import (
    calcular_propuesta,
    ejecutar_propuesta,
)

from negocio.services.pagos import (
    registrar_pago,
)

from negocio.services.recibos import (
    emitir_recibo,
)


def ejecutar_cobro(
    *,
    hermano,
    importe,
    fecha,
    forma_pago,
    usuario,
    referencia="",
    observaciones="",
):
    """
    Ejecuta el proceso completo de cobro.
    """

    resultado = CobroResultado()

    obligaciones = obtener_obligaciones_pendientes(
        hermano,
    )

    propuesta = calcular_propuesta(
        obligaciones,
        importe,
    )

    if not propuesta.aplicaciones:
        resultado.errores.append(
            "El hermano no tiene obligaciones pendientes."
        )
        return resultado

    pago = registrar_pago(
        hermano=hermano,
        importe=importe,
        fecha=fecha,
        forma_pago=forma_pago,
        referencia=referencia,
        observaciones=observaciones,
    )

    ejecutar_propuesta(
        pago,
        propuesta,
    )

    recibo = emitir_recibo(
        pago,
        usuario,
    )

    resultado.pago = pago
    resultado.propuesta = propuesta
    resultado.recibo = recibo
    resultado.saldo_a_favor = propuesta.saldo_a_favor
    resultado.exitoso = True

    return resultado
