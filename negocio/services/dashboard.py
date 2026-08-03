"""Indicadores institucionales para el dashboard."""

from decimal import Decimal

from django.db.models import Exists, OuterRef, Sum
from django.utils import timezone

from miembros.models import Hermano
from negocio.models import Obligacion, Pago
from tesoreria.models import Movimiento


ESTADOS_PENDIENTES = ("PENDIENTE", "PARCIAL")


def obtener_indicadores() -> dict[str, Decimal | int]:
    """Obtiene los indicadores financieros y de membresía actuales."""
    hoy = timezone.localdate()

    # Los indicadores se calculan sobre Movimiento, que es el libro
    # único de la Tesorería: ahí conviven los movimientos generados
    # por el CU-001 y los importados del histórico. Tomar los
    # ingresos de Pago dejaba fuera todo lo anterior al sistema.
    ingresos_registrados = _suma_egresos(Movimiento.objects.filter(tipo="I"))
    egresos_registrados = _suma_egresos(Movimiento.objects.filter(tipo="E"))
    hermanos_activos = Hermano.objects.filter(estatus="ACTIVO")
    obligaciones_pendientes = Obligacion.objects.filter(
        hermano=OuterRef("pk"),
        estado__in=ESTADOS_PENDIENTES,
    )

    hermanos_deudores = hermanos_activos.filter(
        Exists(obligaciones_pendientes)
    ).count()

    # Si el mes en curso todavía no tiene movimientos, las tarjetas
    # muestran el último periodo con operación en lugar de ceros.
    periodo = _periodo_vigente(hoy)

    return {
        "saldo_caja": ingresos_registrados - egresos_registrados,
        "ingresos_mes": _suma_egresos(
            Movimiento.objects.filter(
                tipo="I",
                fecha__year=periodo.year,
                fecha__month=periodo.month,
            )
        ),
        "ingresos_totales": ingresos_registrados,
        "egresos_totales": egresos_registrados,
        "periodo_indicadores": periodo,
        "periodo_es_actual": (
            periodo.year == hoy.year and periodo.month == hoy.month
        ),
        "egresos_mes": _suma_egresos(
            Movimiento.objects.filter(
                tipo="E",
                fecha__year=periodo.year,
                fecha__month=periodo.month,
            )
        ),
        "total_hermanos": hermanos_activos.count(),
        "hermanos_corriente": hermanos_activos.exclude(
            Exists(obligaciones_pendientes)
        ).count(),
        "hermanos_deudores": hermanos_deudores,
    }


def _suma_pagos(pagos) -> Decimal:
    return pagos.aggregate(total=Sum("importe"))["total"] or Decimal("0.00")


def _periodo_vigente(hoy):
    """
    Mes que alimenta las tarjetas de ingresos y egresos.

    Es el mes en curso cuando tiene movimientos; si no, el último
    mes con operación registrada. Así el tablero nunca muestra
    ceros habiendo información en el libro.
    """

    if Movimiento.objects.filter(
        fecha__year=hoy.year,
        fecha__month=hoy.month,
    ).exists():
        return hoy

    ultimo = (
        Movimiento.objects
        .order_by("-fecha")
        .values_list("fecha", flat=True)
        .first()
    )

    return ultimo or hoy


def _suma_egresos(egresos) -> Decimal:
    return egresos.aggregate(total=Sum("total"))["total"] or Decimal("0.00")
