"""SQL parametrizado y transacciones cortas de reportes. No recibe SQL del usuario."""
import json
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from psycopg2.extras import Json
from psycopg2.errors import UndefinedTable
from app.classes.postgres import PostgreSQL
from app.utils.reportes_errors import REPORT_TABLES, ReportesSchemaMissing


def json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    raise TypeError(type(value).__name__)


def j(value):
    return Json(value, dumps=lambda x: json.dumps(x, default=json_default, ensure_ascii=False))


@contextmanager
def transaction(snapshot=False):
    db = PostgreSQL()
    db.create_connection()
    if db.conn is None:
        raise RuntimeError("Base de datos no disponible.")
    try:
        if snapshot:
            db.conn.rollback()
            db.cur.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        db.cur.execute("SET LOCAL statement_timeout = '30s'")
        yield db
        if not snapshot:
            db.conn.commit()
    except UndefinedTable as exc:
        table = getattr(getattr(exc, 'diag', None), 'table_name', None)
        if table in REPORT_TABLES or any(
            f'"obras.{name}"' in str(exc) or f'"{name}"' in str(exc)
            for name in REPORT_TABLES
        ):
            raise ReportesSchemaMissing() from exc
        raise
    finally:
        db.close_connection()


def rows(db, sql, params=()):
    data = db.execute_query(sql, params, fetchall=True) or []
    keys = [x[0] for x in db.cur.description] if db.cur.description else []
    return [dict(zip(keys, row)) for row in data]


def one(db, sql, params=()):
    data = rows(db, sql, params)
    return data[0] if data else None


def actor(db, user):
    return one(db, """SELECT u.id_usuario,u.id_empresa,u.id_persona,u.estado,u.correo,
        r.nombre_rol, COALESCE(array_agg(DISTINCT p.nombre_permiso)
        FILTER (WHERE p.nombre_permiso IS NOT NULL),'{}') AS permisos
        FROM obras.t_usuario u JOIN obras.t_rol r USING(id_rol)
        LEFT JOIN obras.t_rol_permiso rp USING(id_rol)
        LEFT JOIN obras.t_permiso p USING(id_permiso)
        WHERE u.id_usuario=%s GROUP BY u.id_usuario,r.nombre_rol""", (user,))


def works(db, ctx):
    from app.services.reportes.catalog import WORKERS
    clause, params = "", [ctx.empresa]
    if ctx.rol == "CLIENTE":
        clause = "AND EXISTS(SELECT 1 FROM obras.t_detalle_obra d WHERE d.id_obra=o.id_obra AND d.id_cliente=%s)"
        params.append(ctx.persona)
    elif ctx.rol in WORKERS or ctx.rol == "JEFE DE OBRA":
        clause = """AND (EXISTS(SELECT 1 FROM obras.t_obra_usuario ou WHERE ou.id_obra=o.id_obra AND ou.id_usuario=%s)
          OR EXISTS(SELECT 1 FROM obras.t_orden_trabajo ot JOIN obras.t_orden_trabajo_usuario otu
          ON otu.id_orden_trabajo=ot.orden_nro WHERE ot.id_obra=o.id_obra AND otu.id_usuario=%s))"""
        params.extend([ctx.usuario, ctx.usuario])
    elif ctx.rol not in {"ADMINISTRADOR", "ADMINISTRADOR_EMPRESA"}:
        return []
    return rows(db, "SELECT o.id_obra,o.nombre,o.codigo,o.moneda FROM obras.t_obra o WHERE o.id_empresa=%s " + clause + " ORDER BY o.nombre,o.id_obra", params)


