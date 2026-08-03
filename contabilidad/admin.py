from django.contrib import admin

from .models import Cuenta, EjercicioContable, PartidaPoliza, Poliza


@admin.register(EjercicioContable)
class EjercicioContableAdmin(admin.ModelAdmin):
    list_display = ("nombre", "fecha_inicio", "fecha_fin", "cerrado")
    ordering = ("-fecha_inicio",)


@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "tipo", "nivel", "acepta_movimientos", "activa")
    list_filter = ("tipo", "acepta_movimientos", "activa")
    search_fields = ("codigo", "nombre")
    ordering = ("codigo",)


class PartidaPolizaInline(admin.TabularInline):
    model = PartidaPoliza
    extra = 0


@admin.register(Poliza)
class PolizaAdmin(admin.ModelAdmin):
    list_display = ("folio", "tipo", "fecha", "concepto", "estado")
    list_filter = ("tipo", "estado", "ejercicio")
    search_fields = ("folio", "concepto")
    ordering = ("-fecha", "-id")
    inlines = [PartidaPolizaInline]
