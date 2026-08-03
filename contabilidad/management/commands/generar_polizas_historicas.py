from django.core.management.base import BaseCommand
from django.db import transaction

from contabilidad.models import Poliza
from contabilidad.services.generacion import generar_poliza_desde_pago
from negocio.models import Pago


class Command(BaseCommand):

    help = (
        "Genera las pólizas contables faltantes para pagos "
        "existentes (backfill histórico). No modifica "
        "reconstruir_movimientos ni ningún otro comando existente."
    )

    def add_arguments(self, parser):

        parser.add_argument(
            "--desde",
            type=str,
            default=None,
            help="Fecha mínima (AAAA-MM-DD) de los pagos a procesar.",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="No escribe nada, solo informa cuántos pagos se procesarían.",
        )

    def handle(self, *args, **options):

        pagos = Pago.objects.filter(estado="REGISTRADO").order_by("id")

        if options["desde"]:
            pagos = pagos.filter(fecha__gte=options["desde"])

        procesados = 0
        creadas = 0
        omitidos = 0
        errores = 0

        for pago in pagos.iterator():

            if Poliza.objects.filter(pago=pago).exists():
                omitidos += 1
                continue

            procesados += 1

            if options["dry_run"]:
                continue

            try:
                with transaction.atomic():
                    poliza = generar_poliza_desde_pago(pago)
            except Exception as error:
                errores += 1
                self.stderr.write(
                    self.style.ERROR(f"Pago #{pago.pk}: {error}")
                )
                continue

            if poliza is not None:
                creadas += 1
            else:
                omitidos += 1

        self.stdout.write(self.style.SUCCESS(
            f"Pagos procesados: {procesados}. "
            f"Pólizas creadas: {creadas}. "
            f"Omitidos: {omitidos}. "
            f"Errores: {errores}."
        ))
