"""
Servicio de Expediente del Hermano.

Construye la vista consolidada que se despliega en la columna
izquierda del CU-001: datos biográficos, obligaciones pendientes,
obligaciones ya cubiertas y últimos pagos registrados.

No modifica ningún modelo existente: sólo lee.
"""

from decimal import Decimal

from django.templatetags.static import static

from negocio.models import AplicacionPago, Obligacion, Pago


ESTADOS_PENDIENTES = ("PENDIENTE", "PARCIAL")

# Imagen usada cuando el Hermano no tiene fotografía cargada.
SOMBRA_INSTITUCIONAL = "img/escudo.png"


def _decimal(valor):
    return Decimal(valor or "0.00")


def obtener_avatar(hermano):
    """
    Devuelve la URL de la fotografía del Hermano o, en su
    defecto, la sombra institucional.
    """

    if hermano.fotografia:
        try:
            return {
                "url": hermano.fotografia.url,
                "es_fotografia": True,
            }
        except ValueError:
            pass

    return {
        "url": static(SOMBRA_INSTITUCIONAL),
        "es_fotografia": False,
    }


def obtener_biografia(hermano):
    """
    Datos biográficos e institucionales del Hermano.
    """

    return {
        "id": hermano.pk,
        "numero_control": hermano.numero_control,
        "nombre_completo": str(hermano),
        "nombre_simbolico": hermano.nombre_simbolico or "",
        "grado": str(hermano.grado) if hermano.grado_id else "",
        "estatus": hermano.get_estatus_display(),
        "estatus_clave": hermano.estatus,
        "tipo_ingreso": hermano.get_tipo_ingreso_display(),
        "fecha_nacimiento": _fecha(hermano.fecha_nacimiento),
        "lugar_nacimiento": hermano.lugar_nacimiento or "",
        "profesion": hermano.profesion or "",
        "ocupacion": hermano.ocupacion or "",
        "telefono": hermano.telefono or "",
        "celular": hermano.celular or "",
        "correo": hermano.correo or "",
        "direccion": hermano.direccion or "",
        "fecha_ingreso": _fecha(hermano.fecha_ingreso),
        "fecha_iniciacion": _fecha(hermano.fecha_iniciacion),
        "fecha_aumento": _fecha(hermano.fecha_aumento),
        "fecha_exaltacion": _fecha(hermano.fecha_exaltacion),
        "logia_procedencia": hermano.logia_procedencia or "",
        "observaciones": hermano.observaciones or "",
    }


def _fecha(valor):
    return valor.strftime("%d/%m/%Y") if valor else ""


def _serializar_obligacion(obligacion, pagado=None):
    return {
        "id": obligacion.pk,
        "concepto": obligacion.concepto.nombre,
        "periodo": obligacion.periodo,
        "importe": f"{obligacion.importe:.2f}",
        "saldo_pendiente": f"{obligacion.saldo_pendiente:.2f}",
        "pagado": f"{(obligacion.importe - obligacion.saldo_pendiente):.2f}"
        if pagado is None
        else f"{pagado:.2f}",
        "vencimiento": _fecha(obligacion.fecha_vencimiento),
        "estado": obligacion.estado,
        "estado_display": obligacion.get_estado_display(),
    }


def obtener_obligaciones(hermano):
    """
    Separa las obligaciones del Hermano en pendientes y cubiertas.
    """

    consulta = (
        Obligacion.objects
        .filter(hermano=hermano)
        .select_related("concepto")
        .order_by("fecha_vencimiento", "id")
    )

    pendientes = []
    cubiertas = []

    total_pendiente = Decimal("0.00")
    total_cubierto = Decimal("0.00")

    for obligacion in consulta:

        if obligacion.estado in ESTADOS_PENDIENTES:
            pendientes.append(_serializar_obligacion(obligacion))
            total_pendiente += _decimal(obligacion.saldo_pendiente)

        elif obligacion.estado == "LIQUIDADA":
            cubiertas.append(_serializar_obligacion(obligacion))
            total_cubierto += _decimal(obligacion.importe)

    return {
        "pendientes": pendientes,
        "cubiertas": cubiertas,
        "total_pendiente": f"{total_pendiente:.2f}",
        "total_cubierto": f"{total_cubierto:.2f}",
        "numero_pendientes": len(pendientes),
        "numero_cubiertas": len(cubiertas),
    }


def obtener_ultimos_pagos(hermano, limite=8):
    """
    Historial reciente de pagos del Hermano.
    """

    pagos = (
        Pago.objects
        .filter(hermano=hermano)
        .order_by("-fecha", "-id")[:limite]
    )

    aplicaciones = (
        AplicacionPago.objects
        .filter(pago__in=pagos)
        .select_related("obligacion__concepto")
    )

    detalle = {}

    for aplicacion in aplicaciones:
        detalle.setdefault(aplicacion.pago_id, []).append(
            f"{aplicacion.obligacion.concepto.nombre} "
            f"({aplicacion.obligacion.periodo})"
        )

    resultado = []

    for pago in pagos:

        folio = ""
        recibo = getattr(pago, "recibo", None)

        if recibo is not None:
            folio = recibo.folio_formateado

        resultado.append(
            {
                "id": pago.pk,
                "fecha": _fecha(pago.fecha),
                "importe": f"{pago.importe:.2f}",
                "forma_pago": pago.forma_pago,
                "referencia": pago.referencia,
                "estado": pago.estado,
                "folio_recibo": folio,
                "conceptos": detalle.get(pago.pk, []),
            }
        )

    return resultado


def obtener_expediente(hermano):
    """
    Expediente completo del Hermano para el CU-001.
    """

    return {
        "avatar": obtener_avatar(hermano),
        "biografia": obtener_biografia(hermano),
        "obligaciones": obtener_obligaciones(hermano),
        "pagos": obtener_ultimos_pagos(hermano),
    }
