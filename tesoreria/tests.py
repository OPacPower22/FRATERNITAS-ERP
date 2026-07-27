from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


class TesoreriaRoutingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tesorero",
            password="contraseña-segura",
        )
        self.client.force_login(self.user)

    def test_inicio_de_tesoreria_muestra_el_dashboard_institucional(self):
        response = self.client.get(reverse("tesoreria"))

        self.assertTemplateUsed(response, "core/dashboard.html")
        self.assertContains(response, "Centro de Operaciones")

# Create your tests here.
