"""
Lector del histórico de Tesorería (MOVIMIENTOS_2026.xls).

Recorre la hoja 'INGRESOS Y EGRESOS', que está organizada en
bloques mensuales con la misma estructura, y devuelve los
movimientos normalizados.

No depende de Django: puede ejecutarse de forma aislada para
auditar el archivo antes de importarlo.
"""

import datetime
import re
import unicodedata
from decimal import Decimal, InvalidOperation

import xlrd


MESES = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4,
    "MAYO": 5, "JUNIO": 6, "JULIO": 7, "AGOSTO": 8,
    "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11,
    "DICIEMBRE": 12,
}

# Columnas de los bloques mensuales (idénticas en ingresos y egresos)
COL_REFERENCIA = 0
COL_DESCRIPCION = 1
COL_CAPITAS = 4
COL_ANIVERSARIO = 5
COL_SACO = 6
COL_TALLER = 7
COL_OTROS = 8
COL_TOTAL = 9
COL_FECHA = 10
COL_NOTA = 11

FONDOS = (
    ("capitas", COL_CAPITAS),
    ("aniversario", COL_ANIVERSARIO),
    ("saco_beneficencia", COL_SACO),
    ("taller_bj", COL_TALLER),
    ("otros", COL_OTROS),
)

CERO = Decimal("0.00")


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------

def normalizar(texto):
    """Mayúsculas sin acentos ni espacios redundantes."""

    if texto is None:
        return ""

    texto = unicodedata.normalize("NFD", str(texto))
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")

    return re.sub(r"\s+", " ", texto).strip().upper()


def a_decimal(valor):
    """Convierte a Decimal tolerando celdas vacías o con texto."""

    if valor is None or valor == "":
        return CERO

    if isinstance(valor, (int, float)):
        return Decimal(str(valor)).quantize(Decimal("0.01"))

    limpio = re.sub(r"[^\d.\-]", "", str(valor))

    try:
        return Decimal(limpio).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return CERO


def a_fecha(valor, datemode):
    """
    Convierte el serial de Excel a date.

    Devuelve None si la celda contiene texto libre (por ejemplo
    '25 FE'), señalando un dato que requiere corrección manual.
    """

    if isinstance(valor, (int, float)) and valor > 1:
        try:
            partes = xlrd.xldate_as_tuple(valor, datemode)
            return datetime.date(*partes[:3])
        except Exception:
            return None

    return None


# ----------------------------------------------------------------------
# Lectura
# ----------------------------------------------------------------------

def _detectar_bloques(hoja):
    """
    Localiza el inicio de cada bloque mensual.

    Retorna [(fila, anio, mes, etiqueta), ...]
    """

    patron = re.compile(
        r"INGRESOS Y EGRESOS DEL MES DE\s+([A-ZÁÉÍÓÚÑ]+)\s+(\d{4})"
    )

    bloques = []

    for fila in range(hoja.nrows):
        for columna in range(hoja.ncols):

            texto = normalizar(hoja.cell_value(fila, columna))

            if not texto:
                continue

            encontrado = patron.search(texto)

            if encontrado:
                nombre_mes = encontrado.group(1)
                bloques.append(
                    (
                        fila,
                        int(encontrado.group(2)),
                        MESES.get(nombre_mes, 0),
                        f"{nombre_mes} {encontrado.group(2)}",
                    )
                )

    return bloques


def _fila_vacia(hoja, fila):
    return all(
        hoja.cell_value(fila, columna) in ("", None)
        for columna in range(hoja.ncols)
    )


def _es_totales(hoja, fila):
    """
    La fila de totales no tiene referencia ni descripción pero sí
    importes.
    """

    referencia = normalizar(hoja.cell_value(fila, COL_REFERENCIA))
    descripcion = normalizar(hoja.cell_value(fila, COL_DESCRIPCION))

    if referencia or descripcion:
        return False

    return any(
        a_decimal(hoja.cell_value(fila, columna)) != CERO
        for _, columna in FONDOS
    )


def _leer_partidas(hoja, inicio, fin, tipo, periodo):
    """
    Lee las partidas de una sección (ingresos o egresos).
    """

    partidas = []
    totales_declarados = None

    for fila in range(inicio, fin):

        if _fila_vacia(hoja, fila):
            continue

        if _es_totales(hoja, fila):
            totales_declarados = {
                nombre: a_decimal(hoja.cell_value(fila, columna))
                for nombre, columna in FONDOS
            }
            continue

        descripcion = str(
            hoja.cell_value(fila, COL_DESCRIPCION)
        ).strip()

        if not descripcion:
            continue

        importes = {
            nombre: a_decimal(hoja.cell_value(fila, columna))
            for nombre, columna in FONDOS
        }

        total_calculado = sum(importes.values(), CERO)

        if total_calculado == CERO:
            continue

        celda_fecha = hoja.cell_value(fila, COL_FECHA)

        partidas.append(
            {
                "fila_excel": fila + 1,
                "periodo": periodo,
                "tipo": tipo,
                "referencia": str(
                    hoja.cell_value(fila, COL_REFERENCIA)
                ).strip(),
                "descripcion": descripcion,
                "descripcion_normalizada": normalizar(descripcion),
                **{k: str(v) for k, v in importes.items()},
                "total": str(total_calculado),
                "total_declarado": str(
                    a_decimal(hoja.cell_value(fila, COL_TOTAL))
                ),
                "fecha": a_fecha(celda_fecha, hoja.book.datemode),
                "fecha_original": celda_fecha,
                "nota": str(hoja.cell_value(fila, COL_NOTA)).strip(),
            }
        )

    return partidas, totales_declarados


def leer_historico(ruta):
    """
    Lee el archivo completo y devuelve un bloque por mes.
    """

    libro = xlrd.open_workbook(ruta)
    hoja = libro.sheet_by_name("INGRESOS Y EGRESOS")

    bloques = _detectar_bloques(hoja)
    resultado = []

    for indice, (fila_inicio, anio, mes, etiqueta) in enumerate(bloques):

        fila_fin = (
            bloques[indice + 1][0]
            if indice + 1 < len(bloques)
            else hoja.nrows
        )

        # Localiza el encabezado de EGRESOS dentro del bloque
        fila_egresos = fila_fin

        for fila in range(fila_inicio, fila_fin):
            if normalizar(hoja.cell_value(fila, 2)).startswith("EGRESOS"):
                fila_egresos = fila
                break

        periodo = f"{anio}-{mes:02d}"

        ingresos, totales_ingresos = _leer_partidas(
            hoja,
            fila_inicio + 4,
            fila_egresos,
            "I",
            periodo,
        )

        egresos, totales_egresos = _leer_partidas(
            hoja,
            fila_egresos + 3,
            fila_fin,
            "E",
            periodo,
        )

        resultado.append(
            {
                "periodo": periodo,
                "etiqueta": etiqueta,
                "fila_excel": fila_inicio + 1,
                "ingresos": ingresos,
                "egresos": egresos,
                "totales_ingresos_declarados": totales_ingresos,
                "totales_egresos_declarados": totales_egresos,
            }
        )

    return resultado


def totalizar(partidas):
    """Suma por fondo de una lista de partidas."""

    return {
        nombre: sum(
            (Decimal(p[nombre]) for p in partidas),
            CERO,
        )
        for nombre, _ in FONDOS
    }
