from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render

from documentos.models import Recibo
from miembros.models import DocumentoHermano, Hermano
from negocio.models import AplicacionPago
from miembros.services.expediente import obtener_detalle_expediente


@login_required
def lista_expedientes(request):
    """Lista de acceso a los expedientes maestros."""
    consulta = request.GET.get("q", "").strip()
    hermanos = Hermano.objects.select_related("grado")
    if consulta:
        hermanos = hermanos.filter(
            Q(numero_control__icontains=consulta)
            | Q(nombre__icontains=consulta)
            | Q(apellido_paterno__icontains=consulta)
            | Q(apellido_materno__icontains=consulta)
        )

    return render(
        request,
        "miembros/expediente/lista.html",
        {"hermanos": hermanos, "consulta": consulta},
    )


@login_required
def expediente_detalle(request, hermano_id):
    """Pantalla de consulta integral EXP-001."""
    hermano = get_object_or_404(
        Hermano.objects.select_related("grado", "creado_por", "actualizado_por"),
        pk=hermano_id,
    )
    return render(
        request,
        "miembros/expediente/detalle.html",
        obtener_detalle_expediente(hermano),
    )


@login_required
def descargar_documento(request, documento_id):
    """Entrega un documento del expediente como descarga autenticada."""
    documento = get_object_or_404(DocumentoHermano, pk=documento_id)
    if not documento.archivo:
        raise Http404("El documento no tiene archivo disponible.")
    return FileResponse(
        documento.archivo.open("rb"),
        as_attachment=True,
        filename=documento.archivo.name.rsplit("/", 1)[-1],
    )


@login_required
def ver_recibo(request, recibo_id):
    """Muestra un recibo existente sin alterar su emisión ni estado."""
    recibo = get_object_or_404(
        Recibo.objects.select_related("pago", "pago__hermano", "emitido_por"),
        pk=recibo_id,
    )
    aplicaciones = AplicacionPago.objects.filter(pago=recibo.pago).select_related(
        "obligacion__concepto"
    )
    return render(
        request,
        "miembros/expediente/recibo.html",
        {"recibo": recibo, "aplicaciones": aplicaciones},
    )
