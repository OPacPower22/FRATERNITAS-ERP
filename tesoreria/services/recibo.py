from datetime import date
from decimal import Decimal
from uuid import uuid4

from catalogos.models import ParametroSistema


def _obtener_parametro(clave, valor_por_defecto=""):
    valor = (
        ParametroSistema.objects.filter(clave=clave)
        .values_list("valor", flat=True)
        .first()
    )
    return valor or valor_por_defecto


def _crear_qr_svg(contenido):
    bloques = []
    for fila in range(9):
        for columna in range(9):
            if (fila + columna) % 3 == 0 or (fila * columna) % 5 == 0:
                bloques.append('<rect x="%s" y="%s" width="1" height="1" fill="#111" />' % (columna, fila))
            else:
                bloques.append('<rect x="%s" y="%s" width="1" height="1" fill="#fff" />' % (columna, fila))

    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 9 9" role="img" aria-label="QR provisional">'
        '<rect width="9" height="9" fill="#fff" />'
        '<rect x="0" y="0" width="3" height="3" fill="#111" />'
        '<rect x="6" y="0" width="3" height="3" fill="#111" />'
        '<rect x="0" y="6" width="3" height="3" fill="#111" />'
        + "".join(bloques)
        + '<text x="4.5" y="8.5" text-anchor="middle" font-size="0.5" fill="#111">%s</text></svg>' % contenido
    )


def construir_previsualizacion_recibo(hermano, propuesta, datos_formulario, folio=None):
    nombre_logia = _obtener_parametro("LOGIA_NOMBRE", "Logia Fraternitas")
    iniciales_logia = "".join(part[0].upper() for part in nombre_logia.split()[:2] if part)
    fecha = date.today()
    folio_provisional = folio or f"PRV-{fecha.strftime('%Y%m%d')}-{hermano.pk:04d}"
    uuid_interno = str(uuid4())
    url_validacion = f"/recibos/validar/{uuid_interno}"

    conceptos = []
    for item in propuesta.aplicaciones:
        conceptos.append(
            {
                "concepto": str(item.obligacion.concepto),
                "periodo": item.periodo,
                "importe": item.importe_aplicado,
            }
        )

    qr_contenido = f"folio={folio_provisional};uuid={uuid_interno};url={url_validacion}"

    return {
        "logo_texto": nombre_logia,
        "iniciales_logia": iniciales_logia or "FR",
        "folio": folio_provisional,
        "fecha": fecha,
        "nombre_hermano": str(hermano),
        "conceptos": conceptos,
        "distribucion": conceptos,
        "total": propuesta.total_aplicado,
        "saldo_a_favor": propuesta.saldo_a_favor,
        "forma_pago": datos_formulario.get("forma_pago") or "EFECTIVO",
        "observaciones": datos_formulario.get("observaciones", ""),
        "qr_svg": _crear_qr_svg(qr_contenido),
        "uuid_interno": uuid_interno,
        "url_validacion": url_validacion,
    }
