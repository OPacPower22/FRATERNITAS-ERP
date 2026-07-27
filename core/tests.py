from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class DashboardRoutingTests(TestCase):
    def test_raiz_redirige_al_login_sin_autenticar(self):
        response = self.client.get(reverse("dashboard"))

        self.assertRedirects(response, "/login/?next=/")

    def test_raiz_redirige_a_tesoreria_autenticado(self):
        user = get_user_model().objects.create_user(
            username="usuario",
            password="contraseña-segura",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertRedirects(response, "/tesoreria/")
