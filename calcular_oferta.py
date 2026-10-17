"""Paso 20: consulta C5 - oferta para mayores por distrito, cruzando agenda, centros y padrón.
Calcula los indicadores con agregaciones de Elasticsearch y los guarda en el índice 'distritos'
para el mapa de coropletas de Kibana (V2). Escribe también datos/integrados/oferta_distritos.csv."""
import csv
from pathlib import Path

import requests

ES = "http://localhost:9200"


def contar_por_distrito(indice, filtro):
    """Agregación 'terms' por distrito.codigo: cada shard cuenta su parte y el coordinador las suma."""
    cuerpo = {"size": 0, "query": filtro,
              "aggs": {"por_distrito": {"terms": {"field": "distrito.codigo", "size": 30}}}}
    respuesta = requests.post(f"{ES}/{indice}/_search", json=cuerpo)
    respuesta.raise_for_status()
    return {b["key"]: b["doc_count"] for b in respuesta.json()["aggregations"]["por_distrito"]["buckets"]}


def main():
    actividades = contar_por_distrito("actividades", {"terms": {"nivel_mayores": ["dirigida", "apta"]}})
    centros = contar_por_distrito("lugares", {"term": {"tipo": "centro_mayores"}})

    distritos = requests.post(f"{ES}/distritos/_search", json={
        "size": 30, "_source": ["codigo", "nombre", "poblacion_total", "poblacion_65_mas"]}).json()["hits"]["hits"]

    filas = []
    for hit in distritos:
        d = hit["_source"]
        mayores = d["poblacion_65_mas"]
        indicadores = {
            "actividades_mayores": actividades.get(d["codigo"], 0),
            "centros_mayores": centros.get(d["codigo"], 0),
            "pct_65_mas": round(100 * mayores / d["poblacion_total"], 1),
            "actividades_por_1000_mayores": round(1000 * actividades.get(d["codigo"], 0) / mayores, 2),
            "centros_por_10000_mayores": round(10000 * centros.get(d["codigo"], 0) / mayores, 2),
        }
        # Actualización parcial: solo añade estos campos, el resto del documento no se toca
        requests.post(f"{ES}/distritos/_update/{hit['_id']}", json={"doc": indicadores}).raise_for_status()
        filas.append({"codigo": d["codigo"], "distrito": d["nombre"], "poblacion_65_mas": mayores, **indicadores})

    filas.sort(key=lambda f: f["actividades_por_1000_mayores"])
    destino = Path("datos/integrados/oferta_distritos.csv")
    with destino.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        escritor.writeheader()
        escritor.writerows(filas)

    print(f"{'Distrito':<22}{'65+':>9}{'% 65+':>7}{'Activ.':>8}{'/1.000':>8}{'Centros':>9}{'/10.000':>9}")
    for f in filas:
        print(f"{f['distrito']:<22}{f['poblacion_65_mas']:>9,}{f['pct_65_mas']:>6}%{f['actividades_mayores']:>8}"
              f"{f['actividades_por_1000_mayores']:>8}{f['centros_mayores']:>9}{f['centros_por_10000_mayores']:>9}")
    print(f"\nTotal: {sum(actividades.values())} actividades y {sum(centros.values())} centros con distrito asignado")
    print(f"Guardado en {destino} y en el índice 'distritos'")


if __name__ == "__main__":
    main()