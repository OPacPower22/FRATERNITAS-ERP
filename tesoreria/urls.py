from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="tesoreria"),
    path(
        "ingresos/nuevo/",
        views.registrar_ingreso,
        name="registrar_ingreso",
    ),
]
