"""
Generación de pólizas contables (partida doble) a partir de un Pago.

Reutiliza ``negocio.services.contabilidad.generar_movimientos`` para
no reimplementar el prorrateo institucional: cada línea de Haber de
la póliza corresponde exactamente a un Movimiento ya generado. El
excedente de un pago que no cubre ninguna obligación pendiente
(anticipo) se registra como pasivo en vez de perderse, que es lo que
ocurre hoy en el libro de una sola entrada.
"""

from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction

from core.services.folios import obtener_siguiente_folio
from contabilidad.models import EjercicioContable, PartidaPoliza, Poliza
from contabilidad.services.mapeo import (
    cuenta_anticipos_hermanos,
    cuenta_para_concepto,
    cuenta_para_forma_pago,
)
from negocio.models import Pago
from negocio.services.contabilidad import generar_movimientos


CENTAVO = Decimal("0.01")


class EjercicioNoConfiguradoError(Exception):
    """No existe un EjercicioContable vigente para la fecha del pago."""


def generar_poliza_desde_pago(pago):
    """
    Genera (o recupera, si ya existe) la Póliza de Ingreso balanceada
    correspondiente a un Pago.

    Idempotente: llamar dos veces con el mismo pago no duplica la
    póliza ni sus partidas.
    """

    if not isinstance(pago, Pago):
        raise TypeError("pago debe ser una instancia de Pago.")

    with transaction.atomic():

        pago = Pago.objects.select_for_update().get(pk=pago.pk)

        poliza_existente = Poliza.objects.filter(pago=pago).first()
        if poliza_existente is not None:
            return poliza_existente

        if pago.estado != "REGISTRADO":
            return None

        movimientos = generar_movimientos(pago)

        total_aplicado = sum(
            (movimiento.otros for movimiento in movimientos),
            Decimal("0.00"),
        )

        excedente = (pago.importe - total_aplicado).quantize(
            CENTAVO,
            rounding=ROUND_HALF_UP,
        )

        if excedente < 0:
            excedente = Decimal("0.00")

        if not movimientos and excedente <= 0:
            return None

        ejercicio = EjercicioContable.objects.actual(pago.fecha)

        if ejercicio is None:
            raise EjercicioNoConfiguradoError(
                f"No hay un ejercicio contable configurado para "
                f"la fecha {pago.fecha}."
            )

        cuenta_efectivo = cuenta_para_forma_pago(pago.forma_pago)

        poliza = Poliza.objects.create(
            ejercicio=ejercicio,
            tipo="INGRESO",
            folio=obtener_siguiente_folio("PI"),
            fecha=pago.fecha,
            concepto=f"Cobro a {pago.hermano} — Pago #{pago.pk}",
            pago=pago,
            origen="PAGO",
        )

        PartidaPoliza.objects.create(
            poliza=poliza,
            cuenta=cuenta_efectivo,
            debe=pago.importe,
            haber=Decimal("0.00"),
            concepto="Cobro registrado",
            orden=0,
        )

        orden = 1

        for movimiento in movimientos:

            PartidaPoliza.objects.create(
                poliza=poliza,
                cuenta=cuenta_para_concepto(movimiento.concepto_contable),
                debe=Decimal("0.00"),
                haber=movimiento.otros,
                concepto=movimiento.concepto_contable.nombre,
                orden=orden,
            )

            orden += 1

        if excedente > 0:

            PartidaPoliza.objects.create(
                poliza=poliza,
                cuenta=cuenta_anticipos_hermanos(),
                debe=Decimal("0.00"),
                haber=excedente,
                concepto="Anticipo / saldo a favor del Hermano",
                orden=orden,
            )

        poliza.validar_balance()

        return poliza
