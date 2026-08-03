"""
Verificación de comprobantes bancarios de transferencia.

Control riguroso: un pago por TRANSFERENCIA no puede confirmarse en
CU-001 sin un comprobante adjunto cuyo monto coincida exactamente
con el importe capturado, y cuyo folio bancario no haya sido usado
ya en otro cobro. El emisor se captura para el expediente pero su
coincidencia con el Hermano la confirma visualmente el tesorero
(casilla de verificación), no el sistema.
"""

from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from documentos.models import ComprobanteTransferencia, validar_tamano_comprobante


_validar_extension = FileExtensionValidator(
    allowed_extensions=["pdf", "jpg", "jpeg", "png"]
)


def validar_comprobante_transferencia(
    *,
    archivo,
    folio_bancario,
    emisor,
    monto,
    verificado,
    importe_pago,
):
    """
    Valida los datos de un comprobante de transferencia contra el
    pago que se está registrando.

    Retorna la lista de errores encontrados (vacía si es válido).
    """

    errores = []

    if not archivo:
        errores.append(
            "Adjunte el comprobante bancario de la transferencia."
        )
    else:
        try:
            _validar_extension(archivo)
            validar_tamano_comprobante(archivo)
        except ValidationError as error:
            errores.extend(error.messages)

    folio_bancario = (folio_bancario or "").strip()
    if not folio_bancario:
        errores.append(
            "Capture el folio o referencia del comprobante bancario."
        )
    elif ComprobanteTransferencia.objects.filter(
        folio_bancario=folio_bancario
    ).exists():
        errores.append(
            f"El folio de comprobante «{folio_bancario}» ya fue "
            "utilizado en otro cobro."
        )

    emisor = (emisor or "").strip()
    if not emisor:
        errores.append(
            "Capture el nombre del emisor que aparece en el comprobante."
        )

    monto_decimal = None
    monto_texto = (monto or "").strip() if isinstance(monto, str) else monto

    if not monto_texto:
        errores.append(
            "Capture el monto que muestra el comprobante bancario."
        )
    else:
        try:
            monto_decimal = Decimal(str(monto_texto))
        except InvalidOperation:
            errores.append(
                "El monto del comprobante no es un número válido."
            )
        else:
            if monto_decimal != importe_pago:
                errores.append(
                    f"El monto del comprobante (${monto_decimal}) no "
                    f"coincide con el importe capturado (${importe_pago})."
                )

    if not verificado:
        errores.append(
            "Confirme que verificó que el emisor y el monto del "
            "comprobante son correctos."
        )

    return errores, folio_bancario, emisor, monto_decimal
