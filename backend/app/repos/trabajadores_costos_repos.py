from decimal import Decimal

from psycopg2 import errors

from app.classes.postgres import PostgreSQL
from app.config import Config


class TrabajadoresCostosConflictError(Exception):
    pass


def falta_esquema_cu32(exc):
    return isinstance(exc, errors.UndefinedTable) and any(
        table in str(exc) for table in (
            't_salario_trabajador', 't_jornada_trabajador_obra', 't_cu32_mano_obra_cierre'
        )
    )


def _columns(db):
    if not db.cur or not db.cur.description:
        return []
    return [item.name if hasattr(item, "name") else item[0] for item in db.cur.description]


def _many(db, sql, params=()):
    rows = db.execute_query(sql, params, fetchall=True) or []
    return [dict(zip(_columns(db), row)) for row in rows]


def _one(db, sql, params=()):
    row = db.execute_query(sql, params, fetchone=True)
    return dict(zip(_columns(db), row)) if row else None


def _read_many(sql, params=(), db=None):
    if db is not None:
        return _many(db, sql, params)
    db = PostgreSQL()
    db.create_connection()
    try:
        return _many(db, sql, params)
    finally:
        db.close_connection()


def listar_trabajadores_obra(id_empresa, id_obra, db=None):
    return _read_many(
        f"""
        SELECT u.id_usuario,
               COALESCE(NULLIF(p.nombre_completo, ''), u.username) AS nombre_completo,
               r.nombre_rol,
               salario.id_salario,
               salario.salario_diario,
               salario.fecha_vigencia AS salario_vigente_desde
        FROM {Config.SCHEMA}.t_obra o
        JOIN {Config.SCHEMA}.t_obra_usuario ou ON ou.id_obra = o.id_obra
        JOIN {Config.SCHEMA}.t_usuario u ON u.id_usuario = ou.id_usuario
                                         AND u.id_empresa = o.id_empresa
        JOIN {Config.SCHEMA}.t_rol r ON r.id_rol = u.id_rol
        LEFT JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = u.id_persona
        LEFT JOIN LATERAL (
            SELECT s.id_salario, s.salario_diario, s.fecha_vigencia
            FROM {Config.SCHEMA}.t_salario_trabajador s
            WHERE s.id_empresa = o.id_empresa AND s.id_usuario = u.id_usuario
              AND s.fecha_vigencia <= CURRENT_DATE
            ORDER BY s.fecha_vigencia DESC, s.id_salario DESC
            LIMIT 1
        ) salario ON TRUE
        WHERE o.id_empresa = %s AND o.id_obra = %s
        ORDER BY nombre_completo, u.id_usuario
        """,
        (id_empresa, id_obra),
        db=db,
    )


def listar_jornadas_obra(id_empresa, id_obra, db=None):
    return _read_many(
        f"""
        SELECT j.id_jornada, j.id_usuario,
               COALESCE(NULLIF(p.nombre_completo, ''), u.username) AS nombre_completo,
               j.fecha, j.dias_trabajados, s.salario_diario,
               ROUND(j.dias_trabajados * s.salario_diario, 2) AS costo_calculado
        FROM {Config.SCHEMA}.t_jornada_trabajador_obra j
        JOIN {Config.SCHEMA}.t_salario_trabajador s ON s.id_salario = j.id_salario
        JOIN {Config.SCHEMA}.t_usuario u ON u.id_usuario = j.id_usuario
                                         AND u.id_empresa = j.id_empresa
        LEFT JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = u.id_persona
        WHERE j.id_empresa = %s AND j.id_obra = %s
        ORDER BY j.fecha DESC, nombre_completo, j.id_jornada
        """,
        (id_empresa, id_obra),
        db=db,
    )


def listar_cierre_mano_obra(id_empresa, id_obra, db=None):
    return _read_many(
        f"""
        SELECT c.id_usuario,
               COALESCE(NULLIF(p.nombre_completo, ''), u.username) AS nombre_completo,
               r.nombre_rol, c.fecha, c.dias_trabajados,
               c.salario_diario, c.costo_calculado, c.id_salario
        FROM {Config.SCHEMA}.t_cu32_mano_obra_cierre c
        JOIN {Config.SCHEMA}.t_usuario u ON u.id_usuario = c.id_usuario
                                         AND u.id_empresa = c.id_empresa
        JOIN {Config.SCHEMA}.t_rol r ON r.id_rol = u.id_rol
        LEFT JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = u.id_persona
        WHERE c.id_empresa = %s AND c.id_obra = %s
        ORDER BY nombre_completo, c.fecha, c.id_usuario
        """,
        (id_empresa, id_obra),
        db=db,
    )


