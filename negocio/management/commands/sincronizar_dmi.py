from django.core.management.base import BaseCommand

from negocio.services.mid.catalogos import (
    sincronizar_catalogos,
)


class Command(BaseCommand):

    help = (
        "Sincroniza el Documento Maestro Institucional."
    )

    def handle(
        self,
        *args,
        **options,
    ):

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "Iniciando MID..."
            )
        )

        sincronizar_catalogos()

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "MID finalizado correctamente."
            )
        )
