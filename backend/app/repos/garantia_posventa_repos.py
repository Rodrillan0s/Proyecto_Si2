"""
Repositorio CU42 – Garantías Inmobiliarias y Servicio Posventa (HU161–HU168).
Acceso a datos parametrizado sobre obras.t_garantia_inmobiliaria,
obras.t_solicitud_posventa y obras.t_posventa_seguimiento.
"""
from app.classes.postgres import PostgreSQL
from app.config import Config


def _iso(valor):
    return valor.isoformat() if hasattr(valor, "isoformat") else valor


def obtener_unidad_con_empresa(id_unidad: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            f"""
            SELECT u.id_unidad, u.codigo, u.nombre, e.id_obra, o.nombre AS obra_nombre, o.id_empresa
            FROM {Config.SCHEMA}.t_unidad_construccion u
            JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
            JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
            WHERE u.id_unidad = %s
            LIMIT 1;
            """,
            (id_unidad,),
            fetchone=True,
        )
        if not row:
            return None
        return {
            "id_unidad": row[0],
            "unidad_codigo": row[1],
            "unidad_nombre": row[2],
            "id_obra": row[3],
            "obra_nombre": row[4],
            "id_empresa": row[5],
        }
    finally:
        db.close_connection()


def obtener_usuario_activo_empresa(id_usuario: int, id_empresa: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            f"""
            SELECT u.id_usuario, u.id_empresa, r.nombre_rol,
                   COALESCE(NULLIF(p.nombre_completo, ''), u.username) AS nombre_completo
            FROM {Config.SCHEMA}.t_usuario u
            JOIN {Config.SCHEMA}.t_rol r ON r.id_rol = u.id_rol
            LEFT JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = u.id_persona
            WHERE u.id_usuario = %s
              AND u.id_empresa = %s
              AND u.estado = 'ACTIVO'
            LIMIT 1;
            """,
            (id_usuario, id_empresa),
            fetchone=True,
        )
        if not row:
            return None
        return {
            "id_usuario": row[0],
            "id_empresa": row[1],
            "nombre_rol": row[2],
            "nombre_completo": row[3],
        }
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# HU161 / HU162 – GARANTÍAS INMOBILIARIAS
# ─────────────────────────────────────────────────────────────────────────────
def crear_garantia(
    id_empresa: int,
    id_unidad: int,
    codigo: str | None,
    tipo_garantia: str,
    descripcion: str,
    fecha_inicio,
    fecha_fin,
    observaciones: str | None,
    id_usuario_registro: int,
) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            f"""
            INSERT INTO {Config.SCHEMA}.t_garantia_inmobiliaria (
                id_empresa, id_unidad, codigo, tipo_garantia, descripcion,
                fecha_inicio, fecha_fin, observaciones, id_usuario_registro
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_garantia, creado_en;
            """,
            (
                id_empresa,
                id_unidad,
                codigo,
                tipo_garantia,
                descripcion,
                fecha_inicio,
                fecha_fin,
                observaciones,
                id_usuario_registro,
            ),
            fetchone=True,
            commit=True,
        )
        return {
            "id_garantia": row[0],
            "id_empresa": id_empresa,
            "id_unidad": id_unidad,
            "codigo": codigo,
            "tipo_garantia": tipo_garantia,
            "descripcion": descripcion,
            "fecha_inicio": _iso(fecha_inicio),
            "fecha_fin": _iso(fecha_fin),
            "observaciones": observaciones,
            "creado_en": _iso(row[1]),
        }
    finally:
        db.close_connection()


def obtener_garantia_por_id(id_garantia: int, id_empresa: int | None = None):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            f"""
            SELECT g.id_garantia, g.id_empresa, g.id_unidad, u.codigo, u.nombre,
                   o.id_obra, o.nombre, g.codigo, g.tipo_garantia, g.descripcion,
                   g.fecha_inicio, g.fecha_fin, g.observaciones, g.id_usuario_registro, g.creado_en
            FROM {Config.SCHEMA}.t_garantia_inmobiliaria g
            JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = g.id_unidad
            JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
            JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
            WHERE g.id_garantia = %s
              AND (%s IS NULL OR g.id_empresa = %s)
            LIMIT 1;
            """,
            (id_garantia, id_empresa, id_empresa),
            fetchone=True,
        )
        return _map_garantia(row) if row else None
    finally:
        db.close_connection()