def registrar_salario(id_empresa, id_obra, id_usuario, salario_diario, fecha_vigencia, registrado_por):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = _one(
            db,
            f"""
            INSERT INTO {Config.SCHEMA}.t_salario_trabajador
                (id_empresa, id_usuario, salario_diario, fecha_vigencia, registrado_por)
            SELECT o.id_empresa, u.id_usuario, %s, %s, %s
            FROM {Config.SCHEMA}.t_obra o
            JOIN {Config.SCHEMA}.t_obra_usuario ou ON ou.id_obra = o.id_obra
            JOIN {Config.SCHEMA}.t_usuario u ON u.id_usuario = ou.id_usuario
                                             AND u.id_empresa = o.id_empresa
            WHERE o.id_empresa = %s AND o.id_obra = %s AND u.id_usuario = %s
            RETURNING id_salario, id_usuario, salario_diario, fecha_vigencia
            """,
            (
                salario_diario, fecha_vigencia, registrado_por,
                id_empresa, id_obra, id_usuario,
            ),
        )
        if not row:
            raise TrabajadoresCostosConflictError(
                "El trabajador no está asignado a esta obra o no pertenece a su empresa."
            )
        db.conn.commit()
        return row
    except errors.UniqueViolation as exc:
        db.conn.rollback()
        raise TrabajadoresCostosConflictError(
            "Ya existe un salario registrado con esa fecha de vigencia."
        ) from exc
    except Exception:
        db.conn.rollback()
        raise
    finally:
        db.close_connection()


def registrar_jornada(id_empresa, id_obra, id_usuario, fecha, dias_trabajados):
    db = PostgreSQL()
    db.create_connection()
    try:
        trabajador = db.execute_query(
            f"""
            SELECT u.id_usuario, o.estado_obra
            FROM {Config.SCHEMA}.t_obra o
            JOIN {Config.SCHEMA}.t_obra_usuario ou ON ou.id_obra = o.id_obra
            JOIN {Config.SCHEMA}.t_usuario u ON u.id_usuario = ou.id_usuario
                                             AND u.id_empresa = o.id_empresa
            WHERE o.id_empresa = %s AND o.id_obra = %s AND u.id_usuario = %s
            FOR UPDATE OF o, u
            """,
            (id_empresa, id_obra, id_usuario),
            fetchone=True,
        )
        if not trabajador:
            raise TrabajadoresCostosConflictError(
                "El trabajador no está asignado a esta obra o no pertenece a su empresa."
            )
        if trabajador[1] == "FINALIZADO":
            raise TrabajadoresCostosConflictError(
                "No se pueden modificar jornadas de una obra FINALIZADO."
            )

        salario = db.execute_query(
            f"""
            SELECT id_salario
            FROM {Config.SCHEMA}.t_salario_trabajador
            WHERE id_empresa = %s AND id_usuario = %s AND fecha_vigencia <= %s
            ORDER BY fecha_vigencia DESC, id_salario DESC
            LIMIT 1
            """,
            (id_empresa, id_usuario, fecha),
            fetchone=True,
        )
        if not salario:
            raise TrabajadoresCostosConflictError(
                "El trabajador no tiene un salario diario vigente para la fecha indicada."
            )

        existente = db.execute_query(
            f"""
            SELECT id_jornada, dias_trabajados
            FROM {Config.SCHEMA}.t_jornada_trabajador_obra
            WHERE id_empresa = %s AND id_obra = %s AND id_usuario = %s AND fecha = %s
            FOR UPDATE
            """,
            (id_empresa, id_obra, id_usuario, fecha),
            fetchone=True,
        )
        dias_en_otras_obras = db.execute_query(
            f"""
            SELECT COALESCE(SUM(dias_trabajados), 0)
            FROM {Config.SCHEMA}.t_jornada_trabajador_obra
            WHERE id_empresa = %s AND id_usuario = %s AND fecha = %s
              AND id_obra <> %s
            """,
            (id_empresa, id_usuario, fecha, id_obra),
            fetchone=True,
        )[0]
        if Decimal(dias_en_otras_obras) + Decimal(dias_trabajados) > 1:
            raise TrabajadoresCostosConflictError(
                "Las jornadas del trabajador en todas sus obras no pueden superar un día."
            )

        row = _one(
            db,
            f"""
            INSERT INTO {Config.SCHEMA}.t_jornada_trabajador_obra
                (id_empresa, id_obra, id_usuario, id_salario, fecha, dias_trabajados)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id_empresa, id_obra, id_usuario, fecha)
            DO UPDATE SET id_salario = EXCLUDED.id_salario,
                          dias_trabajados = EXCLUDED.dias_trabajados,
                          updated_at = CURRENT_TIMESTAMP
            RETURNING id_jornada, id_usuario, fecha, dias_trabajados, id_salario
            """,
            (id_empresa, id_obra, id_usuario, salario[0], fecha, dias_trabajados),
        )
        db.conn.commit()
        return row
    except Exception:
        db.conn.rollback()
        raise
    finally:
        db.close_connection()