def datasets(db, ctx, request, scope):
    f, kind = request.filtros, request.reporte
    ids = list(scope)
    if kind == "stock":
        # La misma función del inventario, sin paginación y conservando NUMERIC.
        return rows(db, "SELECT * FROM obras.fn_listar_inventario_empresa(%s,%s,%s,%s,NULL,0) LIMIT 20001",
                    (ctx.empresa, f.id_categoria, f.estado, f.q))
    if kind == "comparativo_costos":
        from app.repos.control_costos_repos import comparacion_por_obra
        line = one(db, "SELECT moneda FROM obras.t_control_costo_obra WHERE id_empresa=%s AND id_obra=%s AND estado='ACTIVO' ORDER BY seleccionado_en DESC,id_control_costo DESC LIMIT 1", (ctx.empresa, f.id_obra))
        if not line:
            from fastapi import HTTPException
            raise HTTPException(409, "La obra no tiene una línea base activa de costos.")
        return [dict(row, id_obra=f.id_obra, moneda=line['moneda']) for row in comparacion_por_obra(ctx.empresa, f.id_obra, db=db)]
    if kind == 'saldo_comercial':
        result = rows(db, """SELECT o.id_obra,o.nombre AS obra,o.moneda,
            v.unidades_vendidas,v.ventas_sin_monto,v.monto_pactado,c.costos_registrados
            FROM obras.t_obra o
            LEFT JOIN LATERAL (
                SELECT count(*) AS unidades_vendidas,
                  count(*) FILTER(WHERE vendido.monto_pactado IS NULL) AS ventas_sin_monto,
                  sum(vendido.monto_pactado) AS monto_pactado
                FROM (SELECT DISTINCT ON (cu.id_unidad) cu.id_unidad,cu.monto_pactado
                  FROM obras.t_crm_cliente_unidad cu
                  JOIN obras.t_crm_cliente cli USING(id_cliente)
                  JOIN obras.t_unidad_construccion un USING(id_unidad)
                  JOIN obras.t_estructura_obra es USING(id_estructura)
                  WHERE es.id_obra=o.id_obra AND cli.id_empresa=o.id_empresa
                    AND cu.estado_asociacion IN ('VENDIDO','ENTREGADO')
                  ORDER BY cu.id_unidad,cu.fecha_asociacion DESC,cu.id_cliente_unidad DESC) vendido
            ) v ON TRUE
            LEFT JOIN LATERAL (
                SELECT sum(ce.monto) AS costos_registrados
                FROM obras.t_control_costo_obra cc JOIN obras.t_costo_ejecutado ce USING(id_control_costo)
                WHERE cc.id_empresa=o.id_empresa AND cc.id_obra=o.id_obra AND cc.estado='ACTIVO'
                  AND cc.moneda=o.moneda AND ce.id_empresa=o.id_empresa AND ce.id_obra=o.id_obra
                  AND ce.estado='REGISTRADO'
            ) c ON TRUE
            WHERE o.id_empresa=%s AND o.id_obra=ANY(%s) ORDER BY o.id_obra LIMIT 20001""", (ctx.empresa, ids))
        if len(result)>20000:
            from fastapi import HTTPException
            raise HTTPException(422, 'El reporte excede 20.000 obras. Selecciona una obra para acotar.')
        for row in result:
            sufficient = row['unidades_vendidas']>0 and not row['ventas_sin_monto'] and row['costos_registrados'] is not None
            row['saldo_estimado'] = row['monto_pactado']-row['costos_registrados'] if sufficient else None
            row['estado'] = 'SIN_DATOS_SUFICIENTES' if not sufficient else 'SALDO_POSITIVO' if row['saldo_estimado']>0 else 'SALDO_NEGATIVO' if row['saldo_estimado']<0 else 'EQUILIBRIO'
        if f.estado:
            result = [r for r in result if r['estado']==f.estado.upper()]
        if f.q:
            result = [r for r in result if f.q.casefold() in ' '.join(map(str,r.values())).casefold()]
        return result
    queries = {
        "presupuestario": """SELECT e.id_estimacion,e.id_obra,o.nombre AS obra,o.moneda,e.nombre,e.version,e.estado,e.monto_total,e.created_at
            FROM obras.t_estimacion e JOIN obras.t_obra o USING(id_obra)
            WHERE o.id_empresa=%s AND e.id_empresa=%s AND o.id_obra=ANY(%s) ORDER BY o.id_obra,e.version DESC,e.id_estimacion DESC""",
        "estado_unidades": """SELECT u.id_unidad,s.id_obra,o.nombre AS obra,u.codigo,u.tipo_unidad,u.estado,u.superficie
            FROM obras.t_unidad_construccion u JOIN obras.t_estructura_obra s USING(id_estructura)
            JOIN obras.t_obra o ON o.id_obra=s.id_obra
            WHERE o.id_empresa=%s AND s.id_obra=ANY(%s) ORDER BY s.id_obra,u.codigo""",
        "avance_ejecutivo": """SELECT u.id_unidad,s.id_obra,o.nombre AS obra,u.codigo,u.estado,a.porcentaje_avance,a.fecha_registro
            FROM obras.t_unidad_construccion u JOIN obras.t_estructura_obra s USING(id_estructura)
            JOIN obras.t_obra o ON o.id_obra=s.id_obra
            LEFT JOIN LATERAL (SELECT porcentaje_avance,fecha_registro FROM obras.t_avance_obra av
                WHERE av.id_unidad=u.id_unidad AND av.id_obra=s.id_obra ORDER BY av.fecha_registro DESC,av.id_avance DESC LIMIT 1) a ON TRUE
            WHERE o.id_empresa=%s AND s.id_obra=ANY(%s) ORDER BY s.id_obra,u.codigo""",
        "asignacion_personal": """SELECT ou.id_obra,o.nombre AS obra,u.id_usuario,p.nombre_completo,r.nombre_rol,ou.fecha_asignacion
            FROM obras.t_obra_usuario ou JOIN obras.t_obra o USING(id_obra)
            JOIN obras.t_usuario u USING(id_usuario) LEFT JOIN obras.t_persona p USING(id_persona)
            JOIN obras.t_rol r USING(id_rol)
            WHERE o.id_empresa=%s AND ou.id_obra=ANY(%s) AND u.id_empresa=o.id_empresa""",
        "utilizacion_personal": """SELECT ot.id_obra,o.nombre AS obra,u.id_usuario,p.nombre_completo,ot.orden_nro,ot.tipo_trab,ot.estado,ot.fecha_inicio,ot.fecha_fin
            FROM obras.t_orden_trabajo_usuario otu JOIN obras.t_orden_trabajo ot ON ot.orden_nro=otu.id_orden_trabajo
            JOIN obras.t_obra o USING(id_obra) JOIN obras.t_usuario u USING(id_usuario)
            LEFT JOIN obras.t_persona p USING(id_persona)
            WHERE o.id_empresa=%s AND ot.id_obra=ANY(%s) AND u.id_empresa=o.id_empresa""",
        "consumo_materiales": """SELECT ot.id_obra,o.nombre AS obra,m.id_movimiento,m.fecha_movimiento,m.id_material,mat.nombre_material,m.cantidad_asignada,m.tipo_movimiento,ot.orden_nro
            FROM obras.t_movimiento_almacen m JOIN obras.t_material mat USING(id_material)
            JOIN obras.t_orden_trabajo ot USING(orden_nro) JOIN obras.t_obra o USING(id_obra)
            WHERE o.id_empresa=%s AND ot.id_obra=ANY(%s) AND mat.id_empresa=o.id_empresa
            AND (m.id_empresa IS NULL OR m.id_empresa=o.id_empresa) AND m.tipo_movimiento='SALIDA'""",
        "incidencias": """SELECT i.id_incidencia,i.id_obra,o.nombre AS obra,i.id_unidad,i.titulo,i.prioridad,i.estado,i.created_at
            FROM obras.t_incidencia i JOIN obras.t_obra o USING(id_obra)
            WHERE o.id_empresa=%s AND i.id_obra=ANY(%s)""",
        "costos_periodo": """SELECT ce.id_costo_ejecutado,ce.id_obra,o.nombre AS obra,cc.moneda,ce.fecha,ce.concepto,
            ce.categoria,ce.cantidad,ce.costo_unitario,ce.monto,ce.estado
            FROM obras.t_costo_ejecutado ce JOIN obras.t_control_costo_obra cc USING(id_control_costo)
            JOIN obras.t_obra o ON o.id_obra=ce.id_obra
            WHERE o.id_empresa=%s AND ce.id_obra=ANY(%s) AND ce.id_empresa=o.id_empresa
              AND cc.id_empresa=o.id_empresa AND cc.id_obra=o.id_obra AND cc.estado='ACTIVO' AND ce.estado='REGISTRADO'""",
    }
    key = "incidencias" if kind == "incidencias_criticas" else kind
    params = [ctx.empresa, ids]
    if kind == "presupuestario":
        params = [ctx.empresa, ctx.empresa, ids]
    sql = queries[key]
    if kind=='avance_ejecutivo':
        restrictions = ''
        date_params = []
        for op, value in (('>=', f.desde), ('<=', f.hasta)):
            if value:
                restrictions += f" AND av.fecha_registro {op} %s"
                date_params.append(value)
        sql = sql.replace('ORDER BY av.fecha_registro', restrictions+' ORDER BY av.fecha_registro')
        params = date_params + params
    if kind == "incidencias_criticas":
        sql += " AND i.prioridad='CRITICA'"
    if key=='incidencias' and f.prioridad:
        sql += ' AND i.prioridad=%s'
        params.append(f.prioridad)
    from app.services.reportes.catalog import WORKERS
    if ctx.rol in WORKERS:
        if key == "incidencias":
            sql += " AND (i.id_usuario_registro=%s OR i.id_responsable=%s)"
            params.extend([ctx.usuario, ctx.usuario])
        elif key in {"asignacion_personal", "utilizacion_personal"}:
            sql += " AND u.id_usuario=%s"
            params.append(ctx.usuario)
    if kind in {"incidencias", "incidencias_criticas", "consumo_materiales"}:
        column = "m.fecha_movimiento" if kind == "consumo_materiales" else "(i.created_at AT TIME ZONE 'America/La_Paz')::date"
        for op, value in ((">=", f.desde), ("<=", f.hasta)):
            if value:
                sql += f" AND {column} {op} %s"
                params.append(value)
    date_columns = {'presupuestario': "(created_at AT TIME ZONE 'America/La_Paz')::date",
                    'asignacion_personal': "(fecha_asignacion AT TIME ZONE 'America/La_Paz')::date", 'utilizacion_personal': 'fecha_inicio::date',
                    'costos_periodo': 'fecha'}
    if kind in date_columns and (f.desde or f.hasta):
        sql = 'SELECT * FROM (' + sql + ') dated WHERE TRUE'
        for op, value in (('>=', f.desde), ('<=', f.hasta)):
            if value:
                sql += f' AND {date_columns[kind]} {op} %s'
                params.append(value)
    result = rows(db, sql + ' LIMIT 20001', params)
    if len(result)>20000:
        from fastapi import HTTPException
        raise HTTPException(422,'El reporte excede 20.000 filas. Acota obra o fechas.')
    if f.estado:
        result = [r for r in result if r.get("estado", "").upper() == f.estado.upper()]
    if f.q:
        result = [r for r in result if f.q.casefold() in " ".join(map(str,r.values())).casefold()]
    return result


