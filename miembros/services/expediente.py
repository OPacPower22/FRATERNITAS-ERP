"""Consultas de lectura para el expediente maestro del hermano."""

from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from contabilidad.models import EjercicioContable
from documentos.models import Recibo
from miembros.models import (
    AdscripcionLogial,
    ComisionHermano,
    DistincionHermano,
    DocumentoHermano,
    EventoAuditoriaHermano,
    NombramientoLogial,
    NotaHermano,
)
from negocio.models import Obligacion, Pago


ESTADOS_OBLIGACION_VIGENTES = ("PENDIENTE", "PARCIAL")
ESTADO_PAGO_REGISTRADO = "REGISTRADO"
CERO = Decimal("0.00")


def obtener_expediente(hermano):
    """Devuelve el resumen administrativo y financiero reutilizable del hermano."""
    obligaciones_vigentes = _obligaciones_vigentes(hermano)
    adeudo_actual = _sumar_saldos(obligaciones_vigentes)
    ultimo_pago = _pagos_registrados(hermano).first()

    return {
        "nombre_completo": _nombre_completo(hermano),
        "numero_control": hermano.numero_control,
        "grado": hermano.grado.nombre if hermano.grado else "",
        "fotografia": hermano.fotografia,
        "fecha_nacimiento": hermano.fecha_nacimiento,
        "fecha_ingreso": hermano.fecha_ingreso,
        "fecha_iniciacion": hermano.fecha_iniciacion,
        "fecha_aumento": hermano.fecha_aumento,
        "fecha_exaltacion": hermano.fecha_exaltacion,
        "tipo_ingreso": hermano.tipo_ingreso,
        "tipo_ingreso_display": hermano.get_tipo_ingreso_display(),
        "estatus": hermano.estatus,
        "estatus_display": hermano.get_estatus_display(),
        "ultimo_pago": ultimo_pago,
        "adeudo_actual": adeudo_actual,
        "numero_obligaciones_pendientes": obligaciones_vigentes.count(),
        "estado_administrativo": (
            "DESPLOMADO" if adeudo_actual > CERO else "A PLOMO"
        ),
    }


def obtener_detalle_expediente(hermano):
    """Reúne datos de sólo lectura para todas las secciones de EXP-001."""
    resumen = obtener_expediente(hermano)
    hoy = timezone.localdate()
    obligaciones_vigentes = _obligaciones_vigentes(hermano)
    pagos = _pagos_registrados(hermano)
    ejercicio = EjercicioContable.objects.filter(activo=True).first()
    ultimo_recibo = (
        Recibo.objects.filter(pago__hermano=hermano, pago__estado=ESTADO_PAGO_REGISTRADO)
        .select_related("pago", "emitido_por")
        .first()
    )

    return {
        "resumen": resumen,
        "hermano": hermano,
        "edad": _anios_transcurridos(hermano.fecha_nacimiento, hoy),
        "antiguedad_masonica": _anios_transcurridos(hermano.fecha_ingreso, hoy),
        "adscripcion_actual": (
            AdscripcionLogial.objects.filter(hermano=hermano, vigente=True)
            .select_related("logia")
            .first()
        ),
        "cargos_actuales": NombramientoLogial.objects.filter(
            hermano=hermano,
            vigente=True,
        ).select_related("cargo"),
        "cargos_desempenados": NombramientoLogial.objects.filter(
            hermano=hermano,
        ).select_related("cargo"),
        "comisiones": ComisionHermano.objects.filter(hermano=hermano),
        "distinciones": DistincionHermano.objects.filter(hermano=hermano),
        "obligaciones_vigentes": obligaciones_vigentes.select_related("concepto"),
        "saldo_actual": _sumar_saldos(obligaciones_vigentes),
        "semaforo_financiero": _calcular_semaforo(obligaciones_vigentes, hoy),
        "ultimo_recibo": ultimo_recibo,
        "fecha_ultimo_pago": resumen["ultimo_pago"].fecha if resumen["ultimo_pago"] else None,
        "total_pagado_ejercicio": _total_pagado_ejercicio(pagos, ejercicio),
        "total_pagado_historico": _sumar_importes(pagos),
        "ejercicio_activo": ejercicio,
        "movimientos": _construir_movimientos(hermano),
        "recibos": Recibo.objects.filter(pago__hermano=hermano)
        .select_related("pago", "emitido_por"),
        "documentos": DocumentoHermano.objects.filter(hermano=hermano)
        .select_related("cargado_por"),
        "notas_administrativas": NotaHermano.objects.filter(
            hermano=hermano,
            tipo="ADMINISTRATIVA",
        ).select_related("creada_por"),
        "notas_disciplinarias": NotaHermano.objects.filter(
            hermano=hermano,
            tipo="DISCIPLINARIA",
        ).select_related("creada_por"),
        "notas_generales": NotaHermano.objects.filter(
            hermano=hermano,
            tipo="GENERAL",
        ).select_related("creada_por"),
        "bitacora": EventoAuditoriaHermano.objects.filter(hermano=hermano)
        .select_related("usuario"),
    }