def listar_garantias(id_empresa: int | None = None, id_unidad: int | None = None, id_cliente: int | None = None):
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(
            f"""
            SELECT g.id_garantia, g.id_empresa, g.id_unidad, u.codigo, u.nombre,
                   o.id_obra, o.nombre, g.codigo, g.tipo_garantia, g.descripcion,
                   g.fecha_inicio, g.fecha_fin, g.observaciones, g.id_usuario_registro, g.creado_en
            FROM {Config.SCHEMA}.t_garantia_inmobiliaria g
            JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = g.id_unidad
            JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
            JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
            WHERE (%s IS NULL OR g.id_empresa = %s)
              AND (%s IS NULL OR g.id_unidad = %s)
              AND (
                  %s IS NULL OR EXISTS (
                      SELECT 1 FROM {Config.SCHEMA}.t_crm_cliente_unidad cu
                      WHERE cu.id_cliente = %s AND cu.id_unidad = g.id_unidad
                  )
              )
            ORDER BY g.creado_en DESC, g.id_garantia DESC;
            """,
            (id_empresa, id_empresa, id_unidad, id_unidad, id_cliente, id_cliente),
            fetchall=True,
        ) or []
        return [_map_garantia(r) for r in rows]
    finally:
        db.close_connection()


def _map_garantia(row) -> dict:
    return {
        "id_garantia": row[0],
        "id_empresa": row[1],
        "id_unidad": row[2],
        "unidad_codigo": row[3],
        "unidad_nombre": row[4],
        "id_obra": row[5],
        "obra_nombre": row[6],
        "codigo": row[7],
        "tipo_garantia": row[8],
        "descripcion": row[9],
        "fecha_inicio": _iso(row[10]),
        "fecha_fin": _iso(row[11]),
        "observaciones": row[12],
        "id_usuario_registro": row[13],
        "creado_en": _iso(row[14]),
    }


# ─────────────────────────────────────────────────────────────────────────────
# HU163–HU168 – SOLICITUDES DE POSVENTA Y SEGUIMIENTO
# ─────────────────────────────────────────────────────────────────────────────
def crear_solicitud_posventa(
    id_empresa: int,
    id_unidad: int,
    id_cliente: int,
    id_garantia: int | None,
    titulo: str,
    descripcion: str,
    id_usuario_creacion: int,
) -> int:
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            f"""
            INSERT INTO {Config.SCHEMA}.t_solicitud_posventa (
                id_empresa, id_unidad, id_cliente, id_garantia,
                titulo, descripcion, estado, id_usuario_creacion
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'REGISTRADA', %s)
            RETURNING id_solicitud_posventa;
            """,
            (
                id_empresa,
                id_unidad,
                id_cliente,
                id_garantia,
                titulo,
                descripcion,
                id_usuario_creacion,
            ),
            fetchone=True,
            commit=True,
        )
        return row[0]
    finally:
        db.close_connection()


def registrar_seguimiento(
    id_solicitud_posventa: int,
    id_usuario: int,
    accion: str,
    estado_anterior: str | None,
    estado_nuevo: str | None,
    observacion: str,
) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            f"""
            INSERT INTO {Config.SCHEMA}.t_posventa_seguimiento (
                id_solicitud_posventa, id_usuario, accion,
                estado_anterior, estado_nuevo, observacion
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id_seguimiento, creado_en;
            """,
            (
                id_solicitud_posventa,
                id_usuario,
                accion,
                estado_anterior,
                estado_nuevo,
                observacion,
            ),
            fetchone=True,
            commit=True,
        )
        return {
            "id_seguimiento": row[0],
            "id_solicitud_posventa": id_solicitud_posventa,
            "id_usuario": id_usuario,
            "accion": accion,
            "estado_anterior": estado_anterior,
            "estado_nuevo": estado_nuevo,
            "observacion": observacion,
            "creado_en": _iso(row[1]),
        }
    finally:
        db.close_connection()


def actualizar_clasificacion(id_solicitud_posventa: int, categoria: str, nuevo_estado: str):
    db = PostgreSQL()
    db.create_connection()
    try:
        db.execute_query(
            f"""
            UPDATE {Config.SCHEMA}.t_solicitud_posventa
            SET categoria = %s,
                estado = %s,
                actualizado_en = CURRENT_TIMESTAMP
            WHERE id_solicitud_posventa = %s;
            """,
            (categoria, nuevo_estado, id_solicitud_posventa),
            commit=True,
        )
    finally:
        db.close_connection()


def actualizar_asignacion(id_solicitud_posventa: int, id_responsable: int, nuevo_estado: str):
    db = PostgreSQL()
    db.create_connection()
    try:
        db.execute_query(
            f"""
            UPDATE {Config.SCHEMA}.t_solicitud_posventa
            SET id_responsable = %s,
                estado = %s,
                actualizado_en = CURRENT_TIMESTAMP
            WHERE id_solicitud_posventa = %s;
            """,
            (id_responsable, nuevo_estado, id_solicitud_posventa),
            commit=True,
        )
    finally:
        db.close_connection()


def actualizar_estado(id_solicitud_posventa: int, nuevo_estado: str):
    db = PostgreSQL()
    db.create_connection()
    try:
        db.execute_query(
            f"""
            UPDATE {Config.SCHEMA}.t_solicitud_posventa
            SET estado = %s,
                actualizado_en = CURRENT_TIMESTAMP
            WHERE id_solicitud_posventa = %s;
            """,
            (nuevo_estado, id_solicitud_posventa),
            commit=True,
        )
    finally:
        db.close_connection()


