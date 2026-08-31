from app.classes.postgres import PostgreSQL
from psycopg2 import errors


class MaterialConflictError(Exception):
    pass


def _material(row):
    fields = ("id_material", "codigo", "nombre_material", "descripcion", "id_categoria",
              "categoria_nombre", "id_unidad_medida", "unidad_nombre", "unidad_abreviatura",
              "precio", "stock_actual", "stock_minimo", "estado", "created_at", "updated_at")
    data = dict(zip(fields, row))
    data["categoria"] = {"id_categoria": data.pop("id_categoria"), "nombre": data.pop("categoria_nombre")}
    data["unidad_medida"] = {"id_unidad_medida": data.pop("id_unidad_medida"),
                              "nombre": data.pop("unidad_nombre"), "abreviatura": data.pop("unidad_abreviatura")}
    data["stock_bajo"] = data["stock_actual"] <= data["stock_minimo"]
    return data


BASE = """
 SELECT m.id_material,m.codigo,m.nombre_material,m.descripcion,c.id_categoria,c.nombre,
        um.id_unidad_medida,um.nombre,um.abreviatura,m.precio,
        COALESCE(SUM(a.cantidad_actual),0) AS stock_actual,
        COALESCE(MAX(a.stock_minimo),0) AS stock_minimo,m.estado,m.created_at,m.updated_at
 FROM obras.t_material m
 JOIN obras.t_categoria_material c ON c.id_categoria=m.id_categoria
 JOIN obras.t_unidad_medida um ON um.id_unidad_medida=m.id_unidad_medida
 LEFT JOIN obras.t_materiales_almacen a ON a.id_material=m.id_material
"""


def catalogo_activo(tabla):
    db = PostgreSQL(); db.create_connection()
    try:
        if tabla == "categorias":
            sql = "SELECT id_categoria,nombre,descripcion FROM obras.t_categoria_material WHERE estado='ACTIVO' ORDER BY nombre"
            fields = ("id_categoria", "nombre", "descripcion")
        else:
            sql = "SELECT id_unidad_medida,nombre,abreviatura FROM obras.t_unidad_medida WHERE estado='ACTIVO' ORDER BY nombre"
            fields = ("id_unidad_medida", "nombre", "abreviatura")
        return [dict(zip(fields, r)) for r in (db.execute_query(sql, fetchall=True) or [])]
    finally: db.close_connection()


def referencia_activa(tabla, id_value):
    db = PostgreSQL(); db.create_connection()
    try:
        col = "id_categoria" if tabla == "t_categoria_material" else "id_unidad_medida"
        return bool(db.execute_query(f"SELECT 1 FROM obras.{tabla} WHERE {col}=%s AND estado='ACTIVO'", (id_value,), fetchone=True))
    finally: db.close_connection()


def crear(id_empresa, data):
    db = PostgreSQL(); db.create_connection()
    try:
        row = db.execute_query("""INSERT INTO obras.t_material
            (codigo,nombre_material,descripcion,id_categoria,id_unidad_medida,precio,id_empresa,estado)
            VALUES(%s,%s,%s,%s,%s,%s,%s,'ACTIVO') RETURNING id_material""",
            (data["codigo"],data["nombre_material"],data.get("descripcion"),data["id_categoria"],
             data["id_unidad_medida"],data.get("precio") or 0,id_empresa), fetchone=True)
        material_id = row[0]
        for item in data["caracteristicas"]:
            db.execute_query("INSERT INTO obras.t_material_caracteristica(id_material,nombre,valor) VALUES(%s,%s,%s)",
                             (material_id,item["nombre"],item["valor"]))
        db.execute_query("""INSERT INTO obras.t_materiales_almacen
            (id_material,cantidad_inicial,cantidad_actual,precio_venta,fecha_ingreso,stock_minimo)
            VALUES(%s,%s,%s,%s,%s,%s)""", (material_id,data["cantidad_inicial"],data["cantidad_inicial"],
            data.get("precio") or 0,data["fecha_ingreso"],data["stock_minimo"]))
        db.conn.commit()
        return material_id
    except errors.UniqueViolation as exc:
        db.conn.rollback(); raise MaterialConflictError("El código ya existe en su empresa.") from exc
    except Exception:
        if db.conn: db.conn.rollback()
        raise
    finally: db.close_connection()


