from django.contrib import admin

from .models import Obligacion


@admin.register(Obligacion)
class ObligacionAdmin(admin.ModelAdmin):

    list_display = (
        "hermano",
        "concepto",
        "periodo",
        "importe",
        "saldo_pendiente",
        "estado",
    )

    list_filter = (
        "estado",
        "concepto",
    )

    search_fields = (
        "hermano__nombre",
        "hermano__apellido_paterno",
        "periodo",
    )

    ordering = (
        "fecha_vencimiento",
    )