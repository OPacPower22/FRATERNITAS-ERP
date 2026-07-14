from django.contrib import admin
from .models import Grado

from .models import Grado, ConceptoContable

@admin.register(Grado)
class GradoAdmin(admin.ModelAdmin):

    list_display = (
        "orden",
        "nombre",
        "abreviatura",
        "activo",
    )

    ordering = ("orden",)

@admin.register(ConceptoContable)
class ConceptoContableAdmin(admin.ModelAdmin):

    list_display = (
        "nombre",
        "activo",
    )

    search_fields = (
        "nombre",
    )
