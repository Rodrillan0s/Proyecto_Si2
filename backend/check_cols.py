import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.classes.postgres import PostgreSQL

db = PostgreSQL()
db.create_connection()
print("=== FOREIGN KEYS TO OR FROM t_orden_trabajo ===")
query = """
SELECT
    tc.table_name, kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' 
  AND (tc.table_name='t_orden_trabajo' OR ccu.table_name='t_orden_trabajo' OR tc.table_name='t_unidad_construccion');
"""
print("=== RESUMEN OBRA 2 ===")
print(db.execute_query("SELECT obras.fn_resumen_avances_obra(2, NULL);", fetchone=True))

print("\n=== RESUMEN OBRA 3 ===")
print(db.execute_query("SELECT obras.fn_resumen_avances_obra(3, NULL);", fetchone=True))

print("\n=== LISTADO ORDENES OBRA 2 ===")
print(db.execute_query("SELECT obras.fn_listar_avances_obra(2, NULL, NULL);", fetchone=True))

db.close_connection()
