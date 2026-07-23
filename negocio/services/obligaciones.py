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

def generar_obligaciones(periodo):

    creadas = 0

    hermanos = Hermano.objects.filter(
        estatus="ACTIVO",
    )

    tarifas = TarifaObligacion.objects.filter(
        activa=True,
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
                    "fecha_vencimiento": tarifa.fecha_vencimiento,
                    "estado": "PENDIENTE",
                },
            )

            if creada:
                creadas += 1

    print("\nOBLIGACIONES")
    print(f"Creadas.....: {creadas}")