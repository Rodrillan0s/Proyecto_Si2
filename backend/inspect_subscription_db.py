"""Inspección de solo lectura de los objetos relevantes para suscripciones."""
from pathlib import Path
import os
import psycopg2
from dotenv import load_dotenv


def connect(readonly=True):
    root = Path(__file__).resolve().parent
    for path in (root.parent / '.env', root / '.env'):
        if path.exists():
            load_dotenv(path, override=True)
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'), connect_timeout=10,
        options='-c statement_timeout=15000 -c lock_timeout=5000',
    )
    conn.set_session(readonly=readonly)
    return conn


if __name__ == '__main__':
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_user, to_regclass('obras.t_plan_suscripcion'), to_regclass('obras.t_suscripcion_empresa')")
            print('Destino y objetos:', cur.fetchall())
            cur.execute("SELECT table_name,column_name,data_type FROM information_schema.columns WHERE table_schema='obras' AND table_name IN ('t_empresa','t_usuario','t_rol') ORDER BY table_name,ordinal_position")
            print('Columnas:', cur.fetchall())
            cur.execute("SELECT e.id_empresa,e.nombre_empresa,count(u.id_usuario) FROM obras.t_empresa e LEFT JOIN obras.t_usuario u ON u.id_empresa=e.id_empresa GROUP BY e.id_empresa,e.nombre_empresa ORDER BY e.id_empresa")
            print('Empresas y cantidad de usuarios:', cur.fetchall())
            cur.execute("SELECT id_empresa,codigo_plan,estado,fecha_inicio,fecha_fin FROM obras.t_suscripcion_empresa ORDER BY id_empresa")
            print('Suscripciones actuales:', cur.fetchall())
            cur.execute("SELECT estado_obra,count(*) FROM obras.t_obra GROUP BY estado_obra")
            print('Estados obras:', cur.fetchall())
            cur.execute("SELECT pg_get_functiondef(oid) FROM pg_proc WHERE pronamespace='obras'::regnamespace AND proname IN ('sp_actualizar_estado_obra','sp_registrar_obra')")
            print('Rutinas obras:', cur.fetchall())
            cur.execute("SELECT tgrelid::regclass,tgname,pg_get_triggerdef(oid) FROM pg_trigger WHERE NOT tgisinternal AND tgrelid IN ('obras.t_usuario'::regclass,'obras.t_obra'::regclass,'obras.t_empresa'::regclass)")
            print('Triggers actuales:', cur.fetchall())
    finally:
        conn.rollback()
        conn.close()
