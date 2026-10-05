from psycopg2 import errors

from app.classes.postgres import PostgreSQL
from app.config import Config


class ControlCostosConflictError(Exception):
    """Conflicto de unicidad o estado detectado por PostgreSQL."""


def _columns(db):
    if not db.cur or not db.cur.description:
        return []
    return [item.name if hasattr(item, "name") else item[0] for item in db.cur.description]


def _one(db, sql, params=()):
    row = db.execute_query(sql, params, fetchone=True)
    return dict(zip(_columns(db), row)) if row else None


def _many(db, sql, params=()):
    rows = db.execute_query(sql, params, fetchall=True) or []
    columns = _columns(db)
    return [dict(zip(columns, row)) for row in rows]


def _read_one(sql, params=()):
    db = PostgreSQL()
    db.create_connection()
    try:
        return _one(db, sql, params)
    finally:
        db.close_connection()


def _read_many(sql, params=()):
    db = PostgreSQL()
    db.create_connection()
    try:
        return _many(db, sql, params)
    finally:
        db.close_connection()


def listar_presupuestos_aprobados(id_empresa, id_obra):
    return _read_many(
        f"""
        SELECT e.id_estimacion, e.id_obra, e.nombre, e.version, e.estado,
               e.descripcion, e.cliente, e.monto_total, e.created_at,
               o.codigo AS obra_codigo, o.nombre AS obra_nombre, o.moneda,
               COALESCE(SUM(ROUND(d.cantidad * d.costo_directo_unitario, 2)), 0)
                   AS costo_directo_presupuestado,
               COUNT(d.id_estimacion_analisis_precio_unitario) AS total_partidas
        FROM {Config.SCHEMA}.t_estimacion e
        JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
        LEFT JOIN {Config.SCHEMA}.t_estimacion_analisis_precio_unitario d
               ON d.id_estimacion = e.id_estimacion
        WHERE e.id_empresa = %s AND e.id_obra = %s AND o.id_empresa = %s
          AND e.estado = 'APROBADA'
        GROUP BY e.id_estimacion, o.id_obra
        ORDER BY e.version DESC, e.id_estimacion DESC
        """,
        (id_empresa, id_obra, id_empresa),
    )


def obtener_linea_base(id_empresa, id_obra, solo_activa=True):
    estado_sql = "AND c.estado = 'ACTIVO'" if solo_activa else ""
    return _read_one(
        f"""
        SELECT c.*, e.nombre AS presupuesto_nombre, e.estado AS presupuesto_estado,
               o.codigo AS obra_codigo, o.nombre AS obra_nombre
        FROM {Config.SCHEMA}.t_control_costo_obra c
        JOIN {Config.SCHEMA}.t_estimacion e ON e.id_estimacion = c.id_estimacion_base
        JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = c.id_obra
        WHERE c.id_empresa = %s AND c.id_obra = %s {estado_sql}
        ORDER BY c.seleccionado_en DESC, c.id_control_costo DESC
        LIMIT 1
        """,
        (id_empresa, id_obra),
    )


def obtener_linea_base_por_id(id_control_costo, id_empresa, exigir_activa=False):
    estado_sql = "AND c.estado = 'ACTIVO'" if exigir_activa else ""
    return _read_one(
        f"""
        SELECT c.*, e.nombre AS presupuesto_nombre, e.estado AS presupuesto_estado,
               o.codigo AS obra_codigo, o.nombre AS obra_nombre
        FROM {Config.SCHEMA}.t_control_costo_obra c
        JOIN {Config.SCHEMA}.t_estimacion e ON e.id_estimacion = c.id_estimacion_base
        JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = c.id_obra
        WHERE c.id_control_costo = %s AND c.id_empresa = %s {estado_sql}
        """,
        (id_control_costo, id_empresa),
    )


def crear_linea_base(id_empresa, id_obra, id_estimacion_base, id_usuario):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = _one(
            db,
            f"""
            INSERT INTO {Config.SCHEMA}.t_control_costo_obra
                (id_empresa, id_obra, id_estimacion_base, version_presupuesto,
                 moneda, estado, seleccionado_por)
            SELECT e.id_empresa, e.id_obra, e.id_estimacion, e.version,
                   o.moneda, 'ACTIVO', %s
            FROM {Config.SCHEMA}.t_estimacion e
            JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
            WHERE e.id_estimacion = %s AND e.id_obra = %s
              AND e.id_empresa = %s AND o.id_empresa = %s
              AND e.estado = 'APROBADA'
            RETURNING *
            """,
            (id_usuario, id_estimacion_base, id_obra, id_empresa, id_empresa),
        )
        db.conn.commit()
        return row
    except errors.UniqueViolation as exc:
        db.conn.rollback()
        raise ControlCostosConflictError(
            "La obra ya tiene una linea base ACTIVA."
        ) from exc
    finally:
        db.close_connection()


