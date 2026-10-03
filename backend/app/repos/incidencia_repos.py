from app.classes.postgres import PostgreSQL
from app.repos.orden_trabajo_afectacion import AFECTADA_POR_INCIDENCIA_SQL


def obras_registro(id_empresa, id_usuario=None):
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query("""
            SELECT o.id_obra, o.codigo, o.nombre FROM obras.t_obra o
            WHERE (o.id_empresa = %s OR %s IS NULL)
              AND (%s IS NULL OR EXISTS (
                  SELECT 1 FROM obras.t_obra_usuario ou
                  JOIN obras.t_usuario u ON u.id_usuario = ou.id_usuario
                  WHERE ou.id_obra = o.id_obra AND u.id_usuario = %s
                    AND u.id_empresa = o.id_empresa AND u.estado = 'ACTIVO'
              )) ORDER BY o.nombre
        """, (id_empresa, id_empresa, id_usuario, id_usuario), fetchall=True) or []
        return [dict(zip(("id_obra", "codigo", "nombre"), row)) for row in rows]
    finally:
        db.close_connection()


def trabajador_en_obra(id_obra, id_usuario, id_empresa):
    return any(o["id_obra"] == id_obra for o in obras_registro(id_empresa, id_usuario))


_FIELDS = (
    "id_incidencia", "id_obra", "obra_codigo", "obra_nombre",
    "id_unidad", "unidad_codigo",
    "id_usuario_registro", "usuario_registro_nombre",
    "id_responsable", "responsable_nombre",
    "titulo", "descripcion", "prioridad", "estado",
    "created_at", "updated_at",
    "ubicacion", "fecha_inicio_atencion", "fecha_fin_atencion",
)

_SELECT_BASE = """
    SELECT i.id_incidencia, i.id_obra, o.codigo, o.nombre,
           i.id_unidad, u.codigo,
           i.id_usuario_registro,
           COALESCE(NULLIF(pr.nombre_completo, ''), ur.username),
           i.id_responsable,
           COALESCE(NULLIF(pa.nombre_completo, ''), ra.username),
           i.titulo, i.descripcion, i.prioridad, i.estado,
           i.created_at, i.updated_at,
           i.ubicacion, i.fecha_inicio_atencion, i.fecha_fin_atencion
    FROM obras.t_incidencia i
    JOIN obras.t_obra o ON o.id_obra = i.id_obra
    LEFT JOIN obras.t_unidad_construccion u ON u.id_unidad = i.id_unidad
    LEFT JOIN obras.t_usuario ur ON ur.id_usuario = i.id_usuario_registro
    LEFT JOIN obras.t_persona pr ON pr.id_persona = ur.id_persona
    LEFT JOIN obras.t_usuario ra ON ra.id_usuario = i.id_responsable
    LEFT JOIN obras.t_persona pa ON pa.id_persona = ra.id_persona
"""


def _incidencia(row):
    return dict(zip(_FIELDS, row))


# ─────────────────────────────────────────────────────────────────────────────
# VALIDACIÓN DE PERTENENCIA AL TENANT
# ─────────────────────────────────────────────────────────────────────────────
def obtener_empresa_obra(id_obra, id_empresa=None):
    """Devuelve el id_empresa de la obra si existe y pertenece al tenant (o None)."""
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


def obtener_empresa_incidencia(id_incidencia):
    """Empresa real (sin filtro de tenant) de la obra dueña de la incidencia."""
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            SELECT o.id_empresa
            FROM obras.t_incidencia i
            JOIN obras.t_obra o ON o.id_obra = i.id_obra
            WHERE i.id_incidencia = %s
            """,
            (id_incidencia,), fetchone=True
        )
        return row[0] if row else None
    finally:
        db.close_connection()


def unidad_pertenece_a_obra(id_unidad, id_obra):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            SELECT 1
            FROM obras.t_unidad_construccion u
            JOIN obras.t_estructura_obra e ON e.id_estructura = u.id_estructura
            WHERE u.id_unidad = %s AND e.id_obra = %s
            """,
            (id_unidad, id_obra), fetchone=True
        )
        return bool(row)
    finally:
        db.close_connection()


def usuario_pertenece_a_empresa(id_usuario, id_empresa):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            "SELECT 1 FROM obras.t_usuario WHERE id_usuario=%s AND id_empresa=%s",
            (id_usuario, id_empresa), fetchone=True
        )
        return bool(row)
    finally:
        db.close_connection()


