"""
Vistas del módulo de Miembros.

Expone el expediente del Hermano como servicio JSON para que el
CU-001 lo consuma sin recargar la página, y la ficha (directorio,
alta y edición) que alimenta ese mismo directorio.
"""

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from miembros.forms import HermanoForm
from miembros.models import Hermano
from miembros.services.expediente import obtener_expediente


@login_required
def api_expediente(request, pk):
    """
    Devuelve el expediente completo de un Hermano.

    GET /miembros/api/expediente/<pk>/
    """

    hermano = get_object_or_404(
        Hermano.objects.select_related("grado"),
        pk=pk,
    )

    return JsonResponse(
        obtener_expediente(hermano),
    )


@login_required
def api_directorio(request):
    """
    Lista ligera de Hermanos para el selector del CU-001.

    GET /miembros/api/directorio/?q=texto&estatus=ACTIVO
    """

    consulta = Hermano.objects.select_related("grado")

    estatus = request.GET.get("estatus", "ACTIVO").strip()

    if estatus and estatus.upper() != "TODOS":
        consulta = consulta.filter(estatus=estatus.upper())

    texto = request.GET.get("q", "").strip()

    if texto:
        from django.db.models import Q

        consulta = consulta.filter(
            Q(nombre__icontains=texto)
            | Q(apellido_paterno__icontains=texto)
            | Q(apellido_materno__icontains=texto)
            | Q(numero_control__icontains=texto)
            | Q(nombre_simbolico__icontains=texto)
        )

    return JsonResponse(
        {
            "resultados": [
                {
                    "id": hermano.pk,
                    "numero_control": hermano.numero_control,
                    "nombre_completo": str(hermano),
                    "grado": str(hermano.grado) if hermano.grado_id else "",
                    "estatus": hermano.estatus,
                }
                for hermano in consulta
            ]
        }
    )


@login_required
def directorio(request):
    """
    Ficha institucional: directorio de Hermanos, con alta y edición.

    GET /miembros/?q=texto&estatus=ACTIVO
    """

    consulta = Hermano.objects.select_related("grado").all()

    texto = request.GET.get("q", "").strip()
    if texto:
        consulta = consulta.filter(
            Q(nombre__icontains=texto)
            | Q(apellido_paterno__icontains=texto)
            | Q(apellido_materno__icontains=texto)
            | Q(numero_control__icontains=texto)
            | Q(nombre_simbolico__icontains=texto)
        )

    estatus = request.GET.get("estatus", "").strip().upper()
    if estatus:
        consulta = consulta.filter(estatus=estatus)

    return render(
        request,
        "miembros/directorio.html",
        {
            "hermanos": consulta,
            "texto_busqueda": texto,
            "estatus_filtro": estatus,
            "estatus_choices": Hermano.ESTATUS,
        },
    )


@login_required
def crear_hermano(request):
    """Alta de un nuevo Hermano en la ficha institucional."""

    if request.method == "POST":
        form = HermanoForm(request.POST, request.FILES)
        if form.is_valid():
            hermano = form.save()
            return redirect(f"{reverse('miembros_editar', args=[hermano.pk])}?guardado=1")
    else:
        form = HermanoForm()

    return render(
        request,
        "miembros/ficha_form.html",
        {
            "form": form,
            "hermano": None,
        },
    )


@login_required
def editar_hermano(request, pk):
    """Edición de la ficha de un Hermano existente."""

    hermano = get_object_or_404(Hermano, pk=pk)

    if request.method == "POST":
        form = HermanoForm(request.POST, request.FILES, instance=hermano)
        if form.is_valid():
            form.save()
            return redirect(f"{reverse('miembros_editar', args=[hermano.pk])}?guardado=1")
    else:
        form = HermanoForm(instance=hermano)

    return render(
        request,
        "miembros/ficha_form.html",
        {
            "form": form,
            "hermano": hermano,
            "guardado": request.GET.get("guardado") == "1",
        },
    )
