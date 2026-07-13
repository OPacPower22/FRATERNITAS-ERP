from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class AplicacionPago:
    obligacion: object
    periodo: str
    importe_aplicado: Decimal
    saldo_restante: Decimal


@dataclass
class PropuestaAplicacion:
    aplicaciones: list[AplicacionPago] = field(default_factory=list)
    saldo_a_favor: Decimal = Decimal("0.00")

    @property
    def total_aplicado(self):
        return sum(
            (a.importe_aplicado for a in self.aplicaciones),
            Decimal("0.00"),
        )
