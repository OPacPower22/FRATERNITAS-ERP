"""Importación de ingresos históricos mediante los servicios del dominio."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import logging
from typing import Any
import unicodedata

import xlrd
from django.db import transaction

from miembros.models import Hermano
from negocio.domain.reglas import FormaPago
from negocio.services.aplicacion import calcular_propuesta, ejecutar_propuesta
from negocio.services.obligaciones import obtener_obligaciones_pendientes
from negocio.services.pagos import registrar_pago
from negocio.services.recibos import emitir_recibo
from negocio.services.mid.alias_miembros import ALIAS_MIEMBROS


logger = logging.getLogger(__name__)


class ErrorImportacionHistorica(Exception):
    """Indica que un ingreso histórico no puede ser importado."""


class ImportadorHistorico:
    """Importa ingresos históricos sin procesar los egresos."""

    MESES = ("JUNIO", "JULIO")
    FECHAS_POR_DEFECTO = {
        "JUNIO": date(2026, 6, 1),
        "JULIO": date(2026, 7, 1),
    }
    TOKENS_DE_PERIODO = {
        "ENE", "ENERO", "FEB", "FEBRERO", "MAR", "MARZO",
        "ABR", "ABRIL", "MAY", "MAYO", "JUN", "JUNIO",
        "JUL", "JULIO", "AGO", "AGOSTO", "SEP", "SEPT",
        "SEPTIEMBRE", "OCT", "OCTUBRE", "NOV", "NOVIEMBRE",
        "DIC", "DICIEMBRE", "A",
    }
    REGISTROS_INSTITUCIONALES = {
        "SACO BENEFICENCIA",
        "SACO DE BENEFICENCIA",
        "SAC BENEFICENCIA",
    }

    def __init__(self, usuario: Any) -> None:
        self.usuario = usuario

    def importar(self, datos: dict[str, dict[str, list[dict[str, Any]]]]) -> dict[str, Any]:
        """Importa los ingresos de junio y julio y acumula los errores encontrados."""
        resultado: dict[str, Any] = {
            "procesados": 0,
            "correctos": 0,
            "errores": [],
        }

        hermanos = list(Hermano.objects.all())

        for mes in self.MESES:
            ingresos = datos.get(mes, {}).get("ingresos", [])

            for ingreso in ingresos:
                if self._es_registro_institucional(ingreso.get("miembro")):
                    logger.info("Registro institucional omitido.")
                    continue

                resultado["procesados"] += 1
                error = self._importar_ingreso(ingreso, hermanos, mes)

                if error:
                    resultado["errores"].append(
                        {
                            "mes": mes,
                            "ingreso": ingreso,
                            "error": error,
                        }
                    )
                else:
                    resultado["correctos"] += 1

        return resultado

    def _importar_ingreso(
        self,
        ingreso: dict[str, Any],
        hermanos: list[Hermano],
        mes: str,
    ) -> str | None:
        hermano, error = self._buscar_hermano(ingreso.get("miembro"), hermanos)
        if error:
            return error

        try:
            importe = self._obtener_importe(ingreso.get("total"))
            fecha = self._obtener_fecha(ingreso.get("fecha"), mes)

            with transaction.atomic():
                pago = registrar_pago(
                    hermano=hermano,
                    importe=importe,
                    fecha=fecha,
                    forma_pago=self._obtener_forma_pago(ingreso),
                    referencia=str(ingreso.get("recibo") or "").strip(),
                    observaciones=str(ingreso.get("descripcion") or "").strip(),
                )

                obligaciones = obtener_obligaciones_pendientes(hermano)
                if not obligaciones:
                    raise ErrorImportacionHistorica(
                        "El hermano no tiene obligaciones pendientes."
                    )

                propuesta = calcular_propuesta(obligaciones, importe)

                if not propuesta.aplicaciones:
                    raise ErrorImportacionHistorica(
                        "El hermano no tiene obligaciones pendientes."
                    )

                ejecutar_propuesta(pago, propuesta)
                emitir_recibo(pago, self.usuario)
        except ErrorImportacionHistorica as error_importacion:
            return str(error_importacion)
        except (InvalidOperation, TypeError, ValueError) as error_validacion:
            return f"Datos inválidos: {error_validacion}"
        except Exception as error_inesperado:
            return f"Error al importar el ingreso: {error_inesperado}"

        return None

    def _buscar_hermano(
        self,
        nombre_historico: Any,
        hermanos: list[Hermano],
    ) -> tuple[Hermano | None, str | None]:
        nombre_normalizado = self._normalizar_texto(nombre_historico)
        if not nombre_normalizado:
            return None, "El ingreso no tiene miembro."

        nombre_normalizado = self._resolver_alias(nombre_normalizado)

        candidatos = []
        for hermano in hermanos:
            puntuacion = self._puntuacion_coincidencia(nombre_normalizado, hermano)
            if puntuacion is not None:
                candidatos.append((puntuacion, hermano))

        if not candidatos:
            return None, f"No se encontró al hermano {nombre_historico!r}."

        mejor_puntuacion = max(puntuacion for puntuacion, _ in candidatos)
        mejores = [
            hermano
            for puntuacion, hermano in candidatos
            if puntuacion == mejor_puntuacion
        ]

        if len(mejores) > 1:
            return (
                None,
                f"El miembro {nombre_historico!r} coincide con varios hermanos.",
            )

        return mejores[0], None

    def _resolver_alias(self, nombre_normalizado: str) -> str:
        alias_normalizados = {
            self._normalizar_texto(alias): self._normalizar_texto(nombre)
            for alias, nombre in ALIAS_MIEMBROS.items()
        }
        return alias_normalizados.get(nombre_normalizado, nombre_normalizado)

    def _es_registro_institucional(self, nombre: Any) -> bool:
        return self._normalizar_texto(nombre) in self.REGISTROS_INSTITUCIONALES

    def _puntuacion_coincidencia(
        self,
        nombre_historico: str,
        hermano: Hermano,
    ) -> int | None:
        tokens_historicos = [
            token
            for token in nombre_historico.split()
            if token not in self.TOKENS_DE_PERIODO
        ]
        if not tokens_historicos:
            return None

        tokens_hermano = self._nombre_hermano(hermano).split()
        coincidencias = sum(
            self._token_coincide(token, tokens_hermano)
            for token in tokens_historicos
        )

        if coincidencias < 2 or coincidencias / len(tokens_historicos) < 0.66:
            return None

        return coincidencias

    @staticmethod
    def _token_coincide(token: str, tokens_hermano: list[str]) -> bool:
        if token in tokens_hermano:
            return True

        return len(token) == 1 and any(
            token == token_hermano[:1]
            for token_hermano in tokens_hermano
        )

    def _obtener_importe(self, valor: Any) -> Decimal:
        try:
            importe = Decimal(str(valor))
        except (InvalidOperation, TypeError, ValueError) as error:
            raise ErrorImportacionHistorica("El ingreso no tiene un total válido.") from error

        if importe <= Decimal("0.00"):
            raise ErrorImportacionHistorica(
                "El total del ingreso debe ser mayor que cero."
            )

        return importe

    def _obtener_fecha(self, valor: Any, mes: str) -> date:
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            return self.FECHAS_POR_DEFECTO[mes]

        if isinstance(valor, datetime):
            return valor.date()
        if isinstance(valor, date):
            return valor
        if isinstance(valor, (int, float)):
            try:
                return xlrd.xldate_as_datetime(valor, 0).date()
            except (OverflowError, ValueError, xlrd.XLDateError) as error:
                raise ErrorImportacionHistorica(
                    "La fecha del ingreso no es válida."
                ) from error

        if isinstance(valor, str):
            try:
                return date.fromisoformat(valor.strip())
            except ValueError as error:
                raise ErrorImportacionHistorica(
                    "La fecha del ingreso no es válida."
                ) from error

        raise ErrorImportacionHistorica("El ingreso no tiene fecha.")

    @staticmethod
    def _obtener_forma_pago(ingreso: dict[str, Any]) -> str:
        descripcion = str(ingreso.get("descripcion") or "").upper()
        if "TRANSFERENCIA" in descripcion:
            return FormaPago.TRANSFERENCIA.value

        return FormaPago.EFECTIVO.value

    @staticmethod
    def _nombre_hermano(hermano: Hermano) -> str:
        return ImportadorHistorico._normalizar_texto(
            " ".join(
                (
                    hermano.nombre,
                    hermano.apellido_paterno,
                    hermano.apellido_materno,
                )
            )
        )

    @staticmethod
    def _normalizar_texto(valor: Any) -> str:
        texto = unicodedata.normalize("NFKD", str(valor or ""))
        texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
        return " ".join(texto.upper().split())
