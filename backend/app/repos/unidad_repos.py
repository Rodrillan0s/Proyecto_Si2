from app.classes.postgres import PostgreSQL
import json


def _json_result(row, default_error: str) -> dict:
    if row and row[0]:
        return row[0] if isinstance(row[0], dict) else json.loads(row[0])
    return {"success": False, "error": default_error}


def obtener_empresa_proyecto(id_obra: int, id_empresa: int = None):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            "SELECT id_empresa FROM obras.t_obra WHERE id_obra=%s AND (id_empresa=%s OR %s IS NULL)",
            (id_obra, id_empresa, id_empresa), fetchone=True
        )
        return row[0] if row else None
    finally:
        db.close_connection()


def registrar_unidad_fn(id_obra, id_empresa, id_usuario, data: dict) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        query = """
            SELECT obras.fn_registrar_unidad_construccion(
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::json, %s::json
            );
        """
        params = (
            id_obra, id_empresa, id_usuario, data.get("id_estructura"), data.get("id_padre"),
            data.get("nombre"), data.get("tipo_estructura"), data.get("descripcion"),
            data.get("tipo_unidad"), data.get("superficie"), data.get("cantidad_plantas"),
            data.get("estado"), data.get("id_modelo"),
            json.dumps(data.get("ambientes") or []), json.dumps(data.get("caracteristicas") or [])
        )
        return _json_result(
            db.execute_query(query, params, fetchone=True, commit=True),
            "No se pudo registrar la unidad."
        )
    finally:
        db.close_connection()


def listar_unidades(id_obra: int, id_empresa: int = None) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        query = """
            SELECT u.id_unidad, u.id_estructura, e.id_padre, u.codigo,
                   e.nombre, e.tipo AS tipo_estructura, e.descripcion,
                   u.tipo_unidad, u.superficie, u.cantidad_plantas, u.estado,
                   u.id_modelo, m.nombre AS modelo_nombre, u.created_at, u.updated_at
            FROM obras.t_unidad_construccion u
            INNER JOIN obras.t_estructura_obra e ON e.id_estructura = u.id_estructura
            INNER JOIN obras.t_obra o ON o.id_obra = e.id_obra
            LEFT JOIN obras.t_modelo_unidad m ON m.id_modelo = u.id_modelo
            WHERE o.id_obra = %s AND (o.id_empresa = %s OR %s IS NULL)
            ORDER BY e.orden, u.id_unidad;
        """
        rows = db.execute_query(query, (id_obra, id_empresa, id_empresa), fetchall=True) or []
        fields = (
            "id_unidad", "id_estructura", "id_padre", "codigo", "nombre",
            "tipo_estructura", "descripcion", "tipo_unidad", "superficie",
            "cantidad_plantas", "estado", "id_modelo", "modelo_nombre",
            "created_at", "updated_at"
        )
        return {"success": True, "data": [dict(zip(fields, row)) for row in rows]}
    finally:
        db.close_connection()


def obtener_unidad_detalle(id_obra: int, id_unidad: int, id_empresa: int = None) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        query = """
            WITH RECURSIVE ruta AS (
                SELECT e.id_estructura, e.id_padre, e.nombre, 1 AS profundidad
                FROM obras.t_estructura_obra e
                JOIN obras.t_unidad_construccion u ON u.id_estructura = e.id_estructura
                WHERE u.id_unidad = %s
                UNION ALL
                SELECT p.id_estructura, p.id_padre, p.nombre, r.profundidad + 1
                FROM obras.t_estructura_obra p
                JOIN ruta r ON r.id_padre = p.id_estructura
            )
            SELECT u.id_unidad, u.id_estructura, e.id_padre, u.codigo, e.nombre,
                   e.tipo, e.descripcion, u.tipo_unidad, u.superficie,
                   u.cantidad_plantas, u.estado, u.id_modelo, m.nombre,
                   o.id_obra, o.nombre, o.codigo,
                   (SELECT string_agg(r.nombre, ' / ' ORDER BY r.profundidad DESC) FROM ruta r),
                   u.created_at, u.updated_at
            FROM obras.t_unidad_construccion u
            JOIN obras.t_estructura_obra e ON e.id_estructura = u.id_estructura
            JOIN obras.t_obra o ON o.id_obra = e.id_obra
            LEFT JOIN obras.t_modelo_unidad m ON m.id_modelo = u.id_modelo
            WHERE u.id_unidad = %s AND o.id_obra = %s
              AND (o.id_empresa = %s OR %s IS NULL);
        """
        row = db.execute_query(
            query, (id_unidad, id_unidad, id_obra, id_empresa, id_empresa), fetchone=True
        )
        if not row:
            return {"success": False, "error": "La unidad no existe o no pertenece a su empresa."}
        fields = (
            "id_unidad", "id_estructura", "id_padre", "codigo", "nombre",
            "tipo_estructura", "descripcion", "tipo_unidad", "superficie",
            "cantidad_plantas", "estado", "id_modelo", "modelo_nombre",
            "id_obra", "proyecto_nombre", "proyecto_codigo", "ruta_jerarquica",
            "created_at", "updated_at"
        )
        data = dict(zip(fields, row))
        related = {
            "ambientes": ("SELECT id_ambiente, nombre, cantidad FROM obras.t_unidad_ambiente WHERE id_unidad = %s ORDER BY nombre", ("id_ambiente", "nombre", "cantidad")),
            "caracteristicas": ("SELECT id_caracteristica, nombre, valor FROM obras.t_unidad_caracteristica WHERE id_unidad = %s ORDER BY nombre", ("id_caracteristica", "nombre", "valor")),
            "personalizaciones": ("SELECT id_personalizacion, tipo, descripcion, created_at FROM obras.t_unidad_personalizacion WHERE id_unidad = %s ORDER BY created_at DESC", ("id_personalizacion", "tipo", "descripcion", "created_at")),
            "seguimiento": ("SELECT id_seguimiento, estado_anterior, estado_nuevo, id_usuario, observacion, fecha FROM obras.t_unidad_seguimiento WHERE id_unidad = %s ORDER BY fecha DESC", ("id_seguimiento", "estado_anterior", "estado_nuevo", "id_usuario", "observacion", "fecha")),
            "materiales": ("""SELECT um.id_unidad_material, um.id_material, m.nombre_material,
                                      um.cantidad, um.unidad_medida, um.uso_ubicacion,
                                      um.acabado, um.observacion
                               FROM obras.t_unidad_material um
                               JOIN obras.t_material m ON m.id_material = um.id_material
                               WHERE um.id_unidad = %s ORDER BY m.nombre_material""",
                            ("id_unidad_material", "id_material", "nombre_material", "cantidad", "unidad_medida", "uso_ubicacion", "acabado", "observacion"))
        }
        for key, (sql, child_fields) in related.items():
            rows = db.execute_query(sql, (id_unidad,), fetchall=True) or []
            data[key] = [dict(zip(child_fields, item)) for item in rows]
        return {"success": True, "data": data}
    finally:
        db.close_connection()


