"""
Corrige el padrón de Hermanos importado desde MOVIMIENTOS 2026.

La hoja MEMBRESIA sólo trae nombres abreviados sin grado. Este
script aplica los nombres completos y grados reales confirmados
por Tesorería, e identifica como BAJA a los Hermanos que ya no
están vigentes en el padrón (no mencionados en la lista oficial).

Uso:
    python manage.py shell -c "
        from importaciones.actualizar_membresia_2026 import actualizar
        actualizar()
    "
"""

from catalogos.models import Grado
from miembros.models import Hermano

from importaciones.importar_membresia_2026 import _separar_nombre

# numero_control: (nombre completo, grado)
PADRON_VIGENTE = {
    "2": ("Gabino Sabitri Santamaría Delgado", "Maestro Mason"),
    "3": ("Jorge Luis Mendoza Soriano", "Maestro Mason"),
    "1": ("David García Melgoza", "Maestro Mason"),
    "4": ("Leopoldo García Melgoza", "Maestro Mason"),
    "5": ("Luis Rodríguez Mata", "Maestro Mason"),
    "7": ("Aulio César Ibarra Zavala", "Compañero"),
    "11": ("Rafael Martínez de Jesús", "Compañero"),
    "9": ("José Alfredo González Solís", "Compañero"),
    "6": ("Luis Enrique Ramón Vilaboa", "Maestro Mason"),
    "13": ("Alexis Guerra García", "Aprendiz"),
    "8": ("Guillermo Francisco Motolinia Sánchez", "Maestro Mason"),
    "14": ("Ángel Ricardo Gutiérrez Álvarez", "Aprendiz"),
    "15": ("Ángel Ricardo Gutiérrez Contreras", "Aprendiz"),
    "12": ("Víctor Hugo Ambrosio Guevara", "Compañero"),
    "10": ("José Omar Pacheco Tapia", "Compañero"),
}

# Hermanos que ya no forman parte del padrón vigente.
NUMEROS_CONTROL_BAJA = ("16", "17", "18")


def actualizar():

    actualizados = 0

    for numero_control, (nombre_completo, nombre_grado) in PADRON_VIGENTE.items():

        try:
            hermano = Hermano.objects.get(numero_control=numero_control)
        except Hermano.DoesNotExist:
            continue

        grado = Grado.objects.get(nombre=nombre_grado)

        nombre, apellido_paterno, apellido_materno = _separar_nombre(
            nombre_completo
        )

        hermano.nombre = nombre
        hermano.apellido_paterno = apellido_paterno
        hermano.apellido_materno = apellido_materno
        hermano.grado = grado
        hermano.estatus = "ACTIVO"
        hermano.save()

        actualizados += 1

    bajas = Hermano.objects.filter(
        numero_control__in=NUMEROS_CONTROL_BAJA
    ).update(estatus="BAJA")

    print()
    print("===================================")
    print("ACTUALIZACIÓN DE PADRÓN 2026 FINALIZADA")
    print("===================================")
    print(f"Actualizados : {actualizados}")
    print(f"Bajas        : {bajas}")
    print("===================================")
