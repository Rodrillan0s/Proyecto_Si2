import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.classes.postgres import PostgreSQL

db = PostgreSQL()
db.create_connection()
rows = db.execute_query("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='obras' AND table_name='t_proveedor'", fetchall=True)
print("COLUMNS:")
for r in rows:
    print(r)
db.close_connection()
