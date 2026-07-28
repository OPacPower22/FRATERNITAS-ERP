from django.core.management.base import BaseCommand

from negocio.models import Pago
from negocio.services.contabilidad import generar_movimientos
from tesoreria.models import Movimiento


class Command(BaseCommand):
    help = "Genera los movimientos contables faltantes para pagos existentes."

    def handle(self, *args, **options):
        pagos_procesados = 0
        movimientos_creados = 0

        for pago in Pago.objects.order_by("id").iterator():
            existentes = Movimiento.objects.filter(pago=pago).count()
            generar_movimientos(pago)
            total_actual = Movimiento.objects.filter(pago=pago).count()
            pagos_procesados += 1
            movimientos_creados += total_actual - existentes

        self.stdout.write(
            self.style.SUCCESS(
                "Pagos procesados: "
                f"{pagos_procesados}. Movimientos creados: {movimientos_creados}."
            )
        )
