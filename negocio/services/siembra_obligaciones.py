"""
Siembra del estado de obligaciones a partir de la matriz MEMBRESIA.

La hoja MEMBRESIA del histórico es una matriz de Hermanos por meses
donde cada celda guarda el número de recibo con que se cubrió ese
mes. Es el registro autoritativo de qué está pagado y qué no.

Este servicio la traduce al modelo:

  - Genera una obligación de cápita por Hermano activo y por mes,
    desde el periodo de arranque hasta el mes de corte.
  - Genera además las obligaciones de meses futuros que YA están
    cubiertas, para que los pagos adelantados tengan dónde aplicarse.
  - Por cada número de recibo crea un Pago con sus AplicacionPago,
    de modo que el expediente del Hermano conserve la trazabilidad
    al folio original.

Es idempotente: los pagos sembrados llevan la referencia
``HIST-<recibo>`` y no se duplican al volver a ejecutar.
"""

import calendar
import datetime
import re
import unicodedata
from decimal import Decimal
from pathlib import Path

import xlrd

from django.conf import settings
from django.db import transaction

from catalogos.models import ConceptoContable
from miembros.models import Hermano
from negocio.models import AplicacionPago, Obligacion, Pago


RUTA_PREDETERMINADA = (
    Path(settings.BASE_DIR)
    / "importaciones"
    / "tesoreria"
    / "HISTORICO_MOVIMIENTOS_2026.xls"
)

HOJA = "MEMBRESIA"

FILA_ENCABEZADO = 2      # índice base cero
COLUMNA_NOMBRE = 1

PREFIJO_REFERENCIA = "HIST-"

CONCEPTO_CAPITA = "CAPITA"

DIA_VENCIMIENTO = 10

MESES = {
    "ENE": 1, "FEB": 2, "MAR": 3, "ABR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AGO": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DIC": 12,
}

# Celdas que marcan un mes no aplicable, no un pago.
NO_APLICA = {"X", "BAJA", ""}

# Pagos que cubrieron sólo una parte de la cuota.
# Clave: (apellido distintivo, periodo) → importe efectivamente pagado.
PAGOS_PARCIALES = {
    ("PACHECO", "2026-07"): Decimal("300.00"),
}

PALABRAS_IGNORADAS = {"JOSE", "LUIS", "ANGEL", "MARIA"}


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------

def _sin_acentos(texto):
    texto = unicodedata.normalize("NFD", str(texto or ""))
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto).strip().upper()


def _tokens(nombre):
    limpio = _sin_acentos(nombre).replace(".", " ").replace(",", " ")
    return {
        palabra
        for palabra in limpio.split()
        if len(palabra) > 3 and palabra not in PALABRAS_IGNORADAS
    }


def _periodo(anio, mes):
    return f"{anio}-{mes:02d}"


def _vencimiento(periodo):
    anio, mes = (int(parte) for parte in periodo.split("-"))
    dia = min(DIA_VENCIMIENTO, calendar.monthrange(anio, mes)[1])
    return datetime.date(anio, mes, dia)


def _fecha_pago(periodo):
    """Fecha con que se registra el pago sembrado."""
    anio, mes = (int(parte) for parte in periodo.split("-"))
    return datetime.date(anio, mes, calendar.monthrange(anio, mes)[1])


def _rango(desde, hasta):
    """Lista de periodos entre dos, ambos inclusive."""

    anio, mes = (int(parte) for parte in desde.split("-"))
    anio_fin, mes_fin = (int(parte) for parte in hasta.split("-"))

    periodos = []

    while (anio, mes) <= (anio_fin, mes_fin):
        periodos.append(_periodo(anio, mes))
        mes += 1
        if mes > 12:
            mes = 1
            anio += 1

    return periodos


# ----------------------------------------------------------------------
# Lectura de la matriz
# ----------------------------------------------------------------------

