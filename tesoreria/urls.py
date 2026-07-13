from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="tesoreria"), 
    path(
    "cu001/",
    views.emitir_recibo,
    name="cu001_emitir_recibo",
    ),
    path(
        "ingresos/nuevo/",
        views.registrar_ingreso,
        name="registrar_ingreso",
    ),
    path(
        "recibos/emitir/",
        views.emitir_recibo,
        name="emitir_recibo",
    ),
    ]