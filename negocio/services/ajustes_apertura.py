"""
Ajustes de apertura del ejercicio en el sistema.

El sistema arranca en julio de 2026. Todo lo anterior vive en el
histórico, pero hay cuatro situaciones que no pueden quedarse ahí
porque representan dinero vivo: tres adeudos que la Logia sigue
teniendo derecho a cobrar y un saldo a favor que un Hermano tiene
derecho a que se le reconozca.

Este servicio los captura de forma explícita y auditable. La tabla
de ajustes está escrita a la vista, con la fuente documental de
cada renglón, para que cualquiera pueda verificarla contra el
archivo del Tesorero.

Es idempotente: los registros llevan la referencia ``APERTURA-``
y no se duplican al volver a ejecutar.
"""

import datetime
import re
import unicodedata
from decimal import Decimal

from django.db import transaction

from catalogos.models import ConceptoContable
from miembros.models import Hermano
from negocio.models import AplicacionPago, Obligacion, Pago


PREFIJO_REFERENCIA = "APERTURA-"

CONCEPTO_CAPITA = "CUOTA_ORD"

PERIODO_ANTERIOR = "SALDO-ANTERIOR"

FECHA_CORTE = datetime.date(2026, 6, 30)


# ----------------------------------------------------------------------
# Tabla de ajustes
#
# 'clave' es un apellido distintivo que identifica al Hermano sin
# ambigüedad dentro del padrón.
# ----------------------------------------------------------------------

ADEUDOS = [
    {
        "clave": "LEOPOLDO",
        "nombre": "Leopoldo",
        "periodo": "2026-05",
        "importe": Decimal("350.00"),
        "fuente": (
            "Hoja MEMBRESIA: mayo sin número de recibo. "
            "Último pago cubierto, recibo 49 de abril."
        ),
    },
    {
        "clave": "LEOPOLDO",
        "nombre": "Leopoldo",
        "periodo": "2026-06",
        "importe": Decimal("350.00"),
        "fuente": "Hoja MEMBRESIA: junio sin número de recibo.",
    },
    {
        "clave": "SOLIS",
        "nombre": "José Alfredo",
        "periodo": PERIODO_ANTERIOR,
        "importe": Decimal("350.00"),
        "fuente": (
            "Hoja MEMBRESIA, columna ADEUDO. Corresponde a un "
            "periodo anterior al ejercicio 2026."
        ),
    },
    {
        "clave": "ALVAREZ",
        "nombre": "Ángel Ricardo",
        "periodo": PERIODO_ANTERIOR,
        "importe": Decimal("350.00"),
        "fuente": (
            "Hoja MEMBRESIA, columna ADEUDO. Corresponde a un "
            "periodo anterior al ejercicio 2026."
        ),
    },
]

SALDOS_A_FAVOR = [
    {
        "clave": "MOTOLINIA",
        "nombre": "Guillermo Francisco",
        "importe": Decimal("50.00"),
        "fuente": (
            "Recibo 43 del 30 de marzo de 2026, por $1,800.00: "
            "cinco mensualidades de $350.00 más $50.00 anotados "
            "en el propio recibo como «50 PESOS A FAVOR»."
        ),
    },
]


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------

def _sin_acentos(texto):
    texto = unicodedata.normalize("NFD", str(texto or ""))
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto).strip().upper()


def _localizar(clave):
    """
    Encuentra al Hermano cuyo nombre contiene la clave.

    Falla en voz alta si hay cero o más de una coincidencia: un
    ajuste aplicado al Hermano equivocado es peor que no aplicarlo.
    """

    coincidencias = [
        hermano
        for hermano in Hermano.objects.all()
        if clave in _sin_acentos(
            f"{hermano.nombre} {hermano.apellido_paterno} "
            f"{hermano.apellido_materno}"
        )
    ]

    if len(coincidencias) == 1:
        return coincidencias[0]

    raise ValueError(
        f"La clave «{clave}» identifica a {len(coincidencias)} "
        f"Hermanos: {[str(h) for h in coincidencias]}. "
        f"Ajuste la tabla de ajustes de apertura."
    )


def _vencimiento(periodo):

    if periodo == PERIODO_ANTERIOR:
        return FECHA_CORTE

    anio, mes = (int(parte) for parte in periodo.split("-"))

    return datetime.date(anio, mes, 10)


# ----------------------------------------------------------------------
# Operación
# ----------------------------------------------------------------------