def leer_matriz(ruta, anio):
    """
    Devuelve {nombre_en_la_hoja: {periodo: numero_recibo}}.
    """

    libro = xlrd.open_workbook(str(ruta))
    hoja = libro.sheet_by_name(HOJA)

    # Localiza las columnas de mes por su encabezado. La hoja arrastra
    # meses del ejercicio anterior, así que se toma la ÚLTIMA aparición
    # de cada mes, que es la del ejercicio en curso.
    columnas = {}

    for columna in range(hoja.ncols):
        etiqueta = _sin_acentos(hoja.cell_value(FILA_ENCABEZADO, columna))[:3]
        if etiqueta in MESES:
            columnas[etiqueta] = columna

    matriz = {}

    for fila in range(FILA_ENCABEZADO + 1, hoja.nrows):

        nombre = str(hoja.cell_value(fila, COLUMNA_NOMBRE)).strip()

        if not nombre:
            continue

        cubiertos = {}

        for etiqueta, columna in columnas.items():

            valor = hoja.cell_value(fila, columna)

            if isinstance(valor, float):
                recibo = int(valor)
            else:
                texto = _sin_acentos(valor)
                if not texto or texto in NO_APLICA or not texto.isdigit():
                    continue
                recibo = int(texto)

            cubiertos[_periodo(anio, MESES[etiqueta])] = recibo

        matriz[nombre] = cubiertos

    return matriz, sorted(columnas, key=lambda e: MESES[e])


def emparejar(nombre_hoja, hermanos):
    """Localiza el Hermano correspondiente a un renglón de la matriz."""

    objetivo = _tokens(nombre_hoja)

    mejor = (None, 0)

    for hermano in hermanos:

        tokens = _tokens(
            f"{hermano.apellido_paterno} "
            f"{hermano.apellido_materno} "
            f"{hermano.nombre}"
        )

        comunes = len(tokens & objetivo)

        if comunes > mejor[1]:
            mejor = (hermano, comunes)

    return mejor if mejor[1] >= 2 else (None, mejor[1])


def _importe_parcial(hermano, periodo):
    """Importe pagado cuando la cuota se cubrió sólo en parte."""

    tokens = _tokens(
        f"{hermano.apellido_paterno} {hermano.apellido_materno}"
    )

    for (apellido, per), importe in PAGOS_PARCIALES.items():
        if per == periodo and apellido in tokens:
            return importe

    return None


# ----------------------------------------------------------------------
# Siembra
# ----------------------------------------------------------------------

def revertir():
    """Elimina las obligaciones y pagos sembrados."""

    pagos = Pago.objects.filter(
        referencia__startswith=PREFIJO_REFERENCIA,
    )

    aplicaciones = AplicacionPago.objects.filter(pago__in=pagos)

    obligaciones = Obligacion.objects.filter(
        id__in=aplicaciones.values("obligacion_id"),
    )

    total = {
        "aplicaciones": aplicaciones.count(),
        "pagos": pagos.count(),
        "obligaciones": obligaciones.count(),
    }

    aplicaciones.delete()
    pagos.delete()
    obligaciones.delete()

    return total


