from django.core.management.base import BaseCommand

from negocio.services.mid.catalogos import (
    sincronizar_catalogos,
)

from negocio.services.mid.parametros import (
    sincronizar_parametros_dmi,
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

        sincronizar_parametros_dmi()

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "MID finalizado correctamente."
            )
        )
