from django.contrib import admin

from .models import Recibo


@admin.register(Recibo)
class ReciboAdmin(admin.ModelAdmin):

    list_display = (
        "folio",
        "pago",
        "fecha_emision",
        "estado",
        "emitido_por",
    )

    list_filter = (
        "estado",
        "fecha_emision",
    )

    search_fields = (
        "folio",
        "pago__id",
        "pago__hermano__nombre",
        "pago__hermano__apellido_paterno",
        "pago__hermano__apellido_materno",
    )

    readonly_fields = (
        "folio",
        "fecha_emision",
    )

    ordering = (
        "-folio",
    )