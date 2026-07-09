from django.db import models


class ConceptoContable(models.Model):

    nombre = models.CharField(
        max_length=100,
        unique=True,
    )

    activo = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Concepto Contable"
        verbose_name_plural = "Conceptos Contables"

    def __str__(self):
        return self.nombre
