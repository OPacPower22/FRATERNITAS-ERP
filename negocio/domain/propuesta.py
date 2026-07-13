from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class AplicacionPropuesta:
    """
    Representa la aplicación propuesta
    para una obligación.
    """

    obligacion: object
    importe: Decimal


@dataclass
class PropuestaAplicacion:
    """
    Resultado generado por el motor
    de aplicación de pagos.
    """

    aplicaciones: list[AplicacionPropuesta] = field(default_factory=list)

    saldo_a_favor: Decimal = Decimal("0.00")

    importe_recibido: Decimal = Decimal("0.00")

    def total_aplicado(self):

        return sum(
            (
                item.importe
                for item in self.aplicaciones
            ),
            Decimal("0.00"),
        )