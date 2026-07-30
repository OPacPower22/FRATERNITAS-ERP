from django.conf import settings
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

    ESTADOS_CIVILES = [
        ("SOLTERO", "Soltero"),
        ("CASADO", "Casado"),
        ("UNION_LIBRE", "Unión libre"),
        ("DIVORCIADO", "Divorciado"),
        ("VIUDO", "Viudo"),
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

    curp = models.CharField(
        max_length=18,
        blank=True,
        verbose_name="CURP",
    )

    rfc = models.CharField(
        max_length=13,
        blank=True,
        verbose_name="RFC",
    )

    estado_civil = models.CharField(
        max_length=20,
        choices=ESTADOS_CIVILES,
        blank=True,
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

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="hermanos_creados",
    )

    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="hermanos_actualizados",
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


class Logia(models.Model):
    """Catálogo de logias para las adscripciones de los hermanos."""

    nombre = models.CharField(max_length=200)
    numero = models.CharField(max_length=30, blank=True)
    oriente = models.CharField(max_length=150, blank=True)
    rito = models.CharField(max_length=150, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Logia"
        verbose_name_plural = "Logias"
        ordering = ["nombre", "numero"]

    def __str__(self):
        sufijo = f" No. {self.numero}" if self.numero else ""
        return f"{self.nombre}{sufijo}"


class AdscripcionLogial(models.Model):
    hermano = models.ForeignKey(
        Hermano,
        on_delete=models.CASCADE,
        related_name="adscripciones_logiales",
    )
    logia = models.ForeignKey(Logia, on_delete=models.PROTECT)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    vigente = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Adscripción logial"
        verbose_name_plural = "Adscripciones logiales"
        ordering = ["-vigente", "-fecha_inicio", "-id"]


class NombramientoLogial(models.Model):
    hermano = models.ForeignKey(
        Hermano,
        on_delete=models.CASCADE,
        related_name="nombramientos_logiales",
    )
    cargo = models.ForeignKey("catalogos.Cargo", on_delete=models.PROTECT)
    periodo_inicio = models.DateField(null=True, blank=True)
    periodo_fin = models.DateField(null=True, blank=True)
    vigente = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Nombramiento logial"
        verbose_name_plural = "Nombramientos logiales"
        ordering = ["-vigente", "-periodo_inicio", "-id"]


class ComisionHermano(models.Model):
    hermano = models.ForeignKey(
        Hermano,
        on_delete=models.CASCADE,
        related_name="comisiones",
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    vigente = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Comisión del hermano"
        verbose_name_plural = "Comisiones del hermano"
        ordering = ["-vigente", "nombre"]


class DistincionHermano(models.Model):
    TIPOS = [
        ("CONDECORACION", "Condecoración"),
        ("RECONOCIMIENTO", "Reconocimiento"),
    ]

    hermano = models.ForeignKey(
        Hermano,
        on_delete=models.CASCADE,
        related_name="distinciones",
    )
    tipo = models.CharField(max_length=20, choices=TIPOS)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    fecha = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Distinción del hermano"
        verbose_name_plural = "Distinciones del hermano"
        ordering = ["-fecha", "nombre"]


class DocumentoHermano(models.Model):
    TIPOS = [
        ("IDENTIFICACION", "Identificación"),
        ("CURP", "CURP"),
        ("RFC", "RFC"),
        ("COMPROBANTE_DOMICILIO", "Comprobante de domicilio"),
        ("SOLICITUD", "Solicitud"),
        ("ACTA_INICIACION", "Acta de iniciación"),
        ("ACTA_AUMENTO", "Acta de aumento"),
        ("ACTA_EXALTACION", "Acta de exaltación"),
        ("OTRO", "Otro documento"),
    ]

    hermano = models.ForeignKey(
        Hermano,
        on_delete=models.CASCADE,
        related_name="documentos",
    )
    tipo = models.CharField(max_length=30, choices=TIPOS)
    nombre = models.CharField(max_length=200)
    archivo = models.FileField(upload_to="hermanos/documentos/")
    fecha_carga = models.DateTimeField(auto_now_add=True)
    cargado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="documentos_hermanos_cargados",
    )

    class Meta:
        verbose_name = "Documento del hermano"
        verbose_name_plural = "Documentos del hermano"
        ordering = ["tipo", "-fecha_carga"]


class NotaHermano(models.Model):
    TIPOS = [
        ("ADMINISTRATIVA", "Administrativa"),
        ("DISCIPLINARIA", "Disciplinaria"),
        ("GENERAL", "General"),
    ]

    hermano = models.ForeignKey(
        Hermano,
        on_delete=models.CASCADE,
        related_name="notas",
    )
    tipo = models.CharField(max_length=20, choices=TIPOS)
    contenido = models.TextField()
    creada_en = models.DateTimeField(auto_now_add=True)
    creada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="notas_hermanos_creadas",
    )

    class Meta:
        verbose_name = "Nota del hermano"
        verbose_name_plural = "Notas del hermano"
        ordering = ["-creada_en"]


class EventoAuditoriaHermano(models.Model):
    hermano = models.ForeignKey(
        Hermano,
        on_delete=models.CASCADE,
        related_name="eventos_auditoria",
    )
    accion = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="eventos_auditoria_hermanos",
    )

    class Meta:
        verbose_name = "Evento de auditoría del hermano"
        verbose_name_plural = "Eventos de auditoría del hermano"
        ordering = ["-fecha"]
