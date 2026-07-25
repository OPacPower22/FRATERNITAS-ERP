from django.conf import settings
from django.db import models, transaction
from django.db.models import Max


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

        if self._state.adding and not self.folio:

            with transaction.atomic():

                ultimo = (
                    Recibo.objects
                    .select_for_update()
                    .aggregate(Max("folio"))
                    .get("folio__max")
                )

                self.folio = (ultimo or 0) + 1

                super().save(*args, **kwargs)

            return

        super().save(*args, **kwargs)

    def __str__(self):
        return self.folio_formateado