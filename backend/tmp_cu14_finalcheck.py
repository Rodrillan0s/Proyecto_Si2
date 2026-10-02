from pathlib import Path
import json, os, sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT)); os.chdir(ROOT)
from app.config import Config
import psycopg2
conn=psycopg2.connect(host=Config.DB_HOST,port=Config.DB_PORT,dbname=Config.DB_NAME,user=Config.DB_USER,password=Config.DB_PASSWORD,options='-c default_transaction_read_only=on')
try:
 with conn.cursor() as cur:
  cur.execute("""SELECT m.id_material,m.codigo,m.nombre_material,m.estado,m.id_empresa,m.updated_at,
                        a.cantidad_inicial,a.cantidad_actual,a.stock_minimo,a.fecha_ingreso,
                        c.nombre,um.nombre,um.abreviatura
                 FROM obras.t_material m JOIN obras.t_materiales_almacen a USING(id_material)
                 JOIN obras.t_categoria_material c USING(id_categoria)
                 JOIN obras.t_unidad_medida um USING(id_unidad_medida)
                 WHERE m.codigo IN ('TEST-CU14-001','TEST-CU14-STOCK') ORDER BY m.codigo""")
  print('FINAL_MATERIALS='+json.dumps(cur.fetchall(),default=str,ensure_ascii=False))
  cur.execute("""SELECT m.codigo,c.nombre,c.valor FROM obras.t_material m
                 JOIN obras.t_material_caracteristica c USING(id_material)
                 WHERE m.codigo IN ('TEST-CU14-001','TEST-CU14-STOCK') ORDER BY m.codigo,c.nombre""")
  print('FINAL_CHARS='+json.dumps(cur.fetchall(),default=str,ensure_ascii=False))
  cur.execute("""SELECT b.accion,b.id_usuario,u.username,b.fecha_accion FROM obras.t_bitacora b
                 JOIN obras.t_usuario u USING(id_usuario) WHERE b.modulo='MATERIALES'
                 AND b.descripcion LIKE ANY(ARRAY['%Material 1 %','%Material 3 %']) ORDER BY b.id_bitacora""")
  print('FINAL_LOGS='+json.dumps(cur.fetchall(),default=str,ensure_ascii=False))
finally: conn.rollback(); conn.close()

from app import create_app
app=create_app(); schema=app.openapi()
print(f'APP_IMPORT_OK={len(app.routes)}')
print(f'OPENAPI_OK={len(schema.get("paths",{}))}')
print('CU14_OPENAPI='+json.dumps(sorted(p for p in schema['paths'] if p.startswith('/api/materiales'))))