def actualizar_unidad_fn(id_obra, id_unidad, id_empresa, data: dict) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        query = """
            SELECT obras.fn_actualizar_unidad_construccion(
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::json, %s::json
            );
        """
        params = (
            id_obra, id_unidad, id_empresa, data.get("nombre"), data.get("descripcion"),
            data.get("tipo_unidad"), data.get("superficie"), data.get("cantidad_plantas"),
            data.get("id_modelo"), json.dumps(data.get("ambientes") or []),
            json.dumps(data.get("caracteristicas") or [])
        )
        return _json_result(
            db.execute_query(query, params, fetchone=True, commit=True),
            "No se pudo actualizar la unidad."
        )
    finally:
        db.close_connection()


def eliminar_unidad_fn(id_obra: int, id_unidad: int, id_empresa: int = None) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        query = "SELECT obras.fn_eliminar_unidad_construccion(%s, %s, %s);"
        return _json_result(
            db.execute_query(
                query, (id_obra, id_unidad, id_empresa), fetchone=True, commit=True
            ),
            "No se pudo eliminar la unidad."
        )
    finally:
        db.close_connection()


def cambiar_estado_fn(id_obra, id_unidad, id_empresa, estado, id_usuario, observacion) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        query = "SELECT obras.fn_cambiar_estado_unidad(%s, %s, %s, %s, %s, %s);"
        params = (id_obra, id_unidad, id_empresa, estado, id_usuario, observacion)
        return _json_result(
            db.execute_query(query, params, fetchone=True, commit=True),
            "No se pudo actualizar el estado."
        )
    finally:
        db.close_connection()


def listar_modelos(id_empresa: int = None) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query("""
            SELECT id_modelo, id_empresa, nombre, descripcion, tipo_unidad,
                   superficie_base, cantidad_plantas_base, activo
            FROM obras.t_modelo_unidad
            WHERE (id_empresa = %s OR %s IS NULL) AND activo = TRUE
            ORDER BY nombre;
        """, (id_empresa, id_empresa), fetchall=True) or []
        fields = ("id_modelo", "id_empresa", "nombre", "descripcion", "tipo_unidad", "superficie_base", "cantidad_plantas_base", "activo")
        modelos = []
        for row in rows:
            modelo = dict(zip(fields, row))
            caracteristicas = db.execute_query(
                "SELECT id_modelo_caracteristica, nombre, valor FROM obras.t_modelo_caracteristica WHERE id_modelo=%s ORDER BY nombre",
                (modelo["id_modelo"],), fetchall=True
            ) or []
            modelo["caracteristicas"] = [
                {"id_caracteristica": item[0], "nombre": item[1], "valor": item[2]}
                for item in caracteristicas
            ]
            modelos.append(modelo)
        return {"success": True, "data": modelos}
    finally:
        db.close_connection()


