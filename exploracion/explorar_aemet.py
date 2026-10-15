"""Paso 9: ver la estructura de la predicción diaria de AEMET."""
import json

with open("datos/originales/prevision_aemet.json", encoding="utf-8") as f:
    datos = json.load(f)

print("Tipo raíz:", type(datos).__name__, "| elementos:", len(datos))
raiz = datos[0]
print("Claves de primer nivel:", list(raiz.keys()))
print("Municipio:", raiz.get("nombre"), "| elaborado:", raiz.get("elaborado"))

dias = raiz["prediccion"]["dia"]
print(f"\nDías de predicción: {len(dias)} ({dias[0]['fecha'][:10]} a {dias[-1]['fecha'][:10]})")
print("Claves de cada día:", list(dias[0].keys()))

print("\nPrimer día completo:")
print(json.dumps(dias[0], indent=2, ensure_ascii=False))

print("\nResumen por día (probPrecipitacion y estadoCielo por periodo):")
for d in dias:
    lluvia = [(p.get("periodo", "día"), p.get("value")) for p in d.get("probPrecipitacion", [])]
    cielo = [(c.get("periodo", "día"), c.get("descripcion")) for c in d.get("estadoCielo", [])]
    print(f"  {d['fecha'][:10]}  lluvia={lluvia}")
    print(f"              cielo={cielo}")