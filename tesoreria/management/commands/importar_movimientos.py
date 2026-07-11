from django.core.management.base import BaseCommand

from tesoreria.services.importador_excel import ImportadorExcel


class Command(BaseCommand):

    help = "Importa movimientos desde un archivo Excel."

    def handle(self, *args, **options):

        servicio = ImportadorExcel()

        resultado = servicio.obtener_informacion_libro()

        self.stdout.write("====================================")
        self.stdout.write("FRATERNITAS ERP")
        self.stdout.write("Motor de Importación de Datos")
        self.stdout.write("MID-001")
        self.stdout.write("====================================")

        if not resultado["ok"]:
            self.stdout.write(self.style.ERROR(resultado["mensaje"]))
            return

        self.stdout.write(
            self.style.SUCCESS("Archivo localizado correctamente.")
        )

        self.stdout.write("")
        self.stdout.write("Hojas detectadas:")

        for hoja in resultado["hojas"]:
            self.stdout.write(f" - {hoja}")

        resultado_filas = servicio.obtener_filas()

        if not resultado_filas["ok"]:
            self.stdout.write(self.style.ERROR(resultado_filas["mensaje"]))
            return

        self.stdout.write("")
        self.stdout.write(f"Filas: {resultado_filas['filas']}")
        self.stdout.write(f"Columnas: {resultado_filas['columnas']}")

        resultado = servicio.obtener_primeras_filas()

        self.stdout.write("")
        self.stdout.write("Primeras filas:")

        for fila in resultado["filas"]:
            self.stdout.write(str(fila))

        resultado = servicio.obtener_encabezados()

        self.stdout.write("")
        self.stdout.write("Encabezados:")

        for encabezado in resultado["encabezados"]:
            self.stdout.write(f"- {encabezado}")

            resultado = servicio.obtener_primer_movimiento()

        self.stdout.write("")
        self.stdout.write("Primer movimiento:")

        for campo, valor in resultado["movimiento"].items():
            self.stdout.write(f"{campo}: {valor}")

        resultado = servicio.obtener_movimientos()

        self.stdout.write("")
        self.stdout.write(
            f"Movimientos leídos: {len(resultado['movimientos'])}"
        ) 

        self.stdout.write("")
        self.stdout.write("Primeros 10 movimientos:")

        for movimiento in resultado["movimientos"][:10]:
         self.stdout.write(str(movimiento))