def obtener_usuarios_asignables(id_empresa, id_obra):
    """Jefatura/supervisión activa del tenant y personal activo de la obra.

    Ser candidato no requiere permisos para administrar incidencias.
    La pertenencia a obra es independiente de las órdenes de trabajo.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(
            """
            SELECT DISTINCT u.id_usuario, u.username,
                   COALESCE(NULLIF(p.nombre_completo, ''), u.username),
                   r.nombre_rol
            FROM obras.t_usuario u
            JOIN obras.t_rol r ON r.id_rol = u.id_rol
            JOIN obras.t_obra o ON o.id_empresa = u.id_empresa
            LEFT JOIN obras.t_persona p ON p.id_persona = u.id_persona
            WHERE u.id_empresa = %s
              AND o.id_empresa = u.id_empresa
              AND o.id_obra = %s
              AND u.estado = 'ACTIVO'
              AND (
                  upper(replace(r.nombre_rol, '_', ' ')) IN (
                      'JEFE DE OBRA', 'SUPERVISOR', 'SUPERVISOR OBRA', 'SUPERVISOR DE OBRA'
                  )
                  OR (
                      r.nombre_rol IN ('ELECTRICO', 'PLOMERO', 'MAESTROALBAÑIL', 'ALBAÑIL')
                      AND EXISTS (SELECT 1 FROM obras.t_obra_usuario ou
                                  WHERE ou.id_obra = o.id_obra AND ou.id_usuario = u.id_usuario)
                  )
              )
            ORDER BY 3
            """,
            (id_empresa, id_obra), fetchall=True
        ) or []
        fields = ("nro_usuario", "nombre_usuario", "nombre_completo", "nombre_rol")
        return [dict(zip(fields, r)) for r in rows]
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# CRUD PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
def crear(id_obra, id_unidad, id_usuario_registro, titulo, descripcion, prioridad, ubicacion=None):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            INSERT INTO obras.t_incidencia
                (id_obra, id_unidad, id_usuario_registro, titulo, descripcion, prioridad, ubicacion, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'ABIERTA')
            RETURNING id_incidencia
            """,
            (id_obra, id_unidad, id_usuario_registro, titulo, descripcion, prioridad, ubicacion),
            fetchone=True,
        )
        db.conn.commit()
        return row[0]
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


def listar(id_empresa=None, id_obra=None, id_unidad=None, prioridad=None,
           estado=None, busqueda=None, id_responsable=None, page=1, limit=20,
           id_usuario_visible=None):
    filtros = []
    params = []
    if id_usuario_visible is not None:
        filtros.append("(i.id_usuario_registro = %s OR i.id_responsable = %s)")
        params.extend([id_usuario_visible, id_usuario_visible])
    if id_empresa is not None:
        filtros.append("o.id_empresa = %s")
        params.append(id_empresa)
    if id_obra is not None:
        filtros.append("i.id_obra = %s")
        params.append(id_obra)
    if id_unidad is not None:
        filtros.append("i.id_unidad = %s")
        params.append(id_unidad)
    if prioridad is not None:
        filtros.append("i.prioridad = %s")
        params.append(prioridad)
    if estado is not None:
        filtros.append("i.estado = %s")
        params.append(estado)
    if id_responsable is not None:
        filtros.append("i.id_responsable = %s")
        params.append(id_responsable)
    if busqueda:
        filtros.append("(i.titulo ILIKE %s OR i.descripcion ILIKE %s)")
        like = f"%{busqueda}%"
        params += [like, like]

    where = (" WHERE " + " AND ".join(filtros)) if filtros else ""

    db = PostgreSQL()
    db.create_connection()
    try:
        count_sql = f"""
            SELECT COUNT(*)
            FROM obras.t_incidencia i
            JOIN obras.t_obra o ON o.id_obra = i.id_obra
            {where}
        """
        total = db.execute_query(count_sql, tuple(params), fetchone=True)[0]

        rows = db.execute_query(
            _SELECT_BASE + where + " ORDER BY i.created_at DESC, i.id_incidencia DESC LIMIT %s OFFSET %s",
            tuple(params + [limit, (page - 1) * limit]),
            fetchall=True,
        ) or []
        return [_incidencia(r) for r in rows], total
    finally:
        db.close_connection()


def obtener_detalle(id_incidencia, id_empresa=None):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            _SELECT_BASE + " WHERE i.id_incidencia = %s AND (o.id_empresa = %s OR %s IS NULL)",
            (id_incidencia, id_empresa, id_empresa),
            fetchone=True,
        )
        return _incidencia(row) if row else None
    finally:
        db.close_connection()