def cutoff(db, params=()):
    return one(db, 'SELECT transaction_timestamp() AS corte', params)


def insert_ready_execution(db, params=()):
    return one(db, "INSERT INTO obras.t_reporte_ejecucion(id,id_empresa,id_usuario,solicitud,politica,alcance,resultado,estado)\n            VALUES(%s,%s,%s,%s,%s,%s,%s,'LISTO') RETURNING id", params)


def get_execution(db, params=()):
    return one(db, 'SELECT * FROM obras.t_reporte_ejecucion WHERE id=%s', params)


def list_executions(db, params=()):
    return rows(db, 'SELECT id,estado,solicitud,created_at,error FROM obras.t_reporte_ejecucion WHERE id_empresa=%s AND id_usuario=%s ORDER BY created_at DESC LIMIT 50', params)


def save_file(db, params=()):
    return one(db, "INSERT INTO obras.t_reporte_archivo(id,ejecucion,formato,nombre,contenido,sha256,expires_at)\n          VALUES(%s,%s,%s,%s,%s,%s,now()+interval '7 days') ON CONFLICT(ejecucion,formato)\n          DO UPDATE SET contenido=EXCLUDED.contenido,sha256=EXCLUDED.sha256,expires_at=EXCLUDED.expires_at RETURNING id,nombre", params)


