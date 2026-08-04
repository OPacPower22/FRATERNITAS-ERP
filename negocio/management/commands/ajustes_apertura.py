"""Registra los adeudos y saldos a favor previos al arranque."""

from django.core.management.base import BaseCommand

from negocio.services.ajustes_apertura import aplicar, revertir


class Command(BaseCommand):

    help = (
        "Captura los adeudos anteriores a julio de 2026 y aplica "
        "los saldos a favor reconocidos en el histórico."
    )

    def add_arguments(self, parser):

        parser.add_argument(
            "--revertir",
            action="store_true",
            help="Elimina los ajustes y restituye los saldos.",
        )

        parser.add_argument(
            "--rehacer",
            action="store_true",
            help="Revierte y vuelve a aplicar.",
        )

    def handle(self, *args, **opciones):

        if opciones["revertir"] or opciones["rehacer"]:

            resumen = revertir()

            self.stdout.write(
                self.style.WARNING(
                    f"Eliminado: {resumen['adeudos']} adeudos, "
                    f"{resumen['saldos_a_favor']} saldos a favor."
                )
            )

            if opciones["revertir"]:
                return

        resultado = aplicar()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("ADEUDOS ANTERIORES"))
        self.stdout.write("-" * 78)

        for adeudo in resultado["adeudos"]:
            marca = "nuevo" if adeudo["nueva"] else "ya existía"
            self.stdout.write(
                f"{adeudo['hermano'][:32]:<34}"
                f"{adeudo['periodo']:<16}"
                f"{adeudo['importe']:>10,.2f}   ({marca})"
            )
            self.stdout.write(f"      {adeudo['fuente']}")

        self.stdout.write("-" * 78)
        self.stdout.write(
            f"{'Total por cobrar':<50}"
            f"{resultado['total_adeudos']:>10,.2f}"
        )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("SALDOS A FAVOR"))
        self.stdout.write("-" * 78)

        for credito in resultado["creditos"]:
            self.stdout.write(
                f"{credito['hermano'][:32]:<34}"
                f"{credito['importe']:>10,.2f}   "
                f"aplicado a {credito['aplicado_a']}"
            )
            if "saldo_resultante" in credito:
                self.stdout.write(
                    f"      Saldo resultante de esa obligación: "
                    f"${credito['saldo_resultante']:,.2f}"
                )

        self.stdout.write("-" * 78)
        self.stdout.write(
            f"{'Total reconocido':<50}"
            f"{resultado['total_creditos']:>10,.2f}"
        )
