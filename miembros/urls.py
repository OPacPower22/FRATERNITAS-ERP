from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.directorio,
        name="miembros_directorio",
    ),
    path(
        "nuevo/",
        views.crear_hermano,
        name="miembros_crear",
    ),
    path(
        "<int:pk>/editar/",
        views.editar_hermano,
        name="miembros_editar",
    ),
    path(
        "api/directorio/",
        views.api_directorio,
        name="miembros_api_directorio",
    ),
    path(
        "api/expediente/<int:pk>/",
        views.api_expediente,
        name="miembros_api_expediente",
    ),
]
