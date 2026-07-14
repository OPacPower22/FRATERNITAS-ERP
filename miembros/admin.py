from django.contrib import admin
from .models import Hermano


@admin.register(Hermano)
class HermanoAdmin(admin.ModelAdmin):

    list_display = (
        "numero_control",
        "apellido_paterno",
        "apellido_materno",
        "nombre",
        "grado",
        "estatus",
    )

    list_filter = (
        "grado",
        "estatus",
        "tipo_ingreso",
    )

    search_fields = (
        "numero_control",
        "nombre",
        "apellido_paterno",
        "apellido_materno",
        "nombre_simbolico",
    )

    ordering = (
        "apellido_paterno",
        "apellido_materno",
    )
