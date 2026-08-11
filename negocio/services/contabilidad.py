"""
Generación de movimientos contables.
"""

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

from catalogos.models import ConceptoContable, DistribucionCapita, TarifaObligacion
from negocio.models import AplicacionPago, Pago
from tesoreria.models import Movimiento


CENTAVO = Decimal("0.01")


def _prorratear_distribucion(importe_aplicado, distribuciones):
    """Distribuye un importe aplicado conservando el total a centavos."""
    total_distribucion = sum(
        (distribucion.importe for distribucion in distribuciones),
        Decimal("0.00"),
    )
    if total_distribucion <= Decimal("0.00"):
        return []

    importe_aplicado = Decimal(importe_aplicado)
    importes = []
    acumulado = Decimal("0.00")

    for distribucion in distribuciones[:-1]:
        importe = (
            importe_aplicado * distribucion.importe / total_distribucion
        ).quantize(CENTAVO, rounding=ROUND_HALF_UP)
        importes.append((distribucion, importe))
        acumulado += importe

    ultima_distribucion = distribuciones[-1]
    importes.append((ultima_distribucion, importe_aplicado - acumulado))
    return importes


def _distribuir_por_concepto(importes_por_concepto):
    """Reparte, según DISTRIBUCION_CAPITA, un {concepto_origen_id: importe}.

    Regresa tres diccionarios indexados por ``concepto_destino_id``: los
    importes repartidos, la instancia de ``ConceptoContable`` de destino y
    su ``grupo``/``orden`` (para poder mostrarlo agrupado, p. ej. GLUM vs.
    Local, en el mismo orden institucional configurado).
    """
    distribuciones = (
        DistribucionCapita.objects.filter(
            activa=True,
            concepto_origen_id__in=importes_por_concepto,
        )
        .select_related("concepto_destino")
        .order_by("concepto_origen_id", "orden", "id")
    )
    distribuciones_por_origen = defaultdict(list)
    for distribucion in distribuciones:
        distribuciones_por_origen[distribucion.concepto_origen_id].append(
            distribucion
        )

    importes_por_destino = defaultdict(lambda: Decimal("0.00"))
    conceptos_destino = {}
    metadatos_destino = {}
    for concepto_origen_id, importe_aplicado in importes_por_concepto.items():
        for distribucion, importe in _prorratear_distribucion(
            importe_aplicado,
            distribuciones_por_origen[concepto_origen_id],
        ):
            importes_por_destino[distribucion.concepto_destino_id] += importe
            conceptos_destino[distribucion.concepto_destino_id] = (
                distribucion.concepto_destino
            )
            metadatos_destino[distribucion.concepto_destino_id] = (
                distribucion.grupo,
                distribucion.orden,
            )

    return importes_por_destino, conceptos_destino, metadatos_destino


def generar_movimientos(
    pago,
):
    """Genera los movimientos institucionales derivados de un pago aplicado.

    Sólo se consideran aplicaciones definitivas del pago y reglas de
    distribución activas. La unicidad ``(pago, concepto_contable)`` permite
    que llamadas repetidas recuperen el movimiento existente sin duplicarlo.
    """
    if not isinstance(pago, Pago):
        raise TypeError("pago debe ser una instancia de Pago.")

    with transaction.atomic():
        pago = Pago.objects.select_for_update().get(pk=pago.pk)
        aplicaciones = list(
            AplicacionPago.objects.filter(pago=pago)
            .select_related("obligacion__concepto")
            .order_by("id")
        )

        if not aplicaciones:
            return []

        importes_por_concepto = defaultdict(lambda: Decimal("0.00"))
        for aplicacion in aplicaciones:
            importes_por_concepto[aplicacion.obligacion.concepto_id] += (
                aplicacion.importe_aplicado
            )

        importes_por_destino, conceptos_destino, _metadatos = (
            _distribuir_por_concepto(importes_por_concepto)
        )

        movimientos = []
        for concepto_id in sorted(importes_por_destino):
            concepto = conceptos_destino[concepto_id]
            importe = importes_por_destino[concepto_id].quantize(
                CENTAVO,
                rounding=ROUND_HALF_UP,
            )
            movimiento, _ = Movimiento.objects.get_or_create(
                pago=pago,
                concepto_contable=concepto,
                defaults={
                    "tipo": "I",
                    "hermano": pago.hermano,
                    "concepto": concepto.nombre,
                    "fecha": pago.fecha,
                    # El modelo heredado no tiene una columna genérica de
                    # importe; ``otros`` conserva el total sin reasignar el
                    # destino institucional a un fondo distinto.
                    "otros": importe,
                    "total": Decimal("0.00"),
                },
            )
            movimientos.append(movimiento)

        return movimientos


def _formatear_distribucion(importes_por_concepto):
    """Construye la vista GLUM/Local de un reparto, sin persistir nada."""

    importes_por_destino, conceptos_destino, metadatos_destino = (
        _distribuir_por_concepto(importes_por_concepto)
    )

    filas = sorted(
        importes_por_destino,
        key=lambda concepto_id: (
            metadatos_destino[concepto_id][0] != "GLUM",
            metadatos_destino[concepto_id][1],
        ),
    )
    filas = [
        {
            "concepto": conceptos_destino[concepto_id].nombre,
            "grupo": metadatos_destino[concepto_id][0],
            "importe": importes_por_destino[concepto_id].quantize(
                CENTAVO, rounding=ROUND_HALF_UP,
            ),
        }
        for concepto_id in filas
    ]

    total_glum = sum(
        (fila["importe"] for fila in filas if fila["grupo"] == "GLUM"),
        Decimal("0.00"),
    )
    total_local = sum(
        (fila["importe"] for fila in filas if fila["grupo"] != "GLUM"),
        Decimal("0.00"),
    )

    return {
        "filas": filas,
        "total_glum": total_glum,
        "total_local": total_local,
        "total": total_glum + total_local,
    }


def calcular_distribucion_institucional(aplicaciones):
    """Calcula cómo se reparte (GLUM/Local) una cantidad ya aplicada.

    Acepta la misma lista de aplicaciones que produce
    ``negocio.services.aplicacion.calcular_propuesta`` (o las
    ``AplicacionPago`` reales de un recibo ya confirmado). No persiste
    nada: es sólo para mostrarle al Tesorero, en vivo, el reparto
    institucional de la cantidad pagada según DISTRIBUCION_CAPITA.
    """

    importes_por_concepto = defaultdict(lambda: Decimal("0.00"))
    for aplicacion in aplicaciones:
        importes_por_concepto[aplicacion.obligacion.concepto_id] += (
            aplicacion.importe_aplicado
        )

    if not importes_por_concepto:
        return None

    return _formatear_distribucion(importes_por_concepto)


def distribucion_referencia_cuota_actual():
    """Reparto GLUM/Local de la Cuota Ordinaria vigente, como referencia.

    Se muestra en CU-001 mientras no hay una propuesta calculada, para
    que el Tesorero siempre vea cómo está configurado el reparto
    institucional de una cápita completa.
    """

    try:
        concepto_cuota = ConceptoContable.objects.get(clave="CUOTA_ORD")
        tarifa = TarifaObligacion.objects.get(
            concepto=concepto_cuota,
            estado="ACTIVA",
        )
    except (ConceptoContable.DoesNotExist, TarifaObligacion.DoesNotExist):
        return None

    return _formatear_distribucion({concepto_cuota.id: tarifa.importe})
