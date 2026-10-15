"""Paso 2b: confirmar público, recurrencia y fechas antes de diseñar la transformación."""
import json
from collections import Counter

with open("datos/originales/agenda_300107.json", encoding="utf-8") as f:
    registros = json.load(f)["@graph"]

# Público: cada valor separado por comas, contado por separado
publicos = Counter(p.strip() for r in registros for p in r.get("audience", "").split(",") if p.strip())
print("Público (cada valor por separado):", dict(publicos.most_common()))
print("Con 'Mayores' en audience:", sum("Mayores" in r.get("audience", "") for r in registros))

# Recurrencia: ¿siempre semanal con intervalo 1?
formas = Counter((r["recurrence"].get("frequency"), r["recurrence"].get("interval"))
                 for r in registros if r.get("recurrence"))
print("Recurrencia (frecuencia, intervalo):", dict(formas))

# Fechas: qué periodo cubre la agenda y cuántas actividades duran más de un día
inicios = sorted(r["dtstart"][:10] for r in registros)
print("dtstart desde", inicios[0], "hasta", inicios[-1])
varios_dias = sum(r["dtstart"][:10] != r["dtend"][:10] for r in registros)
print("Actividades de más de un día:", varios_dias)
print("dtend a las 23:59:", sum(r["dtend"][11:16] == "23:59" for r in registros))

# Formato de excluded-days
print("Ejemplos de excluded-days:", [r["excluded-days"] for r in registros if r.get("excluded-days")][:3])