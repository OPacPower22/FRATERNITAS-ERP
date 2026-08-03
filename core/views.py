from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from negocio.services.dashboard import obtener_indicadores


@login_required
def dashboard_redirect(request):
    return render(
        request,
        "core/dashboard.html",
        obtener_indicadores(),
    )
