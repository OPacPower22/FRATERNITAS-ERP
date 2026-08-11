"""Generación del Informe Mensual de Resultados Financieros en PDF.

Reproduce el formato histórico del Tesorero: un bloque por fondo con
Ingreso / Mes Anterior / Sub Total / Egreso / Saldo Total, y la suma
total al final.
"""

from decimal import Decimal
from io import BytesIO
from pathlib import Path

from django.conf import settings

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROJO = colors.HexColor("#8B0000")
GRIS = colors.HexColor("#6c757d")
AMARILLO = colors.HexColor("#ffff99")
GRIS_CLARO = colors.HexColor("#f1f1f1")

ESCUDO = Path(settings.BASE_DIR) / "static" / "img" / "escudo.png"

ANCHO_FONDO = [38 * mm, 28 * mm, 28 * mm, 28 * mm, 28 * mm]


def _estilos():

    base = getSampleStyleSheet()

    return {
        "titulo": ParagraphStyle(
            "titulo",
            parent=base["Title"],
            fontSize=12,
            leading=15,
            textColor=ROJO,
            alignment=TA_CENTER,
        ),
        "subtitulo": ParagraphStyle(
            "subtitulo",
            parent=base["Normal"],
            fontSize=8.5,
            leading=11,
            textColor=GRIS,
            alignment=TA_CENTER,
        ),
        "normal": ParagraphStyle(
            "normal",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
        ),
        "encabezado_tabla": ParagraphStyle(
            "encabezado_tabla",
            parent=base["Normal"],
            fontSize=7.5,
            leading=9,
            alignment=TA_CENTER,
            textColor=GRIS,
        ),
        "valor": ParagraphStyle(
            "valor",
            parent=base["Normal"],
            fontSize=9.5,
            leading=12,
            alignment=TA_CENTER,
        ),
        "fondo_nombre": ParagraphStyle(
            "fondo_nombre",
            parent=base["Normal"],
            fontSize=10,
            leading=13,
            alignment=TA_CENTER,
            textColor=colors.white,
        ),
        "pie": ParagraphStyle(
            "pie",
            parent=base["Normal"],
            fontSize=7.5,
            leading=10,
            textColor=GRIS,
            alignment=TA_CENTER,
        ),
    }


def _moneda(valor):
    return "{:,.2f}".format(Decimal(valor or "0.00"))


def _encabezado(informe, estilos):

    izquierda = ""

    if ESCUDO.exists():
        izquierda = Image(str(ESCUDO), width=20 * mm, height=20 * mm)

    centro = [
        Paragraph(
            "DIG∴ RESP∴ ABN∴ Y SESQUICENT∴ LOG∴ SIMB∴ FRATERNIDAD No. 1",
            estilos["subtitulo"],
        ),
        Paragraph(
            "INFORME MENSUAL DE RESULTADOS FINANCIEROS",
            estilos["titulo"],
        ),
    ]

    derecha = [
        Paragraph(
            f"<b>Miembros activos</b><br/>{informe['miembros_activos']}",
            estilos["subtitulo"],
        ),
        Paragraph(
            f"<b>Fecha</b><br/>{informe['etiqueta_periodo']}",
            estilos["subtitulo"],
        ),
    ]

    tabla = Table(
        [[izquierda, centro, derecha]],
        colWidths=[25 * mm, 100 * mm, 45 * mm],
    )

    tabla.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("LINEBELOW", (0, 0), (-1, 0), 1.2, ROJO),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ]
        )
    )

    return tabla


def _bloque_fondo(fondo, estilos):

    nombre = Table(
        [[Paragraph(fondo["etiqueta"], estilos["fondo_nombre"])]],
        colWidths=[sum(ANCHO_FONDO)],
    )
    nombre.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), ROJO),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    encabezados = [
        "INGRESO", "MES ANT.", "SUB TOTAL", "EGRESO", "SALDO TOTAL",
    ]

    filas = [
        [Paragraph(texto, estilos["encabezado_tabla"]) for texto in encabezados],
        [
            Paragraph(_moneda(fondo["ingreso"]), estilos["valor"]),
            Paragraph(_moneda(fondo["mes_anterior"]), estilos["valor"]),
            Paragraph(_moneda(fondo["subtotal"]), estilos["valor"]),
            Paragraph(_moneda(fondo["egreso"]), estilos["valor"]),
            Paragraph(
                f"<b>{_moneda(fondo['saldo'])}</b>", estilos["valor"]
            ),
        ],
    ]

    tabla = Table(filas, colWidths=ANCHO_FONDO)

    tabla.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, GRIS),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, GRIS),
                ("BACKGROUND", (0, 0), (-1, 0), GRIS_CLARO),
                ("BACKGROUND", (0, 1), (0, 1), AMARILLO),
                ("BACKGROUND", (3, 1), (3, 1), AMARILLO),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    return [nombre, tabla]


def _bloque_suma_total(informe, estilos):

    tabla = Table(
        [
            [
                Paragraph("<b>SUMA TOTAL</b>", estilos["normal"]),
                Paragraph(
                    f"<b>${_moneda(informe['suma_total'])}</b>",
                    estilos["valor"],
                ),
            ]
        ],
        colWidths=[sum(ANCHO_FONDO) - 40 * mm, 40 * mm],
    )

    tabla.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.8, ROJO),
                ("BACKGROUND", (0, 0), (-1, -1), GRIS_CLARO),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (0, 0), 10),
            ]
        )
    )

    return tabla


def generar_informe_mensual_pdf(informe):
    """
    Construye el PDF del Informe Mensual de Resultados Financieros.

    Parámetros
    ----------
    informe : dict
        Estructura devuelta por
        ``tesoreria.services.informe_mensual.calcular_informe_mensual``.

    Retorna
    -------
    bytes
    """

    estilos = _estilos()
    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"Informe Mensual {informe['etiqueta_periodo']}",
        author="FRATERNITAS-ERP",
    )

    elementos = [
        _encabezado(informe, estilos),
        Spacer(1, 8 * mm),
    ]

    for fondo in informe["fondos"]:
        elementos.extend(_bloque_fondo(fondo, estilos))
        elementos.append(Spacer(1, 6 * mm))

    elementos.append(_bloque_suma_total(informe, estilos))
    elementos.append(Spacer(1, 8 * mm))
    elementos.append(
        Paragraph(
            "Documento emitido electrónicamente por FRATERNITAS-ERP.",
            estilos["pie"],
        )
    )

    documento.build(elementos)

    return buffer.getvalue()


def nombre_archivo(informe):
    return f"Informe_{informe['anio']}_{informe['mes']:02d}.pdf"
