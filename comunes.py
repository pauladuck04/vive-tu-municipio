"""Funciones que usan varias transformaciones."""
import re

APOYOS = {"4": "lengua_signos", "5": "senalizacion_podotactil", "6": "bucle_magnetico"}


def id_catalogo(uri):
    """'.../entidadesyorganismos/12692618-centro-....json' -> '12692618'.
    Identificador del lugar en el catálogo municipal; agenda y centros usan el mismo."""
    encontrado = re.search(r"/(\d+)-[^/]*\.json$", uri or "")
    return encontrado.group(1) if encontrado else None


def accesibilidad(codigos_texto):
    """'1,6' -> {'movilidad': 'accesible', 'apoyos': ['bucle_magnetico'], 'codigos': ['1', '6']}.
    Codificación del documento 'Estructura para conjuntos de datos provenientes de www.madrid.es'."""
    codigos = [c.strip() for c in (codigos_texto or "").split(",") if c.strip()]
    if "1" in codigos:
        movilidad = "accesible"
    elif "2" in codigos:
        movilidad = "parcial"
    elif "0" in codigos:
        movilidad = "no_accesible"
    else:
        movilidad = "sin_informacion"  # código 3 o campo vacío
    return {"movilidad": movilidad, "apoyos": [APOYOS[c] for c in codigos if c in APOYOS], "codigos": codigos}