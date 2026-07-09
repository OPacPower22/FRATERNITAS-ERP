from django.db import models


class Hermano(models.Model):
    numero_control = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de Control"
    )

    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre"
    )

    apellido_paterno = models.CharField(
        max_length=100,
        verbose_name="Apellido Paterno"
    )

    apellido_materno = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Apellido Materno"
    )

    nombre_simbolico = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nombre Simbólico"
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

    fecha_alta = models.DateField(
        auto_now_add=True,
        verbose_name="Fecha de Alta"
    )

    class Meta:
        verbose_name = "Hermano"
        verbose_name_plural = "Hermanos"
        ordering = ["apellido_paterno", "apellido_materno", "nombre"]

    def __str__(self):
        return (
            f"{self.apellido_paterno} "
            f"{self.apellido_materno}, "
            f"{self.nombre}"
        )