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

    clave = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
    )

    nombre = models.CharField(
        max_length=100,
        unique=True
    )
    
    activo = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Concepto Contable"
        verbose_name_plural = "Conceptos Contables"

    def __str__(self):
        return  self.nombre

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

class TarifaObligacion(models.Model):

    concepto = models.ForeignKey(
        ConceptoContable,
        on_delete=models.PROTECT,
    )

    importe = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    obligatoria = models.BooleanField(
        default=True,
    )

    estado = models.CharField(
        max_length=20,
        default="ACTIVA",
    )

    periodicidad = models.CharField(
        max_length=20,
        choices=[
            ("MENSUAL", "Mensual"),
            ("ANUAL", "Anual"),
            ("EVENTUAL", "Eventual"),
        ],
        default="MENSUAL",
    )

    class Meta:
        ordering = ["concepto__nombre"]

    def __str__(self):
        return f"{self.concepto.nombre} - ${self.importe}"

class DistribucionCapita(models.Model):

    concepto_origen = models.ForeignKey(
        ConceptoContable,
        related_name="origen",
        on_delete=models.PROTECT,
    )

    concepto_destino = models.ForeignKey(
        ConceptoContable,
        related_name="destino",
        on_delete=models.PROTECT,
    )

    importe = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    grupo = models.CharField(
        max_length=20,
        default="LOCAL",
    )

    orden = models.PositiveIntegerField()

    activa = models.BooleanField(
        default=True,
    )

    class Meta:
            ordering = ["orden"]

    def __str__(self):
        return (
            f"{self.concepto_origen.nombre} → "
            f"{self.concepto_destino.nombre}"
        )