def obtener_estado_actual(id_incidencia, id_empresa=None):
    """Devuelve (estado, id_responsable) bloqueando la fila para actualizaciones seguras."""
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            SELECT i.estado, i.id_responsable
            FROM obras.t_incidencia i
            JOIN obras.t_obra o ON o.id_obra = i.id_obra
            WHERE i.id_incidencia = %s AND (o.id_empresa = %s OR %s IS NULL)
            FOR UPDATE OF i
            """,
            (id_incidencia, id_empresa, id_empresa),
            fetchone=True,
        )
        return (row[0], row[1]) if row else (None, None)
    finally:
        db.close_connection()


def actualizar(id_incidencia, id_empresa, titulo, descripcion, prioridad,
               actualizar_ubicacion=False, ubicacion=None):
    """Si actualizar_ubicacion es False se conserva la ubicación actual
    (un cliente que no envía el campo no la borra)."""
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            UPDATE obras.t_incidencia i
            SET titulo = %s, descripcion = %s, prioridad = %s,
                ubicacion = CASE WHEN %s THEN %s ELSE i.ubicacion END
            FROM obras.t_obra o
            WHERE i.id_obra = o.id_obra
              AND i.id_incidencia = %s
              AND (o.id_empresa = %s OR %s IS NULL)
            RETURNING i.id_incidencia
            """,
            (titulo, descripcion, prioridad, bool(actualizar_ubicacion), ubicacion,
             id_incidencia, id_empresa, id_empresa),
            fetchone=True,
        )
        db.conn.commit()
        return bool(row)
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


def asignar_responsable(id_incidencia, id_empresa, id_responsable, nuevo_estado):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            UPDATE obras.t_incidencia i
            SET id_responsable = %s, estado = %s
            FROM obras.t_obra o
            WHERE i.id_obra = o.id_obra
              AND i.id_incidencia = %s
              AND (o.id_empresa = %s OR %s IS NULL)
            RETURNING i.id_incidencia
            """,
            (id_responsable, nuevo_estado, id_incidencia, id_empresa, id_empresa),
            fetchone=True,
        )
        db.conn.commit()
        return bool(row)
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


def cambiar_estado(id_incidencia, id_empresa, estado_actual, estado_nuevo, id_responsable_requerido=None):
    """
    Transición atómica y condicional: solo actualiza si la incidencia sigue en
    estado_actual (evita iniciar/finalizar dos veces ante peticiones
    concurrentes) y, si se indica, si el responsable asignado es
    id_responsable_requerido. Las fechas de atención se generan SIEMPRE en el
    servidor de BD (CURRENT_TIMESTAMP), nunca se aceptan desde el cliente:
      -> EN_PROCESO: fecha_inicio_atencion = ahora (solo si aún era NULL)
      -> PENDIENTE_VALIDACION:   fecha_fin_atencion    = ahora (nunca menor que el inicio)
    Devuelve False si no se cumplió alguna condición.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            UPDATE obras.t_incidencia i
            SET estado = %s,
                fecha_inicio_atencion = CASE WHEN %s = 'EN_PROCESO'
                    THEN COALESCE(i.fecha_inicio_atencion, CURRENT_TIMESTAMP) ELSE i.fecha_inicio_atencion END,
                fecha_fin_atencion = CASE WHEN %s = 'EN_PROCESO' THEN NULL
                    WHEN %s = 'PENDIENTE_VALIDACION'
                    THEN GREATEST(CURRENT_TIMESTAMP, i.fecha_inicio_atencion) ELSE i.fecha_fin_atencion END
            FROM obras.t_obra o
            WHERE i.id_obra = o.id_obra
              AND i.id_incidencia = %s
              AND (o.id_empresa = %s OR %s IS NULL)
              AND i.estado = %s
              AND (%s::INTEGER IS NULL OR i.id_responsable = %s)
              AND (%s <> 'EN_PROCESO' OR i.fecha_inicio_atencion IS NULL OR i.estado = 'PENDIENTE_VALIDACION')
              AND (%s <> 'PENDIENTE_VALIDACION' OR (i.fecha_inicio_atencion IS NOT NULL AND i.fecha_fin_atencion IS NULL))
            RETURNING i.id_incidencia
            """,
            (estado_nuevo, estado_nuevo, estado_nuevo, estado_nuevo,
             id_incidencia, id_empresa, id_empresa,
             estado_actual, id_responsable_requerido, id_responsable_requerido,
             estado_nuevo, estado_nuevo),
            fetchone=True,
        )
        db.conn.commit()
        return bool(row)
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# SEGUIMIENTO (bitácora funcional de la incidencia)
# ─────────────────────────────────────────────────────────────────────────────
def crear_seguimiento(id_incidencia, id_usuario, estado_anterior, estado_nuevo, observacion):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            INSERT INTO obras.t_incidencia_seguimiento
                (id_incidencia, id_usuario, estado_anterior, estado_nuevo, observacion)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id_seguimiento
            """,
            (id_incidencia, id_usuario, estado_anterior, estado_nuevo, observacion),
            fetchone=True,
        )
        db.conn.commit()
        return row[0]
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


