from django.urls import path

from miembros import views


app_name = "miembros"

urlpatterns = [
    path("", views.lista_expedientes, name="lista_expedientes"),
    path("<int:hermano_id>/", views.expediente_detalle, name="expediente_detalle"),
    path("recibos/<int:recibo_id>/", views.ver_recibo, name="ver_recibo"),
    path(
        "documentos/<int:documento_id>/descargar/",
        views.descargar_documento,
        name="descargar_documento",
    ),
]
