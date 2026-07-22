from catalogos.models import (
    ConceptoContable,
    TarifaObligacion,
)


def sincronizar_tarifas(tarifas):

    creados = 0
    actualizados = 0

    for tarifa in tarifas:

        concepto = ConceptoContable.objects.get(
                  clave=tarifa["concepto"]
        )   

        _, creado = (
            TarifaObligacion.objects.update_or_create(
                concepto=concepto,
                defaults={
                    "importe": tarifa["importe"],
                    "obligatoria": bool(
                        tarifa["obligatorio"]
                    ),
                    "estado": tarifa["estado"],
                },
            )
        )

        if creado:
            creados += 1
        else:
            actualizados += 1

    print()
    print("TARIFAS_OBLIGACIONES")
    print(f"Creados.....: {creados}")
    print(f"Actualizados: {actualizados}")
