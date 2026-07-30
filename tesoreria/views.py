from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from miembros.models import Hermano
from miembros.services.expediente import obtener_expediente
from negocio.domain.cu_002_cobro_integral import ejecutar_cobro
from negocio.models import Obligacion
from negocio.services.aplicacion import calcular_propuesta
from negocio.services.dashboard import obtener_indicadores
from negocio.services.egresos import obtener_saldos
from tesoreria.services.recibo import construir_previsualizacion_recibo


@login_required
def index(request):
    """Muestra el dashboard institucional de Tesorería."""
    return render(
        request,
        "core/dashboard.html",
        obtener_indicadores(),
    )


@login_required
def cu002_procesar_egreso(request):
    """Muestra los saldos disponibles para el procesamiento de egresos."""
    saldos = obtener_saldos()
    total_saldos = sum((item["saldo"] for item in saldos), Decimal("0.00"))

    return render(
        request,
        "tesoreria/cu002_procesar_egreso.html",
        {
            "saldos": saldos,
            "total_saldos": total_saldos,
        },
    )


def _obligaciones_pendientes(hermano):
    """Obtiene las obligaciones que se muestran al capturar un cobro."""
    return (
        Obligacion.objects.filter(
            hermano=hermano,
            estado__in=["PENDIENTE", "PARCIAL"],
        )
        .select_related("concepto")
        .order_by("fecha_vencimiento", "id")
    )


@login_required
def emitir_recibo(request):
    hermanos = Hermano.objects.filter(estatus="ACTIVO").select_related("grado")
    hermano = None
    expediente = None
    obligaciones = []
    propuesta = None
    resultado = None
    errores = []
    previsualizacion_recibo = None
    datos_formulario = {
        "importe": "",
        "forma_pago": "EFECTIVO",
        "referencia": "",
        "observaciones": "",
    }

    if request.method == "POST":
        datos_formulario.update(
            {
                "importe": request.POST.get("importe", "").strip(),
                "forma_pago": request.POST.get("forma_pago", "EFECTIVO").strip(),
                "referencia": request.POST.get("referencia", "").strip(),
                "observaciones": request.POST.get("observaciones", "").strip(),
            }
        )
        hermano_id = request.POST.get("hermano", "").strip()

        if not hermano_id:
            errores.append("Seleccione un hermano.")
        else:
            hermano = get_object_or_404(
                Hermano.objects.select_related("grado"),
                pk=hermano_id,
                estatus="ACTIVO",
            )
            expediente = obtener_expediente(hermano)
            obligaciones = _obligaciones_pendientes(hermano)

        importe = None
        if not datos_formulario["importe"]:
            errores.append("Capture el importe recibido.")
        else:
            try:
                importe = Decimal(datos_formulario["importe"])
            except (InvalidOperation, ValueError):
                errores.append("El importe recibido no es válido.")
            else:
                if importe <= Decimal("0.00"):
                    errores.append("El importe recibido debe ser mayor que cero.")

        accion = request.POST.get("accion")
        if not errores and accion == "confirmar":
            resultado = ejecutar_cobro(
                hermano=hermano,
                importe=importe,
                fecha=date.today(),
                forma_pago=datos_formulario["forma_pago"] or "EFECTIVO",
                usuario=request.user,
                referencia=datos_formulario["referencia"],
                observaciones=datos_formulario["observaciones"],
            )
            errores.extend(resultado.errores)
            if resultado.exitoso:
                propuesta = resultado.propuesta
                obligaciones = _obligaciones_pendientes(hermano)
        elif not errores:
            propuesta = calcular_propuesta(obligaciones, importe)
            if not propuesta.aplicaciones:
                errores.append("El hermano no tiene obligaciones pendientes.")

        if not errores and propuesta is not None and hermano is not None:
            previsualizacion_recibo = construir_previsualizacion_recibo(
                hermano=hermano,
                propuesta=propuesta,
                datos_formulario=datos_formulario,
            )

    return render(
        request,
        "tesoreria/cu001/emitir_recibo.html",
        {
            "hermanos": hermanos,
            "hermano": hermano,
            "expediente": expediente,
            "obligaciones": obligaciones,
            "propuesta": propuesta,
            "resultado": resultado,
            "errores": errores,
            "datos_formulario": datos_formulario,
            "previsualizacion_recibo": previsualizacion_recibo,
        },
    )
