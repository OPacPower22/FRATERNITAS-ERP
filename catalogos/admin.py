from django.contrib import admin
from .models import ConceptoContable


@admin.register(ConceptoContable)
class ConceptoContableAdmin(admin.ModelAdmin):

    list_display = (
        "nombre",
        "activo",
    )

    list_filter = (
        "activo",
    )

    search_fields = (
        "nombre",
    )

    ordering = (
        "nombre",
    )