@transaction.atomic
def sembrar(
    ruta=None,
    desde="2026-07",
    corte=None,
    importe=Decimal("400.00"),
    anio=2026,
):
    """
    Siembra el estado de obligaciones.

    ``corte`` es el último mes que se considera vencido. Los meses
    posteriores sólo generan obligación si ya están cubiertos.
    """

    ruta = Path(ruta) if ruta else RUTA_PREDETERMINADA

    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el histórico:\n{ruta}")

    if corte is None:
        hoy = datetime.date.today()
        corte = _periodo(hoy.year, hoy.month)

    concepto = ConceptoContable.objects.get(clave=CONCEPTO_CAPITA)

    hermanos = list(Hermano.objects.all())
    activos = [h for h in hermanos if h.estatus == "ACTIVO"]

    matriz, meses_en_hoja = leer_matriz(ruta, anio)

    periodos_vencidos = _rango(desde, corte)

    # Recibos agrupados: un recibo puede cubrir varios meses.
    recibos = {}

    sin_emparejar = []
    detalle = []

    creadas = 0
    liquidadas = 0
    parciales = 0
    pendientes = 0

    for nombre_hoja, cubiertos in matriz.items():

        hermano, coincidencias = emparejar(nombre_hoja, hermanos)

        if hermano is None:
            if any(
                periodo >= desde
                for periodo in cubiertos
            ):
                sin_emparejar.append((nombre_hoja, coincidencias))
            continue

        if hermano.estatus != "ACTIVO":
            continue

        # Meses que hay que representar: los vencidos, más los futuros
        # que ya vienen cubiertos en la matriz.
        periodos = set(periodos_vencidos)

        periodos |= {
            periodo
            for periodo in cubiertos
            if periodo >= desde
        }

        for periodo in sorted(periodos):

            recibo = cubiertos.get(periodo)

            pagado = importe if recibo else Decimal("0.00")

            if recibo:
                parcial = _importe_parcial(hermano, periodo)
                if parcial is not None:
                    pagado = parcial

            saldo = importe - pagado

            if saldo <= 0:
                estado = "LIQUIDADA"
                saldo = Decimal("0.00")
                liquidadas += 1
            elif pagado > 0:
                estado = "PARCIAL"
                parciales += 1
            else:
                estado = "PENDIENTE"
                pendientes += 1

            obligacion, creada = Obligacion.objects.get_or_create(
                hermano=hermano,
                concepto=concepto,
                periodo=periodo,
                defaults={
                    "importe": importe,
                    "saldo_pendiente": saldo,
                    "fecha_vencimiento": _vencimiento(periodo),
                    "estado": estado,
                },
            )

            if creada:
                creadas += 1
            else:
                obligacion.importe = importe
                obligacion.saldo_pendiente = saldo
                obligacion.estado = estado
                obligacion.save()

            detalle.append(
                {
                    "hermano": str(hermano),
                    "periodo": periodo,
                    "estado": estado,
                    "pagado": pagado,
                    "saldo": saldo,
                    "recibo": recibo,
                }
            )

            if recibo and pagado > 0:
                recibos.setdefault(
                    (hermano.pk, recibo), []
                ).append((obligacion, pagado))

    # ------------------------------------------------------------------
    # Pagos: uno por recibo, con sus aplicaciones
    # ------------------------------------------------------------------
    pagos_creados = 0

    for (hermano_id, recibo), aplicaciones in recibos.items():

        referencia = f"{PREFIJO_REFERENCIA}{recibo}"

        if Pago.objects.filter(
            hermano_id=hermano_id,
            referencia=referencia,
        ).exists():
            continue

        total = sum(
            (monto for _, monto in aplicaciones),
            Decimal("0.00"),
        )

        primer_periodo = min(
            obligacion.periodo for obligacion, _ in aplicaciones
        )

        pago = Pago.objects.create(
            hermano_id=hermano_id,
            fecha=_fecha_pago(primer_periodo),
            importe=total,
            forma_pago="EFECTIVO",
            referencia=referencia,
            observaciones=(
                f"Sembrado desde la hoja MEMBRESIA. "
                f"Recibo físico número {recibo}."
            ),
            estado="REGISTRADO",
        )

        for obligacion, monto in aplicaciones:
            AplicacionPago.objects.create(
                pago=pago,
                obligacion=obligacion,
                importe_aplicado=monto,
            )

        pagos_creados += 1

    return {
        "desde": desde,
        "corte": corte,
        "importe": importe,
        "hermanos_activos": len(activos),
        "meses_en_hoja": meses_en_hoja,
        "obligaciones_creadas": creadas,
        "liquidadas": liquidadas,
        "parciales": parciales,
        "pendientes": pendientes,
        "pagos_creados": pagos_creados,
        "sin_emparejar": sin_emparejar,
        "detalle": detalle,
    }
