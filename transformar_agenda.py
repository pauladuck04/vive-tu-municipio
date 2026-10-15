"""Paso 3: agenda (300107) -> documentos del índice 'actividades'."""
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from collections import Counter
from comunes import accesibilidad, id_catalogo
from distritos import distrito

ORIGEN = Path("datos/originales/agenda_300107.json")
DESTINO = Path("datos/integrados/actividades.ndjson")
VENTANA_DIAS = 30  # sesiones que se generan a partir de hoy

DIAS_SEMANA = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}

# Categoría del plan a partir de @type
CATEGORIAS = {
    "actividad_fisica": {"ActividadesDeportivas", "DanzaBaile", "CarrerasMaratones", "Ciclismo", "Golf"},
    "talleres_y_formacion": {"CursosTalleres", "Idiomas", "CapacitacionDigital"},
    "charlas_y_lectura": {"ConferenciasColoquios", "RecitalesPresentacionesActosLiterarios",
                          "ClubesLectura", "Literatura"},
    "exposiciones_y_visitas": {"Exposiciones", "ExcursionesItinerariosVisitas", "Historia",
                               "ItinerariosOtrasActividadesAmbientales"},
    "espectaculos": {"TeatroPerformance", "Musica", "CineActividadesAudiovisuales", "CircoMagia",
                     "JazzSoulFunkySwingReagge", "Flamenco", "CoroGospel", "CantautorFolkCountry",
                     "FolcloreEtnica", "LatinaEspanola", "Clasica", "Zarzuela", "RockPop",
                     "ComediaMonologo", "CineFiccion"},
    "fiestas_y_encuentros": {"Fiestas", "ActividadesCalleArteUrbano", "ComemoracionesHomenajes",
                             "Ferias", "ActosSolidarios", "1ciudad21distritos", "ConcursosCertamenes", "LGTBI"},
}
TIPOS_INFANTILES = {"CuentacuentosTiteresMarionetas", "Campamentos", "Skateboarding"}
TIPOS_EXTERIOR = {"ExcursionesItinerariosVisitas", "ItinerariosOtrasActividadesAmbientales",
                  "ActividadesCalleArteUrbano", "CarrerasMaratones", "Ciclismo", "Golf"}
PUBLICOS_NO_APTOS = {"Niños", "Familias", "Jovenes"}
LUGARES_EXTERIOR = ("parque", "jardin", "jardín", "plaza", "quinta", "dehesa", "huerto", "pinar")
DANZA_ESPECTACULO = ("actuación", "actuacion", "espectáculo", "espectaculo", "muestra", "festival",
                     "gala", "compañía", "compania", "ballet")


def tipo_de(r):
    return r.get("@type", "").rsplit("/", 1)[-1]


def categoria_de(tipo):
    for categoria, tipos in CATEGORIAS.items():
        if tipo in tipos:
            return categoria
    return "otros"  # incluye ProgramacionDestacadaAgendaCultura y los registros sin @type


TITULO_EXTERIOR = ("en la calle", "al aire libre", "paseo", "senderismo", "marcha nórdica", "parque")

def es_interior(tipo, lugar, titulo):
    """Exterior si el tipo lo es, si el lugar es un parque o una plaza,
    o si el título indica que se hace fuera (aunque se quede en un centro)."""
    if tipo in TIPOS_EXTERIOR:
        return False
    if any(p in lugar.lower() for p in LUGARES_EXTERIOR):
        return False
    return not any(p in titulo.lower() for p in TITULO_EXTERIOR)


def categoria_final(tipo, titulo):
    """DanzaBaile mezcla clases y actuaciones: las actuaciones van a espectáculos."""
    if tipo == "DanzaBaile" and any(p in titulo.lower() for p in DANZA_ESPECTACULO):
        return "espectaculos"
    return categoria_de(tipo)


def nivel_mayores(r, tipo):
    """dirigida / apta / no_apta (ver propuesta del paso 2)."""
    publicos = {p.strip() for p in r.get("audience", "").split(",") if p.strip()}
    lugar = r.get("event-location", "").lower()
    if "Mayores" in publicos or "centro municipal de mayores" in lugar:
        return "dirigida"
    if tipo in TIPOS_INFANTILES or (publicos and publicos <= PUBLICOS_NO_APTOS):
        return "no_apta"
    return "apta"


def leer_fecha(texto):
    """'2027-01-27 18:00:00.0' -> datetime."""
    return datetime.strptime(texto[:19], "%Y-%m-%d %H:%M:%S")


DIAS_EXCLUIDOS_NO_LEIDOS = []  # valores de excluded-days que no se han podido interpretar


def dias_excluidos(r):
    """'24/12/2026;25/12/2026;' -> {date(2026,12,24), date(2026,12,25)}.
    Algunos registros traen números sueltos ('11', '222') por errores de captura: se ignoran."""
    excluidos, raros = set(), []
    for trozo in r.get("excluded-days", "").split(";"):
        trozo = trozo.strip()
        if not trozo:
            continue
        try:
            excluidos.add(datetime.strptime(trozo, "%d/%m/%Y").date())
        except ValueError:
            raros.append(trozo)
    if raros:
        DIAS_EXCLUIDOS_NO_LEIDOS.append((r["id"], raros))
    return excluidos


