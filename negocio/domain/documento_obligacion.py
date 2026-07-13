from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from negocio.domain.reglas import EstadoObligacion


@dataclass
class DocumentoObligacion:
    """
    Documento de Negocio.

    Representa una obligación económica
    de un hermano.
    """

    id: int | None

    hermano: object

    concepto: object

    periodo: str

    fecha_vencimiento: date

    importe: Decimal

    saldo_pendiente: Decimal

    estado: EstadoObligacion

    def esta_liquidada(self):

        return self.saldo_pendiente <= Decimal("0.00")