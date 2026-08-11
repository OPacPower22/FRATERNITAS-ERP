"""Informe mensual de resultados financieros por fondo.

Reproduce el formato histórico del Tesorero: cada fondo (Cápitas,
Aniversario, Saco de Beneficencia, Taller Benito Juárez y Otros) se
reporta con su ingreso y egreso del mes, el saldo heredado de meses
anteriores y el saldo total resultante.

``Movimiento`` conserva las columnas heredadas del Excel (capitas,
aniversario, saco_beneficencia, taller_bj, otros), pero desde que
CU-002 distribuye la Cuota Ordinaria por ``concepto_contable``
(GLUM, Aportación Fraternidad, Aportación AJEF, Aportación Tesoro,
Saco de Beneficencia...), esas columnas ya no se usan: todo importe
vive en ``otros``/``total`` clasificado por concepto. Este informe
reagrupa esos conceptos en los cinco fondos históricos.
"""

import datetime
from collections import defaultdict
from decimal import Decimal

from django.db.models import Sum

from miembros.models import Hermano
from tesoreria.models import Movimiento


CAPITAS = "CAPITAS"
ANIVERSARIO = "ANIVERSARIO"
SACO_BENEFICENCIA = "SACO DE BENEFICENCIA"
TALLER_BJ = "TALLER BENITO JUÁREZ"
OTROS = "OTROS"

FONDOS = [CAPITAS, ANIVERSARIO, SACO_BENEFICENCIA, TALLER_BJ, OTROS]

# Corresponde a la clave de ConceptoContable → el fondo histórico al
# que pertenece. Verificado contra el desglose real de julio 2026:
# Cápitas = GLUM (Membresía, Revista, Gran Logia, CMI, Servicios
# Recibidos, Fondo Contingencia, Post Mortem, Defunción) + Aportación
# Tesoro, que en el sheet del Tesorero absorbía los incrementos de
# cuota. Lo que no está mapeado cae en "Otros".
MAPA_CONCEPTO_FONDO = {
    "MEMBRESIA": CAPITAS,
    "REVISTA": CAPITAS,
    "CONF_GR_LOG": CAPITAS,
    "CMI": CAPITAS,
    "SERVICIOS_RECIBIDOS": CAPITAS,
    "FONDO_CONT_ANUAL": CAPITAS,
    "POST_MORTEM": CAPITAS,
    "DEFUNCION": CAPITAS,
    "GLUM": CAPITAS,
    "APORTACION_TESORO": CAPITAS,
    "APORTACION_FRATERNIDAD": ANIVERSARIO,
    "SACO_BENEFICENCIA": SACO_BENEFICENCIA,
    "APORTACION_AJEF": TALLER_BJ,
}

MESES = {
    1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL",
    5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO",
    9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE",
}


def etiqueta_periodo(anio, mes):
    return f"{MESES[mes]} {anio}"


def anios_disponibles():
    """Años con movimientos registrados, del más reciente al más antiguo."""

    anios = Movimiento.objects.dates("fecha", "year", order="DESC")

    return [fecha.year for fecha in anios]


def _fondo_de(clave_concepto):
    return MAPA_CONCEPTO_FONDO.get(clave_concepto, OTROS)


def _totales_por_fondo(tipo, **filtros):
    """Suma ``total`` de los movimientos del tipo indicado, agrupada
    por fondo histórico."""

    filas = (
        Movimiento.objects
        .filter(tipo=tipo, **filtros)
        .values("concepto_contable__clave")
        .annotate(importe=Sum("total"))
    )

    totales = defaultdict(lambda: Decimal("0.00"))

    for fila in filas:
        fondo = _fondo_de(fila["concepto_contable__clave"])
        totales[fondo] += fila["importe"] or Decimal("0.00")

    return totales


def calcular_informe_mensual(anio, mes):
    """
    Calcula el informe del periodo indicado.

    El "saldo del mes anterior" de cada fondo es el acumulado de
    todos los movimientos anteriores al primer día del mes (no sólo
    el mes previo), para que el reporte encadene correctamente aun
    si algún mes intermedio no tuvo movimientos.
    """

    inicio_mes = datetime.date(anio, mes, 1)

    ingresos_mes = _totales_por_fondo(
        "I", fecha__year=anio, fecha__month=mes,
    )
    egresos_mes = _totales_por_fondo(
        "E", fecha__year=anio, fecha__month=mes,
    )
    ingresos_previos = _totales_por_fondo("I", fecha__lt=inicio_mes)
    egresos_previos = _totales_por_fondo("E", fecha__lt=inicio_mes)

    fondos = []
    suma_total = Decimal("0.00")

    for nombre_fondo in FONDOS:

        ingreso = ingresos_mes[nombre_fondo]
        egreso = egresos_mes[nombre_fondo]
        mes_anterior = (
            ingresos_previos[nombre_fondo] - egresos_previos[nombre_fondo]
        )

        subtotal = ingreso + mes_anterior
        saldo = subtotal - egreso

        fondos.append(
            {
                "etiqueta": nombre_fondo,
                "ingreso": ingreso,
                "mes_anterior": mes_anterior,
                "subtotal": subtotal,
                "egreso": egreso,
                "saldo": saldo,
            }
        )

        suma_total += saldo

    return {
        "anio": anio,
        "mes": mes,
        "etiqueta_periodo": etiqueta_periodo(anio, mes),
        "miembros_activos": Hermano.objects.filter(estatus="ACTIVO").count(),
        "fondos": fondos,
        "suma_total": suma_total,
    }
