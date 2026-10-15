"""Paso 19: KML de distritos (300497) -> GeoJSON con un polígono por distrito.
El KML trae cada contorno como LineString; lo convertimos en Polygon cerrado y en sentido
antihorario (RFC 7946), que es lo que necesitan Elasticsearch (geo_shape), D3 y Kibana."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from distritos import DISTRITOS

ORIGEN = Path("datos/originales/distritos_300497.kml")
DESTINO = Path("datos/integrados/distritos_limites.geojson")
NS = {"kml": "http://www.opengis.net/kml/2.2"}


def area_con_signo(anillo):
    """Fórmula del área de Gauss: positiva si el anillo va en sentido antihorario."""
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(anillo, anillo[1:])) / 2


def a_poligono(texto_coordenadas):
    """'lon,lat,alt lon,lat,alt ...' -> anillo cerrado y antihorario [[lon, lat], ...]."""
    anillo = [[round(float(x), 6) for x in punto.split(",")[:2]] for punto in texto_coordenadas.split()]
    if anillo[0] != anillo[-1]:
        anillo.append(anillo[0])              # cerrar el anillo
    if area_con_signo(anillo) < 0:
        anillo.reverse()                      # pasar a sentido antihorario
    return {"type": "Polygon", "coordinates": [anillo]}


def main():
    raiz = ET.parse(ORIGEN).getroot()
    features = []
    for pm in raiz.findall(".//kml:Placemark", NS):
        codigo = pm.findtext("kml:name", namespaces=NS).strip().zfill(2)
        lineas = pm.findall(".//kml:LineString/kml:coordinates", NS)
        if len(lineas) != 1:
            print(f"[aviso] distrito {codigo}: {len(lineas)} contornos, se usa el primero")
        geometria = a_poligono(lineas[0].text)
        features.append({"type": "Feature",
                         "properties": {"codigo": codigo, "nombre": DISTRITOS[codigo]},
                         "geometry": geometria})
        print(f"  {codigo} {DISTRITOS[codigo]:<22} {len(geometria['coordinates'][0]):>5} puntos")

    features.sort(key=lambda f: f["properties"]["codigo"])
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False),
                       encoding="utf-8")
    print(f"\nGuardado {DESTINO}: {len(features)} distritos")


if __name__ == "__main__":
    main()