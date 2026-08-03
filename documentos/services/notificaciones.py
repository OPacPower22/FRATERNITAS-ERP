"""
Envío del recibo por correo electrónico y generación del
enlace de WhatsApp.

WhatsApp se resuelve mediante enlace wa.me (sin costo ni API):
el mensaje lleva el folio y la URL de verificación. El PDF se
adjunta únicamente en el envío por correo.
"""

import re
from urllib.parse import quote

from django.conf import settings
from django.core.mail import EmailMessage

from documentos.services.recibo_pdf import generar_recibo_pdf, nombre_archivo


LADA_PREDETERMINADA = "52"


def normalizar_telefono(numero, lada=LADA_PREDETERMINADA):
    """
    Deja el número en formato internacional sin signos.
    """

    digitos = re.sub(r"\D", "", numero or "")

    if not digitos:
        return ""

    if digitos.startswith("00"):
        digitos = digitos[2:]

    if len(digitos) == 10:
        digitos = f"{lada}{digitos}"

    return digitos


def construir_mensaje(datos, url_verificacion):
    """
    Texto institucional del recibo.
    """

    return (
        f"R∴L∴S∴ FRATERNIDAD No. 1\n"
        f"Recibo {datos['folio']}\n"
        f"Hermano: {datos['hermano']}\n"
        f"Importe: ${datos['total']:,.2f}\n\n"
        f"Verificación: {url_verificacion}"
    )


def construir_enlace_whatsapp(datos, url_verificacion, telefono=""):
    """
    Enlace wa.me con el mensaje precargado.
    """

    texto = quote(construir_mensaje(datos, url_verificacion))
    numero = normalizar_telefono(telefono)

    if numero:
        return f"https://wa.me/{numero}?text={texto}"

    return f"https://wa.me/?text={texto}"


def enviar_recibo_por_correo(
    datos,
    url_verificacion,
    destinatario="",
    remitente=None,
):
    """
    Envía el recibo en PDF por correo electrónico.

    Retorna ``True`` si el envío se realizó.
    """

    destinatario = (
        destinatario
        or getattr(datos["hermano"], "correo", "")
    ).strip()

    if not destinatario:
        return False

    pdf = generar_recibo_pdf(datos, url_verificacion)

    mensaje = EmailMessage(
        subject=f"Recibo {datos['folio']} · Fraternidad No. 1",
        body=construir_mensaje(datos, url_verificacion),
        from_email=remitente or getattr(
            settings,
            "DEFAULT_FROM_EMAIL",
            None,
        ),
        to=[destinatario],
    )

    mensaje.attach(
        nombre_archivo(datos),
        pdf,
        "application/pdf",
    )

    mensaje.send(fail_silently=False)

    return True
