"""
Repositorio CU23 – Gestionar consultas técnicas de obra (RFI)
Acceso a datos PostgreSQL para consultas técnicas, respuestas e historial.
Esquema: obras
"""
from app.classes.postgres import PostgreSQL


_CAMPOS_CONSULTA = (
    "id_consulta_tecnica", "id_empresa", "id_obra", "obra_codigo", "obra_nombre",
    "codigo", "asunto", "descripcion", "referencia_tecnica", "estado",
    "creado_por", "creador_nombre",
    "asignado_a", "responsable_nombre", "fecha_asignacion", "asignado_por",
    "fecha_cierre", "cerrado_por", "cerrador_nombre", "motivo_cierre",
    "created_at", "updated_at", "total_respuestas"
)

_SELECT_BASE = """
    SELECT ct.id_consulta_tecnica, ct.id_empresa, ct.id_obra, o.codigo AS obra_codigo, o.nombre AS obra_nombre,
           ct.codigo, ct.asunto, ct.descripcion, ct.referencia_tecnica, ct.estado,
           ct.creado_por,
           COALESCE(NULLIF(pc.nombre_completo, ''), uc.username) AS creador_nombre,
           ct.asignado_a,
           COALESCE(NULLIF(pa.nombre_completo, ''), ua.username) AS responsable_nombre,
           ct.fecha_asignacion, ct.asignado_por,
           ct.fecha_cierre, ct.cerrado_por,
           COALESCE(NULLIF(pz.nombre_completo, ''), uz.username) AS cerrador_nombre,
           ct.motivo_cierre,
           ct.created_at, ct.updated_at,
           (SELECT COUNT(*) FROM obras.t_consulta_tecnica_respuesta ctr WHERE ctr.id_consulta_tecnica = ct.id_consulta_tecnica) AS total_respuestas
    FROM obras.t_consulta_tecnica ct
    JOIN obras.t_obra o ON o.id_obra = ct.id_obra
    LEFT JOIN obras.t_usuario uc ON uc.id_usuario = ct.creado_por
    LEFT JOIN obras.t_persona pc ON pc.id_persona = uc.id_persona
    LEFT JOIN obras.t_usuario ua ON ua.id_usuario = ct.asignado_a
    LEFT JOIN obras.t_persona pa ON pa.id_persona = ua.id_persona
    LEFT JOIN obras.t_usuario uz ON uz.id_usuario = ct.cerrado_por
    LEFT JOIN obras.t_persona pz ON pz.id_persona = uz.id_persona
"""


def _map_row(row):
    if not row:
        return None
    data = dict(zip(_CAMPOS_CONSULTA, row))
    if data.get("created_at"):
        data["created_at"] = data["created_at"].isoformat()
    if data.get("updated_at"):
        data["updated_at"] = data["updated_at"].isoformat()
    if data.get("fecha_asignacion"):
        data["fecha_asignacion"] = data["fecha_asignacion"].isoformat()
    if data.get("fecha_cierre"):
        data["fecha_cierre"] = data["fecha_cierre"].isoformat()
    return data


def obtener_obra(id_obra, id_empresa=None):
    """Verifica existencia de la obra y que coincida con el tenant."""
    db = PostgreSQL()
    db.create_connection()
    try:
        query = "SELECT id_obra, id_empresa, codigo, nombre, estado_obra FROM obras.t_obra WHERE id_obra = %s"
        params = [id_obra]
        if id_empresa is not None:
            query += " AND id_empresa = %s"
            params.append(id_empresa)
        row = db.execute_query(query, tuple(params), fetchone=True)
        if not row:
            return None
        return dict(zip(("id_obra", "id_empresa", "codigo", "nombre", "estado_obra"), row))
    finally:
        db.close_connection()


def generar_siguiente_codigo(id_obra, id_empresa=None):
    """Genera el siguiente correlativo para la consulta de la obra (ej. CT-SCZ01-001)."""
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query("SELECT codigo FROM obras.t_obra WHERE id_obra = %s", (id_obra,), fetchone=True)
        cod_obra = (row[0] if row and row[0] else f"OBRA{id_obra}").strip().replace(" ", "-")

        count_row = db.execute_query(
            "SELECT COUNT(*) FROM obras.t_consulta_tecnica WHERE id_obra = %s",
            (id_obra,), fetchone=True
        )
        secuencia = (count_row[0] or 0) + 1
        return f"CT-{cod_obra}-{secuencia:03d}"
    finally:
        db.close_connection()


