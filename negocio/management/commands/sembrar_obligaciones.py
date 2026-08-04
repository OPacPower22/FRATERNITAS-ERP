"""Siembra el estado de obligaciones desde la matriz MEMBRESIA."""

from decimal import Decimal

from django.core.management.base import BaseCommand

from negocio.services.siembra_obligaciones import revertir, sembrar


class Command(BaseCommand):

    help = (
        "Genera las obligaciones de cápita y marca como cubiertas "
        "las que la hoja MEMBRESIA registra con número de recibo."
    )

    def add_arguments(self, parser):

        parser.add_argument("--archivo", default=None)

        parser.add_argument(
            "--desde",
            default="2026-07",
            help="Primer periodo que genera obligación (AAAA-MM).",
        )

        parser.add_argument(
            "--corte",
            default=None,
            help="Último periodo vencido. Por omisión, el mes en curso.",
        )

        parser.add_argument(
            "--importe",
            default="400.00",
            help="Cuota mensual vigente.",
        )

        parser.add_argument(
            "--revertir",
            action="store_true",
            help="Elimina lo sembrado y termina.",
        )

        parser.add_argument(
            "--rehacer",
            action="store_true",
            help="Revierte y vuelve a sembrar.",
        )

        parser.add_argument(
            "--detalle",
            action="store_true",
            help="Imprime el estado de cada Hermano por periodo.",
        )

    def handle(self, *args, **opciones):

        if opciones["revertir"] or opciones["rehacer"]:

            eliminado = revertir()

            self.stdout.write(
                self.style.WARNING(
                    f"Eliminado: {eliminado['obligaciones']} obligaciones, "
                    f"{eliminado['pagos']} pagos, "
                    f"{eliminado['aplicaciones']} aplicaciones."
                )
            )

            if opciones["revertir"]:
                return

        resultado = sembrar(
            ruta=opciones["archivo"],
            desde=opciones["desde"],
            corte=opciones["corte"],
            importe=Decimal(opciones["importe"]),
        )

        self.stdout.write("")
        self.stdout.write(
            f"Periodo de arranque .....: {resultado['desde']}"
        )
        self.stdout.write(
            f"Último periodo vencido ..: {resultado['corte']}"
        )
        self.stdout.write(
            f"Cuota mensual ...........: ${resultado['importe']}"
        )
        self.stdout.write(
            f"Hermanos activos ........: {resultado['hermanos_activos']}"
        )
        self.stdout.write("")
        self.stdout.write(
            f"Obligaciones creadas ....: {resultado['obligaciones_creadas']}"
        )
        self.stdout.write(
            f"   Liquidadas ...........: {resultado['liquidadas']}"
        )
        self.stdout.write(
            f"   Parciales ............: {resultado['parciales']}"
        )
        self.stdout.write(
            f"   Pendientes ...........: {resultado['pendientes']}"
        )
        self.stdout.write(
            f"Pagos reconstruidos .....: {resultado['pagos_creados']}"
        )

        if opciones["detalle"]:

            self.stdout.write("")
            self.stdout.write(
                f"{'HERMANO':<34}{'PERIODO':<10}"
                f"{'ESTADO':<12}{'PAGADO':>10}{'SALDO':>10}  RECIBO"
            )
            self.stdout.write("-" * 88)

            for fila in resultado["detalle"]:
                self.stdout.write(
                    f"{fila['hermano'][:33]:<34}"
                    f"{fila['periodo']:<10}"
                    f"{fila['estado']:<12}"
                    f"{fila['pagado']:>10,.2f}"
                    f"{fila['saldo']:>10,.2f}"
                    f"  {fila['recibo'] or ''}"
                )

        if resultado["sin_emparejar"]:

            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING("Renglones sin Hermano identificado:")
            )

            for nombre, coincidencias in resultado["sin_emparejar"]:
                self.stdout.write(
                    f"   {nombre}  (coincidencias: {coincidencias})"
                )