_SOLICITUD_SELECT = f"""
    SELECT s.id_solicitud_posventa, s.id_empresa, s.id_unidad,
           u.codigo, u.nombre, o.id_obra, o.nombre,
           s.id_cliente, COALESCE(NULLIF(pc.nombre_completo, ''), 'Cliente #' || s.id_cliente),
           s.id_garantia, g.codigo, g.tipo_garantia,
           s.titulo, s.descripcion, s.categoria, s.estado,
           s.id_responsable, COALESCE(NULLIF(pr.nombre_completo, ''), ur.username),
           s.id_usuario_creacion, s.creado_en, s.actualizado_en
    FROM {Config.SCHEMA}.t_solicitud_posventa s
    JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = s.id_unidad
    JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
    JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
    JOIN {Config.SCHEMA}.t_crm_cliente c ON c.id_cliente = s.id_cliente
    LEFT JOIN {Config.SCHEMA}.t_persona pc ON pc.id_persona = c.id_persona
    LEFT JOIN {Config.SCHEMA}.t_garantia_inmobiliaria g ON g.id_garantia = s.id_garantia
    LEFT JOIN {Config.SCHEMA}.t_usuario ur ON ur.id_usuario = s.id_responsable
    LEFT JOIN {Config.SCHEMA}.t_persona pr ON pr.id_persona = ur.id_persona
"""


def _map_solicitud(row) -> dict:
    return {
        "id_solicitud_posventa": row[0],
        "id_empresa": row[1],
        "id_unidad": row[2],
        "unidad_codigo": row[3],
        "unidad_nombre": row[4],
        "id_obra": row[5],
        "obra_nombre": row[6],
        "id_cliente": row[7],
        "cliente_nombre": row[8],
        "id_garantia": row[9],
        "garantia_codigo": row[10],
        "garantia_tipo": row[11],
        "titulo": row[12],
        "descripcion": row[13],
        "categoria": row[14],
        "estado": row[15],
        "id_responsable": row[16],
        "responsable_nombre": row[17],
        "id_usuario_creacion": row[18],
        "creado_en": _iso(row[19]),
        "actualizado_en": _iso(row[20]),
    }


def obtener_solicitud_por_id(id_solicitud_posventa: int, id_empresa: int | None = None):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            _SOLICITUD_SELECT
            + " WHERE s.id_solicitud_posventa = %s AND (%s IS NULL OR s.id_empresa = %s) LIMIT 1;",
            (id_solicitud_posventa, id_empresa, id_empresa),
            fetchone=True,
        )
        return _map_solicitud(row) if row else None
    finally:
        db.close_connection()


def listar_solicitudes(
    id_empresa: int | None = None,
    id_cliente: int | None = None,
    id_unidad: int | None = None,
    estado: str | None = None,
    categoria: str | None = None,
    id_responsable: int | None = None,
):
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(
            _SOLICITUD_SELECT
            + """
            WHERE (%s IS NULL OR s.id_empresa = %s)
              AND (%s IS NULL OR s.id_cliente = %s)
              AND (%s IS NULL OR s.id_unidad = %s)
              AND (%s IS NULL OR s.estado = %s)
              AND (%s IS NULL OR s.categoria = %s)
              AND (%s IS NULL OR s.id_responsable = %s)
            ORDER BY s.creado_en DESC, s.id_solicitud_posventa DESC;
            """,
            (
                id_empresa, id_empresa,
                id_cliente, id_cliente,
                id_unidad, id_unidad,
                estado, estado,
                categoria, categoria,
                id_responsable, id_responsable,
            ),
            fetchall=True,
        ) or []
        return [_map_solicitud(r) for r in rows]
    finally:
        db.close_connection()


def listar_seguimiento_solicitud(id_solicitud_posventa: int) -> list[dict]:
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(
            f"""
            SELECT sg.id_seguimiento, sg.id_solicitud_posventa, sg.id_usuario,
                   COALESCE(NULLIF(p.nombre_completo, ''), u.username) AS usuario_nombre,
                   sg.accion, sg.estado_anterior, sg.estado_nuevo,
                   sg.observacion, sg.creado_en
            FROM {Config.SCHEMA}.t_posventa_seguimiento sg
            LEFT JOIN {Config.SCHEMA}.t_usuario u ON u.id_usuario = sg.id_usuario
            LEFT JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = u.id_persona
            WHERE sg.id_solicitud_posventa = %s
            ORDER BY sg.creado_en ASC, sg.id_seguimiento ASC;
            """,
            (id_solicitud_posventa,),
            fetchall=True,
        ) or []
        return [
            {
                "id_seguimiento": r[0],
                "id_solicitud_posventa": r[1],
                "id_usuario": r[2],
                "usuario_nombre": r[3],
                "accion": r[4],
                "estado_anterior": r[5],
                "estado_nuevo": r[6],
                "observacion": r[7],
                "creado_en": _iso(r[8]),
            }
            for r in rows
        ]
    finally:
        db.close_connection()