def _obligaciones_vigentes(hermano):
    return Obligacion.objects.filter(
        hermano=hermano,
        estado__in=ESTADOS_OBLIGACION_VIGENTES,
    ).order_by("fecha_vencimiento", "id")


def _pagos_registrados(hermano):
    return (
        Pago.objects.filter(hermano=hermano, estado=ESTADO_PAGO_REGISTRADO)
        .select_related("hermano")
        .order_by("-fecha", "-id")
    )


def _sumar_saldos(obligaciones):
    return obligaciones.aggregate(total=Sum("saldo_pendiente"))["total"] or CERO


def _sumar_importes(pagos):
    return pagos.aggregate(total=Sum("importe"))["total"] or CERO


def _nombre_completo(hermano):
    return " ".join(
        parte.strip()
        for parte in (
            hermano.nombre,
            hermano.apellido_paterno,
            hermano.apellido_materno,
        )
        if parte and parte.strip()
    )


def _anios_transcurridos(fecha_inicio, hoy):
    if not fecha_inicio:
        return None
    return hoy.year - fecha_inicio.year - (
        (hoy.month, hoy.day) < (fecha_inicio.month, fecha_inicio.day)
    )


def _calcular_semaforo(obligaciones_vigentes, hoy):
    if not obligaciones_vigentes.exists():
        return "VERDE"
    if obligaciones_vigentes.filter(fecha_vencimiento__lt=hoy).exists():
        return "ROJO"
    return "AMARILLO"


def _total_pagado_ejercicio(pagos, ejercicio):
    if ejercicio is None:
        return CERO
    return _sumar_importes(
        pagos.filter(
            fecha__range=(ejercicio.fecha_inicio, ejercicio.fecha_fin),
        )
    )


def _construir_movimientos(hermano):
    """Construye el estado de cuenta con cargos y abonos sin persistir duplicados."""
    eventos = []
    for obligacion in Obligacion.objects.filter(hermano=hermano).select_related(
        "concepto"
    ):
        if obligacion.estado == "CANCELADA":
            continue
        eventos.append(
            {
                "fecha": obligacion.fecha_vencimiento,
                "orden": 0,
                "id": obligacion.id,
                "concepto": obligacion.concepto.nombre,
                "cargo": obligacion.importe,
                "abono": CERO,
                "recibo": None,
                "estado": obligacion.get_estado_display(),
            }
        )

    pagos = (
        Pago.objects.filter(hermano=hermano, estado=ESTADO_PAGO_REGISTRADO)
        .select_related("recibo")
        .order_by("fecha", "id")
    )
    for pago in pagos:
        recibo = getattr(pago, "recibo", None)
        eventos.append(
            {
                "fecha": pago.fecha,
                "orden": 1,
                "id": pago.id,
                "concepto": "Pago registrado",
                "cargo": CERO,
                "abono": pago.importe,
                "recibo": recibo,
                "estado": pago.get_estado_display(),
            }
        )

    saldo = CERO
    movimientos = []
    for evento in sorted(eventos, key=lambda item: (item["fecha"], item["orden"], item["id"])):
        saldo += evento["cargo"] - evento["abono"]
        movimientos.append({**evento, "saldo": saldo})
    return movimientos
