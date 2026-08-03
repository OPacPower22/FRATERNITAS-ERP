from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class EjercicioContableManager(models.Manager):

    def actual(self, fecha):
        """
        Resuelve el ejercicio contable vigente para una fecha dada.

        Se resuelve por rango de fechas (no por una bandera única
        "activo") para que el ejercicio correcto también se pueda
        determinar al contabilizar pagos históricos.
        """

        return (
            self.get_queryset()
            .filter(
                fecha_inicio__lte=fecha,
                fecha_fin__gte=fecha,
                cerrado=False,
            )
            .order_by("-fecha_inicio")
            .first()
        )


class EjercicioContable(models.Model):

    nombre = models.CharField(
        max_length=50,
        unique=True,
    )

    fecha_inicio = models.DateField()

    fecha_fin = models.DateField()

    cerrado = models.BooleanField(
        default=False,
    )

    objects = EjercicioContableManager()

    class Meta:
        ordering = ["-fecha_inicio"]
        verbose_name = "Ejercicio Contable"
        verbose_name_plural = "Ejercicios Contables"

    def clean(self):

        if self.fecha_inicio and self.fecha_fin and self.fecha_inicio >= self.fecha_fin:
            raise ValidationError(
                "La fecha de inicio debe ser menor que la fecha de fin."
            )

    def __str__(self):
        return self.nombre


class Cuenta(models.Model):

    TIPOS = [
        ("ACTIVO", "Activo"),
        ("PASIVO", "Pasivo"),
        ("PATRIMONIO", "Patrimonio"),
        ("INGRESO", "Ingreso"),
        ("GASTO", "Gasto"),
    ]

    NATURALEZA_POR_TIPO = {
        "ACTIVO": "DEUDORA",
        "GASTO": "DEUDORA",
        "PASIVO": "ACREEDORA",
        "PATRIMONIO": "ACREEDORA",
        "INGRESO": "ACREEDORA",
    }

    codigo = models.CharField(
        max_length=20,
        unique=True,
    )

    nombre = models.CharField(
        max_length=150,
    )

    tipo = models.CharField(
        max_length=12,
        choices=TIPOS,
    )

    cuenta_padre = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="subcuentas",
    )

    nivel = models.PositiveSmallIntegerField(
        default=1,
        editable=False,
    )

    acepta_movimientos = models.BooleanField(
        default=True,
        verbose_name="Acepta movimientos",
        help_text="Solo las cuentas de detalle (hoja) pueden recibir partidas.",
    )

    concepto_contable = models.OneToOneField(
        "catalogos.ConceptoContable",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="cuenta_contable",
    )

    activa = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["codigo"]
        verbose_name = "Cuenta Contable"
        verbose_name_plural = "Cuentas Contables"

    @property
    def naturaleza(self):
        return self.NATURALEZA_POR_TIPO[self.tipo]

    def clean(self):

        if self.cuenta_padre_id:

            if self.cuenta_padre.acepta_movimientos:
                raise ValidationError(
                    "La cuenta padre debe ser una cuenta de mayor "
                    "(acepta_movimientos=False)."
                )

            if self.cuenta_padre.tipo != self.tipo:
                raise ValidationError(
                    "La cuenta padre debe ser del mismo tipo."
                )

    def save(self, *args, **kwargs):

        self.nivel = (
            self.cuenta_padre.nivel + 1
            if self.cuenta_padre_id
            else 1
        )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} — {self.nombre}"


class Poliza(models.Model):

    TIPOS = [
        ("INGRESO", "Ingreso"),
        ("EGRESO", "Egreso"),
        ("DIARIO", "Diario"),
    ]

    ESTADOS = [
        ("VIGENTE", "Vigente"),
        ("CANCELADA", "Cancelada"),
    ]

    ORIGENES = [
        ("PAGO", "Pago"),
        ("MANUAL", "Manual"),
        ("AJUSTE", "Ajuste"),
    ]

    ejercicio = models.ForeignKey(
        EjercicioContable,
        on_delete=models.PROTECT,
        related_name="polizas",
    )

    tipo = models.CharField(
        max_length=10,
        choices=TIPOS,
    )

    folio = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    fecha = models.DateField()

    concepto = models.CharField(
        max_length=255,
    )

    pago = models.ForeignKey(
        "negocio.Pago",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="polizas_contables",
    )

    origen = models.CharField(
        max_length=10,
        choices=ORIGENES,
        default="PAGO",
    )

    estado = models.CharField(
        max_length=15,
        choices=ESTADOS,
        default="VIGENTE",
    )

    elaborada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-fecha", "-id"]
        verbose_name = "Póliza Contable"
        verbose_name_plural = "Pólizas Contables"
        constraints = [
            models.UniqueConstraint(
                fields=["pago"],
                condition=Q(pago__isnull=False),
                name="uq_poliza_por_pago",
            ),
        ]

    def validar_balance(self):

        totales = self.partidas.aggregate(
            debe=models.Sum("debe"),
            haber=models.Sum("haber"),
        )

        debe = totales["debe"] or Decimal("0.00")
        haber = totales["haber"] or Decimal("0.00")

        if debe != haber:
            raise ValidationError(
                f"La póliza {self.folio} no está balanceada: "
                f"debe=${debe} haber=${haber}."
            )

    def __str__(self):
        return f"{self.folio} — {self.concepto}"


class PartidaPoliza(models.Model):

    poliza = models.ForeignKey(
        Poliza,
        on_delete=models.CASCADE,
        related_name="partidas",
    )

    cuenta = models.ForeignKey(
        Cuenta,
        on_delete=models.PROTECT,
        related_name="partidas",
    )

    debe = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    haber = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    concepto = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    orden = models.PositiveSmallIntegerField(
        default=0,
    )

    class Meta:
        ordering = ["poliza", "orden"]
        verbose_name = "Partida de Póliza"
        verbose_name_plural = "Partidas de Póliza"
        constraints = [
            models.CheckConstraint(
                check=Q(debe__gte=0) & Q(haber__gte=0),
                name="ck_partida_no_negativos",
            ),
            models.CheckConstraint(
                check=(
                    (Q(debe__gt=0) & Q(haber=0))
                    | (Q(debe=0) & Q(haber__gt=0))
                ),
                name="ck_partida_debe_xor_haber",
            ),
        ]

    def clean(self):

        if self.cuenta_id and not self.cuenta.acepta_movimientos:
            raise ValidationError(
                f"La cuenta {self.cuenta} no acepta movimientos "
                "directos (es una cuenta de mayor)."
            )

        if (self.debe > 0) == (self.haber > 0):
            raise ValidationError(
                "Debe capturarse un importe en Debe o en Haber, "
                "pero no en ambos ni en ninguno."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cuenta.codigo} — Debe ${self.debe} / Haber ${self.haber}"
