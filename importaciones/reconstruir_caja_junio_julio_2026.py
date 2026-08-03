"""
Reconstruye desde cero los movimientos de Tesorería de junio y
julio de 2026 a partir de MOVIMIENTOS 2026.xls, corrigiendo la
distribución GLUM/Local duplicada y cubriendo:

  - Cuotas Ordinarias de Hermanos (vía MID-001 / ImportadorHistorico).
  - Los 3 recibos que el emparejamiento automático no pudo resolver
    (dos Hermanos homónimos "Ángel Ricardo Gutiérrez").
  - Saco de Beneficencia (fondo aparte, no es cuota de Hermano).
  - Egresos históricos ya remitidos (CAPITAS GLUM, Abono Aniversario).

Para que los prepagos que exceden julio (ej. "JUL A NOV") se
apliquen por completo en vez de quedar como crédito invisible al
saldo en caja, se generan Cuotas Ordinarias hasta noviembre 2026
a la tarifa vigente desde julio.

Uso:
    python manage.py shell -c "
        from importaciones.reconstruir_caja_junio_julio_2026 import reconstruir
        reconstruir()
    "
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Sum

from catalogos.models import ConceptoContable, DistribucionCapita, ParametroSistema
from documentos.models import Recibo
from negocio.models import AplicacionPago, Obligacion, Pago
from negocio.services.aplicacion import calcular_propuesta, ejecutar_propuesta
from negocio.services.contabilidad import generar_movimientos
from negocio.services.mid.importador_historico import ImportadorHistorico
from negocio.services.mid.migrador_historico import MigradorHistorico
from negocio.services.obligaciones import generar_obligaciones, obtener_obligaciones_pendientes
from negocio.services.pagos import registrar_pago
from negocio.services.recibos import emitir_recibo
from tesoreria.models import Movimiento

from importaciones.configurar_cuota_2026 import (
    CONCEPTOS_GLUM,
    configurar_julio,
    configurar_junio,
)

USUARIO_IMPORTACION = "OPacPower22"

PERIODOS_JULIO_EN_ADELANTE = (
    "2026-07", "2026-08", "2026-09", "2026-10", "2026-11",
)

# Recibos que el emparejamiento por nombre no puede resolver porque
# dos Hermanos comparten exactamente "Ángel Ricardo Gutiérrez".
# Se distinguen por cómo los identifica el libro histórico:
# "ANGEL GUTIERREZ" (recibos 61 y 62, consecutivos) para un Hermano,
# "RICARDO GUTIERREZ" (recibo 63) para el otro.
ASIGNACION_MANUAL = {
    ("61", "ANGEL GUTIERREZ"): "14",
    ("62", "ANGEL GUTIERREZ"): "14",
    ("63", "RICARDO GUTIERREZ"): "15",
}

CONCEPTO_SACO = "Saco de Beneficencia"


def _limpiar_transaccional():
    Movimiento.objects.all().delete()
    Recibo.objects.all().delete()
    AplicacionPago.objects.all().delete()
    Pago.objects.all().delete()
    Obligacion.objects.all().delete()


def _desactivar_distribucion_generica():
    DistribucionCapita.objects.filter(
        concepto_destino__nombre__in=("GLUM", "Aportación Local"),
    ).update(activa=False)


def _asegurar_parametros_folio():
    ParametroSistema.objects.update_or_create(
        clave="EJERCICIO",
        defaults={"valor": "2026", "descripcion": "Año fiscal del sistema"},
    )
    for tipo in ("REC", "PAG", "OBL", "MOV", "AUD"):
        ParametroSistema.objects.get_or_create(
            clave=tipo,
            defaults={"valor": "0", "descripcion": f"Consecutivo de folios {tipo}"},
        )


def _procesar_asignaciones_manuales(usuario, datos):
    from miembros.models import Hermano

    resultados = []

    for ingreso in datos["JUNIO"]["ingresos"]:
        clave = (str(ingreso.get("recibo") or "").strip(), str(ingreso.get("miembro") or "").strip())
        numero_control = ASIGNACION_MANUAL.get(clave)
        if not numero_control:
            continue

        hermano = Hermano.objects.get(numero_control=numero_control)
        importe = Decimal(str(ingreso["total"]))
        fecha = ImportadorHistorico(usuario)._obtener_fecha(ingreso.get("fecha"), "JUNIO")

        with transaction.atomic():
            pago = registrar_pago(
                hermano=hermano,
                importe=importe,
                fecha=fecha,
                forma_pago="EFECTIVO",
                referencia=str(ingreso.get("recibo") or "").strip(),
                observaciones=str(ingreso.get("descripcion") or "").strip(),
            )

            obligaciones = obtener_obligaciones_pendientes(hermano)
            propuesta = calcular_propuesta(obligaciones, importe)
            ejecutar_propuesta(pago, propuesta)
            emitir_recibo(pago, usuario)

        resultados.append((hermano, importe))

    return resultados


def _importar_saco_beneficencia(datos):

    concepto, _ = ConceptoContable.objects.update_or_create(
        nombre=CONCEPTO_SACO,
        defaults={"clave": "SACO_BENEFICENCIA", "activo": True},
    )

    creados = 0

    for mes, fecha_defecto in (("JUNIO", date(2026, 6, 1)), ("JULIO", date(2026, 7, 1))):
        for ingreso in datos[mes]["ingresos"]:
            miembro = str(ingreso.get("miembro") or "").strip().upper()
            if "BENEFICENCIA" not in miembro:
                continue

            importe = ingreso.get("total")
            if not importe:
                continue

            importe = Decimal(str(importe))
            fecha_valor = ingreso.get("fecha")
            try:
                fecha = ImportadorHistorico(None)._obtener_fecha(fecha_valor, mes)
            except Exception:
                fecha = fecha_defecto

            Movimiento.objects.create(
                tipo="I",
                concepto_contable=concepto,
                concepto=concepto.nombre,
                hermano=None,
                fecha=fecha,
                otros=importe,
                observaciones=f"Recibo {ingreso.get('recibo') or ''} — {ingreso.get('descripcion') or ''}".strip(),
            )
            creados += 1

    return creados


def _importar_egresos(datos):

    concepto_fraternidad = ConceptoContable.objects.get(nombre="Aportación Fraternidad")
    conceptos_glum = {
        nombre: ConceptoContable.objects.get(nombre=nombre)
        for nombre, _, _, _ in CONCEPTOS_GLUM
    }
    total_pesos_glum = sum(importe for _, _, importe, _ in CONCEPTOS_GLUM)

    creados = 0

    for mes, fecha_defecto in (("JUNIO", date(2026, 6, 30)), ("JULIO", date(2026, 7, 31))):
        for egreso in datos[mes]["egresos"]:
            concepto_texto = str(egreso.get("concepto") or "").strip().upper()
            importe = egreso.get("importe")
            if not importe:
                continue
            importe = Decimal(str(importe))

            if concepto_texto == "CAPITAS GLUM":
                for nombre, _, peso, _ in CONCEPTOS_GLUM:
                    parte = (importe * peso / total_pesos_glum).quantize(Decimal("0.01"))
                    Movimiento.objects.create(
                        tipo="E",
                        concepto_contable=conceptos_glum[nombre],
                        concepto=nombre,
                        fecha=fecha_defecto,
                        otros=parte,
                        observaciones="CAPITAS GLUM (histórico, prorrateado)",
                    )
                    creados += 1
            elif concepto_texto == "ABONO ANIVERSARIO":
                Movimiento.objects.create(
                    tipo="E",
                    concepto_contable=concepto_fraternidad,
                    concepto=concepto_fraternidad.nombre,
                    fecha=fecha_defecto,
                    otros=importe,
                    observaciones="Abono Aniversario (histórico)",
                )
                creados += 1

    return creados


def reconstruir():

    _asegurar_parametros_folio()
    _limpiar_transaccional()
    _desactivar_distribucion_generica()

    User = get_user_model()
    usuario = User.objects.get(username=USUARIO_IMPORTACION)

    datos = MigradorHistorico().obtener_movimientos()

    # Tarifas y obligaciones: junio a $350, julio-noviembre a $400,
    # para que los prepagos multi-mes se apliquen por completo.
    configurar_junio()
    generar_obligaciones("2026-06")

    configurar_julio()
    for periodo in PERIODOS_JULIO_EN_ADELANTE:
        generar_obligaciones(periodo)

    # Junio y julio juntos: permite que un pago cruce de un periodo
    # pendiente al siguiente en vez de generar crédito artificial.
    resultado = ImportadorHistorico(usuario).importar(datos)

    manuales = _procesar_asignaciones_manuales(usuario, datos)

    saco_creados = _importar_saco_beneficencia(datos)

    for pago in Pago.objects.all():
        generar_movimientos(pago)

    egresos_creados = _importar_egresos(datos)

    ingresos_total = Movimiento.objects.filter(tipo="I").aggregate(
        t=Sum("total")
    )["t"] or Decimal("0.00")
    egresos_total = Movimiento.objects.filter(tipo="E").aggregate(
        t=Sum("total")
    )["t"] or Decimal("0.00")

    print()
    print("===================================")
    print("RECONSTRUCCIÓN JUNIO/JULIO 2026 FINALIZADA")
    print("===================================")
    print(f"MID-001 procesados : {resultado['procesados']}")
    print(f"MID-001 correctos  : {resultado['correctos']}")
    print(f"MID-001 errores    : {len(resultado['errores'])}")
    for error in resultado["errores"]:
        print(f"  [{error['mes']}] {error['ingreso'].get('miembro')!r}: {error['error']}")
    print(f"Asignados manualmente (Gutiérrez): {len(manuales)}")
    print(f"Saco de Beneficencia registrados : {saco_creados}")
    print(f"Egresos históricos registrados   : {egresos_creados}")
    print()
    print(f"Ingresos totales : ${ingresos_total}")
    print(f"Egresos totales  : ${egresos_total}")
    print(f"Saldo en caja    : ${ingresos_total - egresos_total}")
    print("===================================")

    return ingresos_total - egresos_total
