from datetime import date
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from catalogos.models import ConceptoContable, DistribucionCapita, Grado
from miembros.models import Hermano
from negocio.models import AplicacionPago, Obligacion, Pago
from negocio.services.contabilidad import generar_movimientos
from tesoreria.models import Movimiento


class GenerarMovimientosTests(TestCase):
    def setUp(self):
        grado = Grado.objects.create(nombre="Maestro", abreviatura="MM", orden=1)
        self.hermano = Hermano.objects.create(
            numero_control="001",
            nombre="Juan",
            apellido_paterno="Pérez",
            grado=grado,
        )
        self.origen = ConceptoContable.objects.create(nombre="Cápita")
        self.membresia = ConceptoContable.objects.create(nombre="Membresía")
        self.revista = ConceptoContable.objects.create(nombre="Revista")
        DistribucionCapita.objects.create(
            concepto_origen=self.origen,
            concepto_destino=self.membresia,
            importe=Decimal("60.00"),
            orden=1,
        )
        DistribucionCapita.objects.create(
            concepto_origen=self.origen,
            concepto_destino=self.revista,
            importe=Decimal("40.00"),
            orden=2,
        )
        obligacion = Obligacion.objects.create(
            hermano=self.hermano,
            concepto=self.origen,
            periodo="2026-07",
            importe=Decimal("100.00"),
            saldo_pendiente=Decimal("0.00"),
            fecha_vencimiento=date(2026, 7, 31),
            estado="LIQUIDADA",
        )
        self.pago = Pago.objects.create(
            hermano=self.hermano,
            fecha=date(2026, 7, 28),
            importe=Decimal("100.00"),
            forma_pago="EFECTIVO",
        )
        AplicacionPago.objects.create(
            pago=self.pago,
            obligacion=obligacion,
            importe_aplicado=Decimal("100.00"),
        )

    def test_genera_movimientos_por_destino_e_idempotentemente(self):
        movimientos = generar_movimientos(self.pago)

        self.assertEqual(len(movimientos), 2)
        self.assertEqual(Movimiento.objects.filter(pago=self.pago).count(), 2)
        self.assertEqual(
            Movimiento.objects.get(
                pago=self.pago,
                concepto_contable=self.membresia,
            ).total,
            Decimal("60.00"),
        )
        self.assertEqual(
            Movimiento.objects.get(
                pago=self.pago,
                concepto_contable=self.revista,
            ).total,
            Decimal("40.00"),
        )

        generar_movimientos(self.pago)

        self.assertEqual(Movimiento.objects.filter(pago=self.pago).count(), 2)

    def test_comando_reconstruye_solo_los_movimientos_faltantes(self):
        salida = StringIO()

        call_command("reconstruir_movimientos", stdout=salida)
        call_command("reconstruir_movimientos", stdout=salida)

        self.assertEqual(Movimiento.objects.filter(pago=self.pago).count(), 2)
        self.assertIn("Movimientos creados: 2.", salida.getvalue())
        self.assertIn("Movimientos creados: 0.", salida.getvalue())
