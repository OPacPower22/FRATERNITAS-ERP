from django.db import models


class Grado(models.Model):

    nombre = models.CharField(
        max_length=50,
        unique=True
    )

    abreviatura = models.CharField(
        max_length=10,
        blank=True
    )

    orden = models.PositiveSmallIntegerField(
        unique=True
    )

    activo = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["orden"]
        verbose_name = "Grado"
        verbose_name_plural = "Grados"

    def __str__(self):
        return self.nombre


class Cargo(models.Model):

    nombre = models.CharField(
        max_length=100,
        unique=True
    )

    abreviatura = models.CharField(
        max_length=20,
        blank=True
    )

    activo = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"

    def __str__(self):
        return self.nombre


class ConceptoContable(models.Model):

    nombre = models.CharField(
        max_length=100,
        unique=True
    )

    descripcion = models.TextField(
        blank=True
    )

    activo = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Concepto Contable"
        verbose_name_plural = "Conceptos Contables"

    def __str__(self):
        return self.nombre

class ParametroSistema(models.Model):

    clave = models.CharField(
        max_length=100,
        unique=True,
    )

    valor = models.TextField()

    descripcion = models.CharField(
        max_length=255,
        blank=True,
    )

    modificable = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["clave"]
        verbose_name = "Parámetro del Sistema"
        verbose_name_plural = "Parámetros del Sistema"

    def __str__(self):
        return f"{self.clave} = {self.valor}"