def obtener_partida_base(id_partida, id_estimacion, id_empresa):
    return _read_one(
        f"""
        SELECT d.id_estimacion_analisis_precio_unitario AS id_partida_presupuestaria,
               d.id_estimacion, d.id_analisis_precio_unitario,
               d.item_codigo, d.cantidad, d.costo_directo_unitario,
               d.precio_unitario, d.precio_total, d.orden, d.observacion,
               a.nombre AS descripcion_partida, a.id_empresa, a.id_obra AS apu_id_obra,
               um.abreviatura AS unidad,
               d.cantidad + COALESCE((
                   SELECT SUM(od.cantidad_delta)
                   FROM {Config.SCHEMA}.t_orden_cambio_detalle od
                   JOIN {Config.SCHEMA}.t_orden_cambio oc
                     ON oc.id_orden_cambio = od.id_orden_cambio
                   WHERE od.id_partida_presupuestaria = d.id_estimacion_analisis_precio_unitario
                     AND oc.estado = 'APROBADA'
               ), 0) AS cantidad_revisada_actual,
               COALESCE((
                   SELECT od.costo_nuevo
                   FROM {Config.SCHEMA}.t_orden_cambio_detalle od
                   JOIN {Config.SCHEMA}.t_orden_cambio oc
                     ON oc.id_orden_cambio = od.id_orden_cambio
                   WHERE od.id_partida_presupuestaria = d.id_estimacion_analisis_precio_unitario
                     AND oc.estado = 'APROBADA'
                     AND od.tipo_cambio IN ('CAMBIO_COSTO', 'ELIMINACION_PARTIDA')
                   ORDER BY oc.fecha_decision DESC, oc.id_orden_cambio DESC,
                            od.id_orden_cambio_detalle DESC
                   LIMIT 1
               ), d.costo_directo_unitario) AS costo_revisado_actual
        FROM {Config.SCHEMA}.t_estimacion_analisis_precio_unitario d
        JOIN {Config.SCHEMA}.t_estimacion e ON e.id_estimacion = d.id_estimacion
        JOIN {Config.SCHEMA}.t_analisis_precio_unitario a
          ON a.id_analisis_precio_unitario = d.id_analisis_precio_unitario
        JOIN {Config.SCHEMA}.t_unidad_medida um
          ON um.id_unidad_medida = a.id_unidad_medida
        WHERE d.id_estimacion_analisis_precio_unitario = %s
          AND d.id_estimacion = %s
          AND e.id_empresa = %s AND a.id_empresa = %s
        """,
        (id_partida, id_estimacion, id_empresa, id_empresa),
    )


def obtener_apu_para_cambio(id_apu, id_empresa, id_obra):
    return _read_one(
        f"""
        SELECT a.id_analisis_precio_unitario, a.codigo, a.nombre,
               a.costo_directo, a.id_obra, um.abreviatura AS unidad
        FROM {Config.SCHEMA}.t_analisis_precio_unitario a
        JOIN {Config.SCHEMA}.t_unidad_medida um
          ON um.id_unidad_medida = a.id_unidad_medida
        WHERE a.id_analisis_precio_unitario = %s AND a.id_empresa = %s
          AND (a.id_obra IS NULL OR a.id_obra = %s) AND a.activo = TRUE
        """,
        (id_apu, id_empresa, id_obra),
    )


