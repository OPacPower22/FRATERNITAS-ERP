from decimal import Decimal

from negocio.services.aplicacion import (
    proponer_aplicacion_pago,
)


class ObligacionMock:

    def __init__(
        self,
        nombre,
        saldo,
    ):
        self.nombre = nombre
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


propuesta = proponer_aplicacion_pago(

    obligaciones,

    Decimal("500"),

)

print()

print("===== PROPUESTA =====")

for item in propuesta.aplicaciones:

    print(

        item.obligacion.nombre,

        item.importe,

    )

print()

print(

    "Saldo a favor:",

    propuesta.saldo_a_favor,

)