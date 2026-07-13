from django.db import models


class Obligacion(models.Model):

    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("PARCIAL", "Parcial"),
        ("LIQUIDADA", "Liquidada"),
        ("CANCELADA", "Cancelada"),
    ]

    hermano = models.ForeignKey(
        "miembros.Hermano",
        on_delete=models.CASCADE,
    )

    concepto = models.ForeignKey(
    "catalogos.ConceptoContable",
    on_delete=models.PROTECT,
)
    
    periodo = models.CharField(
    max_length=20,
    )

    importe = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    saldo_pendiente = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    fecha_vencimiento = models.DateField()

    estado = models.CharField(
        max_length=15,
        choices=ESTADOS,
        default="PENDIENTE",
    )

    class Meta:
        ordering = [
            "fecha_vencimiento",
        ]

    def __str__(self):
        return (
            f"{self.hermano} - "
            f"{self.periodo}"
        )