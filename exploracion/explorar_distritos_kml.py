"""Paso 18: ver la estructura del KML de distritos (campos, tipo de geometría y coordenadas)."""
import xml.etree.ElementTree as ET
from collections import Counter

NS = {"kml": "http://www.opengis.net/kml/2.2"}
raiz = ET.parse("datos/originales/distritos_300497.kml").getroot()

placemarks = raiz.findall(".//kml:Placemark", NS)
print(f"Placemarks (uno por distrito, en principio): {len(placemarks)}\n")

# Primer distrito: nombre, datos asociados y tipo de geometría
p = placemarks[0]
print("name:", p.findtext("kml:name", namespaces=NS))
print("description:", (p.findtext("kml:description", namespaces=NS) or "")[:300])
for dato in p.findall(".//kml:SimpleData", NS) + p.findall(".//kml:Data", NS):
    print(f"  dato {dato.get('name')}: {dato.text or dato.findtext('kml:value', namespaces=NS)}")

# Tipos de geometría y rango de coordenadas
tipos = Counter(hijo.tag.split('}')[1] for pm in placemarks for hijo in pm.iter()
                if hijo.tag.split('}')[1] in ("Polygon", "MultiGeometry", "LineString", "Point"))
print("\nGeometrías:", dict(tipos))
coords = [c for pm in placemarks for txt in pm.itertext() for c in txt.split()
          if c.count(",") >= 1 and c.replace(",", "").replace(".", "").replace("-", "").isdigit()]
lons = [float(c.split(",")[0]) for c in coords]
lats = [float(c.split(",")[1]) for c in coords]
print(f"Puntos: {len(coords)} | longitud {min(lons):.4f} a {max(lons):.4f} | latitud {min(lats):.4f} a {max(lats):.4f}")

print("\nNombres de todos los placemarks:")
print([pm.findtext("kml:name", namespaces=NS) for pm in placemarks])