def revertir():
    """Elimina únicamente los ajustes de apertura."""

    pagos = Pago.objects.filter(
        referencia__startswith=PREFIJO_REFERENCIA,
    )

    aplicaciones = AplicacionPago.objects.filter(pago__in=pagos)

    # Deshace el efecto del saldo a favor sobre las obligaciones
    # a las que se aplicó, antes de borrarlo.
    for aplicacion in aplicaciones.select_related("obligacion"):

        obligacion = aplicacion.obligacion
        obligacion.saldo_pendiente += aplicacion.importe_aplicado

        if obligacion.saldo_pendiente >= obligacion.importe:
            obligacion.estado = "PENDIENTE"
        else:
            obligacion.estado = "PARCIAL"

        obligacion.save()

    obligaciones = Obligacion.objects.filter(
        periodo__in=[
            ajuste["periodo"]
            for ajuste in ADEUDOS
        ],
        hermano__in=[
            _localizar(ajuste["clave"])
            for ajuste in ADEUDOS
        ],
    )

    resumen = {
        "adeudos": obligaciones.count(),
        "saldos_a_favor": pagos.count(),
    }

    aplicaciones.delete()
    pagos.delete()
    obligaciones.delete()

    return resumen


@transaction.atomic
def aplicar():
    """
    Registra los adeudos anteriores y aplica los saldos a favor.
    """

    concepto = ConceptoContable.objects.get(clave=CONCEPTO_CAPITA)

    adeudos_creados = []
    creditos_aplicados = []

    # ------------------------------------------------------------------
    # Adeudos anteriores a julio
    # ------------------------------------------------------------------
    for ajuste in ADEUDOS:

        hermano = _localizar(ajuste["clave"])

        obligacion, creada = Obligacion.objects.get_or_create(
            hermano=hermano,
            concepto=concepto,
            periodo=ajuste["periodo"],
            defaults={
                "importe": ajuste["importe"],
                "saldo_pendiente": ajuste["importe"],
                "fecha_vencimiento": _vencimiento(ajuste["periodo"]),
                "estado": "PENDIENTE",
            },
        )

        adeudos_creados.append(
            {
                "hermano": str(hermano),
                "periodo": ajuste["periodo"],
                "importe": ajuste["importe"],
                "nueva": creada,
                "fuente": ajuste["fuente"],
            }
        )

    # ------------------------------------------------------------------
    # Saldos a favor: se aplican a la obligación abierta más antigua
    # ------------------------------------------------------------------
    for credito in SALDOS_A_FAVOR:

        hermano = _localizar(credito["clave"])

        referencia = f"{PREFIJO_REFERENCIA}FAVOR-{hermano.pk}"

        if Pago.objects.filter(referencia=referencia).exists():
            creditos_aplicados.append(
                {
                    "hermano": str(hermano),
                    "importe": credito["importe"],
                    "aplicado_a": "(ya estaba registrado)",
                    "nueva": False,
                }
            )
            continue

        objetivo = (
            Obligacion.objects
            .filter(
                hermano=hermano,
                estado__in=["PENDIENTE", "PARCIAL"],
            )
            .order_by("fecha_vencimiento", "id")
            .first()
        )

        if objetivo is None:
            creditos_aplicados.append(
                {
                    "hermano": str(hermano),
                    "importe": credito["importe"],
                    "aplicado_a": "SIN OBLIGACIÓN ABIERTA",
                    "nueva": False,
                }
            )
            continue

        pago = Pago.objects.create(
            hermano=hermano,
            fecha=FECHA_CORTE,
            importe=credito["importe"],
            forma_pago="EFECTIVO",
            referencia=referencia,
            observaciones=(
                f"Saldo a favor reconocido al arranque del sistema. "
                f"{credito['fuente']}"
            ),
            estado="REGISTRADO",
        )

        aplicado = min(credito["importe"], objetivo.saldo_pendiente)

        AplicacionPago.objects.create(
            pago=pago,
            obligacion=objetivo,
            importe_aplicado=aplicado,
        )

        objetivo.saldo_pendiente -= aplicado

        objetivo.estado = (
            "LIQUIDADA"
            if objetivo.saldo_pendiente <= 0
            else "PARCIAL"
        )

        objetivo.save()

        creditos_aplicados.append(
            {
                "hermano": str(hermano),
                "importe": credito["importe"],
                "aplicado_a": f"{objetivo.concepto} {objetivo.periodo}",
                "saldo_resultante": objetivo.saldo_pendiente,
                "nueva": True,
                "fuente": credito["fuente"],
            }
        )

    return {
        "adeudos": adeudos_creados,
        "creditos": creditos_aplicados,
        "total_adeudos": sum(
            (a["importe"] for a in adeudos_creados),
            Decimal("0.00"),
        ),
        "total_creditos": sum(
            (c["importe"] for c in creditos_aplicados),
            Decimal("0.00"),
        ),
    }
