from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models, transaction
from django.db.models import Max


TAMANO_MAXIMO_COMPROBANTE = 10 * 1024 * 1024  # 10 MB


def validar_tamano_comprobante(archivo):
    if archivo.size > TAMANO_MAXIMO_COMPROBANTE:
        raise ValidationError(
            "El comprobante no debe superar los 10 MB."
        )


class Recibo(models.Model):

    ESTADOS = [
        ("VIGENTE", "Vigente"),
        ("CANCELADO", "Cancelado"),
    ]

    pago = models.OneToOneField(
        "negocio.Pago",
        on_delete=models.PROTECT,
        related_name="recibo",
        verbose_name="Pago",
    )

    folio = models.PositiveIntegerField(
        unique=True,
        editable=False,
        verbose_name="Folio",
    )

    fecha_emision = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de emisión",
    )

    emitido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="Emitido por",
    )

    estado = models.CharField(
        max_length=15,
        choices=ESTADOS,
        default="VIGENTE",
    )

    motivo_cancelacion = models.TextField(
        blank=True,
        default="",
        verbose_name="Motivo de cancelación",
    )

    class Meta:
        ordering = ["-folio"]
        verbose_name = "Recibo"
        verbose_name_plural = "Recibos"

    @property
    def folio_formateado(self):
        año = self.fecha_emision.year if self.fecha_emision else "----"
        return f"REC-{año}-{self.folio:06d}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.folio_formateado


class ComprobanteTransferencia(models.Model):
    """
    Evidencia bancaria de un pago por transferencia: el comprobante
    que el tesorero recibe del banco, con los datos que en él
    aparecen capturados manualmente para poder confrontarlos contra
    el pago que se está registrando.

    ``folio_bancario`` es único para impedir que un mismo comprobante
    respalde más de un cobro (control riguroso de operaciones).
    """

    pago = models.OneToOneField(
        "negocio.Pago",
        on_delete=models.PROTECT,
        related_name="comprobante_transferencia",
        verbose_name="Pago",
    )

    archivo = models.FileField(
        upload_to="comprobantes_transferencia/%Y/%m/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf", "jpg", "jpeg", "png"]
            ),
            validar_tamano_comprobante,
        ],
        verbose_name="Comprobante bancario",
    )

    folio_bancario = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Folio o referencia bancaria",
    )

    emisor = models.CharField(
        max_length=150,
        verbose_name="Emisor según el comprobante",
    )

    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto según el comprobante",
    )

    fecha_transferencia = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de la transferencia",
    )

    verificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="comprobantes_verificados",
        verbose_name="Verificado por",
    )

    verificado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Verificado el",
    )

    observaciones = models.TextField(
        blank=True,
        default="",
    )

    class Meta:
        ordering = ["-verificado_en"]
        verbose_name = "Comprobante de Transferencia"
        verbose_name_plural = "Comprobantes de Transferencia"

    def __str__(self):
        return f"Comprobante {self.folio_bancario} — {self.emisor}"