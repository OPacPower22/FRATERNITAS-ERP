from django.urls import path

from . import views


urlpatterns = [
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
