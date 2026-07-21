from catalogos.models import ParametroSistema


def sincronizar_parametros(datos):

    creados = 0
    actualizados = 0

    for registro in datos:

        clave = str(
            registro["parametro"]
        ).strip().upper()

        valor = "" if registro["valor"] is None else str(
            registro["valor"]
        ).strip()

        descripcion = "" if registro["descripcion"] is None else str(
            registro["descripcion"]
        ).strip()

        modificable = (
            str(
                registro["modificable"]
            ).strip().upper()
            == "SI"
        )

        _, creado = ParametroSistema.objects.update_or_create(

            clave=clave,

            defaults={

                "valor": valor,

                "descripcion": descripcion,

                "modificable": modificable,

            },

        )

        if creado:
            creados += 1
        else:
            actualizados += 1

    print()

    print("PARAMETROS")

    print(
        f"Creados.....: {creados}"
    )

    print(
        f"Actualizados: {actualizados}"
    )
