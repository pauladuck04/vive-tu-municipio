"""Paso 2: ver qué campos y valores tiene la agenda completa."""
import json
from collections import Counter

with open("datos/originales/agenda_300107.json", encoding="utf-8") as f:
    registros = json.load(f)["@graph"]
total = len(registros)
print(f"Total de registros: {total}\n")

# 1. Cuántos registros traen cada campo (con algún valor)
campos = Counter()
for r in registros:
    for clave, valor in r.items():
        if valor not in ("", None, {}, {"@id": ""}):
            campos[clave] += 1
print("Campos presentes (registros que los traen con valor):")
for campo, n in campos.most_common():
    print(f"  {campo:<16} {n:>5}  ({100 * n / total:.0f} %)")

# 2. Tipos de actividad (última parte de @type)
tipos = Counter(r.get("@type", "").rsplit("/", 1)[-1] for r in registros)
print("\nTipos de actividad (@type):")
for tipo, n in tipos.most_common():
    print(f"  {tipo or '(vacío)':<40} {n:>5}")

# 3. Ejemplos de los campos que no salían en el primer registro
for campo in ("recurrence", "audience"):
    valores = Counter(json.dumps(r[campo], ensure_ascii=False) for r in registros if r.get(campo))
    print(f"\nValores más frecuentes de '{campo}':")
    for valor, n in valores.most_common(8):
        print(f"  {n:>5}  {valor}")

# 4. Lugares que parecen centros de mayores
mayores = Counter(r.get("event-location", "") for r in registros if "mayores" in r.get("event-location", "").lower())
print(f"\nActividades en lugares con 'mayores' en el nombre: {sum(mayores.values())}")
for lugar, n in mayores.most_common(5):
    print(f"  {n:>5}  {lugar}")