def listar_costos(id_empresa, id_obra=None, id_control_costo=None,
                  id_partida=None, estado=None):
    filters = ["c.id_empresa = %s"]
    params = [id_empresa]
    if id_obra is not None:
        filters.append("c.id_obra = %s")
        params.append(id_obra)
    if id_control_costo is not None:
        filters.append("c.id_control_costo = %s")
        params.append(id_control_costo)
    if id_partida is not None:
        filters.append("c.id_partida_presupuestaria = %s")
        params.append(id_partida)
    if estado is not None:
        filters.append("c.estado = %s")
        params.append(estado)
    where = " AND ".join(filters)
    return _read_many(
        f"""
        SELECT c.*, d.item_codigo, a.nombre AS partida_nombre,
               um.abreviatura AS unidad, e.version AS presupuesto_version
        FROM {Config.SCHEMA}.t_costo_ejecutado c
        JOIN {Config.SCHEMA}.t_control_costo_obra control
          ON control.id_control_costo = c.id_control_costo
        JOIN {Config.SCHEMA}.t_estimacion_analisis_precio_unitario d
          ON d.id_estimacion_analisis_precio_unitario = c.id_partida_presupuestaria
        JOIN {Config.SCHEMA}.t_estimacion e ON e.id_estimacion = d.id_estimacion
        JOIN {Config.SCHEMA}.t_analisis_precio_unitario a
          ON a.id_analisis_precio_unitario = d.id_analisis_precio_unitario
        JOIN {Config.SCHEMA}.t_unidad_medida um
          ON um.id_unidad_medida = a.id_unidad_medida
        WHERE {where}
        ORDER BY c.fecha DESC, c.id_costo_ejecutado DESC
        """,
        tuple(params),
    )


def crear_costo(data, id_empresa, id_usuario):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = _one(
            db,
            f"""
            INSERT INTO {Config.SCHEMA}.t_costo_ejecutado
                (id_control_costo, id_empresa, id_obra,
                 id_partida_presupuestaria, fecha, concepto, categoria,
                 cantidad, costo_unitario, monto, documento, observacion,
                 estado, registrado_por)
            SELECT control.id_control_costo, control.id_empresa, control.id_obra,
                   %s, %s, %s, %s, %s, %s, %s, %s, %s,
                   'REGISTRADO', %s
            FROM {Config.SCHEMA}.t_control_costo_obra control
            WHERE control.id_control_costo = %s AND control.id_empresa = %s
              AND control.estado = 'ACTIVO'
              AND EXISTS (
                  SELECT 1
                  FROM {Config.SCHEMA}.t_estimacion_analisis_precio_unitario d
                  WHERE d.id_estimacion_analisis_precio_unitario = %s
                    AND d.id_estimacion = control.id_estimacion_base
              )
            RETURNING *
            """,
            (
                data["id_partida_presupuestaria"], data["fecha"],
                data["concepto"], data["categoria"], data["cantidad"],
                data["costo_unitario"], data["monto"], data.get("documento"),
                data.get("observacion"), id_usuario, data["id_control_costo"],
                id_empresa, data["id_partida_presupuestaria"],
            ),
        )
        db.conn.commit()
        return row
    finally:
        db.close_connection()


def anular_costo(id_costo, motivo, id_empresa, id_usuario):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = _one(
            db,
            f"""
            UPDATE {Config.SCHEMA}.t_costo_ejecutado
               SET estado = 'ANULADO', motivo_anulacion = %s,
                   anulado_por = %s, anulado_en = CURRENT_TIMESTAMP
             WHERE id_costo_ejecutado = %s AND id_empresa = %s
               AND estado = 'REGISTRADO'
            RETURNING *
            """,
            (motivo, id_usuario, id_costo, id_empresa),
        )
        db.conn.commit()
        return row
    finally:
        db.close_connection()


