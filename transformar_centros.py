"""Paso 5: centros de mayores (200337) -> documentos del índice 'lugares'."""
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from comunes import accesibilidad, id_catalogo
from distritos import distrito

ORIGEN = Path("datos/originales/centros_200337.json")
DESTINO = Path("datos/integrados/lugares.ndjson")


def transporte(descripcion):
    """Extrae el trozo 'Metro: ...' / 'Autobuses: ...' de la descripción, si lo hay."""
    encontrado = re.search(r"((?:Metro|Autob[uú]s(?:es)?|Bus|Cercan[ií]as)\s*:.*)$", descripcion or "")
    return encontrado.group(1).strip()[:300] if encontrado else ""


def transformar(c, extraido):
    org = c.get("organization", {})
    loc = c.get("location", {})
    distrito_uri = c.get("address", {}).get("district", {}).get("@id", "")
    return {
        "id": f"lug_{id_catalogo(c['@id']) or c['id']}",
        "tipo": "centro_mayores",
        "nombre": c["title"],
        "direccion": c.get("address", {}).get("street-address", ""),
        "codigo_postal": c.get("address", {}).get("postal-code", ""),
        "distrito": distrito(distrito_uri.rsplit("/", 1)[-1]),
        "ubicacion": {"type": "Point", "coordinates": [loc["longitude"], loc["latitude"]]} if loc else None,
        "horario": org.get("schedule", ""),
        "servicios": org.get("services", ""),
        "transporte": transporte(org.get("organization-desc", "")),
        "accesibilidad": accesibilidad(org.get("accesibility", "")),
        "url_info": c.get("relation", ""),
        "procedencia": [{"fuente": "200337-centros-mayores", "id_origen": c["id"], "extraido": extraido}],
    }


def main():
    extraido = datetime.fromtimestamp(ORIGEN.stat().st_mtime).isoformat(timespec="seconds")
    with ORIGEN.open(encoding="utf-8") as f:
        centros = json.load(f)["@graph"]
    lugares = [transformar(c, extraido) for c in centros]

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    with DESTINO.open("w", encoding="utf-8") as f:
        for l in lugares:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")

    print(f"Centros guardados en {DESTINO}: {len(lugares)}")
    print("  por distrito:", dict(Counter(l["distrito"]["nombre"] for l in lugares if l["distrito"]).most_common()))
    print("  sin distrito reconocido:", [l["nombre"] for l in lugares if not l["distrito"]])
    print("  con info de transporte:", sum(bool(l["transporte"]) for l in lugares))
    print("  horarios distintos:", len({l["horario"] for l in lugares}))
    for horario, n in Counter(l["horario"] for l in lugares).most_common(5):
        print(f"    {n:>3}  {horario}")
    print("\nEjemplo:")
    print(json.dumps(lugares[0], indent=2, ensure_ascii=False))

    print("\nCentros sin transporte detectado (final de su descripción):")
    with ORIGEN.open(encoding="utf-8") as f:
        originales = {c["id"]: c for c in json.load(f)["@graph"]}
    for l in [l for l in lugares if not l["transporte"]][:5]:
        desc = originales[l["procedencia"][0]["id_origen"]]["organization"]["organization-desc"]
        print(f"  {l['nombre'][:50]}: ...{desc[-150:]!r}")

    print("  accesibilidad:", dict(Counter(l["accesibilidad"]["movilidad"] for l in lugares)))


if __name__ == "__main__":
    main()