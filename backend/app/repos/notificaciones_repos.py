import json
from app.classes.postgres import PostgreSQL
from app.config import Config


class NotificacionesSchemaMissing(Exception):
    """Se lanza cuando la tabla de configuración de alertas CU22 aún no fue migrada."""


def _es_tabla_ausente(exc: Exception) -> bool:
    code = getattr(exc, "pgcode", None)
    if code == "42P01":
        return True
    msg = str(exc).lower()
    return "t_configuracion_alerta_evento" in msg and ("does not exist" in msg or "no existe" in msg)


def _es_columna_ausente(exc: Exception) -> bool:
    code = getattr(exc, "pgcode", None)
    if code in ("42703", "42P10"):
        return True
    msg = str(exc).lower()
    return ("column" in msg or "columna" in msg) and ("does not exist" in msg or "no existe" in msg)


def obtener_usuarios_por_roles(roles: list, id_empresa: int = None):
    """
    Obtiene los usuarios activos de t_usuario filtrados por lista de roles y
    por id_empresa. Solo incluye ADMINISTRADOR global si se solicita explícitamente
    ese rol en la lista.
    """
    if not roles:
        return []
    db = PostgreSQL()
    db.create_connection()
    try:
        roles_upper = [str(rol).strip().upper() for rol in roles if rol and str(rol).strip()]
        if not roles_upper:
            return []
        format_strings = ','.join(['%s'] * len(roles_upper))
        params = list(roles_upper)
        filtro_empresa = ""
        if id_empresa is not None:
            if "ADMINISTRADOR" in roles_upper:
                filtro_empresa = " AND (u.id_empresa = %s OR UPPER(r.nombre_rol) = 'ADMINISTRADOR')"
            else:
                filtro_empresa = " AND u.id_empresa = %s"
            params.append(int(id_empresa))

        query = f"""
            SELECT u.id_usuario, u.username, r.nombre_rol, u.id_empresa
            FROM {Config.SCHEMA}.t_usuario u
            INNER JOIN {Config.SCHEMA}.t_rol r ON u.id_rol = r.id_rol
            WHERE UPPER(r.nombre_rol) IN ({format_strings})
              AND u.estado = 'ACTIVO'
              {filtro_empresa};
        """
        resultados = db.execute_query(query, tuple(params), fetchall=True) or []
        usuarios = []
        for r in resultados:
            usuarios.append({
                "nro_usuario": r[0],
                "nombre_usuario": r[1],
                "nombre_rol": r[2],
                "id_empresa": r[3],
            })
        return usuarios
    finally:
        db.close_connection()


def filtrar_usuarios_autorizados_empresa(usuarios_ids: list, id_empresa: int = None) -> list:
    """
    Verifica que los IDs de usuario existan, estén en estado ACTIVO y pertenezcan
    a la empresa del evento (o sean ADMINISTRADOR global). Evita notificaciones
    cruzadas entre empresas.
    """
    ids_limpios = []
    for uid in usuarios_ids or []:
        try:
            val = int(uid)
            if val > 0 and val not in ids_limpios:
                ids_limpios.append(val)
        except (TypeError, ValueError):
            continue
    if not ids_limpios:
        return []

    db = PostgreSQL()
    db.create_connection()
    try:
        placeholders = ",".join(["%s"] * len(ids_limpios))
        params = list(ids_limpios)
        filtro_empresa = ""
        if id_empresa is not None:
            filtro_empresa = " AND (u.id_empresa = %s OR UPPER(r.nombre_rol) = 'ADMINISTRADOR')"
            params.append(int(id_empresa))

        query = f"""
            SELECT u.id_usuario
            FROM {Config.SCHEMA}.t_usuario u
            INNER JOIN {Config.SCHEMA}.t_rol r ON u.id_rol = r.id_rol
            WHERE u.id_usuario IN ({placeholders})
              AND u.estado = 'ACTIVO'
              {filtro_empresa};
        """
        filas = db.execute_query(query, tuple(params), fetchall=True) or []
        return [int(f[0]) for f in filas if f and f[0] is not None]
    finally:
        db.close_connection()