def comparacion_por_obra(id_empresa, id_obra, db=None):
    # Los reportes comparten una transacción de corte consistente.
    read = (lambda sql, params: _many(db, sql, params)) if db else _read_many
    return read(
        f"""
        WITH control AS (
            SELECT *
            FROM {Config.SCHEMA}.t_control_costo_obra
            WHERE id_empresa = %s AND id_obra = %s AND estado = 'ACTIVO'
            ORDER BY seleccionado_en DESC, id_control_costo DESC
            LIMIT 1
        ), ejecutado AS (
            SELECT c.id_partida_presupuestaria, SUM(c.monto) AS costo_ejecutado
            FROM {Config.SCHEMA}.t_costo_ejecutado c
            JOIN control x ON x.id_control_costo = c.id_control_costo
            WHERE c.estado = 'REGISTRADO'
            GROUP BY c.id_partida_presupuestaria
        ), cambios AS (
            SELECT od.id_partida_presupuestaria, SUM(od.impacto_costo) AS impacto
            FROM {Config.SCHEMA}.t_orden_cambio_detalle od
            JOIN {Config.SCHEMA}.t_orden_cambio oc
              ON oc.id_orden_cambio = od.id_orden_cambio
            JOIN control x ON x.id_control_costo = oc.id_control_costo
            WHERE oc.estado = 'APROBADA' AND od.id_partida_presupuestaria IS NOT NULL
            GROUP BY od.id_partida_presupuestaria
        ), partidas_base AS (
            SELECT d.id_estimacion_analisis_precio_unitario AS id_partida_presupuestaria,
                   d.item_codigo, a.nombre AS partida, um.abreviatura AS unidad,
                   d.cantidad AS cantidad_presupuestada,
                   d.costo_directo_unitario,
                   ROUND(d.cantidad * d.costo_directo_unitario, 2) AS costo_presupuestado,
                   COALESCE(c.impacto, 0) AS impacto_ordenes_aprobadas,
                   ROUND(d.cantidad * d.costo_directo_unitario, 2) + COALESCE(c.impacto, 0)
                       AS presupuesto_revisado,
                   COALESCE(ej.costo_ejecutado, 0) AS costo_ejecutado,
                   FALSE AS nueva_partida
            FROM control x
            JOIN {Config.SCHEMA}.t_estimacion_analisis_precio_unitario d
              ON d.id_estimacion = x.id_estimacion_base
            JOIN {Config.SCHEMA}.t_analisis_precio_unitario a
              ON a.id_analisis_precio_unitario = d.id_analisis_precio_unitario
            JOIN {Config.SCHEMA}.t_unidad_medida um
              ON um.id_unidad_medida = a.id_unidad_medida
            LEFT JOIN ejecutado ej
              ON ej.id_partida_presupuestaria = d.id_estimacion_analisis_precio_unitario
            LEFT JOIN cambios c
              ON c.id_partida_presupuestaria = d.id_estimacion_analisis_precio_unitario
        ), partidas_nuevas AS (
            SELECT NULL::INTEGER AS id_partida_presupuestaria,
                   od.item_codigo_snapshot AS item_codigo,
                   od.descripcion_snapshot AS partida,
                   od.unidad_snapshot AS unidad,
                   od.cantidad_revisada AS cantidad_presupuestada,
                   od.costo_nuevo AS costo_directo_unitario,
                   0::NUMERIC AS costo_presupuestado,
                   od.impacto_costo AS impacto_ordenes_aprobadas,
                   od.impacto_costo AS presupuesto_revisado,
                   0::NUMERIC AS costo_ejecutado,
                   TRUE AS nueva_partida
            FROM control x
            JOIN {Config.SCHEMA}.t_orden_cambio oc
              ON oc.id_control_costo = x.id_control_costo AND oc.estado = 'APROBADA'
            JOIN {Config.SCHEMA}.t_orden_cambio_detalle od
              ON od.id_orden_cambio = oc.id_orden_cambio
             AND od.tipo_cambio = 'NUEVA_PARTIDA'
        ), resultado AS (
            SELECT * FROM partidas_base
            UNION ALL
            SELECT * FROM partidas_nuevas
        )
        SELECT r.*,
               r.costo_ejecutado - r.costo_presupuestado AS variacion_original,
               CASE WHEN r.costo_presupuestado = 0 THEN NULL
                    ELSE ROUND((r.costo_ejecutado - r.costo_presupuestado)
                               * 100 / r.costo_presupuestado, 2) END
                    AS variacion_original_porcentaje,
               r.costo_ejecutado - r.presupuesto_revisado AS variacion_revisada,
               CASE WHEN r.presupuesto_revisado = 0 THEN NULL
                    ELSE ROUND((r.costo_ejecutado - r.presupuesto_revisado)
                               * 100 / r.presupuesto_revisado, 2) END
                    AS variacion_revisada_porcentaje
        FROM resultado r
        ORDER BY r.nueva_partida, r.item_codigo
        """,
        (id_empresa, id_obra),
    )


