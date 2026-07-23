from decimal import Decimal

from catalogos.models import (
    ConceptoContable,
    TarifaObligacion,
)
from miembros.models import Hermano
from negocio.models import Obligacion
from catalogos.models import ParametroSistema

def obtener_importe_capita():
    """
    Obtiene el importe vigente de la Cápita
    desde los parámetros institucionales.
    """

    parametro = ParametroSistema.objects.get(
        clave="CAPITA_MENSUAL",
    )

    return Decimal(parametro.valor)

def generar_capitas_mensuales(
    periodo,
    fecha_vencimiento,
):
    """
    Genera una Cápita mensual para cada Hermano ACTIVO.
    """

    concepto = ConceptoContable.objects.get(
        clave="CAPITA",
    )

    importe = obtener_importe_capita()

    hermanos = Hermano.objects.filter(
        estatus="ACTIVO",
    )

    creadas = 0
    actualizadas = 0

    for hermano in hermanos:

        _, creada = Obligacion.objects.update_or_create(
            hermano=hermano,
            concepto=concepto,
            periodo=periodo,
            defaults={
                "importe": importe,
                "saldo_pendiente": importe,
                "fecha_vencimiento": fecha_vencimiento,
                "estado": "PENDIENTE",
            },
        )

        if creada:
            creadas += 1
        else:
            actualizadas += 1

    print("\nCAPITAS MENSUALES")
    print(f"Creadas.....: {creadas}")
    print(f"Actualizadas: {actualizadas}")
