from django.contrib import admin
from .models import Movimiento


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):

    fieldsets = (
        ("Información general", {
            "fields": (
                "tipo",
                "recibo",
                "hermano",
                "fecha",
                "concepto",
                "descripcion",
            )
        }),

        ("Distribución del ingreso / egreso", {
            "fields": (
                (
                    "capitas",
                    "aniversario",
                ),
                (
                    "saco_beneficencia",
                    "taller_bj",
                ),
                (
                    "otros",
                    "total",
                ),
            )
        }),

        ("Información adicional", {
            "fields": (
                "justificacion",
            )
        }),
    )

    list_display = (
        "fecha",
         "recibo",
         "tipo",
         "hermano",
         "concepto",
         "capitas",
         "aniversario",
         "saco_beneficencia",
         "taller_bj",
         "otros",
         "total",
    )

    list_filter = (
        "tipo",
        "fecha",
    )

    search_fields = (
        "concepto",
        "descripcion",
        "hermano__nombre",
        "hermano__apellido_paterno",
        "hermano__apellido_materno",
    )

    ordering = (
        "-fecha",
        "-id",
    )

    date_hierarchy = "fecha"
