import os
import sys

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.classes.postgres import PostgreSQL

def run_migration():
    migration_path = os.path.join(os.path.dirname(__file__), 'database', 'migration_cu15_proveedores.sql')
    with open(migration_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    db = PostgreSQL()
    db.create_connection()
    try:
        print("Ejecutando migración...")
        db.cur.execute(sql)
        db.conn.commit()
        print("Migración completada con éxito.")
    except Exception as e:
        print(f"Error durante la migración: {e}")
        db.conn.rollback()
    finally:
        db.close_connection()

if __name__ == "__main__":
    run_migration()
