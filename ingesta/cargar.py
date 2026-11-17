import os 
import json
import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

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
        ultima_vez_visto = EXCLUDED.ultima_vez_visto
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

if __name__ == "__main__":
    fecha = "2026-11-11"
    with open(f"datos/crudo/{fecha}/ranking.json", encoding="utf-8") as f:
        traders = json.load(f)
    with open(f"datos/crudo/{fecha}/series.json", encoding="utf-8") as f:
        series = json.load(f)

    with conectar() as conexion:
        cargar_traders(conexion, traders, fecha)
        cargar_snapshots(conexion, traders, fecha)
        cargar_series(conexion, series, traders)
        fila = conexion.execute("SELECT count(*) FROM rendimientos_diarios").fetchone()
        print("Días de rentabilidad:", fila[0])