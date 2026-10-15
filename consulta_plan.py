"""Plan semanal: C1 (cercanía y fechas) + C3 (tiempo) + C4 (variedad) + centro de mayores más cercano."""
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
import shutil

import requests

ES = "http://localhost:9200"

# Dirección de ejemplo (Ciudad Lineal). La geocodificación de direcciones queda para la ampliación.
CASA = {"nombre": "Ejemplo: calle de Alcalá, Ciudad Lineal", "lat": 40.4380, "lon": -3.6550}
RADIO_KM = 2
DIAS = 7
MAX_POR_DIA = 2
MAX_POR_CATEGORIA = 2
UMBRAL_LLUVIA = 50  # % a partir del cual no se proponen actividades al aire libre


def buscar(indice, cuerpo):
    respuesta = requests.post(f"{ES}/{indice}/_search", json=cuerpo)
    respuesta.raise_for_status()
    return respuesta.json()


def consulta_c1(lat, lon, radio_km, desde, hasta):
    """C1: actividades dirigidas o aptas, con hora conocida, a menos de radio_km y con sesión en la semana."""
    cuerpo = {
        "size": 300,
        "_source": {"excludes": ["sesiones", "descripcion"]},
        "query": {"bool": {"filter": [
            {"terms": {"nivel_mayores": ["dirigida", "apta"]}},
            {"term": {"hora_conocida": True}},
            {"geo_distance": {"distance": f"{radio_km}km", "ubicacion": {"lat": lat, "lon": lon}}},
            {"nested": {
                "path": "sesiones",
                "query": {"range": {"sesiones.inicio": {"gte": desde, "lt": hasta}}},
                "inner_hits": {"size": 20, "sort": [{"sesiones.inicio": "asc"}]},
            }},
        ]}},
        "sort": [{"_geo_distance": {"ubicacion": {"lat": lat, "lon": lon}, "order": "asc", "unit": "m"}}],
    }
    datos = buscar("actividades", cuerpo)
    actividades = []
    for hit in datos["hits"]["hits"]:
        act = hit["_source"]
        act["distancia_m"] = round(hit["sort"][0])
        act["sesiones_semana"] = [s["_source"]["inicio"] for s in hit["inner_hits"]["sesiones"]["hits"]["hits"]]
        actividades.append(act)
    return actividades


def consulta_prevision(desde, hasta):
    """Previsión de AEMET de los días de la semana, indexada por fecha."""
    datos = buscar("prevision", {"size": 20, "query": {"range": {"fecha": {"gte": desde[:10], "lte": hasta[:10]}}}})
    return {h["_source"]["fecha"]: h["_source"] for h in datos["hits"]["hits"]}


def centro_mas_cercano(lat, lon):
    """El centro de mayores más cercano a la casa (índice 'lugares')."""
    datos = buscar("lugares", {
        "size": 1,
        "query": {"term": {"tipo": "centro_mayores"}},
        "sort": [{"_geo_distance": {"ubicacion": {"lat": lat, "lon": lon}, "order": "asc", "unit": "m"}}],
    })
    hit = datos["hits"]["hits"][0]
    return {**hit["_source"], "distancia_m": round(hit["sort"][0])}


def prob_lluvia_sesion(prevision_dia, hora):
    """C3: probabilidad de lluvia de la franja de la sesión (mañana/tarde) o, si no hay franjas, del día."""
    if not prevision_dia:
        return None
    franja = prevision_dia["prob_lluvia_manana"] if hora < "12:00" else prevision_dia["prob_lluvia_tarde"]
    return franja if franja is not None else prevision_dia["prob_lluvia"]


