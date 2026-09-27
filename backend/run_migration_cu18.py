"""Script para ejecutar la migración CU18 en la base de datos."""
import sys
sys.path.insert(0, '.')

from app.classes.postgres import PostgreSQL

SQL_FILE = 'database/migration_cu18_avances_obra.sql'

db = PostgreSQL()
db.create_connection()

try:
    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        sql = f.read()

    # Ejecutar todas las sentencias
    db.cur.execute(sql)
    db.conn.commit()
    print("[OK] Migracion CU18 ejecutada correctamente.")

    # Verificar que la tabla fue creada
    r = db.execute_query(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema='obras' AND table_name='t_avance_obra' ORDER BY ordinal_position;",
        fetchall=True
    )
    print("\nColumnas de t_avance_obra:")
    for col in r:
        print(f"  {col[0]}: {col[1]}")

    # Verificar permisos creados
    r2 = db.execute_query(
        "SELECT id_permiso, nombre_permiso FROM obras.t_permiso "
        "WHERE nombre_permiso IN ('Visualizar_avances', 'Registrar_avances');",
        fetchall=True
    )
    print("\nPermisos de avances:")
    for p in r2:
        print(f"  id={p[0]} nombre={p[1]}")

except Exception as e:
    print(f"[ERROR] Error al ejecutar la migracion: {e}")
    db.conn.rollback()
finally:
    db.close_connection()
