"""Tabla común de los 21 distritos de Madrid y conversión desde los distintos formatos de nombre.

Cada fuente escribe el distrito de una forma:
  agenda y centros: 'Chamartin', 'Fuencarral-ElPardo'   (final de la URI de address.district)
  padrón:           'CHAMARTIN', 'FUENCARRAL-EL PARDO'  y código '5'
"""
import re
import unicodedata

DISTRITOS = {
    "01": "Centro", "02": "Arganzuela", "03": "Retiro", "04": "Salamanca", "05": "Chamartín",
    "06": "Tetuán", "07": "Chamberí", "08": "Fuencarral-El Pardo", "09": "Moncloa-Aravaca",
    "10": "Latina", "11": "Carabanchel", "12": "Usera", "13": "Puente de Vallecas",
    "14": "Moratalaz", "15": "Ciudad Lineal", "16": "Hortaleza", "17": "Villaverde",
    "18": "Villa de Vallecas", "19": "Vicálvaro", "20": "San Blas-Canillejas", "21": "Barajas",
}


def clave(nombre):
    """'Fuencarral-El Pardo', 'FUENCARRAL-EL PARDO' y 'Fuencarral-ElPardo' -> 'fuencarralelpardo'."""
    sin_tildes = unicodedata.normalize("NFKD", nombre or "")
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", sin_tildes.lower())


_POR_CLAVE = {clave(nombre): codigo for codigo, nombre in DISTRITOS.items()}


def distrito(nombre_o_codigo):
    """Devuelve {'codigo': '05', 'nombre': 'Chamartín'} a partir de cualquier formato, o None."""
    valor = str(nombre_o_codigo or "").strip()
    if valor.isdigit() and 1 <= int(valor) <= 21:
        codigo = valor.zfill(2)
    else:
        codigo = _POR_CLAVE.get(clave(valor))
    return {"codigo": codigo, "nombre": DISTRITOS[codigo]} if codigo else None