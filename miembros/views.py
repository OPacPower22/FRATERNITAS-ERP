"""
Vistas del módulo de Miembros.

Expone el expediente del Hermano como servicio JSON para que el
CU-001 lo consuma sin recargar la página.
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

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
