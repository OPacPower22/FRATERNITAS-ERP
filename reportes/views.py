from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from contabilidad.models import Cuenta, PartidaPoliza, Poliza
from reportes.services.informe_mensual_pdf import (
    generar_informe_mensual_pdf,
    nombre_archivo,
)
from tesoreria.services.informe_mensual import (
    MESES,
    anios_disponibles,
    calcular_informe_mensual,
)


GRUPOS_TIPO_CUENTA = [
    ("ACTIVO", "Activo", "#0d6efd", "bi-bank"),
    ("PASIVO", "Pasivo", "#fd7e14", "bi-credit-card"),
    ("PATRIMONIO", "Patrimonio", "#6f42c1", "bi-shield-check"),
    ("INGRESO", "Ingresos", "#198754", "bi-graph-up-arrow"),
    ("GASTO", "Gastos", "#dc3545", "bi-graph-down-arrow"),
]


@login_required
def index(request):
    """Portada de CU-003 · Reportes."""
    return render(
        request,
        "reportes/cu003/index.html",
        {
            "total_cuentas": Cuenta.objects.count(),
            "total_polizas": Poliza.objects.count(),
        },
    )


@login_required
def catalogo_cuentas(request):
    """Catálogo de cuentas contables, agrupado por tipo (Activo,
    Pasivo, Patrimonio, Ingreso, Gasto) en orden jerárquico."""

    cuentas = Cuenta.objects.select_related("cuenta_padre", "concepto_contable").all()

    grupos = []

    for tipo, etiqueta, color, icono in GRUPOS_TIPO_CUENTA:

        cuentas_del_grupo = [cuenta for cuenta in cuentas if cuenta.tipo == tipo]

        if cuentas_del_grupo:
            grupos.append({
                "tipo": tipo,
                "etiqueta": etiqueta,
                "color": color,
                "icono": icono,
                "cuentas": cuentas_del_grupo,
            })

    return render(
        request,
        "reportes/cu003/catalogo_cuentas.html",
        {
            "grupos": grupos,
        },
    )


@login_required
def libro_diario(request):
    """Libro Diario: todas las pólizas contables con sus partidas."""
    polizas = (
        Poliza.objects
        .select_related("ejercicio", "pago__hermano", "elaborada_por")
        .prefetch_related("partidas__cuenta")
        .annotate(total_debe=Sum("partidas__debe"))
        .order_by("fecha", "folio")
    )

    return render(
        request,
        "reportes/cu003/libro_diario.html",
        {
            "polizas": polizas,
        },
    )


@login_required
def libro_mayor(request):
    """
    Libro Mayor: balanza de comprobación de todas las cuentas y,
    si se selecciona una, el detalle de sus movimientos con saldo
    acumulado.
    """

    balanza = []

    cuentas = (
        Cuenta.objects
        .filter(acepta_movimientos=True)
        .order_by("codigo")
    )

    for cuenta in cuentas:

        totales = cuenta.partidas.aggregate(
            debe=Sum("debe"),
            haber=Sum("haber"),
        )

        debe = totales["debe"] or Decimal("0.00")
        haber = totales["haber"] or Decimal("0.00")

        balanza.append({
            "cuenta": cuenta,
            "debe": debe,
            "haber": haber,
            "saldo": debe - haber,
        })

    cuenta_seleccionada = None
    movimientos = []

    cuenta_id = request.GET.get("cuenta")

    if cuenta_id:

        cuenta_seleccionada = get_object_or_404(Cuenta, pk=cuenta_id)

        acumulado = Decimal("0.00")

        for partida in (
            PartidaPoliza.objects
            .filter(cuenta=cuenta_seleccionada)
            .select_related("poliza")
            .order_by("poliza__fecha", "poliza__folio", "orden")
        ):

            acumulado += partida.debe - partida.haber

            movimientos.append({
                "partida": partida,
                "acumulado": acumulado,
            })

    return render(
        request,
        "reportes/cu003/libro_mayor.html",
        {
            "balanza": balanza,
            "cuenta_seleccionada": cuenta_seleccionada,
            "movimientos": movimientos,
        },
    )


def _periodo_seleccionado(request):

    hoy = timezone.localdate()

    anio = int(request.GET.get("anio") or hoy.year)
    mes = int(request.GET.get("mes") or hoy.month)

    return anio, mes


@login_required
def informe_mensual(request):
    """
    Informe Mensual de Resultados Financieros: ingreso, egreso y
    saldo por fondo (Cápitas, Aniversario, Saco de Beneficencia,
    Taller Benito Juárez y Otros), en el formato histórico del
    Tesorero.
    """

    anio, mes = _periodo_seleccionado(request)

    informe = calcular_informe_mensual(anio, mes)

    return render(
        request,
        "reportes/cu003/informe_mensual.html",
        {
            "informe": informe,
            "anios": anios_disponibles() or [timezone.localdate().year],
            "meses": MESES.items(),
        },
    )


@login_required
def informe_mensual_pdf(request):
    """Descarga o previsualiza el Informe Mensual en PDF."""

    anio, mes = _periodo_seleccionado(request)

    informe = calcular_informe_mensual(anio, mes)

    contenido = generar_informe_mensual_pdf(informe)

    respuesta = HttpResponse(contenido, content_type="application/pdf")

    disposicion = "attachment" if request.GET.get("descargar") else "inline"

    respuesta["Content-Disposition"] = (
        f'{disposicion}; filename="{nombre_archivo(informe)}"'
    )

    return respuesta
