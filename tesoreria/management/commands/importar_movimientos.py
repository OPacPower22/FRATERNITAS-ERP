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
