from catalogos.models import ConceptoContable


def sincronizar_conceptos(datos):

    creados = 0
    actualizados = 0

    for registro in datos:

        nombre = str(
            registro["descripcion"]
        ).strip()

        descripcion = str(
            registro["clave"]
        ).strip().upper()

        activo = (
            str(
                registro["activo"]
            ).strip().upper()
            == "ACTIVO"
        )

        _, creado = ConceptoContable.objects.update_or_create(

            nombre=nombre,

            defaults={

                "descripcion": descripcion,

                "activo": activo,

            },

        )

        if creado:
            creados += 1
        else:
            actualizados += 1

    print()

    print("OBLIGACION")

    print(
        f"Creados.....: {creados}"
    )

    print(
        f"Actualizados: {actualizados}"
    )
