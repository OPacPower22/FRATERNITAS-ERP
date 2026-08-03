from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max, Min

from catalogos.models import ConceptoContable, ParametroSistema
from contabilidad.models import Cuenta, EjercicioContable
from negocio.models import Pago


# Años hacia adelante desde hoy que siempre deben tener un
# EjercicioContable sembrado, para que generar_poliza_desde_pago no
# falle simplemente porque cambió el año y nadie volvió a correr
# este comando.
ANIOS_EJERCICIO_ADELANTE = 3

# codigo, nombre, tipo, cuenta_padre_codigo, acepta_movimientos, clave_concepto_contable
CUENTAS = [
    ("1.00.000", "ACTIVO", "ACTIVO", None, False, None),
    ("1.01.000", "Activo Circulante", "ACTIVO", "1.00.000", False, None),
    ("1.01.001", "Caja", "ACTIVO", "1.01.000", True, None),
    ("1.01.002", "Bancos", "ACTIVO", "1.01.000", True, None),

    ("2.00.000", "PASIVO", "PASIVO", None, False, None),
    ("2.01.000", "Pasivo Circulante", "PASIVO", "2.00.000", False, None),
    ("2.01.001", "Anticipos de Hermanos", "PASIVO", "2.01.000", True, None),
    ("2.01.002", "Acreedores Diversos", "PASIVO", "2.01.000", True, None),

    ("3.00.000", "PATRIMONIO", "PATRIMONIO", None, False, None),
    ("3.01.000", "Patrimonio Social", "PATRIMONIO", "3.00.000", True, None),
    ("3.02.000", "Resultados Acumulados", "PATRIMONIO", "3.00.000", True, None),
    ("3.03.000", "Resultado del Ejercicio", "PATRIMONIO", "3.00.000", True, None),

    ("4.00.000", "INGRESOS", "INGRESO", None, False, None),
    ("4.01.000", "Ingresos por Cuotas", "INGRESO", "4.00.000", False, None),
    ("4.01.001", "Membresía", "INGRESO", "4.01.000", True, "Membresía"),
    ("4.01.002", "Revista", "INGRESO", "4.01.000", True, "Revista"),
    ("4.01.003", "Conferencia Gran Logia", "INGRESO", "4.01.000", True, "Conferencia Gran Logia"),
    ("4.01.004", "CMI", "INGRESO", "4.01.000", True, "CMI"),
    ("4.01.005", "Servicios Recibidos", "INGRESO", "4.01.000", True, "Servicios Recibidos"),
    ("4.01.006", "Fondo Contingencia Anual", "INGRESO", "4.01.000", True, "Fondo Contingencia Anual"),
    ("4.01.007", "Post Mortem", "INGRESO", "4.01.000", True, "Post Mortem"),
    ("4.01.008", "Defunción", "INGRESO", "4.01.000", True, "Defunción"),
    ("4.01.009", "Aportación Fraternidad", "INGRESO", "4.01.000", True, "Aportación Fraternidad"),
    ("4.01.010", "Aportación AJEF", "INGRESO", "4.01.000", True, "Aportación AJEF"),
    ("4.01.011", "Aportación Tesoro", "INGRESO", "4.01.000", True, "Aportación Tesoro"),
    ("4.02.000", "Otros Ingresos", "INGRESO", "4.00.000", False, None),
    ("4.02.001", "Saco de Beneficencia", "INGRESO", "4.02.000", True, "Saco de Beneficencia"),

    ("5.00.000", "GASTOS", "GASTO", None, False, None),
    ("5.01.000", "Remesas a GLUM", "GASTO", "5.00.000", True, None),
    ("5.02.000", "Gastos Locales y Administrativos", "GASTO", "5.00.000", True, None),
]

FOLIOS_CONTABLES = ("PD", "PI", "PE")


class Command(BaseCommand):

    help = (
        "Siembra el catálogo de cuentas contables, el/los ejercicios "
        "contables y los contadores de folio de pólizas. Idempotente."
    )

    @transaction.atomic
    def handle(self, *args, **options):

        creadas, actualizadas = self._sembrar_cuentas()
        ejercicios = self._sembrar_ejercicios()
        folios = self._sembrar_folios()

        self.stdout.write(self.style.SUCCESS(
            f"Cuentas creadas: {creadas}. Actualizadas: {actualizadas}. "
            f"Ejercicios: {ejercicios}. Folios: {folios}."
        ))

    def _sembrar_cuentas(self):

        creadas = 0
        actualizadas = 0

        for codigo, nombre, tipo, codigo_padre, acepta_movimientos, clave_concepto in CUENTAS:

            cuenta_padre = (
                Cuenta.objects.get(codigo=codigo_padre)
                if codigo_padre
                else None
            )

            concepto_contable = (
                ConceptoContable.objects.get(nombre=clave_concepto)
                if clave_concepto
                else None
            )

            _, creada = Cuenta.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "nombre": nombre,
                    "tipo": tipo,
                    "cuenta_padre": cuenta_padre,
                    "acepta_movimientos": acepta_movimientos,
                    "concepto_contable": concepto_contable,
                    "activa": True,
                },
            )

            if creada:
                creadas += 1
            else:
                actualizadas += 1

        return creadas, actualizadas

    def _sembrar_ejercicios(self):
        """
        Siembra un EjercicioContable por cada año cubierto por los
        pagos existentes, y además varios años hacia adelante desde
        hoy, para que la generación de pólizas no falle en cuanto
        cambie el año si nadie vuelve a correr este comando antes.
        """

        rango = Pago.objects.aggregate(
            desde=Min("fecha"),
            hasta=Max("fecha"),
        )

        if rango["desde"] and rango["hasta"]:
            anio_inicial = rango["desde"].year
        else:
            parametro = ParametroSistema.objects.filter(clave="EJERCICIO").first()
            anio_inicial = int(parametro.valor) if parametro else date.today().year

        anio_final = max(
            rango["hasta"].year if rango["hasta"] else anio_inicial,
            date.today().year + ANIOS_EJERCICIO_ADELANTE,
        )

        creados = 0

        for anio in range(anio_inicial, anio_final + 1):

            _, creado = EjercicioContable.objects.get_or_create(
                nombre=str(anio),
                defaults={
                    "fecha_inicio": date(anio, 1, 1),
                    "fecha_fin": date(anio, 12, 31),
                    "cerrado": False,
                },
            )

            if creado:
                creados += 1

        return creados

    def _sembrar_folios(self):

        creados = 0

        for tipo in FOLIOS_CONTABLES:

            _, creado = ParametroSistema.objects.get_or_create(
                clave=tipo,
                defaults={
                    "valor": "0",
                    "descripcion": f"Consecutivo de folios {tipo}",
                },
            )

            if creado:
                creados += 1

        return creados
