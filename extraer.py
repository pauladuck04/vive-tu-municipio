"""Extracción: descarga las fuentes y las guarda tal cual en datos/originales/."""
from pathlib import Path

import requests

import json
import os

FUENTES = {
    "agenda_300107.json": "https://datos.madrid.es/dataset/300107-0-agenda-actividades-eventos/resource/"
                          "300107-5-agenda-actividades-eventos-json/download/300107-5-agenda-actividades-eventos-json.json",
    "centros_200337.json": "https://datos.madrid.es/dataset/200337-0-centros-mayores/resource/"
                           "200337-1-centros-mayores-json/download/200337-1-centros-mayores-json.json",
    "padron_200076.csv": "https://datos.madrid.es/dataset/200076-0-padron/resource/"
                         "200076-2-padron-csv/download/200076-2-padron-csv.csv",
}

carpeta = Path("datos/originales")
carpeta.mkdir(parents=True, exist_ok=True)

for fichero, url in FUENTES.items():
    try:
        respuesta = requests.get(url, timeout=120)
        respuesta.raise_for_status()
        (carpeta / fichero).write_bytes(respuesta.content)
        print(f"[ok]    {fichero}: {len(respuesta.content) / 1024:.0f} KB")
    except requests.RequestException as error:
        # Si una fuente falla, se avisa y se sigue con las demás
        print(f"[error] {fichero}: {error}")

import json
import os

# --- Servicio externo: AEMET OpenData (predicción diaria de Madrid, código INE 28079) ---
URL_AEMET = "https://opendata.aemet.es/opendata/api/prediccion/especifica/municipio/diaria/28079"
clave = os.environ.get("AEMET_API_KEY")
if not clave:
    print("[error] prevision_aemet.json: falta la variable de entorno AEMET_API_KEY")
else:
    try:
        # Paso 1: AEMET devuelve una URL temporal con los datos
        paso1 = requests.get(URL_AEMET, headers={"api_key": clave}, timeout=60)
        paso1.raise_for_status()
        respuesta = paso1.json()
        print(f"        AEMET paso 1: estado {respuesta.get('estado')}, {respuesta.get('descripcion')}")
        if respuesta.get("estado") != 200:
            raise RuntimeError(respuesta)
        # Paso 2: descargar los datos de esa URL (vienen en ISO-8859-15)
        paso2 = requests.get(respuesta["datos"], timeout=60)
        paso2.raise_for_status()
        texto = paso2.content.decode("iso-8859-15")
        json.loads(texto)  # comprobar que es JSON válido antes de guardarlo
        (carpeta / "prevision_aemet.json").write_text(texto, encoding="utf-8")
        print(f"[ok]    prevision_aemet.json: {len(texto) / 1024:.0f} KB")
    except Exception as error:
        print(f"[error] prevision_aemet.json: {error}")