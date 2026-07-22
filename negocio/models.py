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

class Pago(models.Model):

    ESTADOS = [
        ("REGISTRADO", "Registrado"),
        ("CANCELADO", "Cancelado"),
    ]

    hermano = models.ForeignKey(
        "miembros.Hermano",
        on_delete=models.PROTECT,
    )

    fecha = models.DateField()

    importe = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    forma_pago = models.CharField(
       max_length=20,
    )

    referencia = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    observaciones = models.TextField(
        blank=True,
        default="",
    )

    estado = models.CharField(
        max_length=15,
        choices=ESTADOS,
        default="REGISTRADO",
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return (
            f"Pago #{self.id} - "
            f"{self.hermano}"
        )


class AplicacionPago(models.Model):

    pago = models.ForeignKey(
        Pago,
        on_delete=models.CASCADE,
    )

    obligacion = models.ForeignKey(
        Obligacion,
        on_delete=models.PROTECT,
    )

    importe_aplicado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    fecha_aplicacion = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "fecha_aplicacion",
        ]

    def __str__(self):
        return (
            f"{self.pago} → "
            f"{self.obligacion}"
        )
