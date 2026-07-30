from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalogos.models import Cargo, ConceptoContable, Grado
from contabilidad.models import EjercicioContable
from documentos.models import Recibo
from miembros.models import AdscripcionLogial, Hermano, Logia, NombramientoLogial
from negocio.models import Obligacion, Pago
from miembros.services.expediente import obtener_detalle_expediente, obtener_expediente


class ExpedienteServiceTests(TestCase):
    def test_obtener_expediente_reune_datos_administrativos(self):
        grado = Grado.objects.create(nombre="Maestro", abreviatura="M", orden=1)
        concepto = ConceptoContable.objects.create(nombre="Cuota mensual")
        hermano = Hermano.objects.create(
            numero_control="H-001",
            nombre="Juan",
            apellido_paterno="Pérez",
            apellido_materno="López",
            grado=grado,
            fecha_nacimiento=date(1990, 1, 15),
            fecha_ingreso=date(2020, 3, 1),
            tipo_ingreso="INICIACION",
            estatus="ACTIVO",
        )
        Obligacion.objects.create(
            hermano=hermano,
            concepto=concepto,
            periodo="2024-01",
            importe=Decimal("100.00"),
            saldo_pendiente=Decimal("80.00"),
            fecha_vencimiento=date(2024, 1, 31),
            estado="PENDIENTE",
        )
        Pago.objects.create(
            hermano=hermano,
            fecha=date(2024, 1, 10),
            importe=Decimal("20.00"),
            forma_pago="EFECTIVO",
        )

        expediente = obtener_expediente(hermano)

        self.assertEqual(expediente["nombre_completo"], "Juan Pérez López")
        self.assertEqual(expediente["grado"], "Maestro")
        self.assertEqual(expediente["fecha_nacimiento"], date(1990, 1, 15))
        self.assertEqual(expediente["fecha_ingreso"], date(2020, 3, 1))
        self.assertEqual(expediente["tipo_ingreso"], "INICIACION")
        self.assertEqual(expediente["estatus"], "ACTIVO")
        self.assertEqual(expediente["adeudo_actual"], Decimal("80.00"))
        self.assertEqual(expediente["numero_obligaciones_pendientes"], 1)
        self.assertEqual(expediente["estado_administrativo"], "DESPLOMADO")
        self.assertIsNotNone(expediente["ultimo_pago"])


class ExpedienteDetalleTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="oficial",
            password="secreto-seguro",
        )
        grado = Grado.objects.create(nombre="Compañero", abreviatura="C", orden=2)
        concepto = ConceptoContable.objects.create(nombre="Cápita")
        self.hermano = Hermano.objects.create(
            numero_control="H-EXP-001",
            nombre="Luis",
            apellido_paterno="García",
            apellido_materno="López",
            grado=grado,
            fecha_nacimiento=date(1980, 1, 2),
            fecha_ingreso=date(2010, 2, 3),
            curp="GALL800102HDFRPS01",
            rfc="GALL800102AB1",
            estado_civil="CASADO",
        )
        Obligacion.objects.create(
            hermano=self.hermano,
            concepto=concepto,
            periodo="2026-01",
            importe=Decimal("100.00"),
            saldo_pendiente=Decimal("100.00"),
            fecha_vencimiento=date(2026, 1, 31),
            estado="PENDIENTE",
        )
        pago = Pago.objects.create(
            hermano=self.hermano,
            fecha=date(2026, 1, 15),
            importe=Decimal("50.00"),
            forma_pago="EFECTIVO",
        )
        Recibo.objects.create(pago=pago, folio=1, emitido_por=self.usuario)
        EjercicioContable.objects.create(
            nombre="Ejercicio 2026",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 12, 31),
            activo=True,
        )
        logia = Logia.objects.create(
            nombre="Fraternidad",
            numero="1",
            oriente="Ciudad de México",
            rito="Rito Escocés Antiguo y Aceptado",
        )
        AdscripcionLogial.objects.create(hermano=self.hermano, logia=logia)
        cargo = Cargo.objects.create(nombre="Orador")
        NombramientoLogial.objects.create(hermano=self.hermano, cargo=cargo)

    def test_detalle_reune_fuentes_y_calcula_semaforo_rojo(self):
        detalle = obtener_detalle_expediente(self.hermano)

        self.assertEqual(detalle["semaforo_financiero"], "ROJO")
        self.assertEqual(detalle["total_pagado_ejercicio"], Decimal("50.00"))
        self.assertEqual(detalle["total_pagado_historico"], Decimal("50.00"))
        self.assertEqual(detalle["adscripcion_actual"].logia.numero, "1")
        self.assertEqual(len(detalle["movimientos"]), 2)

    def test_expediente_requiere_autenticacion_y_se_renderiza(self):
        url = reverse("miembros:expediente_detalle", args=[self.hermano.id])
        self.assertEqual(self.client.get(url).status_code, 302)

        self.client.force_login(self.usuario)
        respuesta = self.client.get(url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "EXP-001 · Expediente del Hermano")
        self.assertContains(respuesta, "ROJO")
