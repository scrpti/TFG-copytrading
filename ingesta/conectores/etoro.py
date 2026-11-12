import os
import uuid

import httpx
from dotenv import load_dotenv
import time
import json
from datetime import date

from pathlib import Path


#Cargar el env
load_dotenv()

URL_BASE = "https://public-api.etoro.com"

#---------------------------------------------
#           DEFINICION DE CABECERAS
#---------------------------------------------

def cabeceras(): 
    return {
        "x-api-key": os.environ["ETORO_API_KEY"],
        "x-user-key": os.environ["ETORO_USER_KEY"],
        "x-request-id": str(uuid.uuid4()),
    }

#---------------------------------------------
#        DESCARGA DE PAGINAS DEL RAKING
#---------------------------------------------

def descargar_pagina_ranking(pagina):
    url = URL_BASE + "/api/v2/portfolios/rankings"
    params = {
        "period": "OneYearAgo",
        "popularInvestor": "true",
        "pageSize": 100,
        "page": pagina,
        "sort": "username",
    }
    
    respuesta = get_con_intentos(url, params=params)
    respuesta.raise_for_status()
    return respuesta.json()

#---------------------------------------------
#        DESCARGA DEL RANKING COMPLETO
#---------------------------------------------

def descargar_ranking_completo():
    traders = []
    pagina = 1
    hay_mas = True

    while hay_mas:
        datos = descargar_pagina_ranking(pagina)
        traders.extend(datos["results"])
        hay_mas = datos["pagination"]["hasNext"]
        pagina += 1
        time.sleep(1)

    return traders

#---------------------------------------------
#      LIMPIAR TRADERS DE DATOS PERSONALES
#---------------------------------------------

CAMPOS_PERSONALES = ["fullName", "avatarUrl"]

def limpiar_trader(trader):
    limpio = dict(trader)
    for campo in CAMPOS_PERSONALES:
        limpio.pop(campo, None)
    return limpio

#---------------------------------------------
#           QUITAR TRADERS REPETIDOS 
#---------------------------------------------

def quitar_repetidos(traders):
    vistos = set()
    unicos = []

    for trader in traders:
        username = trader["username"]
        if username in vistos:
            continue
        vistos.add(username)
        unicos.append(trader)
    
    return unicos

#---------------------------------------------
#    DESCARGAR SERIE DIARIA DE UN TRADER
#---------------------------------------------

def descargar_serie_diaria(username):
    url = URL_BASE + f"/api/v2/portfolios/{username}/gain/daily"
    params = {"count": 1000}
    respuesta = get_con_intentos(url, params=params)
    if respuesta.status_code in (403,404):
        return None
    respuesta.raise_for_status()
    respuesta_json = respuesta.json()
    return respuesta_json["gains"]

#---------------------------------------------
#         REINTENTAR EN CASO DE 429
#---------------------------------------------

INTENTOS = 5

def get_con_intentos(url, params):
    for intento in range(INTENTOS):
        try:
            respuesta = httpx.get(url, params=params, headers=cabeceras(), timeout=30)
        except httpx.TransportError as e:
            espera = 5 * 2 ** intento
            print(f"Error de conexion ({e}), reintento en {espera} s")
            time.sleep(espera)
            continue

        if respuesta.status_code != 429 and respuesta.status_code < 500:
            return respuesta
        if respuesta.status_code == 429:
            espera = int(respuesta.headers.get("Retry-After", "60"))
        else: 
            espera = 5 * 2 ** intento
        print(f"Error {respuesta.status_code}, esperando {espera} s")
        time.sleep(espera)
    raise RuntimeError(f"No se pudo completar la petición a {url} tras {INTENTOS} intentos")

#---------------------------------------------
#  DESCARGAR TODAS LAS SERIES DE LOS TRADERS
#---------------------------------------------

def descargar_todas_las_series(traders):
    series = {}
    fallidos = []

    for i, trader in enumerate(traders, start=1):
        username = trader["username"]
        try:
            serie = descargar_serie_diaria(username)
            if serie is None:
                print(f"[{i}/{len(traders)}] {username}: oculto o no encontrado")
            else:
                series[username] = serie
                print(f"[{i}/{len(traders)}] {username}: {len(serie)} dias")

        except Exception as e:
            fallidos.append({"username": username, "error": str(e)})
            print(f"[{i}/{len(traders)}] {username}: ERROR {e}")
        time.sleep(1)
    
    return series, fallidos

#---------------------------------------------
#       GUARDAR DATOS EN UN FICHERO JSON
#---------------------------------------------

def guardar_json(datos, ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

#---------------------------------------------
#                 MAIN
#---------------------------------------------

def main():
    inicio = time.time()
    hoy = date.today().isoformat()
    carpeta = Path("datos") / "crudo" / hoy

    print("Descargando ranking...")
    traders = descargar_ranking_completo()
    traders = [limpiar_trader(t) for t in traders]
    traders = quitar_repetidos(traders)
    guardar_json(traders, carpeta / "ranking.json")

    print(f"Descargando series de {len(traders)} traders...")
    series, fallidos = descargar_todas_las_series(traders)
    guardar_json(series, carpeta / "series.json")

    resumen = {
        "fecha": hoy,
        "traders": len(traders),
        "series_descargadas": len(series),
        "fallidos": fallidos,
        "segundos": round(time.time() - inicio, 1),
    }

    guardar_json(resumen, carpeta / "resumen.json")
    print(f"Terminado: {resumen}")



if __name__ == "__main__":
    main()