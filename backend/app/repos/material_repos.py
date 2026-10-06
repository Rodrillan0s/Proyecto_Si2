from app.classes.postgres import PostgreSQL
from psycopg2 import errors


class MaterialConflictError(Exception):
    pass


def _row_to_material(row):
    return {
        "id_material": row[0],
        "codigo": row[1],
        "nombre_material": row[2],
        "descripcion": row[3],
        "categoria": {
            "id_categoria": row[4],
            "nombre": row[5]
        },
        "unidad_medida": {
            "id_unidad_medida": row[6],
            "nombre": row[7],
            "abreviatura": row[8]
        },
        "precio": float(row[9]) if row[9] is not None else 0.0,
        "stock_actual": 0.0,
        "stock_minimo": 0.0,
        "stock_bajo": False,
        "estado": row[10],
        "id_empresa": row[11],
        "nombre_empresa": row[12],
        "id_material_base": row[13],
        "es_propio": bool(row[14]),
        "created_at": str(row[15]) if row[15] else None,
        "updated_at": str(row[16]) if row[16] else None
    }


def _row_to_material_base(row):
    return {
        "id_material_base": row[0],
        "codigo": row[1],
        "nombre_material": row[2],
        "descripcion": row[3],
        "categoria": {
            "id_categoria": row[4],
            "nombre": row[5]
        },
        "unidad_medida": {
            "id_unidad_medida": row[6],
            "nombre": row[7],
            "abreviatura": row[8]
        },
        "precio_referencial": float(row[9]) if row[9] is not None else None,
        "estado": row[10],
        "created_at": str(row[11]) if row[11] else None,
        "adoptado": bool(row[12]),
        "id_material_empresa": row[13],
        "precio_empresa": float(row[14]) if row[14] is not None else None
    }


def catalogo_activo(tabla):
    db = PostgreSQL()
    db.create_connection()
    try:
        if tabla == "categorias":
            sql = "SELECT id_categoria, nombre, descripcion FROM obras.t_categoria_material WHERE estado = 'ACTIVO' ORDER BY nombre"
            fields = ("id_categoria", "nombre", "descripcion")
        else:
            sql = "SELECT id_unidad_medida, nombre, abreviatura FROM obras.t_unidad_medida WHERE estado = 'ACTIVO' ORDER BY nombre"
            fields = ("id_unidad_medida", "nombre", "abreviatura")
        rows = db.execute_query(sql, fetchall=True) or []
        return [dict(zip(fields, r)) for r in rows]
    finally:
        db.close_connection()


def referencia_activa(tabla, id_value):
    db = PostgreSQL()
    db.create_connection()
    try:
        col = "id_categoria" if tabla == "t_categoria_material" else "id_unidad_medida"
        sql = f"SELECT 1 FROM obras.{tabla} WHERE {col} = %s AND estado = 'ACTIVO'"
        return bool(db.execute_query(sql, (id_value,), fetchone=True))
    finally:
        db.close_connection()


def crear_categoria(nombre, descripcion):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """INSERT INTO obras.t_categoria_material (nombre, descripcion, estado)
               VALUES (%s, %s, 'ACTIVO')
               RETURNING id_categoria, nombre, descripcion""",
            (nombre, descripcion),
            fetchone=True,
            commit=True
        )
        return {"id_categoria": row[0], "nombre": row[1], "descripcion": row[2]}
    except errors.UniqueViolation as exc:
        raise MaterialConflictError("Ya existe una categoría con ese nombre.") from exc
    finally:
        db.close_connection()


def crear(id_empresa, data):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = """
            SELECT obras.fn_registrar_material(
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            );
        """
        params = (
            id_empresa,
            data["codigo"],
            data["nombre_material"],
            data.get("descripcion"),
            data["id_categoria"],
            data["id_unidad_medida"],
            data.get("precio") or 0,
            data.get("id_material_base"),
            data.get("es_propio", True)
        )
        row = db.execute_query(sql, params, fetchone=True)
        material_id = row[0]

        for item in data.get("caracteristicas") or []:
            db.execute_query(
                "INSERT INTO obras.t_material_caracteristica (id_material, nombre, valor) VALUES (%s, %s, %s)",
                (material_id, item["nombre"], item["valor"])
            )

        db.conn.commit()
        return material_id
    except errors.RaiseException as exc:
        if db.conn:
            db.conn.rollback()
        raise MaterialConflictError(str(exc).replace("ERROR:  ", "").strip()) from exc
    except errors.UniqueViolation as exc:
        if db.conn:
            db.conn.rollback()
        raise MaterialConflictError("El código ya existe en su empresa.") from exc
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


