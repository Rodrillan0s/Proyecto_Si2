"""
Repositorio CU41 – Idempotencia y trazabilidad temporal para sincronización offline.
Tabla: obras.t_sync_operacion_offline
"""
import json
from app.classes.postgres import PostgreSQL
from app.config import Config


def reservar_operacion(
    id_empresa: int,
    id_usuario: int,
    tipo_operacion: str,
    id_obra: int,
    client_operation_id: str,
    fecha_ocurrencia_local,
) -> dict:
    """
    Reserva transaccionalmente una clave de idempotencia.
    - Si no existe: inserta en estado EN_PROCESO y retorna {"estado": "NUEVA", "id_sync": ...}.
    - Si ya existe: bloquea/consulta la fila existente y retorna su estado y respuesta guardada.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        insert_sql = f"""
            INSERT INTO {Config.SCHEMA}.t_sync_operacion_offline (
                client_operation_id, id_empresa, id_usuario,
                tipo_operacion, id_obra, fecha_ocurrencia_local, estado
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'EN_PROCESO')
            ON CONFLICT (id_empresa, id_usuario, tipo_operacion, client_operation_id)
            DO NOTHING
            RETURNING id_sync;
        """
        inserted = db.execute_query(
            insert_sql,
            (
                client_operation_id,
                id_empresa,
                id_usuario,
                tipo_operacion,
                id_obra,
                fecha_ocurrencia_local,
            ),
            fetchone=True,
            commit=True,
        )
        if inserted:
            return {"estado": "NUEVA", "id_sync": inserted[0]}

        select_sql = f"""
            SELECT id_sync, estado, id_recurso_creado, respuesta_json,
                   fecha_ocurrencia_local, fecha_sincronizacion
            FROM {Config.SCHEMA}.t_sync_operacion_offline
            WHERE id_empresa = %s
              AND id_usuario = %s
              AND tipo_operacion = %s
              AND client_operation_id = %s
            LIMIT 1;
        """
        row = db.execute_query(
            select_sql,
            (id_empresa, id_usuario, tipo_operacion, client_operation_id),
            fetchone=True,
        )
        if not row:
            return {"estado": "NUEVA", "id_sync": None}

        respuesta = row[3]
        if isinstance(respuesta, str):
            respuesta = json.loads(respuesta)
        return {
            "estado": "EXISTENTE",
            "id_sync": row[0],
            "estado_op": row[1],
            "id_recurso_creado": row[2],
            "respuesta_json": respuesta,
            "fecha_ocurrencia_local": row[4].isoformat() if row[4] else None,
            "fecha_sincronizacion": row[5].isoformat() if row[5] else None,
        }
    finally:
        db.close_connection()


def completar_operacion(id_sync: int, id_recurso_creado, respuesta_json: dict) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = f"""
            UPDATE {Config.SCHEMA}.t_sync_operacion_offline
            SET estado = 'PROCESADO',
                id_recurso_creado = %s,
                respuesta_json = %s::jsonb,
                fecha_sincronizacion = CURRENT_TIMESTAMP
            WHERE id_sync = %s
            RETURNING fecha_sincronizacion;
        """
        row = db.execute_query(
            sql,
            (id_recurso_creado, json.dumps(respuesta_json, default=str), id_sync),
            fetchone=True,
            commit=True,
        )
        return {
            "fecha_sincronizacion": row[0].isoformat() if row and row[0] else None,
        }
    finally:
        db.close_connection()


def liberar_operacion_fallida(id_sync: int) -> None:
    if not id_sync:
        return
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = f"""
            DELETE FROM {Config.SCHEMA}.t_sync_operacion_offline
            WHERE id_sync = %s AND estado = 'EN_PROCESO';
        """
        db.execute_query(sql, (id_sync,), commit=True)
    finally:
        db.close_connection()


def registrar_marcas_temporales_recurso(
    tabla: str,
    columna_pk: str,
    id_recurso: int,
    fecha_ocurrencia_local,
) -> None:
    if tabla not in {"t_avance_obra", "t_incidencia"} or columna_pk not in {"id_avance", "id_incidencia"}:
        return
    if not id_recurso or not fecha_ocurrencia_local:
        return
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = f"""
            UPDATE {Config.SCHEMA}.{tabla}
            SET fecha_ocurrencia_local = %s,
                fecha_sincronizacion = CURRENT_TIMESTAMP
            WHERE {columna_pk} = %s;
        """
        db.execute_query(sql, (fecha_ocurrencia_local, id_recurso), commit=True)
    finally:
        db.close_connection()
