from collections import defaultdict

from openpyxl import load_workbook

from negocio.services.mid.config import DMI, HOJAS

from negocio.services.mid.sincronizar_grados import (
        sincronizar_grados,
        )

from negocio.services.mid.sincronizar_cargos import (
    sincronizar_cargos,
)

from negocio.services.mid.sincronizar_conceptos import (
    sincronizar_conceptos,
)


def sincronizar_catalogos():

    if not DMI.exists():
        raise FileNotFoundError(
            f"No se encontró el DMI:\n{DMI}"
        )

    libro = load_workbook(
        DMI,
        data_only=True,
    )

    nombre_hoja = HOJAS["catalogos"]

    if nombre_hoja not in libro.sheetnames:
        raise ValueError(
            f"La hoja '{nombre_hoja}' no existe."
        )

    hoja = libro[nombre_hoja]

    catalogos = defaultdict(list)

    for fila in hoja.iter_rows(
        min_row=2,
        values_only=True,
    ):

        tipo = fila[0]
        clave = fila[1]
        descripcion = fila[2]
        activo = fila[3]

        if not tipo:
            continue

        catalogos[tipo].append(
            {
                "clave": clave,
                "descripcion": descripcion,
                "activo": activo,
            }
        )

    print()
    print("=" * 60)
    print("CATÁLOGOS ENCONTRADOS")
    print("=" * 60)

    for nombre, elementos in sorted(catalogos.items()):
        print(f"{nombre:<35}{len(elementos):>5}")

    print("=" * 60)

    if "GRADOS_MASONICOS" in catalogos:
          sincronizar_grados(
                 catalogos["GRADOS_MASONICOS"]
           )
    
    if "CARGOS_LOGIA" in catalogos:

           sincronizar_cargos(
                catalogos["CARGOS_LOGIA"]
           )
    
    if "OBLIGACION" in catalogos:

            sincronizar_conceptos(
                catalogos["OBLIGACION"]
            )
    
    return catalogos