def actualizar(id_empresa, id_material, data):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = """
            SELECT obras.fn_modificar_material(
                %s, %s, %s, %s, %s, %s, %s, %s
            );
        """
        params = (
            id_empresa,
            id_material,
            data["codigo"],
            data["nombre_material"],
            data.get("descripcion"),
            data["id_categoria"],
            data["id_unidad_medida"],
            data.get("precio")
        )
        row = db.execute_query(sql, params, fetchone=True)
        if not row or not row[0]:
            db.conn.rollback()
            return False

        db.execute_query("DELETE FROM obras.t_material_caracteristica WHERE id_material = %s", (id_material,))
        for item in data.get("caracteristicas") or []:
            db.execute_query(
                "INSERT INTO obras.t_material_caracteristica (id_material, nombre, valor) VALUES (%s, %s, %s)",
                (id_material, item["nombre"], item["valor"])
            )

        db.conn.commit()
        return True
    except errors.RaiseException as exc:
        if db.conn:
            db.conn.rollback()
        raise MaterialConflictError(str(exc).replace("ERROR:  ", "").strip()) from exc
    except errors.UniqueViolation as exc:
        if db.conn:
            db.conn.rollback()
        raise MaterialConflictError("El código ya existe en su empresa.") from exc
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


def obtener(id_empresa, id_material):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = "SELECT * FROM obras.fn_consultar_material(%s, %s);"
        row = db.execute_query(sql, (id_empresa, id_material), fetchone=True)
        if not row:
            return None
        data = _row_to_material(row)
        chars = db.execute_query(
            "SELECT id_caracteristica, nombre, valor FROM obras.t_material_caracteristica WHERE id_material = %s ORDER BY nombre",
            (id_material,),
            fetchall=True
        ) or []
        data["caracteristicas"] = [{"id_caracteristica": r[0], "nombre": r[1], "valor": r[2]} for r in chars]
        return data
    finally:
        db.close_connection()


def listar(id_empresa=None, q=None, id_categoria=None, estado=None, stock_bajo=None, page=1, limit=20):
    db = PostgreSQL()
    db.create_connection()
    try:
        offset = (page - 1) * limit
        sql = "SELECT * FROM obras.fn_listar_materiales_empresa(%s, %s, %s, %s, %s, %s);"
        params = (id_empresa, q, id_categoria, estado, limit, offset)
        rows = db.execute_query(sql, params, fetchall=True) or []
        if not rows:
            return [], 0
        total = rows[0][17]
        return [_row_to_material(r) for r in rows], total
    finally:
        db.close_connection()


def cambiar_estado(id_empresa, id_material, estado):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = "SELECT obras.fn_desactivar_material(%s, %s, %s);"
        row = db.execute_query(sql, (id_empresa, id_material, estado), fetchone=True, commit=True)
        return bool(row and row[0])
    except errors.RaiseException:
        if db.conn:
            db.conn.rollback()
        return False
    finally:
        db.close_connection()


def copiar_catalogo_base(id_empresa: int) -> int:
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = "SELECT obras.fn_copiar_catalogo_base_empresa(%s);"
        row = db.execute_query(sql, (id_empresa,), fetchone=True, commit=True)
        return row[0] if row else 0
    finally:
        db.close_connection()


def listar_catalogo_base(q: str = None, id_categoria: int = None, id_empresa: int = None, page: int = 1, limit: int = 100):
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
        join_param = [id_empresa]
    else:
        join_param = []

    db = PostgreSQL()
    db.create_connection()
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
        return [_row_to_material_base(r) for r in rows], total
    finally:
        db.close_connection()


def obtener_material_base(id_material_base: int):
    db = PostgreSQL()
    db.create_connection()
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
        return _row_to_material_base(row) if row else None
    finally:
        db.close_connection()


def adoptar_material_base(id_empresa: int, id_material_base: int, precio: float = None,
                          codigo_interno: str = None, id_proveedor: int = None,
                          stock_minimo: float = 0.0):
    db = PostgreSQL()
    db.create_connection()
    try:
        base = db.execute_query("""
            SELECT codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio_referencial
            FROM obras.t_material_base WHERE id_material_base = %s AND estado = 'ACTIVO';
        """, (id_material_base,), fetchone=True)

        if not base:
            return {"success": False, "error": "El material base no existe o está inactivo."}

        cod_base, nombre, desc, id_cat, id_um, precio_ref = base
        codigo_final = (codigo_interno or cod_base).strip()
        precio_final = float(precio if precio is not None else (precio_ref or 0.0))

        existente = db.execute_query("""
            SELECT id_material FROM obras.t_material
            WHERE id_empresa = %s AND id_material_base = %s;
        """, (id_empresa, id_material_base), fetchone=True)

        if existente:
            return {"success": False, "error": "Este material base ya ha sido adoptado en su empresa.", "id_material": existente[0]}

        data = {
            "codigo": codigo_final,
            "nombre_material": nombre,
            "descripcion": desc,
            "id_categoria": id_cat,
            "id_unidad_medida": id_um,
            "precio": precio_final,
            "id_material_base": id_material_base,
            "es_propio": False
        }

        nuevo_id = crear(id_empresa, data)
        return {
            "success": True,
            "id_material": nuevo_id,
            "codigo": codigo_final,
            "nombre_material": nombre,
            "precio": precio_final
        }
    except MaterialConflictError as exc:
        return {"success": False, "error": str(exc)}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        db.close_connection()
