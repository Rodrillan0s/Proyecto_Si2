from datetime import date
from getpass import getpass
import json
import os
from pathlib import Path
import sys

import jwt
import psycopg2
import requests

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT)); os.chdir(ROOT)
from app.config import Config

BASE = "http://127.0.0.1:5000"
identifier = input("Identificador: ").strip()
password = getpass("Password: ")
s = requests.Session()
login = s.post(BASE + "/api/auth/login", json={"ci": identifier, "password": password}, timeout=20)
print(f"LOGIN_HTTP={login.status_code}")
if login.status_code != 200:
    try: print("LOGIN_ERROR=" + json.dumps(login.json(), ensure_ascii=False))
    except Exception: print("LOGIN_ERROR=" + login.text[:500])
    raise SystemExit(2)
body = login.json(); token = body["token"]; user = body["usuario"]
s.headers["Authorization"] = "Bearer " + token
claims = jwt.decode(token, Config.TOKEN_KEY, algorithms=["HS256"])
print("LOGIN_USER=" + json.dumps({"username": claims.get("username"), "rol": claims.get("nombre_rol"), "id_empresa": claims.get("id_empresa"), "id_usuario": claims.get("nro_usuario")}, ensure_ascii=False))

results = {}
def req(label, method, path, expected, **kwargs):
    r = s.request(method, BASE + path, timeout=30, **kwargs)
    ok = r.status_code in expected
    results[label] = {"http": r.status_code, "ok": ok}
    print(f"{label}_HTTP={r.status_code}")
    if not ok:
        try: print(f"{label}_BODY=" + json.dumps(r.json(), ensure_ascii=False)[:1000])
        except Exception: print(f"{label}_BODY=" + r.text[:1000])
    return r

cats = req("CATEGORIAS", "GET", "/api/materiales/categorias", {200}).json()["data"]
units = req("UNIDADES", "GET", "/api/materiales/unidades-medida", {200}).json()["data"]
cat_id = cats[0]["id_categoria"]
unit_id = next((x["id_unidad_medida"] for x in units if x["nombre"] == "Unidad"), units[0]["id_unidad_medida"])
print(f"CAT_ID={cat_id} UNIT_ID={unit_id}")

base_payload = {
 "codigo":"TEST-CU14-001", "nombre_material":"Material prueba CU14",
 "descripcion":"Material temporal de validación CU14", "precio":50,
 "cantidad_inicial":100, "stock_minimo":20, "fecha_ingreso":date.today().isoformat(),
 "id_categoria":cat_id, "id_unidad_medida":unit_id,
 "caracteristicas":[{"nombre":"Marca","valor":"Prueba"},{"nombre":"Presentación","valor":"Unidad"}],
}
created=[]
r=req("HU45_CREATE", "POST", "/api/materiales", {201}, json=base_payload)
if r.status_code != 201: raise SystemExit(3)
material_id=r.json()["id_material"]; created.append(material_id)
print(f"MATERIAL_ID={material_id}")

validation_cases = {
 "DUPLICATE": (base_payload, {409}),
 "NEG_INITIAL": ({**base_payload,"codigo":"TEST-CU14-BAD-I","cantidad_inicial":-1}, {400}),
 "NEG_MIN": ({**base_payload,"codigo":"TEST-CU14-BAD-M","stock_minimo":-1}, {400}),
 "BAD_CATEGORY": ({**base_payload,"codigo":"TEST-CU14-BAD-C","id_categoria":2147483647}, {404}),
 "BAD_UNIT": ({**base_payload,"codigo":"TEST-CU14-BAD-U","id_unidad_medida":2147483647}, {404}),
}
for label,(payload,expected) in validation_cases.items(): req(label,"POST","/api/materiales",expected,json=payload)

for label,path in {
 "LIST":"/api/materiales", "SEARCH":"/api/materiales?q=TEST-CU14-001",
 "ACTIVE":"/api/materiales?estado=ACTIVO", "CATEGORY_FILTER":f"/api/materiales?id_categoria={cat_id}",
}.items():
    rr=req(label,"GET",path,{200}); data=rr.json()["data"]
    found=next((x for x in data if x["id_material"]==material_id),None)
    print(f"{label}_FOUND={bool(found)} PAGINATION="+json.dumps(rr.json().get("pagination")))
    if not found: results[label]["ok"]=False
detail=req("DETAIL","GET",f"/api/materiales/{material_id}", {200}).json()["data"]
print("DETAIL_CHECK="+json.dumps({"stock_actual":str(detail["stock_actual"]),"stock_minimo":str(detail["stock_minimo"]),"stock_bajo":detail["stock_bajo"],"estado":detail["estado"],"chars":len(detail["caracteristicas"])},ensure_ascii=False))

stock_payload={**base_payload,"codigo":"TEST-CU14-STOCK","nombre_material":"Material prueba stock bajo CU14","descripcion":"Material temporal stock bajo CU14","cantidad_inicial":5,"stock_minimo":10}
rs=req("STOCK_CREATE","POST","/api/materiales",{201},json=stock_payload)
stock_id=rs.json()["id_material"]; created.append(stock_id)
low=req("STOCK_FILTER","GET","/api/materiales?stock_bajo=true",{200}).json()["data"]
low_item=next((x for x in low if x["id_material"]==stock_id),None)
print("STOCK_LOW_CHECK="+json.dumps({"found":bool(low_item),"stock_actual":str(low_item["stock_actual"]) if low_item else None,"stock_minimo":str(low_item["stock_minimo"]) if low_item else None,"stock_bajo":low_item["stock_bajo"] if low_item else None}))
if not low_item: results["STOCK_FILTER"]["ok"]=False