def validar_obra_empresa(id_obra: int):
    """
    Obtiene los metadatos mínimos de una obra para validar pertenencia de tenant.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            SELECT id_obra, nombre, id_empresa
            FROM {Config.SCHEMA}.t_obra
            WHERE id_obra = %s;
        """
        fila = db.execute_query(query, (int(id_obra),), fetchone=True)
        if not fila:
            return None
        return {
            "id_obra": int(fila[0]),
            "nombre": fila[1],
            "id_empresa": int(fila[2]) if fila[2] is not None else None,
        }
    finally:
        db.close_connection()


def obtener_configuraciones_alertas_db(id_empresa: int, id_obra: int = None) -> list:
    """
    Recupera las reglas de alertas de una empresa y, si se indica id_obra,
    también las sobrescrituras específicas de esa obra.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        if id_obra is not None:
            query = f"""
                SELECT id_configuracion, id_empresa, id_obra, tipo_evento,
                       activo, roles_destino, actualizado_por, actualizado_en
                FROM {Config.SCHEMA}.t_configuracion_alerta_evento
                WHERE id_empresa = %s AND (id_obra IS NULL OR id_obra = %s)
                ORDER BY id_obra NULLS FIRST, tipo_evento;
            """
            params = (int(id_empresa), int(id_obra))
        else:
            query = f"""
                SELECT id_configuracion, id_empresa, id_obra, tipo_evento,
                       activo, roles_destino, actualizado_por, actualizado_en
                FROM {Config.SCHEMA}.t_configuracion_alerta_evento
                WHERE id_empresa = %s AND id_obra IS NULL
                ORDER BY tipo_evento;
            """
            params = (int(id_empresa),)

        filas = db.execute_query(query, params, fetchall=True) or []
        resultado = []
        for f in filas:
            roles_raw = f[5]
            if isinstance(roles_raw, str):
                try:
                    roles_parsed = json.loads(roles_raw)
                except Exception:
                    roles_parsed = []
            elif isinstance(roles_raw, list):
                roles_parsed = roles_raw
            else:
                roles_parsed = []
            resultado.append({
                "id_configuracion": f[0],
                "id_empresa": int(f[1]),
                "id_obra": int(f[2]) if f[2] is not None else None,
                "tipo_evento": f[3],
                "activo": bool(f[4]),
                "roles_destino": [str(r) for r in roles_parsed if r],
                "actualizado_por": f[6],
                "actualizado_en": f[7].strftime("%Y-%m-%d %H:%M:%S") if f[7] else None,
            })
        return resultado
    except Exception as exc:
        if _es_tabla_ausente(exc):
            raise NotificacionesSchemaMissing(
                "La migración SQL de configuración de alertas (20261121_cu22_notificaciones_alertas.sql) aún no está aplicada."
            ) from exc
        raise
    finally:
        db.close_connection()


def guardar_configuraciones_alertas_db(
    id_empresa: int,
    configuraciones: list,
    id_obra: int = None,
    actualizado_por: int = None,
) -> int:
    """
    Inserta o actualiza de forma atómica las preferencias de alertas para
    (id_empresa, id_obra, tipo_evento).
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            INSERT INTO {Config.SCHEMA}.t_configuracion_alerta_evento
                (id_empresa, id_obra, tipo_evento, activo, roles_destino, actualizado_por, actualizado_en)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (id_empresa, COALESCE(id_obra, 0), tipo_evento)
            DO UPDATE SET
                activo = EXCLUDED.activo,
                roles_destino = EXCLUDED.roles_destino,
                actualizado_por = EXCLUDED.actualizado_por,
                actualizado_en = CURRENT_TIMESTAMP;
        """
        cur = db.conn.cursor()
        try:
            for item in configuraciones:
                cur.execute(
                    query,
                    (
                        int(id_empresa),
                        int(id_obra) if id_obra is not None else None,
                        item["tipo_evento"],
                        bool(item["activo"]),
                        json.dumps(item["roles_destino"]),
                        int(actualizado_por) if actualizado_por is not None else None,
                    ),
                )
            db.conn.commit()
            return len(configuraciones)
        except Exception:
            db.conn.rollback()
            raise
        finally:
            cur.close()
    except Exception as exc:
        if _es_tabla_ausente(exc):
            raise NotificacionesSchemaMissing(
                "La migración SQL de configuración de alertas (20261121_cu22_notificaciones_alertas.sql) aún no está aplicada."
            ) from exc
        raise
    finally:
        db.close_connection()


def eliminar_configuraciones_obra_db(id_empresa: int, id_obra: int) -> int:
    """
    Elimina las sobrescrituras de una obra específica para que vuelva a heredar
    la configuración general de su empresa.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            DELETE FROM {Config.SCHEMA}.t_configuracion_alerta_evento
            WHERE id_empresa = %s AND id_obra = %s;
        """
        filas = db.execute_query(query, (int(id_empresa), int(id_obra)), commit=True)
        return filas or 0
    except Exception as exc:
        if _es_tabla_ausente(exc):
            raise NotificacionesSchemaMissing(
                "La migración SQL de configuración de alertas (20261121_cu22_notificaciones_alertas.sql) aún no está aplicada."
            ) from exc
        raise
    finally:
        db.close_connection()


def obtener_usuarios_por_taller(nro_taller: int):
    """
    Compatibilidad con consultas por empresa/taller usando t_usuario.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            SELECT id_usuario, username
            FROM {Config.SCHEMA}.t_usuario
            WHERE id_empresa = %s AND estado = 'ACTIVO';
        """
        resultados = db.execute_query(query, (nro_taller,), fetchall=True) or []
        return [
            {"nro_usuario": r[0], "nombre_usuario": r[1]}
            for r in resultados
        ]
    finally:
        db.close_connection()


def guardar_notificacion_db(
    titulo: str,
    cuerpo: str,
    tipo_referencia: str,
    nro_usuario: int,
    nro_emergencia: int = None,
    id_empresa: int = None,
    id_obra: int = None,
    clave_evento: str = None,
):
    """
    Persiste la notificación en obras.notificacion.
    Usa columnas aditivas e idempotencia por clave_evento cuando la migración CU22
    está aplicada, con degradación transparente al esquema base si aún no se aplicó.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        if clave_evento or id_empresa is not None or id_obra is not None:
            try:
                query_ext = f"""
                    INSERT INTO {Config.SCHEMA}.notificacion
                        (titulo, cuerpo, tipo_referencia, nro_usuario, nro_emergencia,
                         id_empresa, id_obra, clave_evento)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (nro_usuario, clave_evento) WHERE clave_evento IS NOT NULL
                    DO NOTHING
                    RETURNING id_notificacion, fecha_creacion;
                """
                row = db.execute_query(
                    query_ext,
                    (
                        titulo,
                        cuerpo,
                        tipo_referencia,
                        int(nro_usuario),
                        nro_emergencia,
                        int(id_empresa) if id_empresa is not None else None,
                        int(id_obra) if id_obra is not None else None,
                        clave_evento,
                    ),
                    commit=True,
                    fetchone=True,
                )
                if row:
                    return {
                        "id_notificacion": row[0],
                        "fecha_creacion": row[1].strftime("%Y-%m-%d %H:%M:%S") if row[1] else None,
                        "duplicada": False,
                    }
                if clave_evento:
                    return {
                        "id_notificacion": None,
                        "fecha_creacion": None,
                        "duplicada": True,
                    }
            except Exception as exc:
                if not _es_columna_ausente(exc):
                    raise

        query = f"""
            INSERT INTO {Config.SCHEMA}.notificacion
            (titulo, cuerpo, tipo_referencia, nro_usuario, nro_emergencia)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id_notificacion, fecha_creacion;
        """
        row = db.execute_query(
            query,
            (titulo, cuerpo, tipo_referencia, int(nro_usuario), nro_emergencia),
            commit=True,
            fetchone=True,
        )
        if row:
            return {
                "id_notificacion": row[0],
                "fecha_creacion": row[1].strftime("%Y-%m-%d %H:%M:%S") if row[1] else None,
                "duplicada": False,
            }
        return {"id_notificacion": None, "fecha_creacion": None, "duplicada": False}
    finally:
        db.close_connection()


