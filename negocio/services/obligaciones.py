from django.db.models import QuerySet

from negocio.models import Obligacion


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
