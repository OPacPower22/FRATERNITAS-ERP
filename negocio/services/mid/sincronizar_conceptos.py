from catalogos.models import ConceptoContable


def sincronizar_conceptos(datos):

    creados = 0
    actualizados = 0

    for registro in datos:

        nombre = str(
            registro["descripcion"]
        ).strip()

        # El DMI usa "ACTIVO" en unos catálogos y "SI" en otros.
        activo = str(
            registro["activo"]
        ).strip().upper() in {
            "ACTIVO",
            "SI",
            "TRUE",
            "1",
        }

        try:

            concepto = ConceptoContable.objects.get(
                nombre=nombre
            )

            concepto.clave = registro["clave"]
            concepto.activo = activo
            concepto.save()

            actualizados += 1

        except ConceptoContable.DoesNotExist:

            ConceptoContable.objects.create(
                clave=registro["clave"],
                nombre=nombre,
                activo=activo,
            )

            creados += 1

    print()
    print("OBLIGACION")
    print(f"Creados.....: {creados}")
    print(f"Actualizados: {actualizados}")