def obtener_notificaciones_por_usuario_db(
    nro_usuario: int,
    solo_no_leidas: bool = False,
    tipo: str = None,
    limit: int = 100,
):
    """
    Recupera el historial de alertas del usuario ordenado por las más recientes primero.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        filtros = ["nro_usuario = %s"]
        params = [int(nro_usuario)]
        if solo_no_leidas:
            filtros.append("leido = FALSE")
        if tipo and str(tipo).strip():
            filtros.append("UPPER(COALESCE(tipo_referencia, '')) = %s")
            params.append(str(tipo).strip().upper())

        limite_seguro = max(1, min(int(limit or 100), 200))
        params.append(limite_seguro)
        where_sql = " AND ".join(filtros)

        query = f"""
            SELECT id_notificacion, titulo, cuerpo, tipo_referencia, leido, fecha_creacion, nro_emergencia
            FROM {Config.SCHEMA}.notificacion
            WHERE {where_sql}
            ORDER BY fecha_creacion DESC, id_notificacion DESC
            LIMIT %s;
        """
        resultados = db.execute_query(query, tuple(params), fetchall=True) or []
        alertas = []
        for r in resultados:
            fecha_str = r[5].strftime("%Y-%m-%d %H:%M:%S") if r[5] else None
            tipo_ref = r[3] or "GENERAL"
            alertas.append({
                "id_notificacion": r[0],
                "titulo": r[1],
                "cuerpo": r[2],
                "mensaje": r[2],
                "tipo_referencia": tipo_ref,
                "tipo": tipo_ref,
                "leido": bool(r[4]),
                "fecha_creacion": fecha_str,
                "created_at": fecha_str,
                "nro_emergencia": r[6],
            })
        return alertas
    finally:
        db.close_connection()


def listar_notificaciones_cliente_cu30(id_cliente: int, nro_usuario: int, id_empresa: int):
    """Lista notificaciones personales, validando tenant y relaciones opcionales CU22."""
    db = PostgreSQL()
    db.create_connection()
    try:
        columnas = db.execute_query(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = 'notificacion'
              AND column_name IN ('id_empresa', 'id_obra');
            """,
            (Config.SCHEMA,),
            fetchall=True,
        ) or []
        columnas_disponibles = {fila[0] for fila in columnas}

        filtros = [
            "n.nro_usuario = %s",
            "u.id_usuario = n.nro_usuario",
            "u.id_empresa = %s",
        ]
        params = [int(nro_usuario), int(id_empresa)]
        if "id_empresa" in columnas_disponibles:
            filtros.append("(n.id_empresa IS NULL OR n.id_empresa = %s)")
            params.append(int(id_empresa))
        if "id_obra" in columnas_disponibles:
            filtros.append(
                """
                (
                    n.id_obra IS NULL
                    OR EXISTS (
                        SELECT 1
                        FROM {schema}.t_crm_cliente_unidad cu
                        JOIN {schema}.t_crm_cliente c
                          ON c.id_cliente = cu.id_cliente
                         AND c.id_empresa = %s
                         AND c.id_cliente = %s
                         AND c.tipo_cliente = 'CLIENTE'
                        JOIN {schema}.t_unidad_construccion un
                          ON un.id_unidad = cu.id_unidad
                        JOIN {schema}.t_estructura_obra e
                          ON e.id_estructura = un.id_estructura
                        JOIN {schema}.t_obra o
                          ON o.id_obra = e.id_obra
                         AND o.id_obra = n.id_obra
                         AND o.id_empresa = %s
                    )
                )
                """.format(schema=Config.SCHEMA)
            )
            params.extend((int(id_empresa), int(id_cliente), int(id_empresa)))

        params.append(200)
        query = f"""
            SELECT n.id_notificacion, n.titulo, n.cuerpo, n.tipo_referencia,
                   n.leido, n.fecha_creacion, n.nro_emergencia
            FROM {Config.SCHEMA}.notificacion n
            JOIN {Config.SCHEMA}.t_usuario u ON u.id_usuario = n.nro_usuario
            WHERE {" AND ".join(filtros)}
            ORDER BY n.fecha_creacion DESC, n.id_notificacion DESC
            LIMIT %s;
        """
        rows = db.execute_query(query, tuple(params), fetchall=True) or []
        return [
            {
                "id_notificacion": row[0],
                "titulo": row[1],
                "cuerpo": row[2],
                "mensaje": row[2],
                "tipo_referencia": row[3] or "GENERAL",
                "tipo": row[3] or "GENERAL",
                "leido": bool(row[4]),
                "fecha_creacion": row[5].isoformat() if row[5] else None,
                "created_at": row[5].isoformat() if row[5] else None,
                "nro_emergencia": row[6],
            }
            for row in rows
        ]
    finally:
        db.close_connection()


