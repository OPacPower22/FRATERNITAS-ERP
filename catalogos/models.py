from django.db import models


class ConceptoContable(models.Model):

    TIPO_CHOICES = [
        ("I", "Ingreso"),
        ("E", "Egreso"),
    ]

    nombre = models.CharField(
        max_length=100,
        unique=True,
    )

    tipo = models.CharField(
        max_length=1,
        choices=TIPO_CHOICES,
    default="I",
    )

    activo = models.BooleanField(
        default=True,
    )

    requiere_hermano = models.BooleanField(
    default=True,
    verbose_name="Requiere hermano"
)

    descripcion = models.TextField(
    blank=True
)
    
    orden = models.PositiveIntegerField(
    default=0
)
    
    # Distribución por fondos

    aplica_capitas = models.BooleanField(default=False)

    aplica_aniversario = models.BooleanField(default=False)

    aplica_beneficencia = models.BooleanField(default=False)

    aplica_taller_bj = models.BooleanField(default=False)

    aplica_otros = models.BooleanField(default=False)

    class Meta:

        ordering = ["nombre"]

        verbose_name = "Concepto"

        verbose_name_plural = "Conceptos"

    def __str__(self):

        return self.nombre