def guardar_modelo(id_empresa: int, data: dict, id_modelo: int = None) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        if id_modelo:
            row = db.execute_query("""
                UPDATE obras.t_modelo_unidad
                SET nombre=%s, descripcion=%s, tipo_unidad=%s,
                    superficie_base=%s, cantidad_plantas_base=%s
                WHERE id_modelo=%s AND id_empresa=%s RETURNING id_modelo;
            """, (data["nombre"], data.get("descripcion"), data["tipo_unidad"],
                  data.get("superficie_base"), data.get("cantidad_plantas_base"),
                  id_modelo, id_empresa), fetchone=True)
        else:
            row = db.execute_query("""
                INSERT INTO obras.t_modelo_unidad(
                    id_empresa, nombre, descripcion, tipo_unidad,
                    superficie_base, cantidad_plantas_base
                ) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id_modelo;
            """, (id_empresa, data["nombre"], data.get("descripcion"), data["tipo_unidad"],
                  data.get("superficie_base"), data.get("cantidad_plantas_base")), fetchone=True)
        if not row:
            return {"success": False, "error": "El modelo no existe o no pertenece a su empresa."}
        saved_id = row[0]
        db.execute_query("DELETE FROM obras.t_modelo_caracteristica WHERE id_modelo=%s", (saved_id,))
        for item in data.get("caracteristicas") or []:
            db.execute_query(
                "INSERT INTO obras.t_modelo_caracteristica(id_modelo,nombre,valor) VALUES(%s,%s,%s)",
                (saved_id, item["nombre"], item["valor"])
            )
        db.conn.commit()
        return {"success": True, "id_modelo": saved_id, "message": "Modelo guardado exitosamente."}
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


def agregar_personalizacion(id_obra, id_unidad, id_empresa, tipo, descripcion) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query("""
            INSERT INTO obras.t_unidad_personalizacion(id_unidad, tipo, descripcion)
            SELECT u.id_unidad, %s, %s
            FROM obras.t_unidad_construccion u
            JOIN obras.t_estructura_obra e ON e.id_estructura=u.id_estructura
            JOIN obras.t_obra o ON o.id_obra=e.id_obra
            WHERE u.id_unidad=%s AND o.id_obra=%s AND (o.id_empresa=%s OR %s IS NULL)
            RETURNING id_personalizacion;
        """, (tipo, descripcion, id_unidad, id_obra, id_empresa, id_empresa), fetchone=True, commit=True)
        return {"success": bool(row), "id_personalizacion": row[0] if row else None,
                "message": "Personalización registrada." if row else None,
                "error": None if row else "La unidad no existe o no pertenece a su empresa."}
    finally:
        db.close_connection()


def eliminar_personalizacion(id_obra, id_unidad, id_personalizacion, id_empresa) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query("""
            DELETE FROM obras.t_unidad_personalizacion p
            USING obras.t_unidad_construccion u, obras.t_estructura_obra e, obras.t_obra o
            WHERE p.id_personalizacion=%s AND p.id_unidad=%s
              AND u.id_unidad=p.id_unidad AND e.id_estructura=u.id_estructura
              AND o.id_obra=e.id_obra AND o.id_obra=%s
              AND (o.id_empresa=%s OR %s IS NULL);
        """, (id_personalizacion, id_unidad, id_obra, id_empresa, id_empresa), commit=True)
        return {"success": rows > 0, "message": "Personalización eliminada." if rows > 0 else None,
                "error": None if rows > 0 else "La personalización no existe o no tiene permisos."}
    finally:
        db.close_connection()


def listar_materiales_disponibles() -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(
            "SELECT id_material, nombre_material, precio FROM obras.t_material ORDER BY nombre_material",
            fetchall=True
        ) or []
        return {"success": True, "data": [
            {"id_material": row[0], "nombre_material": row[1], "precio": row[2]} for row in rows
        ]}
    finally:
        db.close_connection()


def reemplazar_materiales(id_obra, id_unidad, id_empresa, materiales: list) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        valid = db.execute_query("""
            SELECT 1 FROM obras.t_unidad_construccion u
            JOIN obras.t_estructura_obra e ON e.id_estructura=u.id_estructura
            JOIN obras.t_obra o ON o.id_obra=e.id_obra
            WHERE u.id_unidad=%s AND o.id_obra=%s AND (o.id_empresa=%s OR %s IS NULL)
        """, (id_unidad, id_obra, id_empresa, id_empresa), fetchone=True)
        if not valid:
            return {"success": False, "error": "La unidad no existe o no pertenece a su empresa."}
        db.execute_query("DELETE FROM obras.t_unidad_material WHERE id_unidad=%s", (id_unidad,))
        for item in materiales:
            db.execute_query("""
                INSERT INTO obras.t_unidad_material(
                    id_unidad,id_material,cantidad,unidad_medida,uso_ubicacion,acabado,observacion
                ) VALUES(%s,%s,%s,%s,%s,%s,%s)
            """, (id_unidad, item["id_material"], item["cantidad"], item.get("unidad_medida"),
                  item.get("uso_ubicacion"), item.get("acabado"), item.get("observacion")))
        db.conn.commit()
        return {"success": True, "message": "Materiales y acabados asociados exitosamente."}
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()
