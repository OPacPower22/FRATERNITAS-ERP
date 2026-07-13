from django.shortcuts import render, redirect

from .forms import MovimientoIngresoForm


def index(request):
    return render(
        request,
        "tesoreria/index.html",
    )


def emitir_recibo(request):
    return render(
        request,
        "tesoreria/cu001/emitir_recibo.html",
    )


def registrar_ingreso(request):

    if request.method == "POST":

        form = MovimientoIngresoForm(request.POST)

        if form.is_valid():

            movimiento = form.save(commit=False)

            movimiento.tipo = "I"

            movimiento.save()

            return redirect("tesoreria")

    else:

        form = MovimientoIngresoForm()

    return render(
        request,
        "tesoreria/registrar_ingreso.html",
        {
            "form": form,
        },
    )