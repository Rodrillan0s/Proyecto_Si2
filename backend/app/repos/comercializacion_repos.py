"""
Repositorio de datos para CU31: Gestión de comercialización de unidades inmobiliarias
(HU143, HU144, HU145, HU146).
Garantiza aislamiento multi-tenant estricto uniendo:
t_unidad_construccion -> t_estructura_obra -> t_obra -> t_empresa
y atomicidad transaccional en reservas, cambios de estado, ventas e historial.
"""
from typing import Dict, List, Optional, Tuple
from app.classes.postgres import PostgreSQL
from app.config import Config


def _commit_tx(db: PostgreSQL):
    """Confirma explícitamente la transacción activa sobre la conexión PostgreSQL."""
    if getattr(db, "conn", None) and not getattr(db.conn, "closed", False):
        db.conn.commit()


def _rollback_tx(db: PostgreSQL):
    """Revierte explícitamente la transacción activa sobre la conexión PostgreSQL."""
    if getattr(db, "conn", None) and not getattr(db.conn, "closed", False):
        try:
            db.conn.rollback()
        except Exception:
            pass


def verificar_pertenencia_unidad_empresa(id_unidad: int, id_empresa: int) -> bool:
    """Valida si la unidad pertenece a la empresa especificada."""
    sql = f"""
        SELECT 1
        FROM {Config.SCHEMA}.t_unidad_construccion u
        INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
        INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
        WHERE u.id_unidad = %s AND o.id_empresa = %s;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(sql, (id_unidad, id_empresa), fetchone=True)
        return bool(row)
    finally:
        db.close_connection()


def verificar_pertenencia_cliente_empresa(id_cliente: int, id_empresa: int) -> Optional[Dict]:
    """Valida que el cliente CRM exista y pertenezca a la misma empresa."""
    sql = f"""
        SELECT c.id_cliente, c.id_empresa, p.nombre_completo, c.email, p.telefono,
               c.tipo_cliente, c.estado
        FROM {Config.SCHEMA}.t_crm_cliente c
        INNER JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = c.id_persona
        WHERE c.id_cliente = %s AND c.id_empresa = %s;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        r = db.execute_query(sql, (id_cliente, id_empresa), fetchone=True)
        if not r:
            return None
        return {
            "id_cliente": r[0],
            "id_empresa": r[1],
            "nombre_completo": r[2],
            "email": r[3],
            "telefono": r[4],
            "tipo_cliente": r[5],
            "estado": r[6],
        }
    finally:
        db.close_connection()


def listar_unidades_comercializacion(
    id_empresa: int,
    id_obra: Optional[int] = None,
    estado_comercial: Optional[str] = None,
    publicado: Optional[bool] = None,
    tipo_unidad: Optional[str] = None,
    solo_disponibles: bool = False,
    q: Optional[str] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None,
    page: int = 1,
    limit: int = 20
) -> Tuple[List[Dict], int]:
    """
    Lista unidades inmobiliarias con su información comercial y estado efectivo de disponibilidad.
    Filtro estricto por id_empresa.
    """
    filtros = ["o.id_empresa = %s"]
    params: List = [id_empresa]

    if id_obra:
        filtros.append("o.id_obra = %s")
        params.append(id_obra)

    if estado_comercial:
        filtros.append("COALESCE(u.estado_comercial, 'DISPONIBLE') = %s")
        params.append(estado_comercial.strip().upper())

    if publicado is not None:
        filtros.append("COALESCE(u.publicado_comercial, FALSE) = %s")
        params.append(bool(publicado))

    if tipo_unidad:
        filtros.append("u.tipo_unidad = %s")
        params.append(tipo_unidad.strip().upper())

    if precio_min is not None:
        filtros.append("COALESCE(u.precio_venta, 0) >= %s")
        params.append(precio_min)

    if precio_max is not None:
        filtros.append("COALESCE(u.precio_venta, 0) <= %s")
        params.append(precio_max)

    if q and q.strip():
        term = f"%{q.strip().lower()}%"
        filtros.append(
            "(LOWER(u.codigo) LIKE %s OR LOWER(e.nombre) LIKE %s "
            "OR LOWER(o.nombre) LIKE %s OR LOWER(COALESCE(u.descripcion_comercial, '')) LIKE %s)"
        )
        params.extend([term, term, term, term])

    if solo_disponibles:
        filtros.append("COALESCE(u.estado_comercial, 'DISPONIBLE') = 'DISPONIBLE'")
        filtros.append(f"""
            NOT EXISTS (
                SELECT 1 FROM {Config.SCHEMA}.t_crm_cliente_unidad cu_sub
                WHERE cu_sub.id_unidad = u.id_unidad
                  AND cu_sub.estado_asociacion IN ('RESERVADO', 'VENDIDO', 'ENTREGADO')
            )
        """)

    where_clause = " AND ".join(filtros)
    offset = max(0, (page - 1) * limit)

    sql = f"""
        SELECT 
            u.id_unidad,
            u.codigo,
            u.tipo_unidad,
            u.superficie,
            u.estado AS estado_constructivo,
            COALESCE(u.estado_comercial, 'DISPONIBLE') AS estado_comercial,
            COALESCE(u.publicado_comercial, FALSE) AS publicado_comercial,
            u.precio_venta,
            COALESCE(u.moneda_comercial, 'BOB') AS moneda_comercial,
            u.descripcion_comercial,
            e.id_estructura,
            e.nombre AS nombre_estructura,
            o.id_obra,
            o.nombre AS nombre_obra,
            o.codigo AS codigo_obra,
            -- Disponibilidad comercial efectiva
            CASE 
                WHEN COALESCE(u.estado_comercial, 'DISPONIBLE') = 'DISPONIBLE'
                     AND NOT EXISTS (
                         SELECT 1 FROM {Config.SCHEMA}.t_crm_cliente_unidad cu
                         WHERE cu.id_unidad = u.id_unidad
                           AND cu.estado_asociacion IN ('RESERVADO', 'VENDIDO', 'ENTREGADO')
                     ) THEN TRUE
                ELSE FALSE
            END AS disponible_efectiva,
            -- Conteo de fotos
            (
                SELECT COUNT(*)
                FROM {Config.SCHEMA}.t_unidad_fotografia f
                WHERE f.id_unidad = u.id_unidad
            ) AS total_fotos,
            -- Foto principal
            (
                SELECT f.ruta_archivo
                FROM {Config.SCHEMA}.t_unidad_fotografia f
                WHERE f.id_unidad = u.id_unidad
                ORDER BY f.es_principal DESC, f.orden ASC, f.id_fotografia ASC
                LIMIT 1
            ) AS foto_principal,
            -- Asociación activa en CRM
            (
                SELECT cu.estado_asociacion
                FROM {Config.SCHEMA}.t_crm_cliente_unidad cu
                WHERE cu.id_unidad = u.id_unidad
                  AND cu.estado_asociacion IN ('RESERVADO', 'VENDIDO', 'ENTREGADO', 'INTERESADO')
                ORDER BY CASE cu.estado_asociacion
                    WHEN 'ENTREGADO' THEN 1
                    WHEN 'VENDIDO' THEN 2
                    WHEN 'RESERVADO' THEN 3
                    ELSE 4
                END
                LIMIT 1
            ) AS estado_crm_activo,
            COUNT(*) OVER() AS total_registros
        FROM {Config.SCHEMA}.t_unidad_construccion u
        INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
        INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
        WHERE {where_clause}
        ORDER BY o.nombre ASC, u.codigo ASC
        LIMIT %s OFFSET %s;
    """

    db = PostgreSQL()
    db.create_connection()
    try:
        query_params = list(params) + [limit, offset]
        rows = db.execute_query(sql, tuple(query_params), fetchall=True) or []
        total = rows[0][19] if rows else 0

        unidades = []
        for r in rows:
            unidades.append({
                "id_unidad": r[0],
                "codigo": r[1],
                "tipo_unidad": r[2],
                "superficie": float(r[3]) if r[3] is not None else None,
                "estado_constructivo": r[4],
                "estado_comercial": r[5],
                "publicado_comercial": bool(r[6]),
                "precio_venta": float(r[7]) if r[7] is not None else None,
                "moneda_comercial": r[8],
                "descripcion_comercial": r[9],
                "id_estructura": r[10],
                "nombre_estructura": r[11],
                "id_obra": r[12],
                "nombre_obra": r[13],
                "codigo_obra": r[14],
                "disponible_efectiva": bool(r[15]),
                "total_fotos": int(r[16] or 0),
                "foto_principal": r[17],
                "estado_crm_activo": r[18],
            })
        return unidades, total
    finally:
        db.close_connection()