def get_file(db, params=()):
    return one(db, 'SELECT * FROM obras.t_reporte_archivo WHERE id=%s AND expires_at>now()', params)


def get_conversation(db, params=()):
    return one(db, 'SELECT * FROM obras.t_asistente_conversacion WHERE id=%s AND id_empresa=%s AND id_usuario=%s AND expires_at>now()', params)


def create_conversation(db, params=()):
    return one(db, 'INSERT INTO obras.t_asistente_conversacion(id,id_empresa,id_usuario) VALUES(%s,%s,%s) RETURNING id', params)


def set_conversation_request(db, params=()):
    return one(db, 'UPDATE obras.t_asistente_conversacion SET solicitud=%s WHERE id=%s RETURNING id', params)


def add_message(db, params=()):
    return one(db, 'INSERT INTO obras.t_asistente_mensaje(conversacion,texto,respuesta) VALUES(%s,%s,%s) RETURNING id', params)


def conversation_inputs(db, params=()):
    return rows(db, "SELECT texto,respuesta->>'tema' AS tema,respuesta->'consultas' AS consultas FROM obras.t_asistente_mensaje WHERE conversacion=%s ORDER BY id DESC LIMIT 10", params)


def list_recipients(db, params=()):
    return rows(db, "SELECT u.id_usuario,COALESCE(p.nombre_completo,u.username) AS nombre FROM obras.t_usuario u LEFT JOIN obras.t_persona p USING(id_persona) WHERE u.id_empresa=%s AND u.estado='ACTIVO' AND u.correo IS NOT NULL ORDER BY nombre", params)


