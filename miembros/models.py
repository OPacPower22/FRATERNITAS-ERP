from django.db import models

from catalogos.models import Grado

class Hermano(models.Model):

    TIPO_INGRESO = [
        ("INICIACION", "Iniciación"),
        ("AFILIACION", "Afiliación"),
        ("REGULARIZACION", "Regularización"),
    ]
    
    ESTATUS = [
        ("ACTIVO", "Activo"),
        ("LICENCIA", "Licencia"),
        ("SUSPENDIDO", "Suspendido"),
        ("BAJA", "Baja"),
        ("FALLECIDO", "Fallecido"),
    ]

    # ==========================
    # IDENTIFICACIÓN
    # ==========================

    numero_control = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de Control"
    )

    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100, blank=True)

    nombre_simbolico = models.CharField(
        max_length=100,
        blank=True
    )

    fotografia = models.ImageField(
        upload_to="hermanos/",
        blank=True,
        null=True
    )

    # ==========================
    # DATOS PERSONALES
    # ==========================

    fecha_nacimiento = models.DateField(
        blank=True,
        null=True
    )

    lugar_nacimiento = models.CharField(
        max_length=150,
        blank=True
    )

    profesion = models.CharField(
        max_length=150,
        blank=True
    )

    ocupacion = models.CharField(
        max_length=150,
        blank=True
    )

    # ==========================
    # CONTACTO
    # ==========================

    telefono = models.CharField(
        max_length=20,
        blank=True
    )

    celular = models.CharField(
        max_length=20,
        blank=True
    )

    correo = models.EmailField(
        blank=True
    )

    direccion = models.TextField(
        blank=True
    )

    # ==========================
    # INFORMACIÓN MASÓNICA
    # ==========================

    grado = models.ForeignKey(
    Grado,
    on_delete=models.PROTECT,
    verbose_name="Grado"
)

    tipo_ingreso = models.CharField(
        max_length=20,
        choices=TIPO_INGRESO,
        default="INICIACION"
    )

    fecha_ingreso = models.DateField(
        blank=True,
        null=True
    )

    fecha_iniciacion = models.DateField(
        blank=True,
        null=True
    )

    fecha_aumento = models.DateField(
        blank=True,
        null=True
    )

    fecha_exaltacion = models.DateField(
        blank=True,
        null=True
    )

    logia_procedencia = models.CharField(
        max_length=200,
        blank=True
    )

    # ==========================
    # ESTATUS
    # ==========================

    estatus = models.CharField(
        max_length=20,
        choices=ESTATUS,
        default="ACTIVO"
    )

    # ==========================
    # OBSERVACIONES
    # ==========================

    observaciones = models.TextField(
        blank=True
    )

    # ==========================
    # AUDITORÍA
    # ==========================

    fecha_alta = models.DateTimeField(
        auto_now_add=True
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Hermano"
        verbose_name_plural = "Hermanos"
        ordering = [
            "apellido_paterno",
            "apellido_materno",
            "nombre",
        ]

    def __str__(self):
        return (
            f"{self.apellido_paterno} "
            f"{self.apellido_materno}, "
            f"{self.nombre}"
        )
