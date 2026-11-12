import os 
import json
import psycopg
from dotenv import load_dotenv

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

def cargar_traders(conexion, traders, fecha):
    filas = []
    for trader in traders:
        filas.append((trader["cid"], trader["username"], fecha, fecha))
    with conexion.cursor() as cursor:
        cursor.executemany(SQL_TRADERS, filas)

if __name__ == "__main__":
    fecha = "2026-11-11"
    with open(f"datos/crudo/{fecha}/ranking.json", encoding="utf-8") as f:
        traders = json.load(f)

    with conectar() as conexion:
        cargar_traders(conexion, traders, fecha)
        fila = conexion.execute("SELECT count(*) FROM traders").fetchone()
        print("Traders en la base de datos:", fila[0])