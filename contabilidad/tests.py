from datetime import date
from decimal import Decimal
from io import StringIO

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db.models import Sum
from django.test import TestCase

from catalogos.models import ConceptoContable, DistribucionCapita, Grado, ParametroSistema
from contabilidad.models import Cuenta, EjercicioContable, PartidaPoliza, Poliza
from contabilidad.services.generacion import generar_poliza_desde_pago
from contabilidad.services.mapeo import cuenta_para_forma_pago
from miembros.models import Hermano
from negocio.models import AplicacionPago, Obligacion, Pago


class BasePolizaTestCase(TestCase):
    """Fixture compartida: catálogo de cuentas + un Hermano con una
    obligación de $100.00 (60 Membresía + 40 Revista)."""

    def setUp(self):

        ParametroSistema.objects.create(clave="EJERCICIO", valor="2026")
        for tipo in ("PD", "PI", "PE"):
            ParametroSistema.objects.create(clave=tipo, valor="0")

        self.ejercicio = EjercicioContable.objects.create(
            nombre="2026",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 12, 31),
        )

        self.caja = Cuenta.objects.create(
            codigo="1.01.001", nombre="Caja", tipo="ACTIVO",
        )
        self.bancos = Cuenta.objects.create(
            codigo="1.01.002", nombre="Bancos", tipo="ACTIVO",
        )
        self.anticipos = Cuenta.objects.create(
            codigo="2.01.001", nombre="Anticipos de Hermanos", tipo="PASIVO",
        )

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

        Cuenta.objects.create(
            codigo="4.01.001", nombre="Membresía", tipo="INGRESO",
            concepto_contable=self.membresia,
        )
        Cuenta.objects.create(
            codigo="4.01.002", nombre="Revista", tipo="INGRESO",
            concepto_contable=self.revista,
        )

        DistribucionCapita.objects.create(
            concepto_origen=self.origen, concepto_destino=self.membresia,
            importe=Decimal("60.00"), orden=1,
        )
        DistribucionCapita.objects.create(
            concepto_origen=self.origen, concepto_destino=self.revista,
            importe=Decimal("40.00"), orden=2,
        )

        self.obligacion = Obligacion.objects.create(
            hermano=self.hermano,
            concepto=self.origen,
            periodo="2026-07",
            importe=Decimal("100.00"),
            saldo_pendiente=Decimal("100.00"),
            fecha_vencimiento=date(2026, 7, 31),
            estado="PENDIENTE",
        )

    def _crear_pago(self, importe, forma_pago="EFECTIVO", fecha=date(2026, 7, 28)):
        return Pago.objects.create(
            hermano=self.hermano,
            fecha=fecha,
            importe=importe,
            forma_pago=forma_pago,
        )


class GenerarPolizaAplicacionExactaTests(BasePolizaTestCase):

    def setUp(self):
        super().setUp()
        self.pago = self._crear_pago(Decimal("100.00"))
        AplicacionPago.objects.create(
            pago=self.pago, obligacion=self.obligacion,
            importe_aplicado=Decimal("100.00"),
        )

    def test_poliza_balanceada_sin_anticipo(self):
        poliza = generar_poliza_desde_pago(self.pago)

        self.assertIsNotNone(poliza)
        poliza.validar_balance()

        partidas = poliza.partidas.all()
        self.assertEqual(partidas.count(), 3)  # caja + membresía + revista

        self.assertFalse(
            partidas.filter(cuenta=self.anticipos).exists()
        )
        self.assertEqual(
            partidas.get(cuenta=self.caja).debe, Decimal("100.00")
        )
        self.assertEqual(
            partidas.get(cuenta__concepto_contable=self.membresia).haber,
            Decimal("60.00"),
        )
        self.assertEqual(
            partidas.get(cuenta__concepto_contable=self.revista).haber,
            Decimal("40.00"),
        )

    def test_idempotente(self):
        primera = generar_poliza_desde_pago(self.pago)
        segunda = generar_poliza_desde_pago(self.pago)

        self.assertEqual(primera.pk, segunda.pk)
        self.assertEqual(
            PartidaPoliza.objects.filter(poliza=primera).count(), 3
        )


