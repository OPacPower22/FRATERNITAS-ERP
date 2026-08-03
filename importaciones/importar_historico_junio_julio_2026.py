"""
Importa los ingresos históricos de junio y julio de 2026 desde
MOVIMIENTOS 2026.xls y genera los movimientos contables (GLUM /
Local) que alimentan los saldos de CU-002 · Procesar Egreso.

Cada mes se procesa con la tarifa y distribución vigentes en ese
periodo (junio: $350 = 260 GLUM + 90 Local; julio en adelante:
$400 = 260 GLUM + 140 Local), para que el reparto histórico sea
correcto y no se calcule con la tarifa más reciente.

Uso:
    python manage.py shell -c "
        from importaciones.importar_historico_junio_julio_2026 import importar
        importar()
    "
"""

from django.contrib.auth import get_user_model

from catalogos.models import ParametroSistema
from negocio.models import Pago
from negocio.services.contabilidad import generar_movimientos
from negocio.services.mid.importador_historico import ImportadorHistorico
from negocio.services.mid.migrador_historico import MigradorHistorico
from negocio.services.obligaciones import generar_obligaciones

from importaciones.configurar_cuota_2026 import configurar_julio, configurar_junio

USUARIO_IMPORTACION = "OPacPower22"


def _asegurar_parametros_folio():

    ParametroSistema.objects.update_or_create(
        clave="EJERCICIO",
        defaults={"valor": "2026", "descripcion": "Año fiscal del sistema"},
    )

    for tipo in ("REC", "PAG", "OBL", "MOV", "AUD"):
        ParametroSistema.objects.get_or_create(
            clave=tipo,
            defaults={
                "valor": "0",
                "descripcion": f"Consecutivo de folios {tipo}",
            },
        )


def _procesar_mes(usuario, datos, mes):

    importador = ImportadorHistorico(usuario)
    resultado = importador.importar({mes: datos[mes]})

    pagos_nuevos = Pago.objects.filter(
        fecha__year=2026,
        fecha__month=6 if mes == "JUNIO" else 7,
    )

    movimientos_generados = 0
    for pago in pagos_nuevos:
        movimientos_generados += len(generar_movimientos(pago))

    print()
    print(f"--- {mes} ---")
    print(f"Procesados : {resultado['procesados']}")
    print(f"Correctos  : {resultado['correctos']}")
    print(f"Errores    : {len(resultado['errores'])}")
    for error in resultado["errores"]:
        print(f"  [{error['mes']}] {error['ingreso'].get('miembro')!r}: {error['error']}")
    print(f"Movimientos: {movimientos_generados}")

    return resultado


def importar():

    _asegurar_parametros_folio()

    User = get_user_model()
    usuario = User.objects.get(username=USUARIO_IMPORTACION)

    datos = MigradorHistorico().obtener_movimientos()

    # Junio: tarifa y distribución vigentes hasta el 30JUN26.
    configurar_junio()
    generar_obligaciones("2026-06")
    resultado_junio = _procesar_mes(usuario, datos, "JUNIO")

    # Julio: tarifa y distribución vigentes a partir del 1JUL26.
    configurar_julio()
    generar_obligaciones("2026-07")
    resultado_julio = _procesar_mes(usuario, datos, "JULIO")

    print()
    print("===================================")
    print("IMPORTACIÓN HISTÓRICA JUNIO/JULIO 2026 FINALIZADA")
    print("===================================")
    print(
        f"Total correctos: "
        f"{resultado_junio['correctos'] + resultado_julio['correctos']}"
    )
    print(
        f"Total errores  : "
        f"{len(resultado_junio['errores']) + len(resultado_julio['errores'])}"
    )
    print("===================================")

    return resultado_junio, resultado_julio
