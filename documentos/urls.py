from django.urls import path

from . import views


urlpatterns = [
    path(
        "recibo/<int:pk>/pdf/",
        views.recibo_pdf,
        name="documentos_recibo_pdf",
    ),
    path(
        "recibo/vista-previa/pdf/",
        views.recibo_pdf_vista_previa,
        name="documentos_recibo_pdf_vista_previa",
    ),
    path(
        "recibo/<int:pk>/enviar/",
        views.enviar_recibo,
        name="documentos_recibo_enviar",
    ),
    path(
        "recibo/<int:pk>/whatsapp/",
        views.enlace_whatsapp,
        name="documentos_recibo_whatsapp",
    ),
    path(
        "verificar/<str:token>/",
        views.verificar_recibo,
        name="documentos_verificar_recibo",
    ),
]
