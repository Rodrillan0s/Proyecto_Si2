from app.classes.postgres import PostgreSQL
from app.config import Config
import json

def registrar_obra_sp(
    codigo: str, nombre: str, descripcion: str, id_tipo_obra: int, estado_obra: str,
    fecha_inicio, fecha_fin, id_empresa: int, moneda: str,
    ubicacion: str, zona: str, distrito: str, uv: str, manzana: str,
    latitud: float, longitud: float, id_supervisor: int, id_cliente: int,
    cotizacion_inicial: float, descripcion_cliente: str, observacion: str
):
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"SELECT {Config.SCHEMA}.sp_registrar_obra(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        params = (
            codigo, nombre, descripcion, id_tipo_obra, estado_obra, fecha_inicio, fecha_fin, id_empresa, moneda,
            ubicacion, zona, distrito, uv, manzana, latitud, longitud, id_supervisor, id_cliente,
            cotizacion_inicial, descripcion_cliente, observacion
        )
        resultado = db.execute_query(query, params, fetchone=True, commit=True)
        if resultado and resultado[0]:
            res = resultado[0]
            if isinstance(res, str):
                res = json.loads(res)
            return res
        return {"success": False, "error": "Error de conexión con la base de datos."}
    finally:
        db.close_connection()

def actualizar_obra_sp(
    id_obra: int, id_empresa: int, id_tipo_obra: int,
    fecha_inicio, fecha_fin, nombre: str, descripcion: str, moneda: str,
    ubicacion: str, zona: str, distrito: str, uv: str, manzana: str,
    latitud: float, longitud: float, id_supervisor: int, id_cliente: int,
    cotizacion_inicial: float, descripcion_cliente: str, observacion: str
):
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"SELECT {Config.SCHEMA}.sp_actualizar_obra(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        params = (
            id_obra, id_empresa, id_tipo_obra, fecha_inicio, fecha_fin, nombre, descripcion, moneda,
            ubicacion, zona, distrito, uv, manzana, latitud, longitud, id_supervisor, id_cliente,
            cotizacion_inicial, descripcion_cliente, observacion
        )
        resultado = db.execute_query(query, params, fetchone=True, commit=True)
        if resultado and resultado[0]:
            res = resultado[0]
            if isinstance(res, str):
                res = json.loads(res)
            return res
        return {"success": False, "error": "Error de conexión con la base de datos."}
    finally:
        db.close_connection()

def obtener_obra_detalle_sp(id_obra: int, id_empresa: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"SELECT {Config.SCHEMA}.sp_obtener_obra_detalle(%s, %s);"
        resultado = db.execute_query(query, (id_obra, id_empresa), fetchone=True)
        if resultado and resultado[0]:
            res = resultado[0]
            if isinstance(res, str):
                res = json.loads(res)
            return res
        return {"success": False, "error": "La obra no existe o no tiene permisos de acceso."}
    finally:
        db.close_connection()

def listar_obras_sp(id_empresa: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"SELECT {Config.SCHEMA}.sp_listar_obras(%s);"
        resultado = db.execute_query(query, (id_empresa,), fetchone=True)
        if resultado and resultado[0]:
            res = resultado[0]
            if isinstance(res, str):
                res = json.loads(res)
            return res
        return {"success": False, "error": "Error de conexión con la base de datos."}
    finally:
        db.close_connection()

def actualizar_estado_obra_sp(id_obra: int, id_empresa: int, nuevo_estado: str):
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"SELECT {Config.SCHEMA}.sp_actualizar_estado_obra(%s, %s, %s);"
        resultado = db.execute_query(query, (id_obra, id_empresa, nuevo_estado), fetchone=True, commit=True)
        if resultado and resultado[0]:
            res = resultado[0]
            if isinstance(res, str):
                res = json.loads(res)
            return res
        return {"success": False, "error": "Error de conexión con la base de datos."}
    finally:
        db.close_connection()

def asignar_responsable_sp(id_obra: int, id_usuario: int, id_empresa: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"SELECT {Config.SCHEMA}.sp_asignar_responsable_obra(%s, %s, %s);"
        resultado = db.execute_query(query, (id_obra, id_usuario, id_empresa), fetchone=True, commit=True)
        if resultado and resultado[0]:
            res = resultado[0]
            if isinstance(res, str):
                res = json.loads(res)
            return res
        return {"success": False, "error": "Error de conexión con la base de datos."}
    finally:
        db.close_connection()

def retirar_responsable_sp(id_obra: int, id_usuario: int, id_empresa: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"SELECT {Config.SCHEMA}.sp_retirar_responsable_obra(%s, %s, %s);"
        resultado = db.execute_query(query, (id_obra, id_usuario, id_empresa), fetchone=True, commit=True)
        if resultado and resultado[0]:
            res = resultado[0]
            if isinstance(res, str):
                res = json.loads(res)
            return res
        return {"success": False, "error": "Error de conexión con la base de datos."}
    finally:
        db.close_connection()

def obtener_tipos_obra():
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"SELECT id_tipo_obra, nombre_obra FROM {Config.SCHEMA}.t_tipo_obra ORDER BY id_tipo_obra;"
        resultados = db.execute_query(query, fetchall=True)
        tipos = []
        if resultados:
            for r in resultados:
                tipos.append({
                    "id_tipo_obra": r[0],
                    "nombre_obra": r[1]
                })
        return {"success": True, "data": tipos}
    finally:
        db.close_connection()
