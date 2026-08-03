"""
Vistas del módulo de Documentos.

Responsables de la descarga del recibo en PDF, del envío por
correo y de la verificación pública mediante código QR.
"""

from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.services.folios import obtener_siguiente_folio
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
from miembros.models import Hermano
from negocio.models import AplicacionPago, Pago
from negocio.services.aplicacion import calcular_propuesta
from negocio.services.obligaciones import obtener_obligaciones_pendientes


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
def recibo_pdf_vista_previa(request):
    """
    Vista previa en PDF del recibo antes de confirmar el cobro.

    No persiste nada: el folio es provisional (no consume el
    consecutivo) y no existe un Recibo real todavía.

    POST /documentos/recibo/vista-previa/pdf/
    """

    hermano = get_object_or_404(
        Hermano.objects.select_related("grado"),
        pk=request.POST.get("hermano"),
        estatus="ACTIVO",
    )

    try:
        importe = Decimal(request.POST.get("importe", ""))
    except InvalidOperation:
        return HttpResponseBadRequest("Importe inválido.")

    obligaciones = obtener_obligaciones_pendientes(hermano)
    propuesta = calcular_propuesta(obligaciones, importe)

    datos = {
        "folio": f"{obtener_siguiente_folio('REC', guardar=False)} (provisional)",
        "fecha": timezone.now(),
        "hermano": hermano,
        "pago": Pago(
            forma_pago=request.POST.get("forma_pago", "EFECTIVO"),
            referencia=request.POST.get("referencia", ""),
        ),
        "aplicaciones": propuesta.aplicaciones,
        "total": importe,
        "estado": "BORRADOR",
    }

    contenido = generar_recibo_pdf(
        datos,
        "Vista previa — no válida para verificación. "
        "El código oficial se genera al confirmar el cobro.",
    )

    respuesta = HttpResponse(
        contenido,
        content_type="application/pdf",
    )
    respuesta["Content-Disposition"] = (
        f'inline; filename="vista-previa-{hermano.numero_control}.pdf"'
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