def listar(id_empresa, q=None, id_categoria=None, estado=None, stock_bajo=None, page=1, limit=20):
    filtros = ["m.id_empresa=%s"]; params = [id_empresa]
    if q: filtros.append("(m.codigo ILIKE %s OR m.nombre_material ILIKE %s)"); params += [f"%{q}%", f"%{q}%"]
    if id_categoria: filtros.append("m.id_categoria=%s"); params.append(id_categoria)
    if estado: filtros.append("m.estado=%s"); params.append(estado)
    having = ""
    if stock_bajo is not None:
        having = "HAVING (COALESCE(SUM(a.cantidad_actual),0) <= COALESCE(MAX(a.stock_minimo),0)) = %s"
        params.append(stock_bajo)
    group = " GROUP BY m.id_material,c.id_categoria,c.nombre,um.id_unidad_medida,um.nombre,um.abreviatura "
    db = PostgreSQL(); db.create_connection()
    try:
        count_sql = "SELECT COUNT(*) FROM (" + BASE + " WHERE " + " AND ".join(filtros) + group + having + ") x"
        total = db.execute_query(count_sql, tuple(params), fetchone=True)[0]
        rows = db.execute_query(BASE + " WHERE " + " AND ".join(filtros) + group + having +
                                " ORDER BY m.nombre_material,m.id_material LIMIT %s OFFSET %s",
                                tuple(params + [limit,(page-1)*limit]), fetchall=True) or []
        return [_material(r) for r in rows], total
    finally: db.close_connection()


def obtener(id_empresa, id_material):
    db = PostgreSQL(); db.create_connection()
    try:
        row = db.execute_query(BASE + " WHERE m.id_empresa=%s AND m.id_material=%s " +
            " GROUP BY m.id_material,c.id_categoria,c.nombre,um.id_unidad_medida,um.nombre,um.abreviatura",
            (id_empresa,id_material), fetchone=True)
        if not row: return None
        data = _material(row)
        chars = db.execute_query("SELECT id_caracteristica,nombre,valor FROM obras.t_material_caracteristica WHERE id_material=%s ORDER BY nombre", (id_material,), fetchall=True) or []
        data["caracteristicas"] = [{"id_caracteristica":r[0],"nombre":r[1],"valor":r[2]} for r in chars]
        return data
    finally: db.close_connection()


def actualizar(id_empresa, id_material, data):
    db = PostgreSQL(); db.create_connection()
    try:
        row = db.execute_query("""UPDATE obras.t_material SET codigo=%s,nombre_material=%s,descripcion=%s,
            id_categoria=%s,id_unidad_medida=%s,precio=COALESCE(%s,precio) WHERE id_material=%s AND id_empresa=%s RETURNING id_material""",
            (data["codigo"],data["nombre_material"],data.get("descripcion"),data["id_categoria"],data["id_unidad_medida"],
             data.get("precio"),id_material,id_empresa), fetchone=True)
        if not row: db.conn.rollback(); return False
        db.execute_query("DELETE FROM obras.t_material_caracteristica WHERE id_material=%s", (id_material,))
        for item in data["caracteristicas"]:
            db.execute_query("INSERT INTO obras.t_material_caracteristica(id_material,nombre,valor) VALUES(%s,%s,%s)", (id_material,item["nombre"],item["valor"]))
        db.execute_query("UPDATE obras.t_materiales_almacen SET stock_minimo=%s WHERE id_material=%s", (data["stock_minimo"],id_material))
        db.conn.commit(); return True
    except errors.UniqueViolation as exc:
        db.conn.rollback(); raise MaterialConflictError("El código ya existe en su empresa.") from exc
    except Exception:
        if db.conn: db.conn.rollback()
        raise
    finally: db.close_connection()


def cambiar_estado(id_empresa, id_material, estado):
    db = PostgreSQL(); db.create_connection()
    try:
        row = db.execute_query("UPDATE obras.t_material SET estado=%s WHERE id_material=%s AND id_empresa=%s RETURNING id_material",
                               (estado,id_material,id_empresa), fetchone=True, commit=True)
        return bool(row)
    finally: db.close_connection()
