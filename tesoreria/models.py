from django.db import models


class Movimiento(models.Model):

    TIPO_CHOICES = [
        ("I", "Ingreso"),
        ("E", "Egreso"),
    ]

    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES)

    recibo = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    hermano = models.ForeignKey(
        "miembros.Hermano",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    concepto = models.CharField(max_length=200)   

    fecha = models.DateField()

    descripcion = models.CharField(
        max_length=255,
        blank=True,
    )

    capitas = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    aniversario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    saco_beneficencia = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    taller_bj = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    otros = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    justificacion = models.CharField(
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha", "-id"]   

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.concepto} - ${self.total}"
