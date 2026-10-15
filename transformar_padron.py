"""Paso 7: padrón (200076) -> documentos del índice 'distritos' (población por distrito)."""
import json
import re
from pathlib import Path

import pandas as pd

from distritos import DISTRITOS, distrito

ORIGEN = Path("datos/originales/padron_200076.csv")
DESTINO = Path("datos/integrados/distritos.ndjson")
COLUMNAS_PERSONAS = ["ESPANOLESHOMBRES", "ESPANOLESMUJERES", "EXTRANJEROSHOMBRES", "EXTRANJEROSMUJERES"]


def edad_numerica(texto):
    """'        81' -> 81; '100 y más' -> 100 (primer número que aparezca); sin número -> None."""
    encontrado = re.search(r"\d+", str(texto))
    return int(encontrado.group()) if encontrado else None


def main():
    df = pd.read_csv(ORIGEN, sep=";", encoding="utf-8", dtype=str)
    df.columns = [c.strip() for c in df.columns]

    # Comprobación: qué edades no son un número limpio
    no_numericas = df.loc[~df["COD_EDAD_INT"].str.strip().str.fullmatch(r"\d+", na=False), "COD_EDAD_INT"]
    print("Edades que no son un número limpio:", dict(no_numericas.fillna("(vacía)").str.strip().value_counts()))

    df["codigo"] = df["COD_DISTRITO"].apply(lambda c: distrito(c)["codigo"])
    df["edad"] = df["COD_EDAD_INT"].apply(edad_numerica)
    df["personas"] = df[COLUMNAS_PERSONAS].apply(pd.to_numeric).sum(axis=1)
    sin_edad = df.loc[df["edad"].isna(), "personas"].sum()
    print(f"Personas en filas sin edad interpretable: {sin_edad}")

    total = df.groupby("codigo")["personas"].sum()
    mayores_65 = df[df["edad"] >= 65].groupby("codigo")["personas"].sum()
    mayores_80 = df[df["edad"] >= 80].groupby("codigo")["personas"].sum()
    fecha_datos = df["FX_DATOS_INI"].str.strip().iloc[0]

    documentos = []
    for codigo, nombre in DISTRITOS.items():
        documentos.append({
            "id": f"dis_{codigo}",
            "codigo": codigo,
            "nombre": nombre,
            "poblacion_total": int(total.get(codigo, 0)),
            "poblacion_65_mas": int(mayores_65.get(codigo, 0)),
            "poblacion_80_mas": int(mayores_80.get(codigo, 0)),
            "procedencia": [{"fuente": "200076-padron", "fecha_datos": fecha_datos}],
        })

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    with DESTINO.open("w", encoding="utf-8") as f:
        for d in documentos:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    print(f"\nDistritos guardados en {DESTINO}: {len(documentos)} (padrón a {fecha_datos})")
    print(f"Total Madrid: {int(total.sum()):,} habitantes, {int(mayores_65.sum()):,} de 65 o más "
          f"({100 * mayores_65.sum() / total.sum():.1f} %)\n")
    print(f"{'Distrito':<22}{'Total':>10}{'65+':>10}{'% 65+':>8}{'80+':>9}")
    for d in documentos:
        pct = 100 * d["poblacion_65_mas"] / d["poblacion_total"]
        print(f"{d['nombre']:<22}{d['poblacion_total']:>10,}{d['poblacion_65_mas']:>10,}{pct:>7.1f}%{d['poblacion_80_mas']:>9,}")


if __name__ == "__main__":
    main()