def insert_delivery(db, params=()):
    return one(db, 'INSERT INTO obras.t_reporte_envio(id,ejecucion,id_usuario,formatos,identidad)\n            VALUES(%s,%s,%s,%s,%s) ON CONFLICT(identidad) DO UPDATE SET identidad=EXCLUDED.identidad RETURNING id', params)


def list_deliveries(db, params=()):
    return rows(db, 'SELECT id,id_usuario,estado,intentos,message_id,error,created_at FROM obras.t_reporte_envio WHERE ejecucion=%s ORDER BY created_at', params)


def insert_schedule(db, params=()):
    return one(db, 'INSERT INTO obras.t_reporte_programacion(id,id_empresa,id_usuario,configuracion,habilitada,next_run) VALUES(%s,%s,%s,%s,%s,%s) RETURNING id', params)


def insert_schedule_recipient(db, params=()):
    return one(db, 'INSERT INTO obras.t_reporte_programacion_destinatario VALUES(%s,%s) RETURNING id_usuario', params)


def list_schedules(db, params=()):
    return rows(db, 'SELECT * FROM obras.t_reporte_programacion WHERE id_empresa=%s AND (%s OR id_usuario=%s) ORDER BY created_at DESC', params)


def get_schedule_locked(db, params=()):
    return one(db, 'SELECT * FROM obras.t_reporte_programacion WHERE id=%s FOR UPDATE', params)


def toggle_schedule(db, params=()):
    return one(db, "UPDATE obras.t_reporte_programacion SET habilitada=%s,next_run=%s,estado='ACTIVA',error=NULL WHERE id=%s RETURNING id,habilitada,next_run", params)


def insert_scheduled_execution(db, params=()):
    return one(db, "INSERT INTO obras.t_reporte_ejecucion(id,id_empresa,id_usuario,programacion,ocurrencia,solicitud,politica,alcance,estado)\n        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'PENDIENTE') ON CONFLICT(programacion,ocurrencia)\n        DO UPDATE SET ocurrencia=EXCLUDED.ocurrencia RETURNING id", params)


def company_exists(db, params=()):
    return one(db, 'SELECT id_empresa FROM obras.t_empresa WHERE id_empresa=%s', params)


def due_schedules(db, params=()):
    return rows(db, 'SELECT * FROM obras.t_reporte_programacion WHERE habilitada AND next_run<=now() ORDER BY next_run FOR UPDATE SKIP LOCKED LIMIT 10', params)


def advance_schedule(db, params=()):
    return one(db, "UPDATE obras.t_reporte_programacion SET next_run=%s,estado='ACTIVA',error=%s WHERE id=%s RETURNING id", params)


def suspend_schedule(db, params=()):
    return one(db, "UPDATE obras.t_reporte_programacion SET habilitada=FALSE,estado='SUSPENDIDA',error=%s WHERE id=%s RETURNING id", params)


