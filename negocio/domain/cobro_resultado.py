"""
Objeto de resultado del Caso de Uso CU-002.

Representa el resultado completo del proceso de Cobro Integral.
"""

from dataclasses import dataclass, field


@dataclass
class CobroResultado:
    """
    Resultado del proceso completo de Cobro Integral.
    """

    pago: object | None = None

    propuesta: object | None = None

    movimientos: list = field(default_factory=list)

    recibo: object | None = None

    saldo_a_favor: float = 0.0

    exitoso: bool = False

    advertencias: list[str] = field(default_factory=list)

    errores: list[str] = field(default_factory=list)

    @property
    def tiene_errores(self) -> bool:
        return len(self.errores) > 0

    @property
    def tiene_advertencias(self) -> bool:
        return len(self.advertencias) > 0