def listar_consultas(id_obra=None, id_empresa=None, estado=None, id_responsable=None, busqueda=None, page=1, limit=20):
    """Listado paginado de consultas técnicas con filtros."""
    db = PostgreSQL()
    db.create_connection()
    try:
        where = []
        params = []

        if id_obra is not None:
            where.append("ct.id_obra = %s")
            params.append(id_obra)

        if id_empresa is not None:
            where.append("ct.id_empresa = %s")
            params.append(id_empresa)

        if estado:
            where.append("ct.estado = %s")
            params.append(estado.strip().upper())

        if id_responsable:
            where.append("ct.asignado_a = %s")
            params.append(id_responsable)

        if busqueda and busqueda.strip():
            b = f"%{busqueda.strip()}%"
            where.append("(ct.codigo ILIKE %s OR ct.asunto ILIKE %s OR ct.descripcion ILIKE %s OR ct.referencia_tecnica ILIKE %s)")
            params.extend([b, b, b, b])

        where_clause = (" WHERE " + " AND ".join(where)) if where else ""

        count_query = "SELECT COUNT(*) FROM obras.t_consulta_tecnica ct " + where_clause
        total_row = db.execute_query(count_query, tuple(params), fetchone=True)
        total = total_row[0] if total_row else 0

        offset = max(0, (page - 1) * limit)
        order_query = _SELECT_BASE + where_clause + " ORDER BY ct.updated_at DESC, ct.id_consulta_tecnica DESC LIMIT %s OFFSET %s"
        query_params = list(params) + [limit, offset]

        rows = db.execute_query(order_query, tuple(query_params), fetchall=True) or []
        items = [_map_row(r) for r in rows]

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }
    finally:
        db.close_connection()


def obtener_por_id(id_consulta_tecnica, id_empresa=None):
    """Detalle completo de una consulta técnica."""
    db = PostgreSQL()
    db.create_connection()
    try:
        where = " WHERE ct.id_consulta_tecnica = %s"
        params = [id_consulta_tecnica]
        if id_empresa is not None:
            where += " AND ct.id_empresa = %s"
            params.append(id_empresa)

        row = db.execute_query(_SELECT_BASE + where, tuple(params), fetchone=True)
        return _map_row(row)
    finally:
        db.close_connection()


def crear_consulta(id_empresa, id_obra, codigo, asunto, descripcion, referencia_tecnica, creado_por, asignado_a=None):
    """Registra una nueva consulta técnica e inserta el evento inicial en el historial."""
    db = PostgreSQL()
    db.create_connection()
    try:
        estado_inicial = "ASIGNADA" if asignado_a else "ABIERTA"
        fecha_asig = "CURRENT_TIMESTAMP" if asignado_a else "NULL"
        asig_por = creado_por if asignado_a else None

        insert_sql = f"""
            INSERT INTO obras.t_consulta_tecnica (
                id_empresa, id_obra, codigo, asunto, descripcion, referencia_tecnica,
                estado, creado_por, asignado_a, fecha_asignacion, asignado_por
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, {fecha_asig}, %s
            ) RETURNING id_consulta_tecnica;
        """
        row = db.execute_query(
            insert_sql,
            (id_empresa, id_obra, codigo, asunto, descripcion, referencia_tecnica, estado_inicial, creado_por, asignado_a, asig_por),
            fetchone=True, commit=False
        )
        if not row:
            db.conn.rollback()
            return None
        id_ct = row[0]

        # Evento en historial
        hist_sql = """
            INSERT INTO obras.t_consulta_tecnica_historial (
                id_consulta_tecnica, actor_id, tipo_evento, estado_anterior, estado_nuevo, detalle
            ) VALUES (%s, %s, %s, NULL, %s, %s);
        """
        detalle = f"Consulta técnica creada con código {codigo}."
        if asignado_a:
            detalle += f" Asignada inicialmente a usuario ID {asignado_a}."

        db.execute_query(
            hist_sql,
            (id_ct, creado_por, "CREACION", estado_inicial, detalle),
            commit=True
        )
        return id_ct
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