def componer_plan(actividades, prevision, fechas):
    """C3 + C4 sobre las candidatas de C1. Devuelve el plan día a día.
    Cada día se rellena en dos pasadas: la primera respeta el límite por categoría (variedad);
    la segunda, solo si faltan huecos, lo ignora. La variedad es una preferencia, no debe dejar días vacíos."""
    # Prioridad: dirigidas antes que aptas; dentro de cada nivel, más cerca primero
    candidatas = sorted(actividades, key=lambda a: (a["nivel_mayores"] != "dirigida", a["distancia_m"]))
    usadas, por_categoria = set(), Counter()
    plan = []

    for fecha in fechas:
        prev = prevision.get(fecha)
        elegidas, lugares_del_dia, descartadas_lluvia = [], set(), set()

        for respetar_categoria in (True, False):          # pasada 1 con límite, pasada 2 sin él
            for act in candidatas:
                if len(elegidas) == MAX_POR_DIA:
                    break
                sesiones_dia = [s for s in act["sesiones_semana"] if s.startswith(fecha)]
                if not sesiones_dia or act["id"] in usadas:
                    continue
                inicio = sesiones_dia[0]
                hora = inicio[11:16]
                prob = prob_lluvia_sesion(prev, hora)
                if not act["interior"] and prob is not None and prob >= UMBRAL_LLUVIA:   # C3
                    descartadas_lluvia.add(act["id"])
                    continue
                if respetar_categoria and por_categoria[act["categoria"]] >= MAX_POR_CATEGORIA:  # C4
                    continue
                if act["lugar_id"] in lugares_del_dia:                                   # C4: lugares distintos
                    continue
                usadas.add(act["id"])
                por_categoria[act["categoria"]] += 1
                lugares_del_dia.add(act["lugar_id"])
                elegidas.append({"hora": hora, "inicio": inicio, "lluvia_franja": prob, **act})

        elegidas.sort(key=lambda a: a["hora"])
        plan.append({"fecha": fecha, "prevision": prev, "actividades": elegidas,
                     "descartadas_lluvia": len(descartadas_lluvia)})
    return plan


def main():
    ahora = datetime.now().replace(microsecond=0)
    desde, hasta = ahora.isoformat(), (ahora + timedelta(days=DIAS)).isoformat()
    fechas = [(ahora + timedelta(days=i)).date().isoformat() for i in range(DIAS)]

    actividades = consulta_c1(CASA["lat"], CASA["lon"], RADIO_KM, desde, hasta)
    prevision = consulta_prevision(desde, hasta)
    centro = centro_mas_cercano(CASA["lat"], CASA["lon"])
    plan = componer_plan(actividades, prevision, fechas)

    print(f"PLAN SEMANAL para '{CASA['nombre']}' ({len(actividades)} actividades candidatas a menos de {RADIO_KM} km)")
    print(f"Tu centro de mayores: {centro['nombre']} ({centro['distancia_m']} m)")
    print(f"   Horario: {centro['horario']}")
    print(f"   Cómo llegar: {centro['transporte'] or 'consultar en la web municipal'}\n")

    for dia in plan:
        p = dia["prevision"]
        tiempo = f"{p['cielo']}, {p['tmin']}-{p['tmax']} °C, lluvia {p['prob_lluvia']} %" if p else "sin previsión"
        print(f"{dia['fecha']}  ({tiempo})")
        for a in dia["actividades"]:
            sitio = "interior" if a["interior"] else "aire libre"
            marca = " [para mayores]" if a["nivel_mayores"] == "dirigida" else ""
            print(f"   {a['hora']}  {a['titulo'][:45]}{marca}")
            print(f"          {a['lugar_nombre'][:40]} · {a['distancia_m']} m · {sitio} · {a['categoria']}")
        if dia["descartadas_lluvia"]:
            print(f"   ({dia['descartadas_lluvia']} actividades al aire libre descartadas por lluvia)")
        if len(dia["actividades"]) < MAX_POR_DIA:
            print(f"   + Tu centro de mayores {centro['nombre']} está abierto: {centro['horario']}")
        print()

    # Guardar el plan para la visualización V1
    Path("v1").mkdir(exist_ok=True)
    salida = {"generado": ahora.isoformat(), "casa": CASA, "radio_km": RADIO_KM,
              "centro": centro, "dias": plan,
              "candidatas": [{"titulo": a["titulo"], "ubicacion": a["ubicacion"]} for a in actividades]}
    Path("v1/plan.json").write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.copy("datos/integrados/distritos_limites.geojson", "v1/distritos_limites.geojson")
    print("Plan guardado en v1/plan.json")


if __name__ == "__main__":
    main()