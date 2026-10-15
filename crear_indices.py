"""Paso 12: crear en Elasticsearch los índices del esquema unificado, con sus mappings."""
import sys

import requests

ES = "http://localhost:9200"
AJUSTES = {"number_of_shards": 3, "number_of_replicas": 1}

DISTRITO = {"properties": {"codigo": {"type": "keyword"}, "nombre": {"type": "keyword"}}}
UBICACION = {"type": "geo_point"}
ACCESIBILIDAD = {"properties": {"movilidad": {"type": "keyword"}, "apoyos": {"type": "keyword"},
                                "codigos": {"type": "keyword"}}}
PROCEDENCIA = {"properties": {
    "fuente": {"type": "keyword"}, "id_origen": {"type": "keyword"},
    "extraido": {"type": "date"}, "fecha_datos": {"type": "date"}, "elaborado": {"type": "date"},
}}
TEXTO = {"type": "text", "fields": {"exacto": {"type": "keyword", "ignore_above": 256}}}

MAPPINGS = {
    "actividades": {
        "id": {"type": "keyword"}, "titulo": TEXTO, "descripcion": {"type": "text"},
        "tipo_origen": {"type": "keyword"}, "categoria": {"type": "keyword"},
        "nivel_mayores": {"type": "keyword"}, "interior": {"type": "boolean"},
        "gratuita": {"type": "boolean"}, "precio": {"type": "keyword"},
        "hora_conocida": {"type": "boolean"},
        "sesiones": {"type": "nested", "properties": {"inicio": {"type": "date"}}},
        "lugar_nombre": TEXTO, "lugar_ref": {"type": "keyword"}, "lugar_id": {"type": "keyword"},
        "distrito": DISTRITO, "accesibilidad_lugar": ACCESIBILIDAD, "ubicacion": UBICACION,
        "url_info": {"type": "keyword", "index": False}, "procedencia": PROCEDENCIA,
    },
    "lugares": {
        "id": {"type": "keyword"}, "tipo": {"type": "keyword"}, "nombre": TEXTO,
        "direccion": {"type": "text"}, "codigo_postal": {"type": "keyword"}, "distrito": DISTRITO,
        "ubicacion": UBICACION, "horario": {"type": "text"}, "servicios": {"type": "text"},
        "transporte": {"type": "text"}, "accesibilidad": ACCESIBILIDAD,
        "url_info": {"type": "keyword", "index": False}, "procedencia": PROCEDENCIA,
    },
    "distritos": {
        "id": {"type": "keyword"}, "codigo": {"type": "keyword"}, "nombre": {"type": "keyword"},
        "poblacion_total": {"type": "integer"}, "poblacion_65_mas": {"type": "integer"},
        "poblacion_80_mas": {"type": "integer"}, "procedencia": PROCEDENCIA,
    },
    "prevision": {
        "id": {"type": "keyword"}, "fecha": {"type": "date"},
        "prob_lluvia": {"type": "integer"}, "prob_lluvia_manana": {"type": "integer"},
        "prob_lluvia_tarde": {"type": "integer"}, "cielo": {"type": "keyword"},
        "tmax": {"type": "integer"}, "tmin": {"type": "integer"}, "procedencia": PROCEDENCIA,
    },
}


def main():
    borrar = "--reset" in sys.argv  # python crear_indices.py --reset  -> borra y vuelve a crear
    for indice, campos in MAPPINGS.items():
        url = f"{ES}/{indice}"
        existe = requests.head(url).status_code == 200
        if existe and borrar:
            requests.delete(url).raise_for_status()
            print(f"[borrado] {indice}")
            existe = False
        if existe:
            print(f"[existe]  {indice} (usa --reset para recrearlo)")
            continue
        cuerpo = {"settings": AJUSTES, "mappings": {"dynamic": "strict", "properties": campos}}
        respuesta = requests.put(url, json=cuerpo)
        if respuesta.status_code >= 400:
            sys.exit(f"[error]   {indice}: {respuesta.text}")
        print(f"[creado]  {indice}")


if __name__ == "__main__":
    main()