def asignar_responsable(id_consulta_tecnica, id_responsable, asignado_por):
    """Asigna o reasigna responsable a la consulta técnica y registra en historial."""
    db = PostgreSQL()
    db.create_connection()
    try:
        # Obtener estado actual
        row_ct = db.execute_query(
            "SELECT estado, asignado_a FROM obras.t_consulta_tecnica WHERE id_consulta_tecnica = %s",
            (id_consulta_tecnica,), fetchone=True
        )
        if not row_ct:
            return False
        estado_ant, asignado_ant = row_ct[0], row_ct[1]

        # Si estaba ABIERTA pasa a ASIGNADA; si ya estaba ASIGNADA o RESPONDIDA mantiene su flujo
        nuevo_estado = "ASIGNADA" if estado_ant == "ABIERTA" else estado_ant

        update_sql = """
            UPDATE obras.t_consulta_tecnica
            SET asignado_a = %s,
                asignado_por = %s,
                fecha_asignacion = CURRENT_TIMESTAMP,
                estado = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id_consulta_tecnica = %s;
        """
        db.execute_query(update_sql, (id_responsable, asignado_por, nuevo_estado, id_consulta_tecnica), commit=False)

        tipo_ev = "REASIGNACION" if asignado_ant else "ASIGNACION"
        hist_sql = """
            INSERT INTO obras.t_consulta_tecnica_historial (
                id_consulta_tecnica, actor_id, tipo_evento, estado_anterior, estado_nuevo, detalle
            ) VALUES (%s, %s, %s, %s, %s, %s);
        """
        detalle = f"Responsable asignado: usuario ID {id_responsable}."
        db.execute_query(hist_sql, (id_consulta_tecnica, asignado_por, tipo_ev, estado_ant, nuevo_estado, detalle), commit=True)
        return True
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


def registrar_respuesta(id_consulta_tecnica, autor_id, contenido):
    """Inserta respuesta técnica, transita a RESPONDIDA y audita en historial."""
    db = PostgreSQL()
    db.create_connection()
    try:
        # Obtener estado actual
        row_ct = db.execute_query(
            "SELECT estado FROM obras.t_consulta_tecnica WHERE id_consulta_tecnica = %s",
            (id_consulta_tecnica,), fetchone=True
        )
        if not row_ct:
            return None
        estado_ant = row_ct[0]
        nuevo_estado = "RESPONDIDA" if estado_ant in ("ABIERTA", "ASIGNADA") else estado_ant

        # 1. Insertar respuesta
        insert_resp = """
            INSERT INTO obras.t_consulta_tecnica_respuesta (id_consulta_tecnica, autor_id, contenido)
            VALUES (%s, %s, %s) RETURNING id_consulta_tecnica_respuesta, created_at;
        """
        resp_row = db.execute_query(insert_resp, (id_consulta_tecnica, autor_id, contenido), fetchone=True, commit=False)
        id_resp = resp_row[0]

        # 2. Actualizar estado y timestamp de la consulta
        update_ct = """
            UPDATE obras.t_consulta_tecnica
            SET estado = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id_consulta_tecnica = %s;
        """
        db.execute_query(update_ct, (nuevo_estado, id_consulta_tecnica), commit=False)

        # 3. Auditoría en historial
        hist_sql = """
            INSERT INTO obras.t_consulta_tecnica_historial (
                id_consulta_tecnica, actor_id, tipo_evento, estado_anterior, estado_nuevo, detalle
            ) VALUES (%s, %s, 'RESPUESTA', %s, %s, %s);
        """
        detalle = f"Respuesta técnica registrada (#{id_resp})."
        db.execute_query(hist_sql, (id_consulta_tecnica, autor_id, estado_ant, nuevo_estado, detalle), commit=True)

        return id_resp
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


def cerrar_consulta(id_consulta_tecnica, cerrado_por, motivo):
    """Cierra la consulta técnica de forma definitiva."""
    db = PostgreSQL()
    db.create_connection()
    try:
        row_ct = db.execute_query(
            "SELECT estado FROM obras.t_consulta_tecnica WHERE id_consulta_tecnica = %s",
            (id_consulta_tecnica,), fetchone=True
        )
        if not row_ct:
            return False
        estado_ant = row_ct[0]

        update_sql = """
            UPDATE obras.t_consulta_tecnica
            SET estado = 'CERRADA',
                fecha_cierre = CURRENT_TIMESTAMP,
                cerrado_por = %s,
                motivo_cierre = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id_consulta_tecnica = %s;
        """
        db.execute_query(update_sql, (cerrado_por, motivo, id_consulta_tecnica), commit=False)

        hist_sql = """
            INSERT INTO obras.t_consulta_tecnica_historial (
                id_consulta_tecnica, actor_id, tipo_evento, estado_anterior, estado_nuevo, detalle
            ) VALUES (%s, %s, 'CIERRE', %s, 'CERRADA', %s);
        """
        detalle = f"Consulta cerrada. Motivo: {motivo}"
        db.execute_query(hist_sql, (id_consulta_tecnica, cerrado_por, estado_ant, detalle), commit=True)
        return True
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


