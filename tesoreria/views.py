from django.shortcuts import render

from .forms import MovimientoIngresoForm

def index(request):
    return render(
        request,
        "tesoreria/index.html",
    )


def registrar_ingreso(request):

    form = MovimientoIngresoForm()

    return render(
        request,
        "tesoreria/registrar_ingreso.html",
        {
            "form": form,
        },
    )
