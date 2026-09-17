from app.classes.postgres import PostgreSQL
from psycopg2 import errors


class MaterialConflictError(Exception):
    pass


def _material(row):
    fields = (
        "id_material", "codigo", "nombre_material", "descripcion", "id_categoria",
        "categoria_nombre", "id_unidad_medida", "unidad_nombre", "unidad_abreviatura",
        "precio", "stock_actual", "stock_minimo", "estado", "created_at", "updated_at",
        "id_empresa", "nombre_empresa", "id_material_base", "es_propio"
    )
    data = dict(zip(fields, row))
    data["categoria"] = {"id_categoria": data.pop("id_categoria"), "nombre": data.pop("categoria_nombre")}
    data["unidad_medida"] = {
        "id_unidad_medida": data.pop("id_unidad_medida"),
        "nombre": data.pop("unidad_nombre"),
        "abreviatura": data.pop("unidad_abreviatura")
    }
    data["stock_bajo"] = data["stock_actual"] <= data["stock_minimo"]
    return data


def _material_base(row):
    fields = (
        "id_material_base", "codigo", "nombre_material", "descripcion",
        "id_categoria", "categoria_nombre", "id_unidad_medida", "unidad_nombre",
        "unidad_abreviatura", "precio_referencial", "estado", "created_at",
        "adoptado", "id_material_empresa", "precio_empresa"
    )
    data = dict(zip(fields, row))
    data["categoria"] = {"id_categoria": data.pop("id_categoria"), "nombre": data.pop("categoria_nombre")}
    data["unidad_medida"] = {
        "id_unidad_medida": data.pop("id_unidad_medida"),
        "nombre": data.pop("unidad_nombre"),
        "abreviatura": data.pop("unidad_abreviatura")
    }
    return data