class GenerarPolizaConExcedenteTests(BasePolizaTestCase):

    def setUp(self):
        super().setUp()
        # Paga 150 pero la obligación pendiente es de 100: 50 de anticipo.
        self.pago = self._crear_pago(Decimal("150.00"))
        AplicacionPago.objects.create(
            pago=self.pago, obligacion=self.obligacion,
            importe_aplicado=Decimal("100.00"),
        )

    def test_excedente_se_registra_como_anticipo(self):
        poliza = generar_poliza_desde_pago(self.pago)
        poliza.validar_balance()

        partida_anticipo = poliza.partidas.get(cuenta=self.anticipos)
        self.assertEqual(partida_anticipo.haber, Decimal("50.00"))

        totales = poliza.partidas.aggregate(
            debe=Sum("debe"),
        )
        self.assertEqual(totales["debe"], Decimal("150.00"))


class GenerarPolizaAnticipoPuroTests(BasePolizaTestCase):
    """Caso defensivo: un Pago sin ninguna AplicacionPago (hoy no
    alcanzable desde ejecutar_cobro/ImportadorHistorico, que exigen
    obligaciones pendientes, pero el servicio debe soportarlo)."""

    def test_pago_sin_aplicaciones_genera_poliza_de_anticipo(self):
        pago = self._crear_pago(Decimal("75.00"))

        poliza = generar_poliza_desde_pago(pago)
        poliza.validar_balance()

        self.assertEqual(poliza.partidas.count(), 2)
        self.assertEqual(
            poliza.partidas.get(cuenta=self.caja).debe, Decimal("75.00")
        )
        self.assertEqual(
            poliza.partidas.get(cuenta=self.anticipos).haber, Decimal("75.00")
        )


class MapeoFormaPagoTests(BasePolizaTestCase):

    def test_efectivo_mapea_a_caja(self):
        self.assertEqual(cuenta_para_forma_pago("EFECTIVO"), self.caja)

    def test_transferencia_cheque_tarjeta_mapean_a_bancos(self):
        for forma in ("TRANSFERENCIA", "CHEQUE", "TARJETA"):
            self.assertEqual(cuenta_para_forma_pago(forma), self.bancos)


class ValidarBalanceTests(BasePolizaTestCase):

    def test_poliza_desbalanceada_lanza_error(self):
        poliza = Poliza.objects.create(
            ejercicio=self.ejercicio, tipo="INGRESO", folio="PI-2026-999999",
            fecha=date(2026, 7, 28), concepto="Prueba desbalanceada",
        )
        PartidaPoliza.objects.create(
            poliza=poliza, cuenta=self.caja,
            debe=Decimal("100.00"), haber=Decimal("0.00"), orden=0,
        )
        PartidaPoliza.objects.create(
            poliza=poliza, cuenta=self.anticipos,
            debe=Decimal("0.00"), haber=Decimal("50.00"), orden=1,
        )

        with self.assertRaises(ValidationError):
            poliza.validar_balance()

    def test_partida_no_permite_debe_y_haber_simultaneos(self):
        poliza = Poliza.objects.create(
            ejercicio=self.ejercicio, tipo="INGRESO", folio="PI-2026-999998",
            fecha=date(2026, 7, 28), concepto="Prueba inválida",
        )
        with self.assertRaises(ValidationError):
            PartidaPoliza.objects.create(
                poliza=poliza, cuenta=self.caja,
                debe=Decimal("10.00"), haber=Decimal("10.00"), orden=0,
            )

    def test_cuenta_de_mayor_no_acepta_movimientos(self):
        cuenta_mayor = Cuenta.objects.create(
            codigo="1.00.000", nombre="ACTIVO", tipo="ACTIVO",
            acepta_movimientos=False,
        )
        poliza = Poliza.objects.create(
            ejercicio=self.ejercicio, tipo="INGRESO", folio="PI-2026-999997",
            fecha=date(2026, 7, 28), concepto="Prueba cuenta de mayor",
        )
        with self.assertRaises(ValidationError):
            PartidaPoliza.objects.create(
                poliza=poliza, cuenta=cuenta_mayor,
                debe=Decimal("10.00"), haber=Decimal("0.00"), orden=0,
            )


class BackfillComandoTests(BasePolizaTestCase):

    def setUp(self):
        super().setUp()
        self.pago = self._crear_pago(Decimal("100.00"))
        AplicacionPago.objects.create(
            pago=self.pago, obligacion=self.obligacion,
            importe_aplicado=Decimal("100.00"),
        )

    def test_comando_es_idempotente(self):
        salida = StringIO()

        call_command("generar_polizas_historicas", stdout=salida)
        call_command("generar_polizas_historicas", stdout=salida)

        self.assertEqual(Poliza.objects.filter(pago=self.pago).count(), 1)
        self.assertIn("Pólizas creadas: 1.", salida.getvalue())
        self.assertIn("Pólizas creadas: 0.", salida.getvalue())
