"""
Vistas del módulo de Documentos.

Responsables de la descarga del recibo en PDF, del envío por
correo y de la verificación pública mediante código QR.
"""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from documentos.models import Recibo
from documentos.services import qr as servicio_qr
from documentos.services.notificaciones import (
    construir_enlace_whatsapp,
    enviar_recibo_por_correo,
)
from documentos.services.recibo_pdf import (
    generar_recibo_pdf,
    nombre_archivo,
)
from negocio.models import AplicacionPago


def _armar_datos(recibo):
    """
    Reconstruye la estructura del recibo a partir del modelo.
    """

    pago = recibo.pago

    aplicaciones = (
        AplicacionPago.objects
        .filter(pago=pago)
        .select_related(
            "obligacion",
            "obligacion__concepto",
        )
    )

    return {
        "recibo": recibo,
        "folio": recibo.folio_formateado,
        "fecha": recibo.fecha_emision,
        "hermano": pago.hermano,
        "pago": pago,
        "aplicaciones": aplicaciones,
        "total": pago.importe,
        "estado": recibo.estado,
    }


@login_required
def recibo_pdf(request, pk):
    """
    Descarga o previsualiza el recibo en PDF.

    GET /documentos/recibo/<pk>/pdf/?descargar=1
    """

    recibo = get_object_or_404(
        Recibo.objects.select_related(
            "pago",
            "pago__hermano",
        ),
        pk=pk,
    )

    datos = _armar_datos(recibo)

    url_verificacion = servicio_qr.construir_url_verificacion(
        recibo,
        request,
    )

    contenido = generar_recibo_pdf(datos, url_verificacion)

    respuesta = HttpResponse(
        contenido,
        content_type="application/pdf",
    )

    disposicion = (
        "attachment"
        if request.GET.get("descargar")
        else "inline"
    )

    respuesta["Content-Disposition"] = (
        f'{disposicion}; filename="{nombre_archivo(datos)}"'
    )

    return respuesta


@login_required
@require_POST
def enviar_recibo(request, pk):
    """
    Envía el recibo por correo electrónico.

    POST /documentos/recibo/<pk>/enviar/
    """

    recibo = get_object_or_404(
        Recibo.objects.select_related(
            "pago",
            "pago__hermano",
        ),
        pk=pk,
    )

    datos = _armar_datos(recibo)

    url_verificacion = servicio_qr.construir_url_verificacion(
        recibo,
        request,
    )

    destinatario = request.POST.get("correo", "").strip()

    try:
        enviado = enviar_recibo_por_correo(
            datos,
            url_verificacion,
            destinatario,
        )

    except Exception as error:
        return JsonResponse(
            {
                "enviado": False,
                "mensaje": str(error),
            },
            status=502,
        )

    return JsonResponse(
        {
            "enviado": enviado,
            "mensaje": (
                "Recibo enviado correctamente."
                if enviado
                else "El Hermano no tiene correo registrado."
            ),
        }
    )


@login_required
def enlace_whatsapp(request, pk):
    """
    Devuelve el enlace de WhatsApp con el recibo precargado.

    GET /documentos/recibo/<pk>/whatsapp/
    """

    recibo = get_object_or_404(
        Recibo.objects.select_related(
            "pago",
            "pago__hermano",
        ),
        pk=pk,
    )

    datos = _armar_datos(recibo)

    url_verificacion = servicio_qr.construir_url_verificacion(
        recibo,
        request,
    )

    telefono = (
        getattr(datos["hermano"], "celular", "")
        or getattr(datos["hermano"], "telefono", "")
    )

    return JsonResponse(
        {
            "url": construir_enlace_whatsapp(
                datos,
                url_verificacion,
                telefono,
            )
        }
    )


def verificar_recibo(request, token):
    """
    Verificación pública del recibo a partir del código QR.

    GET /documentos/verificar/<token>/
    """

    datos_token = servicio_qr.validar_token(token)

    recibo = None

    if datos_token:
        recibo = (
            Recibo.objects
            .select_related("pago", "pago__hermano")
            .filter(
                pk=datos_token.get("recibo"),
                folio=datos_token.get("folio"),
            )
            .first()
        )

    contexto = {
        "valido": recibo is not None,
        "recibo": recibo,
    }

    if recibo is not None:
        contexto["aplicaciones"] = (
            AplicacionPago.objects
            .filter(pago=recibo.pago)
            .select_related("obligacion__concepto")
        )

    return render(
        request,
        "documentos/verificar_recibo.html",
        contexto,
    )
