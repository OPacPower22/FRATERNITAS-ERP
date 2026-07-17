from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.dashboard_redirect,
        name="dashboard",
    ),
    path(
        "dashboard/",
        views.dashboard_redirect,
        name="dashboard_redirect",
    ),
]