def obtener_unidad_comercial(id_unidad: int, id_empresa: int) -> Optional[Dict]:
    """
    Obtiene la ficha comercial detallada de una unidad, con fotos,
    asociaciones CRM activas e historial comercial.
    Aislamiento estricto por id_empresa.
    """
    sql_base = f"""
        SELECT 
            u.id_unidad,
            u.codigo,
            u.tipo_unidad,
            u.superficie,
            u.estado AS estado_constructivo,
            COALESCE(u.estado_comercial, 'DISPONIBLE') AS estado_comercial,
            COALESCE(u.publicado_comercial, FALSE) AS publicado_comercial,
            u.precio_venta,
            COALESCE(u.moneda_comercial, 'BOB') AS moneda_comercial,
            u.descripcion_comercial,
            e.id_estructura,
            e.nombre AS nombre_estructura,
            o.id_obra,
            o.nombre AS nombre_obra,
            o.codigo AS codigo_obra,
            o.id_empresa,
            CASE 
                WHEN COALESCE(u.estado_comercial, 'DISPONIBLE') = 'DISPONIBLE'
                     AND NOT EXISTS (
                         SELECT 1 FROM {Config.SCHEMA}.t_crm_cliente_unidad cu
                         WHERE cu.id_unidad = u.id_unidad
                           AND cu.estado_asociacion IN ('RESERVADO', 'VENDIDO', 'ENTREGADO')
                     ) THEN TRUE
                ELSE FALSE
            END AS disponible_efectiva
        FROM {Config.SCHEMA}.t_unidad_construccion u
        INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
        INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
        WHERE u.id_unidad = %s AND o.id_empresa = %s;
    """

    sql_crm = f"""
        SELECT 
            cu.id_cliente_unidad,
            cu.id_cliente,
            cu.estado_asociacion,
            cu.monto_pactado,
            cu.monto_reserva,
            cu.fecha_vencimiento_reserva,
            cu.fecha_asociacion,
            cu.observaciones,
            p.nombre_completo AS nombre_cliente,
            p.telefono AS telefono_cliente,
            c.email AS email_cliente,
            cu.id_usuario_registro
        FROM {Config.SCHEMA}.t_crm_cliente_unidad cu
        INNER JOIN {Config.SCHEMA}.t_crm_cliente c ON c.id_cliente = cu.id_cliente
        INNER JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = c.id_persona
        WHERE cu.id_unidad = %s
          AND c.id_empresa = %s
          AND cu.estado_asociacion IN ('RESERVADO', 'VENDIDO', 'ENTREGADO', 'INTERESADO')
        ORDER BY CASE cu.estado_asociacion
            WHEN 'ENTREGADO' THEN 1
            WHEN 'VENDIDO' THEN 2
            WHEN 'RESERVADO' THEN 3
            ELSE 4
        END, cu.fecha_asociacion DESC
        LIMIT 1;
    """

    sql_fotos = f"""
        SELECT id_fotografia, ruta_archivo, nombre_archivo, tipo_mime, tamano_bytes,
               es_principal, orden, id_usuario, created_at
        FROM {Config.SCHEMA}.t_unidad_fotografia
        WHERE id_unidad = %s
        ORDER BY es_principal DESC, orden ASC, id_fotografia ASC;
    """

    sql_historial = f"""
        SELECT h.id_historial, h.tipo_evento, h.estado_anterior, h.estado_nuevo,
               h.precio_venta, h.monto_pactado, h.observacion, h.fecha,
               u.username AS usuario_registro,
               p.nombre_completo AS cliente_relacionado,
               h.id_cliente, h.id_cliente_unidad, h.id_usuario
        FROM {Config.SCHEMA}.t_unidad_historial_comercial h
        LEFT JOIN {Config.SCHEMA}.t_usuario u ON u.id_usuario = h.id_usuario
        LEFT JOIN {Config.SCHEMA}.t_crm_cliente c ON c.id_cliente = h.id_cliente
        LEFT JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = c.id_persona
        WHERE h.id_unidad = %s
        ORDER BY h.fecha DESC, h.id_historial DESC
        LIMIT 20;
    """

    db = PostgreSQL()
    db.create_connection()
    try:
        r = db.execute_query(sql_base, (id_unidad, id_empresa), fetchone=True)
        if not r:
            return None

        crm_row = db.execute_query(sql_crm, (id_unidad, id_empresa), fetchone=True)
        asociacion_crm = None
        if crm_row:
            asociacion_crm = {
                "id_cliente_unidad": crm_row[0],
                "id_cliente": crm_row[1],
                "estado_asociacion": crm_row[2],
                "monto_pactado": float(crm_row[3]) if crm_row[3] is not None else None,
                "monto_reserva": float(crm_row[4]) if crm_row[4] is not None else None,
                "fecha_vencimiento_reserva": crm_row[5].isoformat() if hasattr(crm_row[5], "isoformat") else crm_row[5],
                "fecha_asociacion": crm_row[6].isoformat() if hasattr(crm_row[6], "isoformat") else crm_row[6],
                "observaciones": crm_row[7],
                "nombre_cliente": crm_row[8],
                "telefono_cliente": crm_row[9],
                "email_cliente": crm_row[10],
                "id_usuario_registro": crm_row[11] if len(crm_row) > 11 else None,
            }

        fotos_rows = db.execute_query(sql_fotos, (id_unidad,), fetchall=True) or []
        fotografias = [
            {
                "id_fotografia": f[0],
                "ruta_archivo": f[1],
                "nombre_archivo": f[2],
                "tipo_mime": f[3],
                "tamano_bytes": f[4],
                "es_principal": bool(f[5]),
                "orden": f[6],
                "id_usuario": f[7] if len(f) > 7 else None,
                "created_at": f[8].isoformat() if len(f) > 8 and hasattr(f[8], "isoformat") else None,
            }
            for f in fotos_rows
        ]

        hist_rows = db.execute_query(sql_historial, (id_unidad,), fetchall=True) or []
        historial = [
            {
                "id_historial": h[0],
                "tipo_evento": h[1],
                "estado_anterior": h[2],
                "estado_nuevo": h[3],
                "precio_venta": float(h[4]) if h[4] is not None else None,
                "monto_pactado": float(h[5]) if h[5] is not None else None,
                "observacion": h[6],
                "fecha": h[7].isoformat() if hasattr(h[7], "isoformat") else h[7],
                "usuario_registro": h[8],
                "cliente_relacionado": h[9],
                "id_cliente": h[10] if len(h) > 10 else None,
                "id_cliente_unidad": h[11] if len(h) > 11 else None,
                "id_usuario": h[12] if len(h) > 12 else None,
            }
            for h in hist_rows
        ]

        return {
            "id_unidad": r[0],
            "codigo": r[1],
            "tipo_unidad": r[2],
            "superficie": float(r[3]) if r[3] is not None else None,
            "estado_constructivo": r[4],
            "estado_comercial": r[5],
            "publicado_comercial": bool(r[6]),
            "precio_venta": float(r[7]) if r[7] is not None else None,
            "moneda_comercial": r[8],
            "descripcion_comercial": r[9],
            "id_estructura": r[10],
            "nombre_estructura": r[11],
            "id_obra": r[12],
            "nombre_obra": r[13],
            "codigo_obra": r[14],
            "id_empresa": r[15],
            "disponible_efectiva": bool(r[16]),
            "asociacion_crm": asociacion_crm,
            "fotografias": fotografias,
            "historial_reciente": historial,
        }
    finally:
        db.close_connection()


