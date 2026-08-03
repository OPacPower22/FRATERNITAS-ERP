"""
Generación del recibo oficial en PDF.

Recibe el mismo diccionario que devuelve
``negocio.services.recibos.emitir_recibo`` para no duplicar
lógica de negocio.
"""

from decimal import Decimal
from io import BytesIO
from pathlib import Path

from django.conf import settings

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
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

from documentos.services.qr import generar_qr_png


ROJO = colors.HexColor("#8B0000")
GRIS = colors.HexColor("#6c757d")

ESCUDO = Path(settings.BASE_DIR) / "static" / "img" / "escudo.png"


def _estilos():

    base = getSampleStyleSheet()

    return {
        "titulo": ParagraphStyle(
            "titulo",
            parent=base["Title"],
            fontSize=13,
            leading=16,
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
        "etiqueta": ParagraphStyle(
            "etiqueta",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
            textColor=GRIS,
        ),
        "derecha": ParagraphStyle(
            "derecha",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
            alignment=TA_RIGHT,
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
    return "${:,.2f}".format(Decimal(valor or "0.00"))


def _encabezado(estilos):

    izquierda = ""

    if ESCUDO.exists():
        izquierda = Image(
            str(ESCUDO),
            width=22 * mm,
            height=22 * mm,
        )

    centro = [
        Paragraph(
            "DIG∴ RESP∴ ABN∴ Y SESQUICENT∴ LOG∴ SIMB∴",
            estilos["subtitulo"],
        ),
        Paragraph(
            "FRATERNIDAD No. 1",
            estilos["titulo"],
        ),
        Paragraph(
            "Recibo Oficial de Tesorería",
            estilos["subtitulo"],
        ),
    ]

    tabla = Table(
        [[izquierda, centro, ""]],
        colWidths=[30 * mm, 110 * mm, 30 * mm],
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


def _datos_generales(datos, estilos):

    pago = datos["pago"]
    fecha = datos["fecha"]

    filas = [
        [
            Paragraph("Folio", estilos["etiqueta"]),
            Paragraph(f"<b>{datos['folio']}</b>", estilos["normal"]),
            Paragraph("Fecha de emisión", estilos["etiqueta"]),
            Paragraph(
                fecha.strftime("%d/%m/%Y %H:%M") if fecha else "—",
                estilos["normal"],
            ),
        ],
        [
            Paragraph("Hermano", estilos["etiqueta"]),
            Paragraph(str(datos["hermano"]), estilos["normal"]),
            Paragraph("No. de control", estilos["etiqueta"]),
            Paragraph(
                str(getattr(datos["hermano"], "numero_control", "—")),
                estilos["normal"],
            ),
        ],
        [
            Paragraph("Forma de pago", estilos["etiqueta"]),
            Paragraph(str(pago.forma_pago), estilos["normal"]),
            Paragraph("Referencia", estilos["etiqueta"]),
            Paragraph(pago.referencia or "—", estilos["normal"]),
        ],
    ]

    tabla = Table(
        filas,
        colWidths=[28 * mm, 62 * mm, 30 * mm, 50 * mm],
    )

    tabla.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    return tabla


def _detalle(datos, estilos):

    filas = [
        [
            Paragraph("<b>Concepto</b>", estilos["normal"]),
            Paragraph("<b>Periodo</b>", estilos["normal"]),
            Paragraph("<b>Importe</b>", estilos["derecha"]),
        ]
    ]

    for aplicacion in datos["aplicaciones"]:
        filas.append(
            [
                Paragraph(
                    aplicacion.obligacion.concepto.nombre,
                    estilos["normal"],
                ),
                Paragraph(
                    aplicacion.obligacion.periodo,
                    estilos["normal"],
                ),
                Paragraph(
                    _moneda(aplicacion.importe_aplicado),
                    estilos["derecha"],
                ),
            ]
        )

    filas.append(
        [
            Paragraph("<b>Total recibido</b>", estilos["normal"]),
            "",
            Paragraph(
                f"<b>{_moneda(datos['total'])}</b>",
                estilos["derecha"],
            ),
        ]
    )

    tabla = Table(
        filas,
        colWidths=[95 * mm, 40 * mm, 35 * mm],
        repeatRows=1,
    )

    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f1f1")),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, ROJO),
                ("LINEABOVE", (0, -1), (-1, -1), 0.8, ROJO),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("SPAN", (0, -1), (1, -1)),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -2),
                    [colors.white, colors.HexColor("#fbfbfb")],
                ),
            ]
        )
    )

    return tabla


def _bloque_qr(url_verificacion, estilos):

    qr = Image(
        BytesIO(generar_qr_png(url_verificacion)),
        width=28 * mm,
        height=28 * mm,
    )

    texto = Paragraph(
        "Verificación y validación institucional.<br/>"
        "Escanee el código para confirmar la autenticidad "
        "de este recibo.<br/>"
        f"<font size=6>{url_verificacion}</font>",
        estilos["etiqueta"],
    )

    tabla = Table(
        [[qr, texto]],
        colWidths=[32 * mm, 138 * mm],
    )

    tabla.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (1, 0), (1, 0), 8),
            ]
        )
    )

    return tabla


def generar_recibo_pdf(datos, url_verificacion):
    """
    Construye el PDF del recibo.

    Parámetros
    ----------
    datos : dict
        Estructura devuelta por ``emitir_recibo``.
    url_verificacion : str
        URL absoluta codificada en el QR.

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
        title=f"Recibo {datos['folio']}",
        author="FRATERNITAS-ERP",
    )

    elementos = [
        _encabezado(estilos),
        Spacer(1, 8 * mm),
        _datos_generales(datos, estilos),
        Spacer(1, 6 * mm),
        _detalle(datos, estilos),
        Spacer(1, 10 * mm),
        _bloque_qr(url_verificacion, estilos),
        Spacer(1, 8 * mm),
        Paragraph(
            "Documento emitido electrónicamente por FRATERNITAS-ERP. "
            "Su validez está sujeta a la verificación del código QR.",
            estilos["pie"],
        ),
    ]

    if datos.get("estado") == "CANCELADO":
        elementos.insert(
            1,
            Paragraph(
                "<b><font color='#8B0000'>RECIBO CANCELADO</font></b>",
                estilos["titulo"],
            ),
        )

    documento.build(elementos)

    return buffer.getvalue()


def nombre_archivo(datos):
    return f"{datos['folio']}.pdf"
