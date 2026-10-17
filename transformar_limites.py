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

from shapely.geometry import MultiPolygon, Polygon, mapping
from shapely.geometry.polygon import orient
from shapely.validation import explain_validity, make_valid


def solo_poligonos(geometria):
    """Devuelve las piezas poligonales de una geometría (make_valid puede devolver
    también líneas o puntos sueltos, que no sirven para rellenar un distrito)."""
    if isinstance(geometria, Polygon):
        return [geometria]
    if hasattr(geometria, "geoms"):                 # MultiPolygon o GeometryCollection
        return [p for g in geometria.geoms for p in solo_poligonos(g)]
    return []


def a_poligono(texto_coordenadas):
    """'lon,lat,alt lon,lat,alt ...' -> Polygon o MultiPolygon válido y en sentido antihorario (RFC 7946)."""
    anillo = [[round(float(x), 6) for x in punto.split(",")[:2]] for punto in texto_coordenadas.split()]
    poligono = Polygon(anillo)                       # shapely cierra el anillo si hace falta
    if not poligono.is_valid:
        print(f"    reparado: {explain_validity(poligono)}")
        poligono = make_valid(poligono)
    piezas = [orient(p, sign=1.0) for p in solo_poligonos(poligono) if p.area > 0]   # sign=1 -> antihorario
    geometria = piezas[0] if len(piezas) == 1 else MultiPolygon(piezas)
    return mapping(geometria)

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
        print(f"  {codigo} {DISTRITOS[codigo]:<22} {geometria['type']}")

    features.sort(key=lambda f: f["properties"]["codigo"])
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False),
                       encoding="utf-8")
    print(f"\nGuardado {DESTINO}: {len(features)} distritos")
    


if __name__ == "__main__":
    main()