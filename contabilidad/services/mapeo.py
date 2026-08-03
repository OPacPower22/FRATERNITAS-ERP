"""
Mapeo entre el catálogo institucional existente (ConceptoContable,
forma_pago) y el catálogo de cuentas de partida doble.
"""

from contabilidad.models import Cuenta


class MapeoContableNoConfiguradoError(Exception):
    """Indica que no existe una cuenta contable configurada para
    resolver una póliza. Se lanza en vez de omitir en silencio,
    porque una póliza con destino ambiguo quedaría desbalanceada."""


FORMA_PAGO_CODIGO_CUENTA = {
    "EFECTIVO": "1.01.001",
    "TRANSFERENCIA": "1.01.002",
    "CHEQUE": "1.01.002",
    "TARJETA": "1.01.002",
}

CODIGO_ANTICIPOS_HERMANOS = "2.01.001"


def cuenta_para_concepto(concepto_contable):
    """Resuelve la Cuenta contable mapeada a un ConceptoContable."""

    try:
        return Cuenta.objects.get(
            concepto_contable=concepto_contable,
            activa=True,
        )
    except Cuenta.DoesNotExist as error:
        raise MapeoContableNoConfiguradoError(
            f"El concepto '{concepto_contable.nombre}' no tiene "
            "una cuenta contable asociada."
        ) from error


def cuenta_para_forma_pago(forma_pago):
    """Resuelve la Cuenta de Caja/Bancos según la forma de pago."""

    codigo = FORMA_PAGO_CODIGO_CUENTA.get(
        str(forma_pago or "").strip().upper()
    )

    if codigo is None:
        raise MapeoContableNoConfiguradoError(
            f"Forma de pago {forma_pago!r} no tiene cuenta "
            "contable asociada."
        )

    return Cuenta.objects.get(codigo=codigo, activa=True)


def cuenta_anticipos_hermanos():
    """Cuenta de pasivo donde se registran los excedentes de pago
    (anticipos) que no cubren ninguna obligación pendiente."""

    return Cuenta.objects.get(
        codigo=CODIGO_ANTICIPOS_HERMANOS,
        activa=True,
    )
