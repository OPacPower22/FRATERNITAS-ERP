from django.contrib import admin
from .models import Grado, Cargo, ConceptoContable


@admin.register(Grado)
class GradoAdmin(admin.ModelAdmin):
    list_display = ("orden", "nombre", "abreviatura", "activo")
    ordering = ("orden",)


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "abreviatura", "activo")
    search_fields = ("nombre",)


@admin.register(ConceptoContable)
class ConceptoContableAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    search_fields = ("nombre",)
