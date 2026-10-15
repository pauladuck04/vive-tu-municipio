"""Paso 4: ver qué traen los centros de mayores y si se pueden unir con la agenda."""
import json
from collections import Counter

with open("datos/originales/centros_200337.json", encoding="utf-8") as f:
    centros = json.load(f)["@graph"]
with open("datos/originales/agenda_300107.json", encoding="utf-8") as f:
    agenda = json.load(f)["@graph"]

print(f"Centros: {len(centros)}\n")
print("Primer centro:")
print(json.dumps(centros[0], indent=2, ensure_ascii=False))

# Campos de primer nivel y dentro de 'organization'
campos = Counter(k for c in centros for k, v in c.items() if v not in ("", None, {}))
print("\nCampos presentes:", dict(campos))
org = Counter(k for c in centros for k, v in c.get("organization", {}).items() if v not in ("", None))
print("Campos en 'organization':", dict(org))
print("Códigos de accesibilidad:", dict(Counter(c.get("organization", {}).get("accesibility", "") for c in centros)))

# ¿Coincide el @id del centro con el relation.@id de las actividades?
ids_centros = {c["@id"]: c["title"] for c in centros}
coinciden = Counter(ids_centros[a["relation"]["@id"]] for a in agenda
                    if a.get("relation", {}).get("@id") in ids_centros)
print(f"\nActividades de la agenda cuyo relation.@id es un centro de mayores: {sum(coinciden.values())}")
for nombre, n in coinciden.most_common(10):
    print(f"  {n:>3}  {nombre}")

# Por si no coinciden: ¿hay actividades con el nombre exacto de un centro?
nombres = {c["title"].strip().lower() for c in centros}
por_nombre = sum(a.get("event-location", "").strip().lower() in nombres for a in agenda)
print(f"Actividades cuyo event-location coincide con el nombre de un centro: {por_nombre}")