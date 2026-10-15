"""Paso 10: predicción diaria de AEMET -> documentos del índice 'prevision'."""
import json
from pathlib import Path

ORIGEN = Path("datos/originales/prevision_aemet.json")
DESTINO = Path("datos/integrados/prevision.ndjson")


def numero(valor):
    """AEMET usa "" cuando no hay dato; lo convertimos en None."""
    return valor if isinstance(valor, (int, float)) else None


def valor_periodo(lista, periodo):
    """Valor de un periodo concreto ('00-12'), o None si AEMET no lo da para ese día."""
    for p in lista:
        if p.get("periodo") == periodo:
            return numero(p.get("value"))
    return None


def cielo_del_dia(lista):
    """El de 00-24 si viene relleno; si no (periodos ya pasados), el último con descripción."""
    con_texto = [c for c in lista if c.get("descripcion")]
    dia_entero = [c for c in con_texto if c.get("periodo", "00-24") == "00-24"]
    elegido = dia_entero[0] if dia_entero else (con_texto[-1] if con_texto else {})
    return elegido.get("descripcion")


def transformar(dia, elaborado):
    lluvias = [numero(p.get("value")) for p in dia.get("probPrecipitacion", [])]
    lluvias = [v for v in lluvias if v is not None]
    fecha = dia["fecha"][:10]
    return {
        "id": f"prev_{fecha}",
        "fecha": fecha,
        "prob_lluvia": max(lluvias) if lluvias else None,
        "prob_lluvia_manana": valor_periodo(dia.get("probPrecipitacion", []), "00-12"),
        "prob_lluvia_tarde": valor_periodo(dia.get("probPrecipitacion", []), "12-24"),
        "cielo": cielo_del_dia(dia.get("estadoCielo", [])),
        "tmax": numero(dia.get("temperatura", {}).get("maxima")),
        "tmin": numero(dia.get("temperatura", {}).get("minima")),
        "procedencia": [{"fuente": "aemet-prediccion-diaria-28079", "elaborado": elaborado}],
    }


def main():
    with ORIGEN.open(encoding="utf-8") as f:
        raiz = json.load(f)[0]
    elaborado = raiz["elaborado"]
    prevision = [transformar(d, elaborado) for d in raiz["prediccion"]["dia"]]

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    with DESTINO.open("w", encoding="utf-8") as f:
        for p in prevision:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(f"Previsión guardada en {DESTINO}: {len(prevision)} días (elaborada {elaborado})\n")
    print(f"{'Fecha':<12}{'Lluvia':>7}{'Mañana':>8}{'Tarde':>7}  {'Temp.':<9}Cielo")
    for p in prevision:
        fmt = lambda v: "-" if v is None else f"{v}%"
        print(f"{p['fecha']:<12}{fmt(p['prob_lluvia']):>7}{fmt(p['prob_lluvia_manana']):>8}"
              f"{fmt(p['prob_lluvia_tarde']):>7}  {p['tmin']}-{p['tmax']} °C   {p['cielo']}")


if __name__ == "__main__":
    main()