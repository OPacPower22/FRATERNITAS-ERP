from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from core.services.folios import obtener_siguiente_folio
from documentos.models import ComprobanteTransferencia
from documentos.services.comprobantes import validar_comprobante_transferencia
from documentos.services.qr import (
    construir_url_verificacion,
    generar_qr_base64,
)
from miembros.models import Hermano
from miembros.services.expediente import obtener_expediente
from negocio.domain.cu_002_cobro_integral import ejecutar_cobro
from negocio.models import Obligacion
from negocio.services.aplicacion import calcular_propuesta
from negocio.services.contabilidad import (
    calcular_distribucion_institucional,
    distribucion_referencia_cuota_actual,
)
from negocio.services.dashboard import obtener_indicadores
from negocio.services.egresos import obtener_saldos


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
    obligaciones = []
    propuesta = None
    resultado = None
    errores = []
    datos_formulario = {
        "importe": "",
        "forma_pago": "EFECTIVO",
        "referencia": "",
        "observaciones": "",
        "comprobante_folio": "",
        "comprobante_emisor": "",
        "comprobante_monto": "",
    }

    if request.method == "POST":
        datos_formulario.update(
            {
                "importe": request.POST.get("importe", "").strip(),
                "forma_pago": request.POST.get("forma_pago", "EFECTIVO").strip(),
                "referencia": request.POST.get("referencia", "").strip(),
                "observaciones": request.POST.get("observaciones", "").strip(),
                "comprobante_folio": request.POST.get("comprobante_folio", "").strip(),
                "comprobante_emisor": request.POST.get("comprobante_emisor", "").strip(),
                "comprobante_monto": request.POST.get("comprobante_monto", "").strip(),
            }
        )
        hermano_id = request.POST.get("hermano", "").strip()

        if not hermano_id:
            errores.append("Seleccione un hermano.")
        else:
            # Limitar el cobro a hermanos activos, igual que el selector.
            hermano = get_object_or_404(
                Hermano.objects.select_related("grado"),
                pk=hermano_id,
                estatus="ACTIVO",
            )
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

        comprobante_archivo = request.FILES.get("comprobante_archivo")
        comprobante_datos = None

        accion = request.POST.get("accion")

        if (
            not errores
            and accion == "confirmar"
            and datos_formulario["forma_pago"] == "TRANSFERENCIA"
        ):
            errores_comprobante, folio_bancario, emisor, monto_comprobante = (
                validar_comprobante_transferencia(
                    archivo=comprobante_archivo,
                    folio_bancario=datos_formulario["comprobante_folio"],
                    emisor=datos_formulario["comprobante_emisor"],
                    monto=datos_formulario["comprobante_monto"],
                    verificado=request.POST.get("comprobante_verificado") == "on",
                    importe_pago=importe,
                )
            )
            errores.extend(errores_comprobante)
            if not errores_comprobante:
                comprobante_datos = {
                    "archivo": comprobante_archivo,
                    "folio_bancario": folio_bancario,
                    "emisor": emisor,
                    "monto": monto_comprobante,
                }

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
                if comprobante_datos:
                    ComprobanteTransferencia.objects.create(
                        pago=resultado.pago,
                        verificado_por=request.user,
                        **comprobante_datos,
                    )
        elif not errores:
            propuesta = calcular_propuesta(obligaciones, importe)
            if not propuesta.aplicaciones:
                errores.append("El hermano no tiene obligaciones pendientes.")

    expediente = obtener_expediente(hermano) if hermano else None

    recibo_qr = None
    recibo_url_verificacion = None
    recibo_id = None

    if resultado and resultado.exitoso:
        recibo_modelo = resultado.recibo["recibo"]
        recibo_id = recibo_modelo.pk
        recibo_url_verificacion = construir_url_verificacion(
            recibo_modelo,
            request,
        )
        recibo_qr = generar_qr_base64(recibo_url_verificacion)

    distribucion = None
    if propuesta and propuesta.aplicaciones:
        distribucion = calcular_distribucion_institucional(propuesta.aplicaciones)
    if distribucion is None:
        distribucion = distribucion_referencia_cuota_actual()

    vista_previa = None
    if propuesta and propuesta.aplicaciones and not (resultado and resultado.exitoso):
        vista_previa = {
            "folio": obtener_siguiente_folio("REC", guardar=False),
            "fecha": timezone.now(),
            "qr": generar_qr_base64(
                "Vista previa — folio provisional. El código de "
                "verificación oficial se genera al confirmar el cobro."
            ),
        }

    return render(
        request,
        "tesoreria/cu001/emitir_recibo.html",
        {
            "hermanos": hermanos,
            "hermano": hermano,
            "expediente": expediente,
            "recibo_id": recibo_id,
            "recibo_qr": recibo_qr,
            "recibo_url_verificacion": recibo_url_verificacion,
            "obligaciones": obligaciones,
            "propuesta": propuesta,
            "distribucion": distribucion,
            "distribucion_es_referencia": propuesta is None,
            "vista_previa": vista_previa,
            "resultado": resultado,
            "errores": errores,
            "datos_formulario": datos_formulario,
        },
    )
