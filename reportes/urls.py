from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.index,
        name="cu003_reportes_index",
    ),
    path(
        "catalogo-cuentas/",
        views.catalogo_cuentas,
        name="cu003_catalogo_cuentas",
    ),
    path(
        "libro-diario/",
        views.libro_diario,
        name="cu003_libro_diario",
    ),
    path(
        "libro-mayor/",
        views.libro_mayor,
        name="cu003_libro_mayor",
    ),
    path(
        "informe-mensual/",
        views.informe_mensual,
        name="cu003_informe_mensual",
    ),
    path(
        "informe-mensual/pdf/",
        views.informe_mensual_pdf,
        name="cu003_informe_mensual_pdf",
    ),
]
