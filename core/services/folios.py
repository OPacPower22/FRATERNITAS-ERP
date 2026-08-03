"""
Servicio institucional de generación de folios.

Todos los documentos oficiales del sistema deben obtener su
folio mediante este servicio.

Ejemplos:

REC-2026-000001
PAG-2026-000001
OBL-2026-000001
MOV-2026-000001
"""

from django.db import transaction

from catalogos.models import ParametroSistema


TIPOS_VALIDOS = {
    "REC": "REC",
    "PAG": "PAG",
    "OBL": "OBL",
    "MOV": "MOV",
    "AUD": "AUD",
    "PD": "PD",
    "PI": "PI",
    "PE": "PE",
}


@transaction.atomic
def obtener_siguiente_folio(
    tipo: str,
    guardar: bool = True,
) -> str:
    """
    Obtiene el siguiente folio institucional.

    Parámetros
    ----------
    tipo : str
        REC, PAG, OBL, MOV, AUD

    guardar : bool
        Si es False, no incrementa el consecutivo.
        Útil para pruebas.

    Retorna
    -------
    str

    Ejemplo
    --------
    REC-2026-000001
    """

    tipo = tipo.upper()

    if tipo not in TIPOS_VALIDOS:
        raise ValueError(
            f"Tipo de folio no válido: {tipo}"
        )

    ejercicio = ParametroSistema.objects.get(
        clave="EJERCICIO",
    )

    consecutivo = ParametroSistema.objects.select_for_update().get(
        clave=tipo,
    )

    siguiente = int(consecutivo.valor) + 1

    folio = (
        f"{tipo}-"
        f"{ejercicio.valor}-"
        f"{siguiente:06d}"
    )

    if guardar:

        consecutivo.valor = str(siguiente)

        consecutivo.save(
            update_fields=[
                "valor",
            ]
        )

    return folio