def listar_seguimiento(id_incidencia, id_empresa=None):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            SELECT 1 FROM obras.t_incidencia i
            JOIN obras.t_obra o ON o.id_obra = i.id_obra
            WHERE i.id_incidencia = %s AND (o.id_empresa = %s OR %s IS NULL)
            """,
            (id_incidencia, id_empresa, id_empresa), fetchone=True
        )
        if not row:
            return None

        rows = db.execute_query(
            """
            SELECT s.id_seguimiento, s.id_usuario,
                   COALESCE(NULLIF(p.nombre_completo, ''), u.username),
                   s.estado_anterior, s.estado_nuevo, s.observacion, s.fecha
            FROM obras.t_incidencia_seguimiento s
            LEFT JOIN obras.t_usuario u ON u.id_usuario = s.id_usuario
            LEFT JOIN obras.t_persona p ON p.id_persona = u.id_persona
            WHERE s.id_incidencia = %s
            ORDER BY s.fecha DESC, s.id_seguimiento DESC
            """,
            (id_incidencia,), fetchall=True
        ) or []
        fields = ("id_seguimiento", "id_usuario", "usuario_nombre",
                  "estado_anterior", "estado_nuevo", "observacion", "fecha")
        return [dict(zip(fields, r)) for r in rows]
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# EVIDENCIAS (HU73)
# ─────────────────────────────────────────────────────────────────────────────
def crear_evidencia(id_incidencia, id_usuario, ruta_archivo, nombre_archivo, tipo_mime, tamano_bytes):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            INSERT INTO obras.t_incidencia_evidencia
                (id_incidencia, id_usuario, ruta_archivo, nombre_archivo, tipo_mime, tamano_bytes)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id_evidencia
            """,
            (id_incidencia, id_usuario, ruta_archivo, nombre_archivo, tipo_mime, tamano_bytes),
            fetchone=True,
        )
        db.conn.commit()
        return row[0]
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()


def listar_evidencias(id_incidencia, id_empresa=None):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            SELECT 1 FROM obras.t_incidencia i
            JOIN obras.t_obra o ON o.id_obra = i.id_obra
            WHERE i.id_incidencia = %s AND (o.id_empresa = %s OR %s IS NULL)
            """,
            (id_incidencia, id_empresa, id_empresa), fetchone=True
        )
        if not row:
            return None

        rows = db.execute_query(
            """
            SELECT id_evidencia, id_incidencia, id_usuario, ruta_archivo,
                   nombre_archivo, tipo_mime, tamano_bytes, fecha
            FROM obras.t_incidencia_evidencia
            WHERE id_incidencia = %s
            ORDER BY fecha DESC, id_evidencia DESC
            """,
            (id_incidencia,), fetchall=True
        ) or []
        fields = ("id_evidencia", "id_incidencia", "id_usuario", "ruta_archivo",
                  "nombre_archivo", "tipo_mime", "tamano_bytes", "fecha")
        return [dict(zip(fields, r)) for r in rows]
    finally:
        db.close_connection()


def obtener_evidencia(id_incidencia, id_evidencia, id_empresa=None):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            SELECT ev.id_evidencia, ev.id_incidencia, ev.ruta_archivo,
                   ev.nombre_archivo, ev.tipo_mime
            FROM obras.t_incidencia_evidencia ev
            JOIN obras.t_incidencia i ON i.id_incidencia = ev.id_incidencia
            JOIN obras.t_obra o ON o.id_obra = i.id_obra
            WHERE ev.id_evidencia = %s AND ev.id_incidencia = %s
              AND (o.id_empresa = %s OR %s IS NULL)
            """,
            (id_evidencia, id_incidencia, id_empresa, id_empresa), fetchone=True
        )
        if not row:
            return None
        fields = ("id_evidencia", "id_incidencia", "ruta_archivo", "nombre_archivo", "tipo_mime")
        return dict(zip(fields, row))
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# ÓRDENES DE TRABAJO AFECTADAS (relación M:N obras.t_incidencia_orden_trabajo)
# Solo LECTURA de obras.t_orden_trabajo: no se modifica nada del módulo de OT.
# El tenant de una OT se deriva siempre por t_orden_trabajo -> t_obra -> id_empresa.
# ─────────────────────────────────────────────────────────────────────────────
_OT_FIELDS = ("orden_nro", "id_obra", "tipo_trab", "cuadrilla", "estado",
              "fecha_inicio", "fecha_fin")