update={k:v for k,v in base_payload.items() if k not in ("cantidad_inicial","fecha_ingreso")}
update.update({"nombre_material":"Material prueba CU14 modificado","descripcion":"Material temporal CU14 modificado","stock_minimo":25,"caracteristicas":[{"nombre":"Marca","valor":"Prueba modificada"},{"nombre":"Presentación","valor":"Bolsa"}]})
before=detail["updated_at"]
req("HU46_UPDATE","PUT",f"/api/materiales/{material_id}",{200},json=update)
after=req("DETAIL_UPDATED","GET",f"/api/materiales/{material_id}",{200}).json()["data"]
print("UPDATE_CHECK="+json.dumps({"name":after["nombre_material"],"stock_minimo":str(after["stock_minimo"]),"updated_changed":after["updated_at"]!=before,"chars":len(after["caracteristicas"])},ensure_ascii=False))
for field,value in (("cantidad_actual",1),("cantidad_inicial",1),("id_empresa",999),("id_material",999),("estado","INACTIVO")):
    req("PROTECTED_"+field.upper(),"PUT",f"/api/materiales/{material_id}",{400},json={**update,field:value})

req("DEACTIVATE","PATCH",f"/api/materiales/{material_id}/estado",{200},json={"estado":"INACTIVO"})
inactive=req("INACTIVE_FILTER","GET","/api/materiales?estado=INACTIVO",{200}).json()["data"]
active=req("ACTIVE_AFTER_DEACTIVATE","GET","/api/materiales?estado=ACTIVO",{200}).json()["data"]
print(f"DEACTIVATE_CHECK=inactive:{any(x['id_material']==material_id for x in inactive)},active:{any(x['id_material']==material_id for x in active)}")
req("REACTIVATE","PATCH",f"/api/materiales/{material_id}/estado",{200},json={"estado":"ACTIVO"})

conn=psycopg2.connect(host=Config.DB_HOST,port=Config.DB_PORT,dbname=Config.DB_NAME,user=Config.DB_USER,password=Config.DB_PASSWORD)
try:
 with conn.cursor() as cur:
  cur.execute("SELECT id_obra FROM obras.t_obra WHERE id_empresa=%s ORDER BY CASE WHEN estado_obra='ACTIVO' THEN 0 ELSE 1 END,id_obra LIMIT 1",(claims["id_empresa"],))
  obra=cur.fetchone()
 if obra:
  obra_id=obra[0]
  cu=req("CU12_ACTIVE","GET",f"/api/proyectos/{obra_id}/unidades/materiales-disponibles",{200})
  print("CU12_ACTIVE_BODY="+json.dumps(cu.json(),default=str,ensure_ascii=False)[:1500])
  req("CU12_DEACTIVATE","PATCH",f"/api/materiales/{material_id}/estado",{200},json={"estado":"INACTIVO"})
  cu2=req("CU12_INACTIVE","GET",f"/api/proyectos/{obra_id}/unidades/materiales-disponibles",{200})
  print("CU12_INACTIVE_BODY="+json.dumps(cu2.json(),default=str,ensure_ascii=False)[:1500])
  req("CU12_REACTIVATE","PATCH",f"/api/materiales/{material_id}/estado",{200},json={"estado":"ACTIVO"})
 else: print("CU12_NO_PROJECT")
 with conn.cursor() as cur:
  cur.execute("""SELECT m.id_material,m.codigo,m.estado,m.id_empresa,a.cantidad_inicial,a.cantidad_actual,a.stock_minimo,
                        (SELECT count(*) FROM obras.t_material_caracteristica c WHERE c.id_material=m.id_material)
                 FROM obras.t_material m JOIN obras.t_materiales_almacen a USING(id_material)
                 WHERE m.id_material IN (%s,%s) ORDER BY m.id_material""",(material_id,stock_id))
  print("DB_MATERIALS="+json.dumps(cur.fetchall(),default=str,ensure_ascii=False))
  cur.execute("""SELECT accion,id_usuario,fecha_accion FROM obras.t_bitacora WHERE modulo='MATERIALES'
                 AND descripcion LIKE ANY(ARRAY[%s,%s]) ORDER BY id_bitacora""",(f"%Material {material_id}%",f"%Material {stock_id}%"))
  logs=cur.fetchall(); print("BITACORA="+json.dumps(logs,default=str,ensure_ascii=False))
  cur.execute("SELECT count(*) FROM obras.t_material WHERE codigo LIKE 'TEST-CU14-BAD-%'")
  print(f"PARTIAL_BAD_ROWS={cur.fetchone()[0]}")
finally: conn.close()

# Estado final trazable: ambos materiales inactivos.
for mid in created:
    req("FINAL_INACTIVE_"+str(mid),"PATCH",f"/api/materiales/{mid}/estado",{200},json={"estado":"INACTIVO"})

unauth=requests.get(BASE+"/api/materiales",timeout=20)
print(f"UNAUTH_HTTP={unauth.status_code}")
print("RESULTS="+json.dumps(results,ensure_ascii=False))
