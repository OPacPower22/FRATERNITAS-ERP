"""
Servicio de verificación y validación de recibos mediante QR.

El token NO se almacena en la base de datos: se firma
criptográficamente con la SECRET_KEY del proyecto usando
``django.core.signing``. Esto evita alterar el modelo Recibo
y garantiza que un QR alterado sea rechazado.
"""

import base64
from io import BytesIO

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from django.core import signing
from django.urls import reverse


SALT = "fraternitas.documentos.recibo"


def firmar_recibo(recibo):
    """
    Genera el token firmado de un recibo.
    """

    return signing.dumps(
        {
            "recibo": recibo.pk,
            "folio": recibo.folio,
        },
        salt=SALT,
    )


def validar_token(token, max_age=None):
    """
    Valida un token de verificación.

    Retorna el diccionario firmado o ``None`` si el token es
    inválido, fue alterado o expiró.
    """

    try:
        return signing.loads(
            token,
            salt=SALT,
            max_age=max_age,
        )

    except signing.BadSignature:
        return None


def construir_url_verificacion(recibo, request=None):
    """
    URL pública de verificación del recibo.
    """

    ruta = reverse(
        "documentos_verificar_recibo",
        args=[firmar_recibo(recibo)],
    )

    if request is None:
        return ruta

    return request.build_absolute_uri(ruta)


def generar_qr_png(contenido):
    """
    Genera el PNG del código QR como bytes.
    """

    codigo = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )

    codigo.add_data(contenido)
    codigo.make(fit=True)

    imagen = codigo.make_image(
        fill_color="black",
        back_color="white",
    )

    buffer = BytesIO()
    imagen.save(buffer, format="PNG")

    return buffer.getvalue()


def generar_qr_base64(contenido):
    """
    Devuelve el QR listo para incrustarse en una plantilla HTML.
    """

    datos = base64.b64encode(
        generar_qr_png(contenido)
    ).decode("ascii")

    return f"data:image/png;base64,{datos}"
