from django.contrib import admin
from .models import Grado

from .models import Grado, ConceptoContable
from .models import Grado, Cargo, ConceptoContable

@admin.register(Grado)
class GradoAdmin(admin.ModelAdmin):

    list_display = (
        "orden",
        "nombre",
        "abreviatura",
        "activo",
    )

    search_fields = (
        "nombre",
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
