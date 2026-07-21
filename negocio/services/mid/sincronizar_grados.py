from catalogos.models import Grado


def sincronizar_grados(datos):

    creados = 0
    actualizados = 0

    orden = 1

    for registro in datos:

        _, creado = Grado.objects.update_or_create(

            abreviatura=registro["clave"],

            defaults={

                "nombre": registro["descripcion"],

                "orden": orden,

                "activo": (
                    str(registro["activo"]).upper()
                    == "ACTIVO"
                ),

            },

        )

        if creado:
            creados += 1
        else:
            actualizados += 1

        orden += 1

    print()

    print("GRADOS_MASONICOS")

    print(
        f"Creados.....: {creados}"
    )

    print(
        f"Actualizados: {actualizados}"
    )

