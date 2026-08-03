"""
Configura la aportación mensual (Cuota Ordinaria) y su distribución
institucional GLUM / Local, con el desglose granular real que usa
CU-002 · Procesar Egreso (tomado de TARIFAS_OBLIGACIONES y
DISTRIBUCION_CAPITA de MOVIMIENTOS 2026.xls / TESORERIA WEB APP).

Vigencias:
  - Hasta el 30JUN26: $350.00 (GLUM $260.00 + Local $90.00)
  - A partir del 1JUL26: $400.00 (GLUM $260.00 + Local $140.00,
    el incremento de $50.00 se aplica íntegro a Aportación Tesoro)

Uso:
    python manage.py shell -c "
        from importaciones.configurar_cuota_2026 import configurar_junio, configurar_julio
        configurar_julio()
    "
"""

from decimal import Decimal

from catalogos.models import ConceptoContable, DistribucionCapita, TarifaObligacion

# Conceptos GLUM: no cambian entre junio y julio.
CONCEPTOS_GLUM = (
    ("Membresía", "MEMBRESIA", Decimal("120.00"), 1),
    ("Revista", "REVISTA", Decimal("18.00"), 2),
    ("Conferencia Gran Logia", "CONF_GR_LOG", Decimal("9.00"), 3),
    ("CMI", "CMI", Decimal("5.00"), 4),
    ("Servicios Recibidos", "SERVICIOS_RECIBIDOS", Decimal("45.00"), 5),
    ("Fondo Contingencia Anual", "FONDO_CONT_ANUAL", Decimal("3.00"), 6),
    ("Post Mortem", "POST_MORTEM", Decimal("10.00"), 7),
    ("Defunción", "DEFUNCION", Decimal("50.00"), 8),
)

# Conceptos locales antes del 1JUL26 (suman $90.00).
CONCEPTOS_LOCALES_JUNIO = (
    ("Aportación Fraternidad", "APORTACION_FRATERNIDAD", Decimal("50.00"), 9),
    ("Aportación AJEF", "APORTACION_AJEF", Decimal("15.00"), 10),
    ("Aportación Tesoro", "APORTACION_TESORO", Decimal("25.00"), 11),
)

# Conceptos locales a partir del 1JUL26 (suman $140.00): el
# incremento de $50.00 se aplica íntegro a Aportación Tesoro.
CONCEPTOS_LOCALES_JULIO = (
    ("Aportación Fraternidad", "APORTACION_FRATERNIDAD", Decimal("50.00"), 9),
    ("Aportación AJEF", "APORTACION_AJEF", Decimal("15.00"), 10),
    ("Aportación Tesoro", "APORTACION_TESORO", Decimal("75.00"), 11),
)


def _aplicar(importe_cuota, conceptos_locales):

    concepto_cuota, _ = ConceptoContable.objects.update_or_create(
        nombre="Cuota Ordinaria",
        defaults={"clave": "CUOTA_ORD", "activo": True},
    )

    TarifaObligacion.objects.update_or_create(
        concepto=concepto_cuota,
        defaults={
            "importe": importe_cuota,
            "obligatoria": True,
            "estado": "ACTIVA",
            "periodicidad": "MENSUAL",
        },
    )

    for nombre, clave, importe, orden in CONCEPTOS_GLUM + conceptos_locales:

        concepto_destino, _ = ConceptoContable.objects.update_or_create(
            nombre=nombre,
            defaults={"clave": clave, "activo": True},
        )

        grupo = "GLUM" if (nombre, clave, importe, orden) in CONCEPTOS_GLUM else "LOCAL"

        DistribucionCapita.objects.update_or_create(
            concepto_origen=concepto_cuota,
            concepto_destino=concepto_destino,
            defaults={
                "importe": importe,
                "grupo": grupo,
                "orden": orden,
                "activa": True,
            },
        )

    total_glum = sum(importe for _, _, importe, _ in CONCEPTOS_GLUM)
    total_local = sum(importe for _, _, importe, _ in conceptos_locales)

    print()
    print("===================================")
    print("CUOTA ORDINARIA CONFIGURADA")
    print("===================================")
    print(f"Cuota mensual : ${importe_cuota}")
    print(f"  GLUM        : ${total_glum}")
    print(f"  Local       : ${total_local}")
    print("===================================")


def configurar_junio():
    """Vigencia hasta el 30JUN26: $350.00 (260 GLUM + 90 Local)."""
    _aplicar(Decimal("350.00"), CONCEPTOS_LOCALES_JUNIO)


def configurar_julio():
    """Vigencia a partir del 1JUL26: $400.00 (260 GLUM + 140 Local)."""
    _aplicar(Decimal("400.00"), CONCEPTOS_LOCALES_JULIO)
