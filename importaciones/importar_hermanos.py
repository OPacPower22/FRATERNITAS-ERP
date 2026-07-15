from openpyxl import load_workbook

from miembros.models import Hermano


def importar_hermanos(ruta_excel):

    wb = load_workbook(ruta_excel)

    ws = wb["MEMBRESIA"]

    creados = 0

    for fila in ws.iter_rows(min_row=4, values_only=True):

        numero = fila[0]
        nombre_completo = fila[1]

        if not numero or not nombre_completo:
            continue

        partes = str(nombre_completo).split()

        nombre = partes[0]

        apellido_paterno = (
            partes[-2] if len(partes) >= 3 else ""
        )

        apellido_materno = (
            partes[-1] if len(partes) >= 2 else ""
        )

        Hermano.objects.get_or_create(

            numero_control=str(numero),

            defaults={

                "nombre": nombre,

                "apellido_paterno": apellido_paterno,

                "apellido_materno": apellido_materno,

                "activo": True,

            },

        )

        creados += 1

    print(f"Hermanos importados: {creados}")