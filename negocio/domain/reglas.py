"""
FRATERNITAS-ERP

Reglas generales del dominio.

Este archivo contiene exclusivamente reglas de negocio.
No debe importar vistas, formularios ni templates.
"""

from enum import Enum


class EstadoObligacion(Enum):
    PENDIENTE = "PENDIENTE"
    PARCIAL = "PARCIAL"
    LIQUIDADA = "LIQUIDADA"
    CANCELADA = "CANCELADA"


class EstadoAdministrativo(Enum):
    A_PLOMO = "A_PLOMO"
    DESPLOMADO = "DESPLOMADO"


class FormaPago(Enum):
    EFECTIVO = "EFECTIVO"
    TRANSFERENCIA = "TRANSFERENCIA"
    DEPOSITO = "DEPOSITO"
    OTRO = "OTRO"