def marcar_notificacion_leida_db(id_notificacion: int, nro_usuario: int):
    """
    Modifica el estado de 'leido' a TRUE para una sola alerta (comprobando pertenencia).
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            UPDATE {Config.SCHEMA}.notificacion
            SET leido = TRUE
            WHERE id_notificacion = %s AND nro_usuario = %s;
        """
        filas_afectadas = db.execute_query(
            query,
            (int(id_notificacion), int(nro_usuario)),
            commit=True,
        )
        return (filas_afectadas or 0) > 0
    finally:
        db.close_connection()


def marcar_todas_las_notificaciones_leidas_db(nro_usuario: int):
    """
    Actualiza masivamente todas las alertas de un usuario a leídas (Botón masivo).
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            UPDATE {Config.SCHEMA}.notificacion
            SET leido = TRUE
            WHERE nro_usuario = %s AND leido = FALSE;
        """
        filas_afectadas = db.execute_query(query, (int(nro_usuario),), commit=True)
        return filas_afectadas or 0
    finally:
        db.close_connection()


def crear_comunicacion_cliente_db(
    titulo: str,
    cuerpo: str,
    tipo_referencia: str,
    nro_usuario: int,
    id_empresa: int,
    id_obra: int = None,
):
    """
    Inserta una comunicación directa de la constructora en obras.notificacion (HU116).
    Garantiza leido = FALSE, fecha_creacion = CURRENT_TIMESTAMP y aislamiento de tenant.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        columnas = db.execute_query(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = 'notificacion'
              AND column_name IN ('id_empresa', 'id_obra');
            """,
            (Config.SCHEMA,),
            fetchall=True,
        ) or []
        columnas_disponibles = {fila[0] for fila in columnas}

        if "id_empresa" in columnas_disponibles and "id_obra" in columnas_disponibles:
            query = f"""
                INSERT INTO {Config.SCHEMA}.notificacion
                    (titulo, cuerpo, tipo_referencia, nro_usuario, id_empresa, id_obra, leido, fecha_creacion)
                VALUES (%s, %s, %s, %s, %s, %s, FALSE, CURRENT_TIMESTAMP)
                RETURNING id_notificacion, titulo, cuerpo, tipo_referencia, nro_usuario, id_empresa, id_obra, leido, fecha_creacion;
            """
            params = (
                titulo,
                cuerpo,
                tipo_referencia,
                int(nro_usuario),
                int(id_empresa),
                int(id_obra) if id_obra is not None else None,
            )
        elif "id_empresa" in columnas_disponibles:
            query = f"""
                INSERT INTO {Config.SCHEMA}.notificacion
                    (titulo, cuerpo, tipo_referencia, nro_usuario, id_empresa, leido, fecha_creacion)
                VALUES (%s, %s, %s, %s, %s, FALSE, CURRENT_TIMESTAMP)
                RETURNING id_notificacion, titulo, cuerpo, tipo_referencia, nro_usuario, id_empresa, NULL, leido, fecha_creacion;
            """
            params = (titulo, cuerpo, tipo_referencia, int(nro_usuario), int(id_empresa))
        else:
            query = f"""
                INSERT INTO {Config.SCHEMA}.notificacion
                    (titulo, cuerpo, tipo_referencia, nro_usuario, leido, fecha_creacion)
                VALUES (%s, %s, %s, %s, FALSE, CURRENT_TIMESTAMP)
                RETURNING id_notificacion, titulo, cuerpo, tipo_referencia, nro_usuario, NULL, NULL, leido, fecha_creacion;
            """
            params = (titulo, cuerpo, tipo_referencia, int(nro_usuario))

        row = db.execute_query(query, params, commit=True, fetchone=True)
        if not row:
            raise RuntimeError("No se pudo registrar la comunicación en la base de datos.")
        return {
            "id_notificacion": row[0],
            "titulo": row[1],
            "cuerpo": row[2],
            "mensaje": row[2],
            "tipo_referencia": row[3],
            "tipo": row[3],
            "nro_usuario": row[4],
            "id_empresa": row[5],
            "id_obra": row[6],
            "leido": bool(row[7]),
            "fecha_creacion": row[8].isoformat() if hasattr(row[8], "isoformat") else str(row[8]),
            "created_at": row[8].isoformat() if hasattr(row[8], "isoformat") else str(row[8]),
        }
    finally:
        db.close_connection()
