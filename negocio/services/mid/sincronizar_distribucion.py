from catalogos.models import (
    ConceptoContable,
    DistribucionCapita,
)


def sincronizar_distribucion(datos):

    creados = 0
    actualizados = 0

    for registro in datos:

        origen = ConceptoContable.objects.get(
            clave=str(
                registro["capita"]
            ).strip().upper()
        )

        destino = ConceptoContable.objects.get(
            clave=str(
                registro["componente"]
            ).strip().upper()
        )

        _, creado = DistribucionCapita.objects.update_or_create(

            concepto_origen=origen,
            concepto_destino=destino,

            defaults={

                "importe": registro["importe"],

                "grupo": str(
                    registro["grupo"]
                ).strip().upper(),

                "orden": registro["orden"],

            },

        )

        if creado:
            creados += 1
        else:
            actualizados += 1

    print()
    print("DISTRIBUCION_CAPITA")
    print(f"Creados.....: {creados}")
    print(f"Actualizados: {actualizados}")
