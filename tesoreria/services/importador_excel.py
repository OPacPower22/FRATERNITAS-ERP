from pathlib import Path

from openpyxl import load_workbook


class ImportadorExcel:

    def obtener_informacion_libro(self):

        ruta = (
            Path(__file__)
            .resolve()
            .parent.parent.parent
            / "importaciones"
            / "tesoreria"
            / "TESORERIA_MOVIMIENTOS_2026.xlsx"
        )

        if not ruta.exists():
            return {
                "ok": False,
                "mensaje": "No se encontró el archivo de importación.",
            }

        libro = load_workbook(
            filename=ruta,
            read_only=True,
            data_only=True,
        )

        return {
            "ok": True,
            "archivo": str(ruta),
            "hojas": libro.sheetnames,
        }