def actualizar_unidad_comercial(
    id_unidad: int,
    id_empresa: int,
    publicado_comercial: Optional[bool] = None,
    precio_venta: Optional[float] = None,
    actualizar_precio: bool = False,
    moneda_comercial: Optional[str] = None,
    descripcion_comercial: Optional[str] = None,
    actualizar_descripcion: bool = False,
    estado_comercial: Optional[str] = None,
    eventos_historial: Optional[List[Dict]] = None
) -> bool:
    """
    Actualiza de forma atómica los atributos comerciales de la unidad y registra
    los eventos correspondientes en t_unidad_historial_comercial.
    Garantiza aislamiento multi-tenant verificando pertenencia a id_empresa.
    NO altera la columna 'estado' constructivo.
    """
    campos = []
    params = []

    if publicado_comercial is not None:
        campos.append("publicado_comercial = %s")
        params.append(bool(publicado_comercial))

    if actualizar_precio or precio_venta is not None:
        campos.append("precio_venta = %s")
        params.append(precio_venta)

    if moneda_comercial is not None:
        campos.append("moneda_comercial = %s")
        params.append(moneda_comercial.strip().upper())

    if actualizar_descripcion or descripcion_comercial is not None:
        campos.append("descripcion_comercial = %s")
        params.append(descripcion_comercial.strip() if descripcion_comercial else None)

    if estado_comercial is not None:
        campos.append("estado_comercial = %s")
        params.append(estado_comercial.strip().upper())

    if not campos and not eventos_historial:
        return True

    db = PostgreSQL()
    db.create_connection()
    try:
        if campos:
            update_params = list(params) + [id_unidad, id_empresa]
            sql_update = f"""
                UPDATE {Config.SCHEMA}.t_unidad_construccion u
                SET {', '.join(campos)}
                WHERE u.id_unidad = %s
                  AND u.id_estructura IN (
                      SELECT e.id_estructura
                      FROM {Config.SCHEMA}.t_estructura_obra e
                      INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
                      WHERE o.id_empresa = %s
                  );
            """
            db.execute_query(sql_update, tuple(update_params), commit=False)

        if eventos_historial:
            sql_hist = f"""
                INSERT INTO {Config.SCHEMA}.t_unidad_historial_comercial (
                    id_unidad, tipo_evento, estado_anterior, estado_nuevo,
                    precio_venta, monto_pactado, observacion, id_usuario,
                    id_cliente, id_cliente_unidad
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            for ev in eventos_historial:
                db.execute_query(sql_hist, (
                    id_unidad,
                    str(ev.get("tipo_evento", "ACTUALIZACION_COMERCIAL")).strip().upper(),
                    ev.get("estado_anterior"),
                    ev.get("estado_nuevo"),
                    ev.get("precio_venta"),
                    ev.get("monto_pactado"),
                    ev.get("observacion"),
                    ev.get("id_usuario"),
                    ev.get("id_cliente"),
                    ev.get("id_cliente_unidad"),
                ), commit=False)

        _commit_tx(db)
        return True
    except Exception:
        _rollback_tx(db)
        raise
    finally:
        db.close_connection()


def registrar_historial_comercial(
    id_unidad: int,
    tipo_evento: str,
    estado_anterior: Optional[str] = None,
    estado_nuevo: Optional[str] = None,
    precio_venta: Optional[float] = None,
    monto_pactado: Optional[float] = None,
    observacion: Optional[str] = None,
    id_usuario: Optional[int] = None,
    id_cliente: Optional[int] = None,
    id_cliente_unidad: Optional[int] = None
) -> Optional[int]:
    """Registra una entrada en el historial comercial inmutable de la unidad."""
    sql = f"""
        INSERT INTO {Config.SCHEMA}.t_unidad_historial_comercial (
            id_unidad, tipo_evento, estado_anterior, estado_nuevo,
            precio_venta, monto_pactado, observacion, id_usuario,
            id_cliente, id_cliente_unidad
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id_historial;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        res = db.execute_query(sql, (
            id_unidad, tipo_evento.strip().upper(), estado_anterior, estado_nuevo,
            precio_venta, monto_pactado, observacion, id_usuario,
            id_cliente, id_cliente_unidad
        ), fetchone=True, commit=True)
        return res[0] if res else None
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# HU143: GESTIÓN DE FOTOGRAFÍAS DE LA UNIDAD
# ─────────────────────────────────────────────────────────────────────────────
def listar_fotografias_unidad(id_unidad: int, id_empresa: int) -> List[Dict]:
    """Lista las fotografías de una unidad verificando pertenencia a la empresa."""
    sql = f"""
        SELECT f.id_fotografia, f.id_unidad, f.ruta_archivo, f.nombre_archivo,
               f.tipo_mime, f.tamano_bytes, f.es_principal, f.orden,
               f.id_usuario, f.created_at
        FROM {Config.SCHEMA}.t_unidad_fotografia f
        INNER JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = f.id_unidad
        INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
        INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
        WHERE f.id_unidad = %s AND o.id_empresa = %s
        ORDER BY f.es_principal DESC, f.orden ASC, f.id_fotografia ASC;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(sql, (id_unidad, id_empresa), fetchall=True) or []
        return [
            {
                "id_fotografia": r[0],
                "id_unidad": r[1],
                "ruta_archivo": r[2],
                "nombre_archivo": r[3],
                "tipo_mime": r[4],
                "tamano_bytes": r[5],
                "es_principal": bool(r[6]),
                "orden": r[7],
                "id_usuario": r[8],
                "created_at": r[9].isoformat() if hasattr(r[9], "isoformat") else r[9],
            }
            for r in rows
        ]
    finally:
        db.close_connection()


def obtener_fotografia_unidad(id_fotografia: int, id_unidad: int, id_empresa: int) -> Optional[Dict]:
    """Obtiene una fotografía específica validando aislamiento por unidad y empresa."""
    sql = f"""
        SELECT f.id_fotografia, f.id_unidad, f.ruta_archivo, f.nombre_archivo,
               f.tipo_mime, f.tamano_bytes, f.es_principal, f.orden,
               f.id_usuario, f.created_at
        FROM {Config.SCHEMA}.t_unidad_fotografia f
        INNER JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = f.id_unidad
        INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
        INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
        WHERE f.id_fotografia = %s AND f.id_unidad = %s AND o.id_empresa = %s;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        r = db.execute_query(sql, (id_fotografia, id_unidad, id_empresa), fetchone=True)
        if not r:
            return None
        return {
            "id_fotografia": r[0],
            "id_unidad": r[1],
            "ruta_archivo": r[2],
            "nombre_archivo": r[3],
            "tipo_mime": r[4],
            "tamano_bytes": r[5],
            "es_principal": bool(r[6]),
            "orden": r[7],
            "id_usuario": r[8],
            "created_at": r[9].isoformat() if hasattr(r[9], "isoformat") else r[9],
        }
    finally:
        db.close_connection()


def crear_fotografia_unidad_transaccional(
    id_unidad: int,
    id_empresa: int,
    ruta_archivo: str,
    nombre_archivo: str,
    tipo_mime: str,
    tamano_bytes: int,
    es_principal: bool,
    orden: int,
    id_usuario: Optional[int],
    estado_actual: str,
    precio_actual: Optional[float]
) -> Dict:
    """
    Inserta una fotografía en t_unidad_fotografia, actualiza la fotografía principal si corresponde
    y registra el evento en el historial comercial dentro de una sola transacción.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        row_count = db.execute_query(
            f"SELECT COUNT(*) FROM {Config.SCHEMA}.t_unidad_fotografia WHERE id_unidad = %s;",
            (id_unidad,),
            fetchone=True,
            commit=False
        )
        total_existentes = int(row_count[0]) if row_count else 0
        es_principal_efectivo = True if total_existentes == 0 else bool(es_principal)

        if es_principal_efectivo and total_existentes > 0:
            db.execute_query(
                f"UPDATE {Config.SCHEMA}.t_unidad_fotografia SET es_principal = FALSE WHERE id_unidad = %s;",
                (id_unidad,),
                commit=False
            )

        sql_insert = f"""
            INSERT INTO {Config.SCHEMA}.t_unidad_fotografia (
                id_unidad, ruta_archivo, nombre_archivo, tipo_mime,
                tamano_bytes, es_principal, orden, id_usuario
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_fotografia, created_at;
        """
        inserted = db.execute_query(
            sql_insert,
            (id_unidad, ruta_archivo, nombre_archivo, tipo_mime, tamano_bytes, es_principal_efectivo, orden, id_usuario),
            fetchone=True,
            commit=False
        )
        id_foto = inserted[0] if inserted else None
        created_at = inserted[1].isoformat() if inserted and len(inserted) > 1 and hasattr(inserted[1], "isoformat") else None

        sql_hist = f"""
            INSERT INTO {Config.SCHEMA}.t_unidad_historial_comercial (
                id_unidad, tipo_evento, estado_anterior, estado_nuevo,
                precio_venta, observacion, id_usuario
            )
            VALUES (%s, 'FOTOGRAFIA_AGREGADA', %s, %s, %s, %s, %s);
        """
        db.execute_query(
            sql_hist,
            (
                id_unidad,
                estado_actual,
                estado_actual,
                precio_actual,
                f"Fotografía comercial agregada: {nombre_archivo}" + (" (principal)" if es_principal_efectivo else ""),
                id_usuario
            ),
            commit=False
        )

        _commit_tx(db)
        return {
            "id_fotografia": id_foto,
            "id_unidad": id_unidad,
            "ruta_archivo": ruta_archivo,
            "nombre_archivo": nombre_archivo,
            "tipo_mime": tipo_mime,
            "tamano_bytes": tamano_bytes,
            "es_principal": es_principal_efectivo,
            "orden": orden,
            "id_usuario": id_usuario,
            "created_at": created_at,
        }
    except Exception:
        _rollback_tx(db)
        raise
    finally:
        db.close_connection()


def marcar_fotografia_principal_transaccional(
    id_fotografia: int,
    id_unidad: int,
    id_empresa: int,
    id_usuario: Optional[int] = None
) -> Optional[Dict]:
    """Marca una fotografía como principal y desmarca las demás de la unidad atómicamente."""
    db = PostgreSQL()
    db.create_connection()
    try:
        sql_check = f"""
            SELECT f.id_fotografia, f.nombre_archivo, COALESCE(u.estado_comercial, 'DISPONIBLE'), u.precio_venta
            FROM {Config.SCHEMA}.t_unidad_fotografia f
            INNER JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = f.id_unidad
            INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
            INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
            WHERE f.id_fotografia = %s AND f.id_unidad = %s AND o.id_empresa = %s
            FOR UPDATE;
        """
        foto = db.execute_query(sql_check, (id_fotografia, id_unidad, id_empresa), fetchone=True, commit=False)
        if not foto:
            return None

        db.execute_query(
            f"""
            UPDATE {Config.SCHEMA}.t_unidad_fotografia
            SET es_principal = (id_fotografia = %s)
            WHERE id_unidad = %s;
            """,
            (id_fotografia, id_unidad),
            commit=False
        )

        db.execute_query(
            f"""
            INSERT INTO {Config.SCHEMA}.t_unidad_historial_comercial (
                id_unidad, tipo_evento, estado_anterior, estado_nuevo,
                precio_venta, observacion, id_usuario
            )
            VALUES (%s, 'ACTUALIZACION_COMERCIAL', %s, %s, %s, %s, %s);
            """,
            (id_unidad, foto[2], foto[2], foto[3], f"Fotografía principal actualizada: {foto[1]}", id_usuario),
            commit=False
        )

        _commit_tx(db)
        return {
            "id_fotografia": id_fotografia,
            "id_unidad": id_unidad,
            "nombre_archivo": foto[1],
            "es_principal": True,
        }
    except Exception:
        _rollback_tx(db)
        raise
    finally:
        db.close_connection()


def eliminar_fotografia_unidad_transaccional(
    id_fotografia: int,
    id_unidad: int,
    id_empresa: int,
    id_usuario: Optional[int] = None
) -> Optional[Dict]:
    """Elimina una fotografía de la unidad, promueve otra como principal si era principal y registra historial."""
    db = PostgreSQL()
    db.create_connection()
    try:
        sql_check = f"""
            SELECT f.id_fotografia, f.ruta_archivo, f.nombre_archivo, f.es_principal,
                   COALESCE(u.estado_comercial, 'DISPONIBLE'), u.precio_venta
            FROM {Config.SCHEMA}.t_unidad_fotografia f
            INNER JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = f.id_unidad
            INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
            INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
            WHERE f.id_fotografia = %s AND f.id_unidad = %s AND o.id_empresa = %s
            FOR UPDATE;
        """
        foto = db.execute_query(sql_check, (id_fotografia, id_unidad, id_empresa), fetchone=True, commit=False)
        if not foto:
            return None

        era_principal = bool(foto[3])

        db.execute_query(
            f"DELETE FROM {Config.SCHEMA}.t_unidad_fotografia WHERE id_fotografia = %s AND id_unidad = %s;",
            (id_fotografia, id_unidad),
            commit=False
        )

        if era_principal:
            siguiente = db.execute_query(
                f"""
                SELECT id_fotografia
                FROM {Config.SCHEMA}.t_unidad_fotografia
                WHERE id_unidad = %s
                ORDER BY orden ASC, id_fotografia ASC
                LIMIT 1;
                """,
                (id_unidad,),
                fetchone=True,
                commit=False
            )
            if siguiente:
                db.execute_query(
                    f"UPDATE {Config.SCHEMA}.t_unidad_fotografia SET es_principal = TRUE WHERE id_fotografia = %s;",
                    (siguiente[0],),
                    commit=False
                )

        db.execute_query(
            f"""
            INSERT INTO {Config.SCHEMA}.t_unidad_historial_comercial (
                id_unidad, tipo_evento, estado_anterior, estado_nuevo,
                precio_venta, observacion, id_usuario
            )
            VALUES (%s, 'FOTOGRAFIA_ELIMINADA', %s, %s, %s, %s, %s);
            """,
            (id_unidad, foto[4], foto[4], foto[5], f"Fotografía eliminada: {foto[2]}", id_usuario),
            commit=False
        )

        _commit_tx(db)
        return {
            "id_fotografia": foto[0],
            "id_unidad": id_unidad,
            "ruta_archivo": foto[1],
            "nombre_archivo": foto[2],
        }
    except Exception:
        _rollback_tx(db)
        raise
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# HU144: REGISTRAR RESERVA TRANSACCIONAL
# ─────────────────────────────────────────────────────────────────────────────
def registrar_reserva_transaccional(
    id_unidad: int,
    id_empresa: int,
    id_cliente: int,
    monto_reserva: float,
    monto_pactado: Optional[float],
    fecha_vencimiento_reserva: Optional[str],
    observaciones: Optional[str],
    id_usuario: Optional[int]
) -> Dict:
    """
    Ejecuta en una única transacción atómica:
    1. Validación de pertenencia de la unidad a id_empresa con bloqueo FOR UPDATE.
    2. Validación de pertenencia del cliente a la misma id_empresa.
    3. Verificación de que la unidad esté DISPONIBLE y no tenga reserva/venta activa.
    4. Creación o actualización de t_crm_cliente_unidad a estado 'RESERVADO'.
    5. Actualización de t_unidad_construccion.estado_comercial a 'RESERVADA'.
    6. Inserción del evento 'RESERVA' en t_unidad_historial_comercial.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        # 1. Bloquear y verificar unidad en la empresa autorizada
        sql_unidad = f"""
            SELECT u.id_unidad, u.codigo, COALESCE(u.estado_comercial, 'DISPONIBLE'),
                   u.precio_venta, COALESCE(u.moneda_comercial, 'BOB')
            FROM {Config.SCHEMA}.t_unidad_construccion u
            INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
            INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
            WHERE u.id_unidad = %s AND o.id_empresa = %s
            FOR UPDATE;
        """
        u_row = db.execute_query(sql_unidad, (id_unidad, id_empresa), fetchone=True, commit=False)
        if not u_row:
            raise LookupError("La unidad no existe o no pertenece a su empresa autorizada.")

        codigo_unidad = u_row[1]
        estado_actual = u_row[2]
        precio_venta = float(u_row[3]) if u_row[3] is not None else None
        moneda = u_row[4]

        # 2. Verificar cliente en la misma empresa
        sql_cliente = f"""
            SELECT c.id_cliente, p.nombre_completo, c.estado
            FROM {Config.SCHEMA}.t_crm_cliente c
            INNER JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = c.id_persona
            WHERE c.id_cliente = %s AND c.id_empresa = %s;
        """
        c_row = db.execute_query(sql_cliente, (id_cliente, id_empresa), fetchone=True, commit=False)
        if not c_row:
            raise PermissionError("El cliente especificado no existe o no pertenece a su empresa autorizada.")

        nombre_cliente = c_row[1]

        # 3. Impedir doble reserva o venta activa (por estado comercial o asociación CRM)
        if estado_actual != "DISPONIBLE":
            raise RuntimeError(f"CONFLICTO_ESTADO:La unidad '{codigo_unidad}' no está disponible (estado actual: {estado_actual}).")

        sql_crm_activa = f"""
            SELECT id_cliente_unidad, estado_asociacion, id_cliente
            FROM {Config.SCHEMA}.t_crm_cliente_unidad
            WHERE id_unidad = %s
              AND estado_asociacion IN ('RESERVADO', 'VENDIDO', 'ENTREGADO')
            FOR UPDATE;
        """
        activa_row = db.execute_query(sql_crm_activa, (id_unidad,), fetchone=True, commit=False)
        if activa_row:
            raise RuntimeError(
                f"CONFLICTO_RESERVA:La unidad '{codigo_unidad}' ya posee una asociación activa ({activa_row[1]})."
            )

        monto_pactado_efectivo = monto_pactado if monto_pactado is not None else precio_venta

        # 4. Actualizar asociación previa en estado INTERESADO del mismo cliente o insertar nueva fila RESERVADO
        sql_interesado = f"""
            SELECT id_cliente_unidad
            FROM {Config.SCHEMA}.t_crm_cliente_unidad
            WHERE id_unidad = %s AND id_cliente = %s AND estado_asociacion = 'INTERESADO'
            FOR UPDATE;
        """
        interesado_row = db.execute_query(sql_interesado, (id_unidad, id_cliente), fetchone=True, commit=False)

        if interesado_row:
            id_cliente_unidad = interesado_row[0]
            sql_upd_crm = f"""
                UPDATE {Config.SCHEMA}.t_crm_cliente_unidad
                SET estado_asociacion = 'RESERVADO',
                    monto_reserva = %s,
                    monto_pactado = %s,
                    fecha_vencimiento_reserva = %s,
                    id_usuario_registro = %s,
                    observaciones = COALESCE(%s, observaciones),
                    fecha_asociacion = CURRENT_TIMESTAMP
                WHERE id_cliente_unidad = %s;
            """
            db.execute_query(
                sql_upd_crm,
                (monto_reserva, monto_pactado_efectivo, fecha_vencimiento_reserva, id_usuario, observaciones, id_cliente_unidad),
                commit=False
            )
        else:
            sql_ins_crm = f"""
                INSERT INTO {Config.SCHEMA}.t_crm_cliente_unidad (
                    id_cliente, id_unidad, estado_asociacion, monto_pactado,
                    monto_reserva, fecha_vencimiento_reserva, id_usuario_registro, observaciones
                )
                VALUES (%s, %s, 'RESERVADO', %s, %s, %s, %s, %s)
                RETURNING id_cliente_unidad;
            """
            ins_crm = db.execute_query(
                sql_ins_crm,
                (id_cliente, id_unidad, monto_pactado_efectivo, monto_reserva, fecha_vencimiento_reserva, id_usuario, observaciones),
                fetchone=True,
                commit=False
            )
            id_cliente_unidad = ins_crm[0] if ins_crm else None

        # 5. Actualizar estado comercial en t_unidad_construccion a RESERVADA (sin tocar estado constructivo)
        db.execute_query(
            f"UPDATE {Config.SCHEMA}.t_unidad_construccion SET estado_comercial = 'RESERVADA' WHERE id_unidad = %s;",
            (id_unidad,),
            commit=False
        )

        # 6. Registrar evento RESERVA en historial comercial
        obs_hist = observaciones or f"Reserva registrada para {nombre_cliente} por {monto_reserva} {moneda}"
        sql_hist = f"""
            INSERT INTO {Config.SCHEMA}.t_unidad_historial_comercial (
                id_unidad, id_cliente, id_cliente_unidad, tipo_evento,
                estado_anterior, estado_nuevo, precio_venta, monto_pactado,
                observacion, id_usuario
            )
            VALUES (%s, %s, %s, 'RESERVA', %s, 'RESERVADA', %s, %s, %s, %s)
            RETURNING id_historial;
        """
        hist_row = db.execute_query(
            sql_hist,
            (
                id_unidad, id_cliente, id_cliente_unidad,
                estado_actual, precio_venta, monto_pactado_efectivo,
                obs_hist, id_usuario
            ),
            fetchone=True,
            commit=False
        )
        id_historial = hist_row[0] if hist_row else None

        _commit_tx(db)
        return {
            "id_unidad": id_unidad,
            "codigo_unidad": codigo_unidad,
            "id_cliente": id_cliente,
            "nombre_cliente": nombre_cliente,
            "id_cliente_unidad": id_cliente_unidad,
            "id_historial": id_historial,
            "estado_anterior": estado_actual,
            "estado_comercial": "RESERVADA",
            "estado_asociacion": "RESERVADO",
            "monto_reserva": monto_reserva,
            "monto_pactado": monto_pactado_efectivo,
            "fecha_vencimiento_reserva": fecha_vencimiento_reserva,
            "id_usuario_registro": id_usuario,
        }
    except Exception:
        _rollback_tx(db)
        raise
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# HU145: CANCELAR RESERVA Y CONFIRMAR VENTA TRANSACCIONALES
# ─────────────────────────────────────────────────────────────────────────────
def cancelar_reserva_transaccional(
    id_unidad: int,
    id_empresa: int,
    motivo: Optional[str],
    id_usuario: Optional[int]
) -> Dict:
    """
    Cancela/libera una reserva activa de forma atómica:
    1. Verifica que la unidad pertenezca a la empresa y esté RESERVADA o con reserva CRM activa.
    2. Actualiza t_crm_cliente_unidad a 'CANCELADO'.
    3. Actualiza t_unidad_construccion.estado_comercial a 'DISPONIBLE'.
    4. Registra evento 'CANCELACION' en t_unidad_historial_comercial.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        sql_unidad = f"""
            SELECT u.id_unidad, u.codigo, COALESCE(u.estado_comercial, 'DISPONIBLE'), u.precio_venta
            FROM {Config.SCHEMA}.t_unidad_construccion u
            INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
            INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
            WHERE u.id_unidad = %s AND o.id_empresa = %s
            FOR UPDATE;
        """
        u_row = db.execute_query(sql_unidad, (id_unidad, id_empresa), fetchone=True, commit=False)
        if not u_row:
            raise LookupError("La unidad no existe o no pertenece a su empresa autorizada.")

        codigo_unidad = u_row[1]
        estado_actual = u_row[2]
        precio_venta = float(u_row[3]) if u_row[3] is not None else None

        if estado_actual == "VENDIDA":
            raise RuntimeError("ESTADO_INCONSISTENTE:No se puede cancelar una reserva sobre una unidad que ya figura como VENDIDA.")

        sql_res = f"""
            SELECT id_cliente_unidad, id_cliente, monto_pactado, estado_asociacion
            FROM {Config.SCHEMA}.t_crm_cliente_unidad
            WHERE id_unidad = %s
              AND estado_asociacion IN ('RESERVADO', 'VENDIDO', 'ENTREGADO')
            FOR UPDATE;
        """
        res_row = db.execute_query(sql_res, (id_unidad,), fetchone=True, commit=False)

        if res_row and res_row[3] in ("VENDIDO", "ENTREGADO"):
            raise RuntimeError("ESTADO_INCONSISTENTE:La unidad ya tiene una venta cerrada en CRM.")

        if estado_actual != "RESERVADA" and not res_row:
            raise RuntimeError("SIN_RESERVA_ACTIVA:La unidad no tiene una reserva activa para cancelar.")

        id_cliente_unidad = res_row[0] if res_row else None
        id_cliente = res_row[1] if res_row else None
        monto_pactado = float(res_row[2]) if res_row and res_row[2] is not None else None

        obs_cancelacion = motivo or "Reserva cancelada y unidad liberada comercialmente"

        if id_cliente_unidad:
            db.execute_query(
                f"""
                UPDATE {Config.SCHEMA}.t_crm_cliente_unidad
                SET estado_asociacion = 'CANCELADO',
                    observaciones = %s
                WHERE id_cliente_unidad = %s;
                """,
                (obs_cancelacion, id_cliente_unidad),
                commit=False
            )

        db.execute_query(
            f"UPDATE {Config.SCHEMA}.t_unidad_construccion SET estado_comercial = 'DISPONIBLE' WHERE id_unidad = %s;",
            (id_unidad,),
            commit=False
        )

        hist_row = db.execute_query(
            f"""
            INSERT INTO {Config.SCHEMA}.t_unidad_historial_comercial (
                id_unidad, id_cliente, id_cliente_unidad, tipo_evento,
                estado_anterior, estado_nuevo, precio_venta, monto_pactado,
                observacion, id_usuario
            )
            VALUES (%s, %s, %s, 'CANCELACION', %s, 'DISPONIBLE', %s, %s, %s, %s)
            RETURNING id_historial;
            """,
            (id_unidad, id_cliente, id_cliente_unidad, estado_actual, precio_venta, monto_pactado, obs_cancelacion, id_usuario),
            fetchone=True,
            commit=False
        )
        id_historial = hist_row[0] if hist_row else None

        _commit_tx(db)
        return {
            "id_unidad": id_unidad,
            "codigo_unidad": codigo_unidad,
            "id_cliente": id_cliente,
            "id_cliente_unidad": id_cliente_unidad,
            "id_historial": id_historial,
            "estado_anterior": estado_actual,
            "estado_comercial": "DISPONIBLE",
            "estado_asociacion": "CANCELADO" if id_cliente_unidad else None,
            "observacion": obs_cancelacion,
        }
    except Exception:
        _rollback_tx(db)
        raise
    finally:
        db.close_connection()


def confirmar_venta_transaccional(
    id_unidad: int,
    id_empresa: int,
    id_cliente: Optional[int],
    monto_pactado: Optional[float],
    observaciones: Optional[str],
    id_usuario: Optional[int]
) -> Dict:
    """
    Confirma la venta de una unidad inmobiliaria en una sola transacción:
    1. Valida pertenencia de la unidad a la empresa y bloquea la fila.
    2. Impide vender unidades en estado VENDIDA o NO_DISPONIBLE.
    3. Sincroniza con t_crm_cliente_unidad (promueve reserva activa a VENDIDO o asocia al cliente de la misma empresa).
    4. Actualiza t_unidad_construccion.estado_comercial a 'VENDIDA'.
    5. Registra evento 'VENTA' en t_unidad_historial_comercial.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        sql_unidad = f"""
            SELECT u.id_unidad, u.codigo, COALESCE(u.estado_comercial, 'DISPONIBLE'),
                   u.precio_venta, COALESCE(u.moneda_comercial, 'BOB')
            FROM {Config.SCHEMA}.t_unidad_construccion u
            INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
            INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
            WHERE u.id_unidad = %s AND o.id_empresa = %s
            FOR UPDATE;
        """
        u_row = db.execute_query(sql_unidad, (id_unidad, id_empresa), fetchone=True, commit=False)
        if not u_row:
            raise LookupError("La unidad no existe o no pertenece a su empresa autorizada.")

        codigo_unidad = u_row[1]
        estado_actual = u_row[2]
        precio_venta = float(u_row[3]) if u_row[3] is not None else None
        moneda = u_row[4]

        if estado_actual == "VENDIDA":
            raise RuntimeError("CONFLICTO_ESTADO:La unidad ya se encuentra en estado VENDIDA.")
        if estado_actual == "NO_DISPONIBLE":
            raise RuntimeError("ESTADO_INCONSISTENTE:No se puede confirmar venta de una unidad marcada como NO_DISPONIBLE.")

        sql_crm_activa = f"""
            SELECT id_cliente_unidad, id_cliente, estado_asociacion, monto_pactado
            FROM {Config.SCHEMA}.t_crm_cliente_unidad
            WHERE id_unidad = %s
              AND estado_asociacion IN ('RESERVADO', 'VENDIDO', 'ENTREGADO')
            FOR UPDATE;
        """
        activa_row = db.execute_query(sql_crm_activa, (id_unidad,), fetchone=True, commit=False)

        if activa_row and activa_row[2] in ("VENDIDO", "ENTREGADO"):
            raise RuntimeError("CONFLICTO_ESTADO:La unidad ya posee una venta confirmada en CRM.")

        if activa_row and activa_row[2] == "RESERVADO":
            id_cliente_unidad = activa_row[0]
            id_cliente_reserva = activa_row[1]
            if id_cliente is not None and int(id_cliente) != int(id_cliente_reserva):
                raise RuntimeError(
                    "CONFLICTO_CLIENTE:La unidad tiene una reserva activa a nombre de otro cliente. Debe cancelar la reserva antes de vender a un tercero."
                )
            id_cliente_efectivo = id_cliente_reserva
            monto_reserva_pactado = float(activa_row[3]) if activa_row[3] is not None else None
            monto_pactado_efectivo = monto_pactado if monto_pactado is not None else (monto_reserva_pactado or precio_venta)

            db.execute_query(
                f"""
                UPDATE {Config.SCHEMA}.t_crm_cliente_unidad
                SET estado_asociacion = 'VENDIDO',
                    monto_pactado = %s,
                    observaciones = COALESCE(%s, observaciones)
                WHERE id_cliente_unidad = %s;
                """,
                (monto_pactado_efectivo, observaciones, id_cliente_unidad),
                commit=False
            )
        else:
            if not id_cliente:
                raise RuntimeError("CLIENTE_REQUERIDO:Para confirmar una venta sin reserva previa debe especificar id_cliente.")

            # Validar pertenencia del cliente a la misma empresa
            c_row = db.execute_query(
                f"""
                SELECT c.id_cliente, p.nombre_completo
                FROM {Config.SCHEMA}.t_crm_cliente c
                INNER JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = c.id_persona
                WHERE c.id_cliente = %s AND c.id_empresa = %s;
                """,
                (id_cliente, id_empresa),
                fetchone=True,
                commit=False
            )
            if not c_row:
                raise PermissionError("El cliente especificado no existe o no pertenece a su empresa autorizada.")

            id_cliente_efectivo = int(id_cliente)
            monto_pactado_efectivo = monto_pactado if monto_pactado is not None else precio_venta

            interesado_row = db.execute_query(
                f"""
                SELECT id_cliente_unidad
                FROM {Config.SCHEMA}.t_crm_cliente_unidad
                WHERE id_unidad = %s AND id_cliente = %s AND estado_asociacion = 'INTERESADO'
                FOR UPDATE;
                """,
                (id_unidad, id_cliente_efectivo),
                fetchone=True,
                commit=False
            )
            if interesado_row:
                id_cliente_unidad = interesado_row[0]
                db.execute_query(
                    f"""
                    UPDATE {Config.SCHEMA}.t_crm_cliente_unidad
                    SET estado_asociacion = 'VENDIDO',
                        monto_pactado = %s,
                        id_usuario_registro = COALESCE(%s, id_usuario_registro),
                        observaciones = COALESCE(%s, observaciones)
                    WHERE id_cliente_unidad = %s;
                    """,
                    (monto_pactado_efectivo, id_usuario, observaciones, id_cliente_unidad),
                    commit=False
                )
            else:
                ins_crm = db.execute_query(
                    f"""
                    INSERT INTO {Config.SCHEMA}.t_crm_cliente_unidad (
                        id_cliente, id_unidad, estado_asociacion, monto_pactado,
                        id_usuario_registro, observaciones
                    )
                    VALUES (%s, %s, 'VENDIDO', %s, %s, %s)
                    RETURNING id_cliente_unidad;
                    """,
                    (id_cliente_efectivo, id_unidad, monto_pactado_efectivo, id_usuario, observaciones),
                    fetchone=True,
                    commit=False
                )
                id_cliente_unidad = ins_crm[0] if ins_crm else None

        # Actualizar estado comercial de la unidad a VENDIDA
        db.execute_query(
            f"UPDATE {Config.SCHEMA}.t_unidad_construccion SET estado_comercial = 'VENDIDA' WHERE id_unidad = %s;",
            (id_unidad,),
            commit=False
        )

        obs_venta = observaciones or f"Venta confirmada por {monto_pactado_efectivo} {moneda}"
        hist_row = db.execute_query(
            f"""
            INSERT INTO {Config.SCHEMA}.t_unidad_historial_comercial (
                id_unidad, id_cliente, id_cliente_unidad, tipo_evento,
                estado_anterior, estado_nuevo, precio_venta, monto_pactado,
                observacion, id_usuario
            )
            VALUES (%s, %s, %s, 'VENTA', %s, 'VENDIDA', %s, %s, %s, %s)
            RETURNING id_historial;
            """,
            (
                id_unidad, id_cliente_efectivo, id_cliente_unidad,
                estado_actual, precio_venta, monto_pactado_efectivo,
                obs_venta, id_usuario
            ),
            fetchone=True,
            commit=False
        )
        id_historial = hist_row[0] if hist_row else None

        _commit_tx(db)
        return {
            "id_unidad": id_unidad,
            "codigo_unidad": codigo_unidad,
            "id_cliente": id_cliente_efectivo,
            "id_cliente_unidad": id_cliente_unidad,
            "id_historial": id_historial,
            "estado_anterior": estado_actual,
            "estado_comercial": "VENDIDA",
            "estado_asociacion": "VENDIDO",
            "monto_pactado": monto_pactado_efectivo,
            "observacion": obs_venta,
        }
    except Exception:
        _rollback_tx(db)
        raise
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# HU146: HISTORIAL COMERCIAL Y RESUMEN / KPIs
# ─────────────────────────────────────────────────────────────────────────────
def listar_historial_unidad(
    id_unidad: int,
    id_empresa: int,
    tipo_evento: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """
    Lista cronológicamente los eventos históricos comerciales de la unidad
    incluyendo cliente, usuario, fechas, montos y estados.
    """
    filtros = ["h.id_unidad = %s", "o.id_empresa = %s"]
    params: List = [id_unidad, id_empresa]

    if tipo_evento and tipo_evento.strip():
        filtros.append("h.tipo_evento = %s")
        params.append(tipo_evento.strip().upper())

    params.append(limit)
    where_clause = " AND ".join(filtros)

    sql = f"""
        SELECT h.id_historial,
               h.id_unidad,
               h.tipo_evento,
               h.estado_anterior,
               h.estado_nuevo,
               h.precio_venta,
               h.monto_pactado,
               h.observacion,
               h.fecha,
               u.username AS usuario_registro,
               p.nombre_completo AS cliente_relacionado,
               h.id_cliente,
               h.id_cliente_unidad,
               h.id_usuario,
               cu.monto_reserva,
               cu.fecha_vencimiento_reserva,
               cu.estado_asociacion
        FROM {Config.SCHEMA}.t_unidad_historial_comercial h
        INNER JOIN {Config.SCHEMA}.t_unidad_construccion uc ON uc.id_unidad = h.id_unidad
        INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = uc.id_estructura
        INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
        LEFT JOIN {Config.SCHEMA}.t_usuario u ON u.id_usuario = h.id_usuario
        LEFT JOIN {Config.SCHEMA}.t_crm_cliente c ON c.id_cliente = h.id_cliente
        LEFT JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = c.id_persona
        LEFT JOIN {Config.SCHEMA}.t_crm_cliente_unidad cu ON cu.id_cliente_unidad = h.id_cliente_unidad
        WHERE {where_clause}
        ORDER BY h.fecha DESC, h.id_historial DESC
        LIMIT %s;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(sql, tuple(params), fetchall=True) or []
        resultado = []
        for r in rows:
            item = {
                "id_historial": r[0],
                "id_unidad": r[1],
                "tipo_evento": r[2],
                "estado_anterior": r[3],
                "estado_nuevo": r[4],
                "precio_venta": float(r[5]) if r[5] is not None else None,
                "monto_pactado": float(r[6]) if r[6] is not None else None,
                "observacion": r[7],
                "fecha": r[8].isoformat() if hasattr(r[8], "isoformat") else r[8],
                "usuario_registro": r[9],
                "cliente_relacionado": r[10],
            }
            if len(r) > 11:
                item["id_cliente"] = r[11]
                item["id_cliente_unidad"] = r[12]
                item["id_usuario"] = r[13]
                item["monto_reserva"] = float(r[14]) if r[14] is not None else None
                item["fecha_vencimiento_reserva"] = r[15].isoformat() if hasattr(r[15], "isoformat") else r[15]
                item["estado_asociacion_crm"] = r[16]
            resultado.append(item)
        return resultado
    finally:
        db.close_connection()


def obtener_resumen_comercial(id_empresa: int, id_obra: Optional[int] = None) -> Dict:
    """Métricas y KPIs comerciales resumidos del inventario por empresa y opcionalmente por obra."""
    filtros = ["o.id_empresa = %s"]
    params = [id_empresa]
    if id_obra:
        filtros.append("o.id_obra = %s")
        params.append(id_obra)

    where_clause = " AND ".join(filtros)
    sql = f"""
        SELECT 
            COUNT(*) AS total_unidades,
            COUNT(*) FILTER (WHERE COALESCE(u.publicado_comercial, FALSE) = TRUE) AS total_publicadas,
            COUNT(*) FILTER (WHERE COALESCE(u.estado_comercial, 'DISPONIBLE') = 'DISPONIBLE') AS estado_disponibles,
            COUNT(*) FILTER (WHERE COALESCE(u.estado_comercial, 'DISPONIBLE') = 'RESERVADA') AS estado_reservadas,
            COUNT(*) FILTER (WHERE COALESCE(u.estado_comercial, 'DISPONIBLE') = 'VENDIDA') AS estado_vendidas,
            COUNT(*) FILTER (WHERE COALESCE(u.estado_comercial, 'DISPONIBLE') = 'NO_DISPONIBLE') AS estado_no_disponibles,
            -- Conteo efectivo: disponible comercial y sin reserva/venta activa en CRM
            COUNT(*) FILTER (
                WHERE COALESCE(u.estado_comercial, 'DISPONIBLE') = 'DISPONIBLE'
                  AND NOT EXISTS (
                      SELECT 1 FROM {Config.SCHEMA}.t_crm_cliente_unidad cu
                      WHERE cu.id_unidad = u.id_unidad
                        AND cu.estado_asociacion IN ('RESERVADO', 'VENDIDO', 'ENTREGADO')
                  )
            ) AS disponibles_efectivas,
            COALESCE(SUM(u.precio_venta) FILTER (WHERE COALESCE(u.estado_comercial, 'DISPONIBLE') = 'DISPONIBLE'), 0) AS valor_disponible,
            COALESCE(SUM(u.precio_venta) FILTER (WHERE COALESCE(u.estado_comercial, 'DISPONIBLE') = 'RESERVADA'), 0) AS valor_reservado,
            COALESCE(SUM(u.precio_venta) FILTER (WHERE COALESCE(u.estado_comercial, 'DISPONIBLE') = 'VENDIDA'), 0) AS valor_vendido
        FROM {Config.SCHEMA}.t_unidad_construccion u
        INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
        INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
        WHERE {where_clause};
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        r = db.execute_query(sql, tuple(params), fetchone=True) or (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        total_unidades = int(r[0] or 0)
        total_publicadas = int(r[1] or 0)
        return {
            "total_unidades": total_unidades,
            "total_publicadas": total_publicadas,
            "total_no_publicadas": max(0, total_unidades - total_publicadas),
            "por_estado_comercial": {
                "DISPONIBLE": int(r[2] or 0),
                "RESERVADA": int(r[3] or 0),
                "VENDIDA": int(r[4] or 0),
                "NO_DISPONIBLE": int(r[5] or 0),
            },
            "disponibles_efectivas": int(r[6] or 0),
            "kpis_financieros": {
                "valor_inventario_disponible": float(r[7]) if len(r) > 7 and r[7] is not None else 0.0,
                "valor_inventario_reservado": float(r[8]) if len(r) > 8 and r[8] is not None else 0.0,
                "valor_inventario_vendido": float(r[9]) if len(r) > 9 and r[9] is not None else 0.0,
            }
        }
    finally:
        db.close_connection()
