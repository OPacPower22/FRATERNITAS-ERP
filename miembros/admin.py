from django.contrib import admin

from .models import (
    AdscripcionLogial,
    ComisionHermano,
    DistincionHermano,
    DocumentoHermano,
    EventoAuditoriaHermano,
    Hermano,
    Logia,
    NombramientoLogial,
    NotaHermano,
)


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
    list_filter = ("grado", "estatus", "tipo_ingreso")
    search_fields = (
        "numero_control",
        "nombre",
        "apellido_paterno",
        "apellido_materno",
        "nombre_simbolico",
        "curp",
        "rfc",
    )
    readonly_fields = ("fecha_alta", "fecha_actualizacion", "creado_por", "actualizado_por")
    ordering = ("apellido_paterno", "apellido_materno")

    def save_model(self, request, obj, form, change):
        if not change and not obj.creado_por_id:
            obj.creado_por = request.user
        obj.actualizado_por = request.user
        super().save_model(request, obj, form, change)
        EventoAuditoriaHermano.objects.create(
            hermano=obj,
            usuario=request.user,
            accion="Actualización" if change else "Creación",
            descripcion="Registro de hermano actualizado desde administración.",
        )


@admin.register(Logia)
class LogiaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "numero", "oriente", "rito", "activa")
    list_filter = ("activa", "rito")
    search_fields = ("nombre", "numero", "oriente")


@admin.register(AdscripcionLogial)
class AdscripcionLogialAdmin(admin.ModelAdmin):
    list_display = ("hermano", "logia", "fecha_inicio", "fecha_fin", "vigente")
    list_filter = ("vigente", "logia")
    search_fields = ("hermano__nombre", "hermano__apellido_paterno", "logia__nombre")


@admin.register(NombramientoLogial)
class NombramientoLogialAdmin(admin.ModelAdmin):
    list_display = ("hermano", "cargo", "periodo_inicio", "periodo_fin", "vigente")
    list_filter = ("vigente", "cargo")
    search_fields = ("hermano__nombre", "hermano__apellido_paterno")


@admin.register(ComisionHermano)
class ComisionHermanoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "hermano", "fecha_inicio", "fecha_fin", "vigente")
    list_filter = ("vigente",)
    search_fields = ("nombre", "hermano__nombre", "hermano__apellido_paterno")


@admin.register(DistincionHermano)
class DistincionHermanoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "hermano", "fecha")
    list_filter = ("tipo",)
    search_fields = ("nombre", "hermano__nombre", "hermano__apellido_paterno")


@admin.register(DocumentoHermano)
class DocumentoHermanoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "hermano", "fecha_carga", "cargado_por")
    list_filter = ("tipo",)
    search_fields = ("nombre", "hermano__nombre", "hermano__apellido_paterno")
    readonly_fields = ("fecha_carga",)

    def save_model(self, request, obj, form, change):
        if not obj.cargado_por_id:
            obj.cargado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(NotaHermano)
class NotaHermanoAdmin(admin.ModelAdmin):
    list_display = ("hermano", "tipo", "creada_en", "creada_por")
    list_filter = ("tipo",)
    search_fields = ("hermano__nombre", "hermano__apellido_paterno", "contenido")
    readonly_fields = ("creada_en",)

    def save_model(self, request, obj, form, change):
        if not obj.creada_por_id:
            obj.creada_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(EventoAuditoriaHermano)
class EventoAuditoriaHermanoAdmin(admin.ModelAdmin):
    list_display = ("hermano", "accion", "fecha", "usuario")
    list_filter = ("accion", "fecha")
    search_fields = ("hermano__nombre", "hermano__apellido_paterno", "descripcion")
    readonly_fields = ("hermano", "accion", "descripcion", "fecha", "usuario")