def cerrar_mano_obra(id_empresa, id_obra, db):
    jornadas = db.execute_query(
        f"""
        SELECT COUNT(*)
        FROM {Config.SCHEMA}.t_jornada_trabajador_obra j
        JOIN {Config.SCHEMA}.t_salario_trabajador s ON s.id_salario = j.id_salario
        WHERE j.id_empresa = %s AND j.id_obra = %s AND j.dias_trabajados > 0
        """,
        (id_empresa, id_obra),
        fetchone=True,
    )[0]
    if not jornadas:
        return

    costos_manuales = db.execute_query(
        f"""
        SELECT EXISTS (
            SELECT 1
            FROM {Config.SCHEMA}.t_costo_ejecutado
            WHERE id_empresa = %s AND id_obra = %s
          AND categoria = 'MANO_OBRA' AND estado = 'REGISTRADO' AND monto > 0
        )
        """,
        (id_empresa, id_obra),
        fetchone=True,
    )[0]
    if costos_manuales:
        raise TrabajadoresCostosConflictError(
            "Hay costos MANO_OBRA manuales y jornadas de trabajadores para esta obra. "
            "Revise los costos manuales y anúlelos si representan los mismos salarios antes de finalizar."
        )

    db.execute_query(
        f"""
        INSERT INTO {Config.SCHEMA}.t_cu32_mano_obra_cierre
            (id_empresa, id_obra, id_jornada, id_usuario, id_salario,
             fecha, dias_trabajados, salario_diario, costo_calculado)
        SELECT j.id_empresa, j.id_obra, j.id_jornada, j.id_usuario, j.id_salario,
               j.fecha, j.dias_trabajados, s.salario_diario,
               ROUND(j.dias_trabajados * s.salario_diario, 2)
        FROM {Config.SCHEMA}.t_jornada_trabajador_obra j
        JOIN {Config.SCHEMA}.t_salario_trabajador s ON s.id_salario = j.id_salario
        WHERE j.id_empresa = %s AND j.id_obra = %s
        ON CONFLICT (id_jornada) DO NOTHING
        """,
        (id_empresa, id_obra),
    )


def tiene_mano_obra_calculada(id_empresa, id_obra, db=None):
    own_connection = db is None
    if own_connection:
        db = PostgreSQL()
        db.create_connection()
    try:
        row = db.execute_query(
            f"""
            SELECT EXISTS (
                SELECT 1 FROM {Config.SCHEMA}.t_cu32_mano_obra_cierre
                WHERE id_empresa = %s AND id_obra = %s AND costo_calculado > 0
            )
            """,
            (id_empresa, id_obra),
            fetchone=True,
        )
        return bool(row and row[0])
    except errors.UndefinedTable as exc:
        # CU17 sigue funcionando antes de instalar CU32. No hay cierres
        # calculados si su tabla todavía no existe. Nunca ocultar un error
        # dentro de una transacción compartida que quedaría abortada.
        if own_connection and falta_esquema_cu32(exc):
            return False
        raise
    finally:
        if own_connection:
            db.close_connection()
