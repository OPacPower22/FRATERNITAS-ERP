"""Carga el histórico de Tesorería en la tabla Movimiento."""

from django.core.management.base import BaseCommand

from tesoreria.services.importador_historico import importar, revertir


class Command(BaseCommand):

    help = (
        "Importa los movimientos históricos del archivo XLS de Tesorería."
    )

    def add_arguments(self, parser):

        parser.add_argument(
            "--archivo",
            default=None,
            help="Ruta del histórico. Por omisión usa importaciones/tesoreria/.",
        )

        parser.add_argument(
            "--revertir",
            action="store_true",
            help="Elimina los movimientos importados previamente y termina.",
        )

        parser.add_argument(
            "--rehacer",
            action="store_true",
            help="Revierte y vuelve a importar.",
        )

    def handle(self, *args, **opciones):

        if opciones["revertir"] or opciones["rehacer"]:

            eliminados = revertir()

            self.stdout.write(
                self.style.WARNING(
                    f"Movimientos históricos eliminados: {eliminados}"
                )
            )

            if opciones["revertir"]:
                return

        resultado = importar(opciones["archivo"])

        self.stdout.write("")
        self.stdout.write(
            f"{'Periodo':<16}{'Ingresos':>14}{'Egresos':>14}{'Neto':>14}"
        )
        self.stdout.write("-" * 58)

        acumulado = 0

        for fila in resultado["resumen"]:

            acumulado += fila["neto"]

            self.stdout.write(
                f"{fila['etiqueta']:<16}"
                f"{fila['ingresos']:>14,.2f}"
                f"{fila['egresos']:>14,.2f}"
                f"{fila['neto']:>14,.2f}"
            )

        self.stdout.write("-" * 58)
        self.stdout.write(
            self.style.SUCCESS(f"{'SALDO ACUMULADO':<44}{acumulado:>14,.2f}")
        )

        self.stdout.write("")
        self.stdout.write(f"Movimientos creados .....: {resultado['creados']}")
        self.stdout.write(
            f"Traspasos omitidos ......: {resultado['omitidos_traspaso']}"
        )
        self.stdout.write(
            f"Sin fecha en el Excel ...: {resultado['sin_fecha']} "
            f"(se asignó el último día del periodo)"
        )

        if resultado["sin_hermano"]:

            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    "Partidas sin Hermano identificado "
                    f"({len(resultado['sin_hermano'])}):"
                )
            )

            for periodo, fila_excel, descripcion in resultado["sin_hermano"]:
                self.stdout.write(
                    f"   {periodo}  fila {fila_excel:<5} {descripcion}"
                )