def expire_generations(db, params=()):
    return rows(db, "UPDATE obras.t_reporte_ejecucion SET estado='FALLIDO',error='Se agotaron los intentos de generación.'\n            WHERE intentos>=3 AND ((estado='PENDIENTE' AND (lease_until IS NULL OR lease_until<now())) OR (estado='GENERANDO' AND lease_until<now())) RETURNING id", params)


def claim_execution_row(db, params=()):
    return one(db, "WITH job AS (SELECT id FROM obras.t_reporte_ejecucion\n            WHERE intentos<3 AND ((estado='PENDIENTE' AND (lease_until IS NULL OR lease_until<now())) OR (estado='GENERANDO' AND lease_until<now()))\n            ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1)\n            UPDATE obras.t_reporte_ejecucion e SET estado='GENERANDO',lease_until=now()+interval '20 minutes',intentos=intentos+1\n            FROM job WHERE e.id=job.id RETURNING e.*", params)


def get_schedule_enabled(db, params=()):
    return one(db, 'SELECT habilitada FROM obras.t_reporte_programacion WHERE id=%s', params)


def complete_execution(db, params=()):
    return one(db, "UPDATE obras.t_reporte_ejecucion SET resultado=%s,alcance=%s,politica=%s,estado='LISTO',lease_until=NULL WHERE id=%s AND estado='GENERANDO' RETURNING id", params)


def fail_execution(db, params=()):
    return one(db, "UPDATE obras.t_reporte_ejecucion SET estado=%s,error=%s,lease_until=now()+interval '1 minute' WHERE id=%s RETURNING id", params)


def expire_deliveries(db, params=()):
    return rows(db, "UPDATE obras.t_reporte_envio SET estado='INCIERTO',error='El worker perdió la confirmación del envío.' WHERE estado='ENVIANDO' AND lease_until<now() RETURNING id", params)


def fail_deliveries_generation(db, params=()):
    return rows(db, "UPDATE obras.t_reporte_envio d SET estado='FALLIDO',error='La generación del reporte falló.' FROM obras.t_reporte_ejecucion e WHERE d.ejecucion=e.id AND d.estado='PENDIENTE' AND e.estado='FALLIDO' RETURNING d.id", params)


def claim_delivery_row(db, params=()):
    return one(db, "WITH job AS (SELECT d.id FROM obras.t_reporte_envio d JOIN obras.t_reporte_ejecucion e ON e.id=d.ejecucion\n            WHERE d.estado='PENDIENTE' AND d.next_run<=now() AND e.estado='LISTO' ORDER BY d.created_at\n            FOR UPDATE OF d SKIP LOCKED LIMIT 1)\n            UPDATE obras.t_reporte_envio d SET estado='ENVIANDO',lease_until=now()+interval '20 minutes',intentos=intentos+1\n            FROM job WHERE d.id=job.id RETURNING d.*", params)


def complete_delivery(db, params=()):
    return one(db, "UPDATE obras.t_reporte_envio SET estado=%s,error=%s,message_id=%s,resultado=%s,lease_until=NULL,next_run=now()+interval '5 minutes' WHERE id=%s RETURNING id", params)


def purge_files(db, params=()):
    return rows(db, 'DELETE FROM obras.t_reporte_archivo WHERE expires_at<now() RETURNING id', params)


def purge_conversations(db, params=()):
    return rows(db, 'DELETE FROM obras.t_asistente_conversacion WHERE expires_at<now() RETURNING id', params)


def purge_results(db, params=()):
    return rows(db, "UPDATE obras.t_reporte_ejecucion SET resultado=NULL WHERE resultado IS NOT NULL AND created_at<now()-interval '30 days' RETURNING id", params)


def pending_purchases(db, empresa):
    return rows(db,"""SELECT d.id_material,
        SUM(GREATEST(d.cantidad_solicitada-d.cantidad_recibida,0)) AS pendiente
        FROM obras.t_orden_compra_detalle d JOIN obras.t_orden_compra oc USING(id_orden_compra)
        JOIN obras.t_material m USING(id_material)
        WHERE oc.id_empresa=%s AND m.id_empresa=oc.id_empresa
          AND oc.estado IN ('APROBADA','RECIBIDA_PARCIAL')
        GROUP BY d.id_material""",(empresa,))
