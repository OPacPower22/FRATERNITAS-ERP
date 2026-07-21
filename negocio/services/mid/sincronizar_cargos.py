from catalogos.models import Cargo


def sincronizar_cargos(datos):

    creados = 0
    actualizados = 0

    for registro in datos:

        clave = str(
            registro["clave"]
        ).strip().upper()

        descripcion = str(
            registro["descripcion"]
        ).strip()

        activo = (
            str(
                registro["activo"]
            ).strip().upper()
            == "ACTIVO"
        )

        _, creado = Cargo.objects.update_or_create(

            nombre=descripcion,

            defaults={

                "abreviatura": clave,

                "activo": activo,

            },

        )

        if creado:
            creados += 1
        else:
            actualizados += 1

    print()

    print("CARGOS_LOGIA")

    print(
        f"Creados.....: {creados}"
    )

    print(
        f"Actualizados: {actualizados}"
    )
