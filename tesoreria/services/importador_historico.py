"""
Importación del histórico de Tesorería a la tabla Movimiento.

Aprovecha que el modelo ``Movimiento`` tiene exactamente las cinco
columnas de fondo del archivo histórico (cápitas, aniversario, saco
de beneficencia, taller AJEF y otros), por lo que la carga es una
correspondencia directa renglón por renglón.

Cada movimiento importado queda marcado en ``observaciones`` con
``[HIST periodo Ffila]``, lo que hace la operación idempotente y
permite revertirla sin tocar los movimientos capturados en el
sistema.
"""

import calendar
import datetime
import re
import unicodedata
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.db import transaction

from miembros.models import Hermano
from tesoreria.models import Movimiento


MARCADOR = "[HIST"

RUTA_PREDETERMINADA = (
    Path(settings.BASE_DIR)
    / "importaciones"
    / "tesoreria"
    / "HISTORICO_MOVIMIENTOS_2026.xls"
)

# Partidas que sólo mueven dinero entre caja y banco.
TRASPASOS = ("DEPOSITO DE CAPITAS A BANCO",)

# Descripciones que no corresponden a un Hermano.
NO_NOMINATIVAS = (
    "SACO",
    "BENEFICENCIA",
    "DEPOSITO",
    "DONATIVO",
    "RIFA",
    "VENTA",
    "APORTACION",
)

# Equivalencias que no se resuelven por coincidencia de apellidos.
ALIAS = {
    "ENRIQUE RAMON (MESERO)": "RAMON",
    "J ALFREDO GONZALEZ": "GONZALEZ",
    "JOSE ALFREDO GONZALEZ": "GONZALEZ",
}

PALABRAS_IGNORADAS = {
    "JOSE", "LUIS", "ANGEL", "PAGO", "CAPITAS", "CAPITA",
    "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
    "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE",
    "DICIEMBRE",
}


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


class ResolutorHermanos:
    """Empareja la descripción del histórico con un Hermano."""

    def __init__(self):
        self.catalogo = [
            (hermano, _tokens(f"{hermano.apellido_paterno} "
                              f"{hermano.apellido_materno} "
                              f"{hermano.nombre}"))
            for hermano in Hermano.objects.all()
        ]

    def resolver(self, descripcion):
        """
        Retorna (hermano, confianza).

        confianza: ALTA, MEDIA o NINGUNA.
        """

        normalizada = _sin_acentos(descripcion)

        if any(clave in normalizada for clave in NO_NOMINATIVAS):
            return None, "NO NOMINATIVA"

        objetivo = _tokens(descripcion)

        for alias, apellido in ALIAS.items():
            if alias in normalizada:
                objetivo = objetivo | {apellido}

        mejor = (None, 0)

        for hermano, tokens in self.catalogo:
            comunes = len(tokens & objetivo)
            if comunes > mejor[1]:
                mejor = (hermano, comunes)

        if mejor[1] >= 2:
            return mejor[0], "ALTA"

        if mejor[1] == 1:
            return mejor[0], "MEDIA"

        return None, "NINGUNA"


def _fecha_respaldo(periodo):
    """Último día del periodo, para partidas sin fecha."""

    anio, mes = (int(parte) for parte in periodo.split("-"))

    return datetime.date(
        anio,
        mes,
        calendar.monthrange(anio, mes)[1],
    )


def _numero_recibo(referencia):
    """Extrae el consecutivo cuando la referencia lo contiene."""

    digitos = re.sub(r"\D", "", str(referencia or ""))

    return int(digitos) if digitos else None


def revertir(periodo=None):
    """
    Elimina los movimientos previamente importados.

    No toca los movimientos capturados por el sistema, porque
    éstos no llevan el marcador.
    """

    consulta = Movimiento.objects.filter(
        observaciones__startswith=MARCADOR,
    )

    if periodo:
        consulta = consulta.filter(
            observaciones__startswith=f"{MARCADOR} {periodo}",
        )

    total = consulta.count()
    consulta.delete()

    return total


@transaction.atomic
def importar(ruta=None, resolver_nombres=True):
    """
    Importa el histórico completo.

    Retorna un diccionario con el detalle de la operación.
    """

    import sys

    carpeta = Path(settings.BASE_DIR) / "importaciones"

    if str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))

    from historico import leer_historico

    ruta = Path(ruta) if ruta else RUTA_PREDETERMINADA

    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el histórico:\n{ruta}")

    bloques = leer_historico(str(ruta))

    resolutor = ResolutorHermanos() if resolver_nombres else None

    creados = 0
    omitidos_traspaso = 0
    sin_hermano = []
    sin_fecha = 0
    resumen = []

    for bloque in bloques:

        ingresos_periodo = Decimal("0.00")
        egresos_periodo = Decimal("0.00")

        for partida in bloque["ingresos"] + bloque["egresos"]:

            descripcion = partida["descripcion"]

            if any(
                clave in partida["descripcion_normalizada"]
                for clave in TRASPASOS
            ):
                omitidos_traspaso += 1
                continue

            marcador = (
                f"{MARCADOR} {partida['periodo']} "
                f"F{partida['fila_excel']}]"
            )

            fecha = partida["fecha"]

            if fecha is None:
                fecha = _fecha_respaldo(partida["periodo"])
                sin_fecha += 1

            hermano = None

            if resolutor and partida["tipo"] == "I":
                hermano, confianza = resolutor.resolver(descripcion)

                if confianza == "NINGUNA":
                    sin_hermano.append(
                        (partida["periodo"], partida["fila_excel"],
                         descripcion)
                    )

            observaciones = marcador

            if partida["nota"]:
                observaciones = f"{marcador} {partida['nota']}"

            ya_existe = Movimiento.objects.filter(
                observaciones__startswith=marcador,
            ).exists()

            if not ya_existe:

                Movimiento.objects.create(
                    tipo=partida["tipo"],
                    recibo=_numero_recibo(partida["referencia"]),
                    hermano=hermano,
                    concepto=descripcion[:200],
                    fecha=fecha,
                    capitas=Decimal(partida["capitas"]),
                    aniversario=Decimal(partida["aniversario"]),
                    saco_beneficencia=Decimal(
                        partida["saco_beneficencia"]
                    ),
                    taller_bj=Decimal(partida["taller_bj"]),
                    otros=Decimal(partida["otros"]),
                    total=Decimal(partida["total"]),
                    observaciones=observaciones,
                )

                creados += 1

            if partida["tipo"] == "I":
                ingresos_periodo += Decimal(partida["total"])
            else:
                egresos_periodo += Decimal(partida["total"])

        resumen.append(
            {
                "periodo": bloque["periodo"],
                "etiqueta": bloque["etiqueta"],
                "ingresos": ingresos_periodo,
                "egresos": egresos_periodo,
                "neto": ingresos_periodo - egresos_periodo,
            }
        )

    return {
        "creados": creados,
        "omitidos_traspaso": omitidos_traspaso,
        "sin_fecha": sin_fecha,
        "sin_hermano": sin_hermano,
        "resumen": resumen,
    }
