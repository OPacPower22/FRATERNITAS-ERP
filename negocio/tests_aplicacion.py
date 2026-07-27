from decimal import Decimal

from negocio.services.aplicacion import (
    calcular_propuesta,
)


class ObligacionMock:

    def __init__(
        self,
        nombre,
        saldo,
    ):
        self.nombre = nombre
        self.periodo = nombre
        self.saldo_pendiente = Decimal(str(saldo))


obligaciones = [

    ObligacionMock(
        "Julio",
        280,
    ),

    ObligacionMock(
        "Agosto",
        280,
    ),

    ObligacionMock(
        "Septiembre",
        280,
    ),
]


propuesta = calcular_propuesta(

    obligaciones,

    Decimal("500"),

)

print()

print("===== PROPUESTA =====")

for item in propuesta.aplicaciones:

    print(

        item.obligacion.nombre,

        item.importe_aplicado,

    )

print()

print(

    "Saldo a favor:",

    propuesta.saldo_a_favor,

)
