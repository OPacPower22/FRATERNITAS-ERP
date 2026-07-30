from django.core.exceptions import ValidationError
from django.db import models


class EjercicioContable(models.Model):
    nombre = models.CharField(
        "Nombre",
        max_length=100,
        unique=True,
    )

    fecha_inicio = models.DateField(
        "Fecha de inicio",
    )

    fecha_fin = models.DateField(
        "Fecha de fin",
    )

    abierto = models.BooleanField(
        "Abierto",
        default=True,
    )

    activo = models.BooleanField(
        "Activo",
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Ejercicio Contable"
        verbose_name_plural = "Ejercicios Contables"
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return self.nombre

    def clean(self):
        if self.fecha_inicio >= self.fecha_fin:
            raise ValidationError(
                "La fecha de inicio debe ser menor que la fecha de fin."
            )

        if self.activo:
            existe = (
                EjercicioContable.objects.filter(activo=True)
                .exclude(pk=self.pk)
                .exists()
            )

            if existe:
                raise ValidationError(
                    "Solo puede existir un ejercicio contable activo."
                )