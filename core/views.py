from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


@login_required
def dashboard_redirect(request):

    if request.user.is_superuser:
        return render(request, "core/dashboard_admin.html")

    grupos = request.user.groups.values_list("name", flat=True)

    if "Venerable Maestro" in grupos:
        return render(request, "core/dashboard_vm.html")

    if "Secretario" in grupos:
        return render(request, "core/dashboard_secretario.html")

    if "Tesorero" in grupos:
        return render(request, "core/dashboard_tesorero.html")

    return render(request, "core/dashboard_consulta.html")
