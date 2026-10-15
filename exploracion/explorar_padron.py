"""Paso 6: ver formato, columnas y valores del padrón antes de agregarlo."""
from pathlib import Path

import pandas as pd

RUTA = Path("datos/originales/padron_200076.csv")

# 1. Las primeras líneas en bruto, para ver separador y codificación
crudo = RUTA.read_bytes()[:600]
for codificacion in ("utf-8", "latin-1"):
    try:
        print(f"Se lee como {codificacion}:\n{crudo.decode(codificacion)}\n")
        break
    except UnicodeDecodeError:
        print(f"No es {codificacion}")

# 2. Cargar el fichero completo como texto para no perder ceros a la izquierda
df = pd.read_csv(RUTA, sep=";", encoding=codificacion, dtype=str)
df.columns = [c.strip() for c in df.columns]
print(f"Filas: {len(df)}  Columnas: {list(df.columns)}\n")
print(df.head(3).to_string(), "\n")

# 3. Valores de las columnas que vamos a usar
for col in df.columns:
    if "DISTRITO" in col.upper():
        print(f"{col}: {sorted(df[col].str.strip().unique())[:25]}")
edad = next(c for c in df.columns if "EDAD" in c.upper())
edades = pd.to_numeric(df[edad].str.strip(), errors="coerce")
print(f"\n{edad}: de {edades.min()} a {edades.max()}, vacías: {edades.isna().sum()}")

# 4. ¿Hay celdas vacías en las columnas de personas?
for col in df.columns:
    if any(p in col.lower() for p in ("hombres", "mujeres")):
        vacias = (df[col].fillna("").str.strip() == "").sum()
        print(f"{col}: {vacias} celdas vacías")