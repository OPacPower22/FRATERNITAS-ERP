from django.db.models import QuerySet
from negocio.models import Obligacion
from decimal import Decimal
from catalogos.models import TarifaObligacion
from miembros.models import Hermano


def obtener_obligaciones_pendientes(hermano) -> QuerySet:
    """
    Recupera las obligaciones pendientes o parciales
    ordenadas por vencimiento.
    """
    return (
        Obligacion.objects
        .filter(
            hermano=hermano,
            estado__in=[
                "PENDIENTE",
                "PARCIAL",
            ],
        )
        .order_by("fecha_vencimiento")
    )

def _fecha_vencimiento(periodo, dia=10):
    """
    Calcula la fecha de vencimiento a partir del periodo.

    Acepta los formatos ``AAAA-MM`` y ``AAAA``.
    """

    from datetime import date

    partes = str(periodo).strip().split("-")

    anio = int(partes[0])
    mes = int(partes[1]) if len(partes) > 1 else 12

    return date(anio, mes, dia)


def generar_obligaciones(periodo, fecha_vencimiento=None):
    """
    Genera las obligaciones del periodo para los Hermanos activos.

    ``periodo`` se expresa como ``AAAA-MM``.
    """

    creadas = 0

    if fecha_vencimiento is None:
        fecha_vencimiento = _fecha_vencimiento(periodo)

    hermanos = Hermano.objects.filter(
        estatus="ACTIVO",
    )

    tarifas = (
        TarifaObligacion.objects
        .filter(estado__in=["ACTIVA", "ACTIVO"])
        .select_related("concepto")
    )

    for hermano in hermanos:

        for tarifa in tarifas:

            _, creada = Obligacion.objects.get_or_create(
                hermano=hermano,
                concepto=tarifa.concepto,
                periodo=periodo,
                defaults={
                    "importe": tarifa.importe,
                    "saldo_pendiente": tarifa.importe,
                    "fecha_vencimiento": fecha_vencimiento,
                    "estado": "PENDIENTE",
                },
            )

            if creada:
                creadas += 1

    print("\nOBLIGACIONES")
    print(f"Periodo.....: {periodo}")
    print(f"Creadas.....: {creadas}")

    return creadas
