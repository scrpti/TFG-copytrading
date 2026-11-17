import os 
import json
import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb
from pathlib import Path


load_dotenv()

def conectar():
    return psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
    )

SQL_TRADERS = """
    INSERT INTO traders (cid, username, primera_vez_visto, ultima_vez_visto)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (cid) DO UPDATE SET
        username = EXCLUDED.username,
        primera_vez_visto = LEAST(traders.primera_vez_visto, EXCLUDED.primera_vez_visto),
        ultima_vez_visto = GREATEST(traders.ultima_vez_visto, EXCLUDED.ultima_vez_visto)
"""

SQL_SNAPSHOTS = """
    INSERT INTO snapshots_ranking (fecha, cid, rentabilidad, riesgo, copiadores, aum, datos)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (cid, fecha) DO UPDATE SET
        rentabilidad = EXCLUDED.rentabilidad,
        riesgo = EXCLUDED.riesgo,
        copiadores = EXCLUDED.copiadores,
        aum = EXCLUDED.aum,
        datos = EXCLUDED.datos
"""

SQL_SERIES = """
    INSERT INTO rendimientos_diarios (cid, fecha, rentabilidad)
    VALUES (%s, %s, %s)
    ON CONFLICT (cid, fecha) DO UPDATE SET
        rentabilidad = EXCLUDED.rentabilidad
"""

def cargar_traders(conexion, traders, fecha):
    filas = []
    for trader in traders:
        filas.append((trader["cid"], trader["username"], fecha, fecha))
    with conexion.cursor() as cursor:
        cursor.executemany(SQL_TRADERS, filas)

def cargar_snapshots(conexion, traders, fecha):
    filas = []
    for trader in traders:
        filas.append((
            fecha, 
            trader["cid"],
            trader.get("gain"),
            trader.get("riskScore"),
            trader.get("copiers"),
            trader.get("aumValue"),
            Jsonb(trader),
        ))

    with conexion.cursor() as cursor:
        cursor.executemany(SQL_SNAPSHOTS, filas)

def cargar_series(conexion, series, traders):
    cid_por_usuario = {t["username"]: t["cid"] for t in traders}
    filas = []
    for username, serie in series.items():
        cid = cid_por_usuario[username]
        for dia in serie:
            filas.append((cid, dia["date"], dia["gain"]))

    with conexion.cursor() as cursor:
        cursor.executemany(SQL_SERIES, filas)

def cargar_dia(conexion, carpeta):
    fecha = carpeta.name
    with open(carpeta / "ranking.json", encoding="utf-8") as f:
        ranking = json.load(f)
    with open(carpeta / "series.json", encoding="utf-8") as f:
        series = json.load(f)


    cargar_traders(conexion, ranking, fecha)
    cargar_snapshots(conexion, ranking, fecha)
    cargar_series(conexion, series, ranking)

if __name__ == "__main__":
    carpetas = sorted(Path("datos/crudo").iterdir())
    with conectar() as conexion:
        for carpeta in carpetas:
            print(f"Cargando {carpeta.name}...")
            cargar_dia(conexion, carpeta)
        fila = conexion.execute("SELECT count(*) FROM snapshots_ranking").fetchone()
        print("Snapshots en la base de datos:", fila[0])