BASE = """
 SELECT m.id_material,m.codigo,m.nombre_material,m.descripcion,c.id_categoria,c.nombre,
        um.id_unidad_medida,um.nombre,um.abreviatura,m.precio,
        COALESCE(SUM(a.cantidad_actual),0) AS stock_actual,
        COALESCE(MAX(a.stock_minimo),0) AS stock_minimo,m.estado,m.created_at,m.updated_at,
        m.id_empresa,COALESCE(e.nombre_empresa, 'Sin Empresa') AS nombre_empresa,
        m.id_material_base, COALESCE(m.es_propio, FALSE) AS es_propio
 FROM obras.t_material m
 JOIN obras.t_categoria_material c ON c.id_categoria=m.id_categoria
 JOIN obras.t_unidad_medida um ON um.id_unidad_medida=m.id_unidad_medida
 LEFT JOIN obras.t_materiales_almacen a ON a.id_material=m.id_material
 LEFT JOIN obras.t_empresa e ON e.id_empresa=m.id_empresa
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


def crear_categoria(nombre, descripcion):
    db = PostgreSQL(); db.create_connection()
    try:
        row = db.execute_query(
            """INSERT INTO obras.t_categoria_material(nombre,descripcion,estado)
               VALUES(%s,%s,'ACTIVO') RETURNING id_categoria,nombre,descripcion""",
            (nombre, descripcion), fetchone=True, commit=True)
        return {"id_categoria": row[0], "nombre": row[1], "descripcion": row[2]}
    except errors.UniqueViolation as exc:
        raise MaterialConflictError("Ya existe una categoría con ese nombre.") from exc
    finally: db.close_connection()


def crear(id_empresa, data):
    db = PostgreSQL(); db.create_connection()
    try:
        row = db.execute_query("""INSERT INTO obras.t_material
            (codigo,nombre_material,descripcion,id_categoria,id_unidad_medida,precio,id_empresa,estado,id_material_base,es_propio)
            VALUES(%s,%s,%s,%s,%s,%s,%s,'ACTIVO',NULL,TRUE) RETURNING id_material""",
            (data["codigo"],data["nombre_material"],data.get("descripcion"),data["id_categoria"],
             data["id_unidad_medida"],data.get("precio") or 0,id_empresa), fetchone=True)
        material_id = row[0]
        for item in data.get("caracteristicas") or []:
            db.execute_query("INSERT INTO obras.t_material_caracteristica(id_material,nombre,valor) VALUES(%s,%s,%s)",
                             (material_id,item["nombre"],item["valor"]))
        db.execute_query("""INSERT INTO obras.t_materiales_almacen
            (id_material,cantidad_inicial,cantidad_actual,precio_venta,fecha_ingreso,stock_minimo)
            VALUES(%s,%s,%s,%s,%s,%s)""", (material_id,data.get("cantidad_inicial", 0),data.get("cantidad_inicial", 0),
            data.get("precio") or 0,data.get("fecha_ingreso"),data.get("stock_minimo", 0)))
        db.conn.commit()
        return material_id
    except errors.UniqueViolation as exc:
        db.conn.rollback(); raise MaterialConflictError("El código ya existe en su empresa.") from exc
    except Exception:
        if db.conn: db.conn.rollback()
        raise
    finally: db.close_connection()


def listar(id_empresa=None, q=None, id_categoria=None, estado=None, stock_bajo=None, page=1, limit=20):
    filtros = []
    params = []
    if id_empresa is not None:
        filtros.append("m.id_empresa=%s")
        params.append(id_empresa)
    if q: filtros.append("(m.codigo ILIKE %s OR m.nombre_material ILIKE %s)"); params += [f"%{q}%", f"%{q}%"]
    if id_categoria: filtros.append("m.id_categoria=%s"); params.append(id_categoria)
    if estado: filtros.append("m.estado=%s"); params.append(estado)
    having = ""
    if stock_bajo is not None:
        having = "HAVING (COALESCE(SUM(a.cantidad_actual),0) <= COALESCE(MAX(a.stock_minimo),0)) = %s"
        params.append(stock_bajo)
    group = " GROUP BY m.id_material,c.id_categoria,c.nombre,um.id_unidad_medida,um.nombre,um.abreviatura,m.id_empresa,e.nombre_empresa,m.id_material_base,m.es_propio "
    where_sql = (" WHERE " + " AND ".join(filtros)) if filtros else ""
    db = PostgreSQL(); db.create_connection()
    try:
        count_sql = "SELECT COUNT(*) FROM (" + BASE + where_sql + group + having + ") x"
        total = db.execute_query(count_sql, tuple(params), fetchone=True)[0]
        rows = db.execute_query(BASE + where_sql + group + having +
                                " ORDER BY m.nombre_material,m.id_material LIMIT %s OFFSET %s",
                                tuple(params + [limit,(page-1)*limit]), fetchall=True) or []
        return [_material(r) for r in rows], total
    finally: db.close_connection()


def obtener(id_empresa, id_material):
    db = PostgreSQL(); db.create_connection()
    try:
        filtros = ["m.id_material=%s"]
        params = [id_material]
        if id_empresa is not None:
            filtros.append("m.id_empresa=%s")
            params.append(id_empresa)
        where_sql = " WHERE " + " AND ".join(filtros)
        row = db.execute_query(BASE + where_sql +
            " GROUP BY m.id_material,c.id_categoria,c.nombre,um.id_unidad_medida,um.nombre,um.abreviatura,m.id_empresa,e.nombre_empresa,m.id_material_base,m.es_propio",
            tuple(params), fetchone=True)
        if not row: return None
        data = _material(row)
        chars = db.execute_query("SELECT id_caracteristica,nombre,valor FROM obras.t_material_caracteristica WHERE id_material=%s ORDER BY nombre", (id_material,), fetchall=True) or []
        data["caracteristicas"] = [{"id_caracteristica":r[0],"nombre":r[1],"valor":r[2]} for r in chars]
        return data
    finally: db.close_connection()


def actualizar(id_empresa, id_material, data):
    db = PostgreSQL(); db.create_connection()
    try:
        where_cond = "id_material=%s"
        params = [data["codigo"],data["nombre_material"],data.get("descripcion"),data["id_categoria"],data["id_unidad_medida"],data.get("precio"),id_material]
        if id_empresa is not None:
            where_cond += " AND id_empresa=%s"
            params.append(id_empresa)
        row = db.execute_query(f"""UPDATE obras.t_material SET codigo=%s,nombre_material=%s,descripcion=%s,
            id_categoria=%s,id_unidad_medida=%s,precio=COALESCE(%s,precio) WHERE {where_cond} RETURNING id_material""",
            tuple(params), fetchone=True)
        if not row: db.conn.rollback(); return False
        db.execute_query("DELETE FROM obras.t_material_caracteristica WHERE id_material=%s", (id_material,))
        for item in data.get("caracteristicas") or []:
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
        where_cond = "id_material=%s"
        params = [estado, id_material]
        if id_empresa is not None:
            where_cond += " AND id_empresa=%s"
            params.append(id_empresa)
        row = db.execute_query(f"UPDATE obras.t_material SET estado=%s WHERE {where_cond} RETURNING id_material",
                               tuple(params), fetchone=True, commit=True)
        return bool(row)
    finally: db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# CU14 REDEFINIDO: Catálogo Base de la Plataforma y Adopción por Empresa
# ─────────────────────────────────────────────────────────────────────────────

def listar_catalogo_base(q: str = None, id_categoria: int = None, id_empresa: int = None, page: int = 1, limit: int = 100):
    """
    Lista materiales del catálogo base maestro de la plataforma.
    Si se provee id_empresa, indica si cada material ya fue adoptado por la empresa.
    """
    condiciones = ["mb.estado = 'ACTIVO'"]
    params = []

    if q:
        condiciones.append("(mb.codigo ILIKE %s OR mb.nombre_material ILIKE %s OR mb.descripcion ILIKE %s)")
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

    if id_categoria:
        condiciones.append("mb.id_categoria = %s")
        params.append(id_categoria)

    where_sql = " WHERE " + " AND ".join(condiciones)

    empresa_join = ""
    empresa_fields = "FALSE AS adoptado, NULL::INT AS id_material_empresa, NULL::NUMERIC AS precio_empresa"
    if id_empresa is not None:
        empresa_join = "LEFT JOIN obras.t_material em ON em.id_material_base = mb.id_material_base AND em.id_empresa = %s"
        empresa_fields = "(em.id_material IS NOT NULL) AS adoptado, em.id_material AS id_material_empresa, em.precio AS precio_empresa"
        # El id_empresa va al principio para el join
        join_param = [id_empresa]
    else:
        join_param = []

    db = PostgreSQL(); db.create_connection()
    try:
        count_sql = f"SELECT COUNT(*) FROM obras.t_material_base mb {where_sql}"
        total = db.execute_query(count_sql, tuple(params), fetchone=True)[0]

        sql = f"""
            SELECT mb.id_material_base, mb.codigo, mb.nombre_material, mb.descripcion,
                   c.id_categoria, c.nombre AS categoria_nombre,
                   um.id_unidad_medida, um.nombre AS unidad_nombre, um.abreviatura AS unidad_abreviatura,
                   mb.precio_referencial, mb.estado, mb.created_at,
                   {empresa_fields}
            FROM obras.t_material_base mb
            JOIN obras.t_categoria_material c ON c.id_categoria = mb.id_categoria
            JOIN obras.t_unidad_medida um ON um.id_unidad_medida = mb.id_unidad_medida
            {empresa_join}
            {where_sql}
            ORDER BY c.nombre ASC, mb.nombre_material ASC
            LIMIT %s OFFSET %s;
        """
        full_params = join_param + params + [limit, (page - 1) * limit]
        rows = db.execute_query(sql, tuple(full_params), fetchall=True) or []
        return [_material_base(r) for r in rows], total
    finally:
        db.close_connection()


def obtener_material_base(id_material_base: int):
    db = PostgreSQL(); db.create_connection()
    try:
        sql = """
            SELECT mb.id_material_base, mb.codigo, mb.nombre_material, mb.descripcion,
                   c.id_categoria, c.nombre AS categoria_nombre,
                   um.id_unidad_medida, um.nombre AS unidad_nombre, um.abreviatura AS unidad_abreviatura,
                   mb.precio_referencial, mb.estado, mb.created_at,
                   FALSE AS adoptado, NULL::INT AS id_material_empresa, NULL::NUMERIC AS precio_empresa
            FROM obras.t_material_base mb
            JOIN obras.t_categoria_material c ON c.id_categoria = mb.id_categoria
            JOIN obras.t_unidad_medida um ON um.id_unidad_medida = mb.id_unidad_medida
            WHERE mb.id_material_base = %s;
        """
        row = db.execute_query(sql, (id_material_base,), fetchone=True)
        return _material_base(row) if row else None
    finally:
        db.close_connection()


def adoptar_material_base(id_empresa: int, id_material_base: int, precio: float = None,
                          codigo_interno: str = None, id_proveedor: int = None,
                          stock_minimo: float = 0.0):
    """
    Adopta un material del catálogo base hacia el catálogo de la empresa.
    """
    db = PostgreSQL(); db.create_connection()
    try:
        # 1. Obtener datos del material base
        base = db.execute_query("""
            SELECT codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio_referencial
            FROM obras.t_material_base WHERE id_material_base = %s AND estado = 'ACTIVO';
        """, (id_material_base,), fetchone=True)

        if not base:
            return {"success": False, "error": "El material base no existe o está inactivo."}

        cod_base, nombre, desc, id_cat, id_um, precio_ref = base

        # Usar código personalizado o el del material base
        codigo_final = (codigo_interno or cod_base).strip()
        precio_final = float(precio if precio is not None else (precio_ref or 0.0))

        # Verificar si la empresa ya adoptó este material base
        existente = db.execute_query("""
            SELECT id_material FROM obras.t_material
            WHERE id_empresa = %s AND id_material_base = %s;
        """, (id_empresa, id_material_base), fetchone=True)

        if existente:
            return {"success": False, "error": "Este material base ya ha sido adoptado en el catálogo de su empresa.", "id_material": existente[0]}

        # Insertar en catálogo de empresa t_material
        row = db.execute_query("""
            INSERT INTO obras.t_material (
                codigo, nombre_material, descripcion, id_categoria, id_unidad_medida,
                precio, id_empresa, id_proveedor, id_material_base, es_propio, estado
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE, 'ACTIVO')
            RETURNING id_material;
        """, (codigo_final, nombre, desc, id_cat, id_um, precio_final, id_empresa, id_proveedor, id_material_base),
        fetchone=True)

        nuevo_id = row[0]

        # Insertar en t_materiales_almacen con stock inicial 0
        db.execute_query("""
            INSERT INTO obras.t_materiales_almacen (
                id_material, cantidad_inicial, cantidad_actual, precio_venta, fecha_ingreso, stock_minimo
            ) VALUES (%s, 0, 0, %s, CURRENT_DATE, %s);
        """, (nuevo_id, precio_final, stock_minimo))

        db.conn.commit()
        return {
            "success": True,
            "id_material": nuevo_id,
            "codigo": codigo_final,
            "nombre_material": nombre,
            "precio": precio_final
        }
    except errors.UniqueViolation:
        if db.conn: db.conn.rollback()
        return {"success": False, "error": f"El código '{codigo_final}' ya existe en su empresa. Especifique un código interno diferente."}
    except Exception as e:
        if db.conn: db.conn.rollback()
        raise e
    finally:
        db.close_connection()
