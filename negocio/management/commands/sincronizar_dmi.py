from django.core.management.base import BaseCommand

from negocio.services.mid.catalogos import (
    sincronizar_catalogos,
)

from negocio.services.mid.parametros import (
    sincronizar_parametros_dmi,
)

from negocio.services.mid.miembros import (
    sincronizar_miembros,
)

from negocio.services.mid.tarifas import (
    sincronizar_tarifas_dmi,
)  

from negocio.services.mid.distribucion import (
    sincronizar_distribucion_dmi,
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

            sincronizar_miembros()

            sincronizar_tarifas_dmi()

            sincronizar_distribucion_dmi()

            self.stdout.write("")
    
            self.stdout.write(
                    self.style.SUCCESS(
                            "MID finalizado correctamente."
                    )
            )
