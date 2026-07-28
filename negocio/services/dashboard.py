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
    ingresos_registrados = _suma_pagos(Pago.objects.filter(estado="REGISTRADO"))
    egresos_registrados = _suma_egresos(Movimiento.objects.filter(tipo="E"))
    hermanos_activos = Hermano.objects.filter(estatus="ACTIVO")
    obligaciones_pendientes = Obligacion.objects.filter(
        hermano=OuterRef("pk"),
        estado__in=ESTADOS_PENDIENTES,
    )

    hermanos_deudores = hermanos_activos.filter(
        Exists(obligaciones_pendientes)
    ).count()

    return {
        "saldo_caja": ingresos_registrados - egresos_registrados,
        "ingresos_mes": _suma_pagos(
            Pago.objects.filter(
                estado="REGISTRADO",
                fecha__year=hoy.year,
                fecha__month=hoy.month,
            )
        ),
        "egresos_mes": _suma_egresos(
            Movimiento.objects.filter(
                tipo="E",
                fecha__year=hoy.year,
                fecha__month=hoy.month,
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


def _suma_egresos(egresos) -> Decimal:
    return egresos.aggregate(total=Sum("total"))["total"] or Decimal("0.00")