def generar_sesiones(r, hoy):
    """Lista de inicios de sesión (ISO) entre hoy y hoy + VENTANA_DIAS."""
    inicio, fin = leer_fecha(r["dtstart"]), leer_fecha(r["dtend"])
    hora_conocida = bool(r.get("time")) or inicio.strftime("%H:%M") != "00:00"
    hora = r.get("time") or inicio.strftime("%H:%M")
    excluidos = dias_excluidos(r)
    if r.get("recurrence"):
        dias_validos = {DIAS_SEMANA[d] for d in r["recurrence"]["days"].split(",")}
    else:
        dias_validos = set(range(7))  # un solo día, o varios días seguidos sin recurrencia

    sesiones = []
    dia = max(inicio.date(), hoy)
    ultimo = min(fin.date(), hoy + timedelta(days=VENTANA_DIAS))
    while dia <= ultimo:
        if dia.weekday() in dias_validos and dia not in excluidos:
            sesiones.append({"inicio": f"{dia.isoformat()}T{hora}:00" if hora_conocida else dia.isoformat()})
        dia += timedelta(days=1)
    return sesiones


def transformar(registro, hoy, extraido):
    tipo = tipo_de(registro)
    loc = registro.get("location", {})
    distrito_uri = registro.get("address", {}).get("district", {}).get("@id", "")
    return {
        "id": f"act_{registro['id']}",
        "titulo": registro["title"],
        "descripcion": registro.get("description", ""),
        "tipo_origen": tipo,
        "categoria": categoria_final(tipo, registro["title"]),
        "nivel_mayores": nivel_mayores(registro, tipo),
        "interior": es_interior(tipo, registro.get("event-location", ""), registro["title"]),
        "gratuita": registro.get("free") == 1,
        "precio": registro.get("price", ""),
        "hora_conocida": bool(registro.get("time")) or registro["dtstart"][11:16] != "00:00",
        "sesiones": generar_sesiones(registro, hoy),
        "lugar_nombre": registro.get("event-location", ""),
        "lugar_ref": registro.get("relation", {}).get("@id", ""),
        "lugar_id": f"lug_{id_catalogo(registro.get('relation', {}).get('@id', ''))}"
                    if id_catalogo(registro.get("relation", {}).get("@id", "")) else None,
        "distrito": distrito(distrito_uri.rsplit("/", 1)[-1]),
        "accesibilidad_lugar": accesibilidad(registro.get("organization", {}).get("accesibility", "")),
        "ubicacion": {"type": "Point", "coordinates": [loc["longitude"], loc["latitude"]]} if loc else None,
        "url_info": registro.get("link", ""),
        "procedencia": [{"fuente": "300107-agenda-actividades", "id_origen": registro["id"],
                         "extraido": extraido}],
    }


def main():
    hoy = date.today()
    extraido = datetime.fromtimestamp(ORIGEN.stat().st_mtime).isoformat(timespec="seconds")
    with ORIGEN.open(encoding="utf-8") as f:
        registros = json.load(f)["@graph"]

    actividades = [transformar(r, hoy, extraido) for r in registros]
    validas = [a for a in actividades if a["ubicacion"] and a["sesiones"] and a["nivel_mayores"] != "no_apta"]

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    with DESTINO.open("w", encoding="utf-8") as f:
        for a in validas:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")

    # Estadísticas para comprobar que el resultado tiene sentido
    print(f"Registros leídos: {len(actividades)}")
    print(f"  sin ubicación: {sum(not a['ubicacion'] for a in actividades)}")
    print(f"  sin sesiones en los próximos {VENTANA_DIAS} días: {sum(not a['sesiones'] for a in actividades)}")
    print(f"  no aptas: {sum(a['nivel_mayores'] == 'no_apta' for a in actividades)}")
    print(f"Guardadas en {DESTINO}: {len(validas)}")
    print("  por nivel:", dict(Counter(a["nivel_mayores"] for a in validas)))
    print("  por categoría:", dict(Counter(a["categoria"] for a in validas).most_common()))
    print("  interior / exterior:", dict(Counter(a["interior"] for a in validas)))
    print("  con hora conocida:", sum(a["hora_conocida"] for a in validas))
    print("  sin distrito reconocido:", sum(not a["distrito"] for a in validas))
    print("  accesibilidad del lugar:", dict(Counter(a["accesibilidad_lugar"]["movilidad"] for a in validas)))
    semana = (hoy + timedelta(days=7)).isoformat()
    print("  con sesión en los próximos 7 días:",
          sum(any(s["inicio"][:10] <= semana for s in a["sesiones"]) for a in validas))
    print("\nEjemplo de actividad dirigida a mayores:")
    ejemplo = next((a for a in validas if a["nivel_mayores"] == "dirigida"), validas[0])
    print(json.dumps({**ejemplo, "sesiones": ejemplo["sesiones"][:3]}, indent=2, ensure_ascii=False))

    print("\nActividades dirigidas a mayores (revisar a mano):")
    for a in sorted((a for a in validas if a["nivel_mayores"] == "dirigida"), key=lambda a: a["sesiones"][0]["inicio"]):
        sitio = "interior" if a["interior"] else "EXTERIOR"
        print(f"  {a['sesiones'][0]['inicio'][:16]}  {a['categoria']:<22} {sitio:<9} {a['titulo'][:45]:<45} | {a['lugar_nombre'][:30]}")

    print(f"\nRegistros con excluded-days erróneos (ignorados): {len(DIAS_EXCLUIDOS_NO_LEIDOS)}")
    for id_origen, raros in DIAS_EXCLUIDOS_NO_LEIDOS:
        print(f"  {id_origen}: {raros}")


if __name__ == "__main__":
    main()