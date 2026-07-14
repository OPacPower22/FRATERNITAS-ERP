from django.urls import path
from . import views

from django.contrib.auth import views as auth_views
from django.urls import path, include

urlpatterns = [
    path("", views.dashboard_redirect, name="dashboard"),
    path("dashboard/", views.dashboard_redirect),
]

path("accounts/login/", auth_views.LoginView.as_view(
    template_name="base/login.html"
), name="login"),

path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),

path("", include("core.urls")),
