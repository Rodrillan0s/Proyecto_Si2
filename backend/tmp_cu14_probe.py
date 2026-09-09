from pathlib import Path
import json
import os
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from app.config import Config
import psycopg2

print(f"host={Config.DB_HOST}")
print(f"port={Config.DB_PORT}")
print(f"database={Config.DB_NAME}")
print(f"configured_schema={Config.SCHEMA}")

try:
    conn = psycopg2.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        connect_timeout=10,
        options="-c default_transaction_read_only=on",
    )
    conn.autocommit = False
    with conn.cursor() as cur:
        cur.execute("SELECT current_database(), current_schema()")
        db, schema = cur.fetchone()
        print(f"current_database={db}")
        print(f"current_schema={schema}")
        cur.execute("SELECT has_schema_privilege(current_user, 'obras', 'USAGE')")
        print(f"obras_usage={cur.fetchone()[0]}")

        tables = ["t_empresa", "t_material", "t_materiales_almacen", "t_unidad_material"]
        for table in tables:
            cur.execute(
                """SELECT column_name, data_type, is_nullable, column_default
                   FROM information_schema.columns
                   WHERE table_schema='obras' AND table_name=%s
                   ORDER BY ordinal_position""",
                (table,),
            )
            cols = cur.fetchall()
            print(f"COLUMNS {table}=" + json.dumps(cols, default=str, ensure_ascii=False))
            if cols:
                cur.execute(f'SELECT COUNT(*) FROM obras."{table}"')
                print(f"COUNT {table}={cur.fetchone()[0]}")

        cur.execute("""SELECT column_name FROM information_schema.columns
                       WHERE table_schema='obras' AND table_name='t_empresa'
                       ORDER BY ordinal_position""")
        empresa_cols = [r[0] for r in cur.fetchall()]
        name_col = next((c for c in empresa_cols if c in ('nombre_empresa','nombre','razon_social')), None)
        if name_col:
            cur.execute(f'SELECT id_empresa, "{name_col}" FROM obras.t_empresa ORDER BY id_empresa')
            print("EMPRESAS=" + json.dumps(cur.fetchall(), default=str, ensure_ascii=False))

        cur.execute("""SELECT column_name FROM information_schema.columns
                       WHERE table_schema='obras' AND table_name='t_material'
                       ORDER BY ordinal_position""")
        material_cols = {r[0] for r in cur.fetchall()}
        requested = [c for c in ('id_material','nombre_material','precio','id_proveedor','id_empresa') if c in material_cols]
        if requested:
            cur.execute('SELECT ' + ','.join(f'"{c}"' for c in requested) + ' FROM obras.t_material ORDER BY id_material')
            print("MATERIALES_FIELDS=" + json.dumps(requested))
            print("MATERIALES=" + json.dumps(cur.fetchall(), default=str, ensure_ascii=False))

        cur.execute("""SELECT column_name FROM information_schema.columns
                       WHERE table_schema='obras' AND table_name='t_materiales_almacen'
                       ORDER BY ordinal_position""")
        almacen_cols = {r[0] for r in cur.fetchall()}
        requested = [c for c in ('id_lote','id_material','cantidad_inicial','cantidad_actual','precio_venta','fecha_ingreso') if c in almacen_cols]
        if requested:
            cur.execute('SELECT ' + ','.join(f'"{c}"' for c in requested) + ' FROM obras.t_materiales_almacen ORDER BY id_lote')
            print("LOTES_FIELDS=" + json.dumps(requested))
            print("LOTES=" + json.dumps(cur.fetchall(), default=str, ensure_ascii=False))

        checks = {
            "MATERIALES_USADOS_UNIDAD": "SELECT COUNT(DISTINCT id_material) FROM obras.t_unidad_material",
            "MATERIALES_SIN_LOTE": "SELECT COUNT(*) FROM obras.t_material m WHERE NOT EXISTS (SELECT 1 FROM obras.t_materiales_almacen a WHERE a.id_material=m.id_material)",
            "LOTES_HUERFANOS": "SELECT COUNT(*) FROM obras.t_materiales_almacen a WHERE NOT EXISTS (SELECT 1 FROM obras.t_material m WHERE m.id_material=a.id_material)",
            "MATERIALES_SIN_PROVEEDOR": "SELECT COUNT(*) FROM obras.t_material WHERE id_proveedor IS NULL",
        }
        for label, query in checks.items():
            try:
                cur.execute(query)
                print(f"{label}={cur.fetchone()[0]}")
            except Exception as exc:
                conn.rollback()
                cur.execute("SET TRANSACTION READ ONLY")
                print(f"{label}_ERROR={type(exc).__name__}: {exc}")

        cur.execute("""SELECT tc.table_name, tc.constraint_name, tc.constraint_type,
                              kcu.column_name, ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
                       FROM information_schema.table_constraints tc
                       LEFT JOIN information_schema.key_column_usage kcu
                         ON tc.constraint_catalog=kcu.constraint_catalog AND tc.constraint_schema=kcu.constraint_schema
                        AND tc.constraint_name=kcu.constraint_name
                       LEFT JOIN information_schema.constraint_column_usage ccu
                         ON tc.constraint_catalog=ccu.constraint_catalog AND tc.constraint_schema=ccu.constraint_schema
                        AND tc.constraint_name=ccu.constraint_name
                       WHERE tc.table_schema='obras'
                         AND tc.table_name IN ('t_material','t_materiales_almacen','t_unidad_material','t_proveedor','t_empresa')
                       ORDER BY tc.table_name, tc.constraint_type, tc.constraint_name, kcu.ordinal_position""")
        print("CONSTRAINTS=" + json.dumps(cur.fetchall(), default=str, ensure_ascii=False))

    conn.rollback()
    conn.close()
except Exception as exc:
    print(f"CONNECTION_ERROR={type(exc).__name__}: {exc}")
    raise SystemExit(2)