def listar_ordenes_trabajo_incidencia(id_incidencia):
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(
            f"""
            SELECT ot.orden_nro, ot.id_obra, ot.tipo_trab, ot.cuadrilla, ot.estado,
                   ot.fecha_inicio, ot.fecha_fin,
                   io.fecha_registro,
                   COALESCE(NULLIF(p.nombre_completo, ''), u.username),
                   {AFECTADA_POR_INCIDENCIA_SQL} AS afectada_por_incidencia
            FROM obras.t_incidencia_orden_trabajo io
            JOIN obras.t_incidencia i ON i.id_incidencia = io.id_incidencia
            JOIN obras.t_orden_trabajo ot ON ot.orden_nro = io.orden_nro AND ot.id_obra = i.id_obra
            LEFT JOIN obras.t_usuario u ON u.id_usuario = io.id_usuario
            LEFT JOIN obras.t_persona p ON p.id_persona = u.id_persona
            WHERE io.id_incidencia = %s
            ORDER BY ot.orden_nro
            """,
            (id_incidencia,), fetchall=True
        ) or []
        fields = _OT_FIELDS + ("fecha_vinculo", "usuario_vinculo_nombre", "afectada_por_incidencia")
        return [dict(zip(fields, r)) for r in rows]
    finally:
        db.close_connection()


def listar_ordenes_trabajo_obra(id_obra, id_empresa, id_incidencia):
    """OT candidatas: solo las de la MISMA obra y empresa real de la incidencia."""
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(
            """
            SELECT ot.orden_nro, ot.id_obra, ot.tipo_trab, ot.cuadrilla, ot.estado,
                   ot.fecha_inicio, ot.fecha_fin,
                   (io.orden_nro IS NOT NULL) AS afectada
            FROM obras.t_orden_trabajo ot
            JOIN obras.t_obra o ON o.id_obra = ot.id_obra
            LEFT JOIN obras.t_incidencia_orden_trabajo io
                   ON io.orden_nro = ot.orden_nro AND io.id_incidencia = %s
            WHERE ot.id_obra = %s AND o.id_empresa = %s
            ORDER BY ot.orden_nro
            """,
            (id_incidencia, id_obra, id_empresa), fetchall=True
        ) or []
        return [dict(zip(_OT_FIELDS + ("afectada",), r)) for r in rows]
    finally:
        db.close_connection()


def filtrar_ordenes_de_obra(ordenes, id_obra, id_empresa):
    """Subconjunto de 'ordenes' que pertenece a la obra Y a la empresa indicadas."""
    if not ordenes:
        return set()
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(
            """
            SELECT ot.orden_nro
            FROM obras.t_orden_trabajo ot
            JOIN obras.t_obra o ON o.id_obra = ot.id_obra
            WHERE ot.orden_nro = ANY(%s) AND ot.id_obra = %s AND o.id_empresa = %s
            """,
            (list(ordenes), id_obra, id_empresa), fetchall=True
        ) or []
        return {r[0] for r in rows}
    finally:
        db.close_connection()


def reemplazar_ordenes_trabajo(id_incidencia, ordenes, id_usuario):
    """
    Deja exactamente 'ordenes' como OT afectadas de la incidencia, en una sola
    transacción. Devuelve (agregadas, quitadas) como listas ordenadas.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        actuales = {
            r[0] for r in (db.execute_query(
                "SELECT orden_nro FROM obras.t_incidencia_orden_trabajo WHERE id_incidencia = %s",
                (id_incidencia,), fetchall=True
            ) or [])
        }
        nuevas = set(ordenes)
        quitar = sorted(actuales - nuevas)
        agregar = sorted(nuevas - actuales)

        if quitar:
            db.execute_query(
                "DELETE FROM obras.t_incidencia_orden_trabajo WHERE id_incidencia = %s AND orden_nro = ANY(%s)",
                (id_incidencia, quitar),
            )
        for orden_nro in agregar:
            db.execute_query(
                """
                INSERT INTO obras.t_incidencia_orden_trabajo (id_incidencia, orden_nro, id_usuario)
                VALUES (%s, %s, %s)
                ON CONFLICT (id_incidencia, orden_nro) DO NOTHING
                """,
                (id_incidencia, orden_nro, id_usuario),
            )
        db.conn.commit()
        return agregar, quitar
    except Exception:
        if db.conn:
            db.conn.rollback()
        raise
    finally:
        db.close_connection()