def listar_ordenes(id_empresa, id_obra=None, id_control_costo=None, estado=None):
    filters = ["oc.id_empresa = %s"]
    params = [id_empresa]
    if id_obra is not None:
        filters.append("oc.id_obra = %s")
        params.append(id_obra)
    if id_control_costo is not None:
        filters.append("oc.id_control_costo = %s")
        params.append(id_control_costo)
    if estado is not None:
        filters.append("oc.estado = %s")
        params.append(estado)
    return _read_many(
        f"""
        SELECT oc.*, o.codigo AS obra_codigo, o.nombre AS obra_nombre,
               e.version AS presupuesto_version,
               COUNT(od.id_orden_cambio_detalle) AS total_detalles
        FROM {Config.SCHEMA}.t_orden_cambio oc
        JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = oc.id_obra
        JOIN {Config.SCHEMA}.t_estimacion e ON e.id_estimacion = oc.id_estimacion_base
        LEFT JOIN {Config.SCHEMA}.t_orden_cambio_detalle od
          ON od.id_orden_cambio = oc.id_orden_cambio
        WHERE {' AND '.join(filters)}
        GROUP BY oc.id_orden_cambio, o.id_obra, e.id_estimacion
        ORDER BY oc.fecha DESC, oc.id_orden_cambio DESC
        """,
        tuple(params),
    )


def obtener_orden(id_orden, id_empresa):
    header = _read_one(
        f"""
        SELECT oc.*, o.codigo AS obra_codigo, o.nombre AS obra_nombre,
               e.nombre AS presupuesto_nombre, e.version AS presupuesto_version
        FROM {Config.SCHEMA}.t_orden_cambio oc
        JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = oc.id_obra
        JOIN {Config.SCHEMA}.t_estimacion e ON e.id_estimacion = oc.id_estimacion_base
        WHERE oc.id_orden_cambio = %s AND oc.id_empresa = %s
        """,
        (id_orden, id_empresa),
    )
    if not header:
        return None
    header["detalles"] = _read_many(
        f"""
        SELECT * FROM {Config.SCHEMA}.t_orden_cambio_detalle
        WHERE id_orden_cambio = %s
        ORDER BY id_orden_cambio_detalle
        """,
        (id_orden,),
    )
    return header


