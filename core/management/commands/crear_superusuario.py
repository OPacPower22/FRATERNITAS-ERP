"""
Crea el usuario administrador a partir de variables de entorno.

Render en su plan gratuito no ofrece consola interactiva, así que
'createsuperuser' no puede ejecutarse a mano. Este comando es
idempotente: si el usuario ya existe, no hace nada.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = "Crea el superusuario definido en las variables de entorno."

    def handle(self, *args, **opciones):

        usuario = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        correo = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
        clave = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")

        if not usuario or not clave:
            self.stdout.write(
                "Sin DJANGO_SUPERUSER_USERNAME o DJANGO_SUPERUSER_PASSWORD: "
                "no se crea ningún administrador."
            )
            return

        Usuario = get_user_model()

        if Usuario.objects.filter(username=usuario).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"El usuario «{usuario}» ya existe; no se modifica."
                )
            )
            return

        Usuario.objects.create_superuser(
            username=usuario,
            email=correo or None,
            password=clave,
        )

        self.stdout.write(
            self.style.SUCCESS(f"Administrador «{usuario}» creado.")
        )
