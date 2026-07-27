"""Lector de movimientos históricos del MID.

Este módulo únicamente interpreta el archivo XLS histórico; no persiste datos.
"""

from pathlib import Path
from typing import Any
import unicodedata

import xlrd


class MigradorHistorico:
    """Obtiene los ingresos y egresos históricos de junio y julio de 2026."""

    NOMBRE_HOJA = "INGRESOS Y EGRESOS"
    MARCADOR_MES = "INGRESOS Y EGRESOS DEL MES DE"
    MARCADOR_INGRESOS = "M I E M B R O"
    MARCADOR_EGRESOS = "C O N C E P T O"
    MARCADOR_FIN_EGRESOS = "REMANENTE DEL MES"
    MESES = {
        "JUNIO": "JUNIO 2026",
        "JULIO": "JULIO 2026",
    }

    def __init__(self, ruta_archivo: Path | None = None) -> None:
        raiz_proyecto = Path(__file__).resolve().parents[3]
        self.ruta_archivo = ruta_archivo or (
            raiz_proyecto
            / "importaciones"
            / "tesoreria"
            / "MOVIMIENTOS 2026.xls"
        )
        self._libro: Any | None = None

    def abrir_libro(self) -> Any:
        """Abre el libro histórico y conserva la instancia para lecturas posteriores."""
        if self._libro is None:
            self._libro = xlrd.open_workbook(str(self.ruta_archivo))

        return self._libro

    def obtener_bloque_mes(self, nombre_mes: str) -> dict[str, int]:
        """Localiza las filas que delimitan el bloque de un mes solicitado."""
        mes = self._normalizar_nombre_mes(nombre_mes)
        hoja = self.abrir_libro().sheet_by_name(self.NOMBRE_HOJA)
        inicios_meses = self._buscar_inicios_meses(hoja)
        inicio = self._buscar_inicio_mes(inicios_meses, mes)
        fin = self._siguiente_inicio_mes(inicios_meses, inicio, hoja.nrows)

        inicio_ingresos = self._buscar_marcador(
            hoja,
            self.MARCADOR_INGRESOS,
            inicio,
            fin,
        )
        inicio_egresos = self._buscar_marcador(
            hoja,
            self.MARCADOR_EGRESOS,
            inicio,
            fin,
        )

        return {
            "inicio": inicio,
            "fin": fin,
            "inicio_ingresos": inicio_ingresos,
            "inicio_egresos": inicio_egresos,
        }

    def obtener_ingresos(self, nombre_mes: str) -> list[dict[str, Any]]:
        """Extrae las filas de ingresos del bloque indicado."""
        hoja = self.abrir_libro().sheet_by_name(self.NOMBRE_HOJA)
        bloque = self.obtener_bloque_mes(nombre_mes)
        ingresos = []

        for fila in range(bloque["inicio_ingresos"] + 1, bloque["inicio_egresos"]):
            valores = hoja.row_values(fila)
            if not self._tiene_valor(valores[1]):
                continue

            ingresos.append(
                {
                    "recibo": self._valor(valores[0]),
                    "miembro": self._valor(valores[1]),
                    "capitas": self._valor(valores[4]),
                    "aniversario": self._valor(valores[5]),
                    "beneficencia": self._valor(valores[6]),
                    "taller": self._valor(valores[7]),
                    "otros": self._valor(valores[8]),
                    "total": self._valor(valores[9]),
                    "fecha": self._valor(valores[10]),
                    "descripcion": self._valor(valores[11]),
                }
            )

        return ingresos

    def obtener_egresos(self, nombre_mes: str) -> list[dict[str, Any]]:
        """Extrae las filas de egresos del bloque indicado."""
        hoja = self.abrir_libro().sheet_by_name(self.NOMBRE_HOJA)
        bloque = self.obtener_bloque_mes(nombre_mes)
        egresos = []

        for fila in range(bloque["inicio_egresos"] + 1, bloque["fin"]):
            valores = hoja.row_values(fila)
            if self.MARCADOR_FIN_EGRESOS in self._texto_fila(valores):
                break

            if not self._tiene_valor(valores[1]):
                continue

            egresos.append(
                {
                    "concepto": self._valor(valores[1]),
                    "importe": self._valor(valores[9]),
                    "fecha": self._valor(valores[10]),
                    "descripcion": self._valor(valores[11]),
                }
            )

        return egresos

    def obtener_movimientos(self) -> dict[str, dict[str, list[dict[str, Any]]]]:
        """Regresa los movimientos históricos disponibles para el MID."""
        return {
            mes: {
                "ingresos": self.obtener_ingresos(mes),
                "egresos": self.obtener_egresos(mes),
            }
            for mes in self.MESES
        }

    def _buscar_inicios_meses(self, hoja: Any) -> list[int]:
        return [
            fila
            for fila in range(hoja.nrows)
            if self.MARCADOR_MES in self._texto_fila(hoja.row_values(fila))
        ]

    def _buscar_inicio_mes(self, inicios_meses: list[int], mes: str) -> int:
        hoja = self.abrir_libro().sheet_by_name(self.NOMBRE_HOJA)
        texto_mes = self.MESES[mes]

        for fila in inicios_meses:
            if texto_mes in self._texto_fila(hoja.row_values(fila)):
                return fila

        raise ValueError(f"No se encontró el bloque histórico de {texto_mes}.")

    @staticmethod
    def _siguiente_inicio_mes(inicios_meses: list[int], inicio: int, fin_hoja: int) -> int:
        for fila in inicios_meses:
            if fila > inicio:
                return fila

        return fin_hoja

    def _buscar_marcador(
        self,
        hoja: Any,
        marcador: str,
        inicio: int,
        fin: int,
    ) -> int:
        for fila in range(inicio, fin):
            if marcador in self._texto_fila(hoja.row_values(fila)):
                return fila

        raise ValueError(f"No se encontró el marcador {marcador!r}.")

    def _normalizar_nombre_mes(self, nombre_mes: str) -> str:
        nombre_normalizado = self._normalizar_texto(nombre_mes)

        for mes, texto_mes in self.MESES.items():
            if nombre_normalizado in {mes, texto_mes}:
                return mes

        raise ValueError(f"Mes histórico no soportado: {nombre_mes!r}.")

    @staticmethod
    def _texto_fila(valores: list[Any]) -> str:
        return " ".join(
            MigradorHistorico._normalizar_texto(valor)
            for valor in valores
            if isinstance(valor, str) and valor.strip()
        )

    @staticmethod
    def _normalizar_texto(valor: Any) -> str:
        texto = unicodedata.normalize("NFKD", str(valor))
        texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
        return " ".join(texto.upper().split())

    @staticmethod
    def _tiene_valor(valor: Any) -> bool:
        return valor is not None and (not isinstance(valor, str) or bool(valor.strip()))

    @staticmethod
    def _valor(valor: Any) -> Any:
        return valor.strip() if isinstance(valor, str) else valor