def _insertar_detalles(db, id_orden, detalles):
    for detail in detalles:
        db.execute_query(
            f"""
            INSERT INTO {Config.SCHEMA}.t_orden_cambio_detalle
                (id_orden_cambio, id_partida_presupuestaria,
                 id_analisis_precio_unitario, tipo_cambio,
                 item_codigo_snapshot, descripcion_snapshot, unidad_snapshot,
                 cantidad_anterior, cantidad_delta, cantidad_revisada,
                 costo_anterior, costo_nuevo, impacto_costo, observacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                id_orden, detail.get("id_partida_presupuestaria"),
                detail.get("id_analisis_precio_unitario"), detail["tipo_cambio"],
                detail["item_codigo_snapshot"], detail["descripcion_snapshot"],
                detail["unidad_snapshot"], detail["cantidad_anterior"],
                detail["cantidad_delta"], detail["cantidad_revisada"],
                detail["costo_anterior"], detail["costo_nuevo"],
                detail["impacto_costo"], detail.get("observacion"),
            ),
        )


def crear_orden(data, detalles, impacto_total, id_empresa, id_usuario, ip):
    db = PostgreSQL()
    db.create_connection()
    try:
        line = _one(
            db,
            f"""
            SELECT * FROM {Config.SCHEMA}.t_control_costo_obra
            WHERE id_control_costo = %s AND id_empresa = %s AND estado = 'ACTIVO'
            FOR SHARE
            """,
            (data["id_control_costo"], id_empresa),
        )
        if not line:
            db.conn.rollback()
            return None
        order = _one(
            db,
            f"""
            INSERT INTO {Config.SCHEMA}.t_orden_cambio
                (codigo, id_control_costo, id_empresa, id_obra,
                 id_estimacion_base, titulo, descripcion, justificacion,
                 fecha, impacto_costo, impacto_plazo_dias, estado, solicitado_por)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    'PENDIENTE', %s)
            RETURNING *
            """,
            (
                data["codigo"], line["id_control_costo"], id_empresa,
                line["id_obra"], line["id_estimacion_base"], data["titulo"],
                data.get("descripcion"), data["justificacion"], data["fecha"],
                impacto_total, data.get("impacto_plazo_dias", 0), id_usuario,
            ),
        )
        _insertar_detalles(db, order["id_orden_cambio"], detalles)
        db.execute_query(
            f"""
            INSERT INTO {Config.SCHEMA}.t_orden_cambio_historial
                (id_orden_cambio, estado_anterior, estado_nuevo, accion,
                 comentario, id_usuario, ip_origen)
            VALUES (%s, NULL, 'PENDIENTE', 'CREACION', %s, %s, %s)
            """,
            (order["id_orden_cambio"], "Orden de cambio creada.", id_usuario, ip),
        )
        db.conn.commit()
        return order
    except errors.UniqueViolation as exc:
        db.conn.rollback()
        raise ControlCostosConflictError(
            "Ya existe una orden con ese codigo para la obra."
        ) from exc
    except Exception:
        db.conn.rollback()
        raise
    finally:
        db.close_connection()


def actualizar_orden(id_orden, data, detalles, impacto_total,
                     id_empresa, id_usuario, ip):
    db = PostgreSQL()
    db.create_connection()
    try:
        order = _one(
            db,
            f"""
            UPDATE {Config.SCHEMA}.t_orden_cambio
               SET titulo = %s, descripcion = %s, justificacion = %s,
                   fecha = %s, impacto_costo = %s, impacto_plazo_dias = %s
             WHERE id_orden_cambio = %s AND id_empresa = %s
               AND estado = 'PENDIENTE'
            RETURNING *
            """,
            (
                data["titulo"], data.get("descripcion"), data["justificacion"],
                data["fecha"], impacto_total, data.get("impacto_plazo_dias", 0),
                id_orden, id_empresa,
            ),
        )
        if not order:
            db.conn.rollback()
            return None
        db.execute_query(
            f"DELETE FROM {Config.SCHEMA}.t_orden_cambio_detalle WHERE id_orden_cambio = %s",
            (id_orden,),
        )
        _insertar_detalles(db, id_orden, detalles)
        db.execute_query(
            f"""
            INSERT INTO {Config.SCHEMA}.t_orden_cambio_historial
                (id_orden_cambio, estado_anterior, estado_nuevo, accion,
                 comentario, id_usuario, ip_origen)
            VALUES (%s, 'PENDIENTE', 'PENDIENTE', 'MODIFICACION', %s, %s, %s)
            """,
            (id_orden, "Orden de cambio modificada.", id_usuario, ip),
        )
        db.conn.commit()
        return order
    except errors.UniqueViolation as exc:
        db.conn.rollback()
        raise ControlCostosConflictError(
            "La actualizacion produce datos duplicados."
        ) from exc
    except Exception:
        db.conn.rollback()
        raise
    finally:
        db.close_connection()


def decidir_orden(id_orden, nuevo_estado, motivo, id_empresa, id_usuario, ip):
    action = "APROBACION" if nuevo_estado == "APROBADA" else "RECHAZO"
    db = PostgreSQL()
    db.create_connection()
    try:
        order = _one(
            db,
            f"""
            UPDATE {Config.SCHEMA}.t_orden_cambio
               SET estado = %s, decidido_por = %s,
                   fecha_decision = CURRENT_TIMESTAMP, motivo_decision = %s
             WHERE id_orden_cambio = %s AND id_empresa = %s
               AND estado = 'PENDIENTE'
            RETURNING *
            """,
            (nuevo_estado, id_usuario, motivo, id_orden, id_empresa),
        )
        if not order:
            db.conn.rollback()
            return None
        db.execute_query(
            f"""
            INSERT INTO {Config.SCHEMA}.t_orden_cambio_historial
                (id_orden_cambio, estado_anterior, estado_nuevo, accion,
                 comentario, id_usuario, ip_origen)
            VALUES (%s, 'PENDIENTE', %s, %s, %s, %s, %s)
            """,
            (id_orden, nuevo_estado, action, motivo, id_usuario, ip),
        )
        db.conn.commit()
        return order
    except Exception:
        db.conn.rollback()
        raise
    finally:
        db.close_connection()


def listar_historial(id_orden, id_empresa):
    return _read_many(
        f"""
        SELECT h.id_orden_cambio_historial, h.id_orden_cambio,
               h.estado_anterior, h.estado_nuevo, h.accion, h.comentario,
               h.id_usuario, h.fecha_evento, h.ip_origen,
               COALESCE(NULLIF(p.nombre_completo, ''), u.username) AS usuario
        FROM {Config.SCHEMA}.t_orden_cambio_historial h
        JOIN {Config.SCHEMA}.t_orden_cambio oc
          ON oc.id_orden_cambio = h.id_orden_cambio
        LEFT JOIN {Config.SCHEMA}.t_usuario u ON u.id_usuario = h.id_usuario
        LEFT JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = u.id_persona
        WHERE h.id_orden_cambio = %s AND oc.id_empresa = %s
        ORDER BY h.fecha_evento, h.id_orden_cambio_historial
        """,
        (id_orden, id_empresa),
    )