def reabrir_consulta(id_consulta_tecnica, actor_id, motivo):
    """Reabre una consulta técnica cerrada previamente."""
    db = PostgreSQL()
    db.create_connection()
    try:
        update_sql = """
            UPDATE obras.t_consulta_tecnica
            SET estado = 'ABIERTA',
                fecha_cierre = NULL,
                cerrado_por = NULL,
                motivo_cierre = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id_consulta_tecnica = %s AND estado = 'CERRADA';
        """
        db.execute_query(update_sql, (id_consulta_tecnica,), commit=False)

        hist_sql = """
            INSERT INTO obras.t_consulta_tecnica_historial (
                id_consulta_tecnica, actor_id, tipo_evento, estado_anterior, estado_nuevo, detalle
            ) VALUES (%s, %s, 'REAPERTURA', 'CERRADA', 'ABIERTA', %s);
        """
        detalle = f"Reapertura de consulta técnica. Motivo: {motivo}"
        db.execute_query(hist_sql, (id_consulta_tecnica, actor_id, detalle), commit=True)
        return True
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


def obtener_respuestas(id_consulta_tecnica):
    """Obtiene todas las respuestas de una consulta técnica en orden cronológico."""
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = """
            SELECT r.id_consulta_tecnica_respuesta, r.id_consulta_tecnica, r.autor_id,
                   COALESCE(NULLIF(p.nombre_completo, ''), u.username) AS autor_nombre,
                   rol.nombre_rol AS autor_rol,
                   r.contenido, r.created_at
            FROM obras.t_consulta_tecnica_respuesta r
            JOIN obras.t_usuario u ON u.id_usuario = r.autor_id
            LEFT JOIN obras.t_persona p ON p.id_persona = u.id_persona
            LEFT JOIN obras.t_rol rol ON rol.id_rol = u.id_rol
            WHERE r.id_consulta_tecnica = %s
            ORDER BY r.created_at ASC, r.id_consulta_tecnica_respuesta ASC;
        """
        rows = db.execute_query(sql, (id_consulta_tecnica,), fetchall=True) or []
        campos = ("id_consulta_tecnica_respuesta", "id_consulta_tecnica", "autor_id", "autor_nombre", "autor_rol", "contenido", "created_at")
        res = []
        for r in rows:
            d = dict(zip(campos, r))
            if d.get("created_at"):
                d["created_at"] = d["created_at"].isoformat()
            res.append(d)
        return res
    finally:
        db.close_connection()


def obtener_historial(id_consulta_tecnica):
    """Obtiene la bitácora de eventos de una consulta técnica."""
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = """
            SELECT h.id_historial, h.id_consulta_tecnica, h.actor_id,
                   COALESCE(NULLIF(p.nombre_completo, ''), u.username) AS actor_nombre,
                   rol.nombre_rol AS actor_rol,
                   h.tipo_evento, h.estado_anterior, h.estado_nuevo, h.detalle, h.created_at
            FROM obras.t_consulta_tecnica_historial h
            JOIN obras.t_usuario u ON u.id_usuario = h.actor_id
            LEFT JOIN obras.t_persona p ON p.id_persona = u.id_persona
            LEFT JOIN obras.t_rol rol ON rol.id_rol = u.id_rol
            WHERE h.id_consulta_tecnica = %s
            ORDER BY h.created_at ASC, h.id_historial ASC;
        """
        rows = db.execute_query(sql, (id_consulta_tecnica,), fetchall=True) or []
        campos = ("id_historial", "id_consulta_tecnica", "actor_id", "actor_nombre", "actor_rol", "tipo_evento", "estado_anterior", "estado_nuevo", "detalle", "created_at")
        res = []
        for r in rows:
            d = dict(zip(campos, r))
            if d.get("created_at"):
                d["created_at"] = d["created_at"].isoformat()
            res.append(d)
        return res
    finally:
        db.close_connection()


def obtener_usuarios_asignables(id_obra, id_empresa=None):
    """Obtiene los usuarios de la empresa y del proyecto que pueden responder consultas técnicas."""
    db = PostgreSQL()
    db.create_connection()
    try:
        # Obtenemos usuarios activos de la empresa con roles técnicos (Admin, Admin Empresa, Jefe Obra, Supervisor)
        sql = """
            SELECT DISTINCT u.id_usuario,
                   COALESCE(NULLIF(p.nombre_completo, ''), u.username) AS nombre_completo,
                   u.correo, r.nombre_rol
            FROM obras.t_usuario u
            LEFT JOIN obras.t_persona p ON p.id_persona = u.id_persona
            JOIN obras.t_rol r ON r.id_rol = u.id_rol
            WHERE u.estado = 'ACTIVO'
              AND r.id_rol IN (1, 3, 4, 9)
              AND (%s IS NULL OR u.id_empresa = %s)
            ORDER BY nombre_completo ASC;
        """
        rows = db.execute_query(sql, (id_empresa, id_empresa), fetchall=True) or []
        campos = ("id_usuario", "nombre_completo", "correo", "nombre_rol")
        return [dict(zip(campos, r)) for r in rows]
    finally:
        db.close_connection()
