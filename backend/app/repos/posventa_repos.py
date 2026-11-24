"""
Repositorio de datos para CU33: Gestión de Garantías y Posventa
(HU161 a HU168).
Aislamiento multi-tenant estricto sobre el esquema obras.
"""
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
from app.classes.postgres import PostgreSQL
from app.config import Config


def _commit(db: PostgreSQL):
    if getattr(db, "conn", None) and not getattr(db.conn, "closed", False):
        db.conn.commit()


def _rollback(db: PostgreSQL):
    if getattr(db, "conn", None) and not getattr(db.conn, "closed", False):
        try:
            db.conn.rollback()
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# 1. HELPERS DE VÍNCULOS Y TENANT
# ─────────────────────────────────────────────────────────────────────────────

def obtener_cliente_por_usuario(id_usuario: int, id_empresa: int) -> Optional[Dict[str, Any]]:
    """Obtiene el registro t_crm_cliente asociado a un id_usuario en su empresa."""
    sql = f"""
        SELECT c.id_cliente, c.id_empresa, c.id_persona,
               COALESCE(NULLIF(TRIM(p.nombre_completo), ''), c.email) AS nombre_cliente,
               c.email
        FROM {Config.SCHEMA}.t_usuario u
        INNER JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = u.id_persona
        INNER JOIN {Config.SCHEMA}.t_crm_cliente c ON c.id_persona = p.id_persona AND c.id_empresa = %s
        WHERE u.id_usuario = %s;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(sql, (id_empresa, id_usuario), fetchone=True)
        if not row:
            return None
        return {
            "id_cliente": row[0],
            "id_empresa": row[1],
            "id_persona": row[2],
            "nombre_cliente": row[3],
            "email": row[4],
        }
    finally:
        db.close_connection()


def verificar_unidad_pertenece_empresa(id_unidad: int, id_empresa: int) -> Optional[Dict[str, Any]]:
    """Verifica si la unidad existe y pertenece a la empresa, retornando id_obra y datos básicos."""
    sql = f"""
        SELECT u.id_unidad, u.codigo, o.id_obra, o.nombre, o.id_empresa
        FROM {Config.SCHEMA}.t_unidad_construccion u
        INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
        INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
        WHERE u.id_unidad = %s AND o.id_empresa = %s;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(sql, (id_unidad, id_empresa), fetchone=True)
        if not row:
            return None
        return {
            "id_unidad": row[0],
            "nombre_unidad": row[1],
            "id_obra": row[2],
            "nombre_obra": row[3],
            "id_empresa": row[4],
        }
    finally:
        db.close_connection()


def verificar_cliente_propietario_unidad(id_cliente: int, id_unidad: int, id_empresa: int) -> bool:
    """Verifica si el cliente tiene la unidad comprada, entregada o reservada."""
    sql = f"""
        SELECT 1
        FROM {Config.SCHEMA}.t_crm_cliente_unidad cu
        INNER JOIN {Config.SCHEMA}.t_crm_cliente c ON c.id_cliente = cu.id_cliente
        WHERE cu.id_cliente = %s AND cu.id_unidad = %s AND c.id_empresa = %s
          AND cu.estado_asociacion IN ('VENDIDO', 'ENTREGADO', 'RESERVADO');
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(sql, (id_cliente, id_unidad, id_empresa), fetchone=True)
        return bool(row)
    finally:
        db.close_connection()


def listar_opciones_garantia(id_empresa: int) -> List[Dict[str, Any]]:
    """Lista unidades con propietario asociado dentro de la empresa autenticada."""
    sql = f"""
        SELECT DISTINCT
            u.id_unidad,
            u.codigo,
            e.nombre AS nombre_estructura,
            o.id_obra,
            o.nombre AS nombre_obra,
            c.id_cliente,
            COALESCE(NULLIF(TRIM(p.nombre_completo), ''), c.email) AS nombre_cliente,
            cu.estado_asociacion
        FROM {Config.SCHEMA}.t_crm_cliente_unidad cu
        INNER JOIN {Config.SCHEMA}.t_crm_cliente c
            ON c.id_cliente = cu.id_cliente AND c.id_empresa = %s
        INNER JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = c.id_persona
        INNER JOIN {Config.SCHEMA}.t_unidad_construccion u
            ON u.id_unidad = cu.id_unidad
        INNER JOIN {Config.SCHEMA}.t_estructura_obra e
            ON e.id_estructura = u.id_estructura
        INNER JOIN {Config.SCHEMA}.t_obra o
            ON o.id_obra = e.id_obra AND o.id_empresa = %s
        WHERE cu.estado_asociacion IN ('RESERVADO', 'VENDIDO', 'ENTREGADO')
        ORDER BY u.codigo, nombre_cliente;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(sql, (id_empresa, id_empresa), fetchall=True)
        return [{
            "id_unidad": row[0],
            "codigo_unidad": row[1],
            "nombre_estructura": row[2],
            "id_obra": row[3],
            "nombre_obra": row[4],
            "id_cliente": row[5],
            "nombre_cliente": row[6],
            "estado_asociacion": row[7],
        } for row in (rows or [])]
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# 2. GARANTÍAS INMOBILIARIAS (HU161, HU162, HU168)
# ─────────────────────────────────────────────────────────────────────────────

def registrar_garantia(
    id_empresa: int,
    id_unidad: int,
    id_cliente: int,
    tipo_garantia: str,
    descripcion_cobertura: str,
    condiciones: Optional[str],
    fecha_inicio: date,
    fecha_fin: date,
    id_usuario_registro: Optional[int]
) -> int:
    """Crea una garantía en t_unidad_garantia y retorna su ID."""
    sql = f"""
        INSERT INTO {Config.SCHEMA}.t_unidad_garantia (
            id_empresa, id_unidad, id_cliente, tipo_garantia,
            descripcion_cobertura, condiciones, fecha_inicio, fecha_fin,
            estado, id_usuario_registro
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, 'VIGENTE', %s
        ) RETURNING id_garantia;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            sql,
            (id_empresa, id_unidad, id_cliente, tipo_garantia, descripcion_cobertura,
             condiciones, fecha_inicio, fecha_fin, id_usuario_registro),
            fetchone=True
        )
        _commit(db)
        return row[0]
    except Exception:
        _rollback(db)
        raise
    finally:
        db.close_connection()


def listar_garantias(
    id_empresa: int,
    id_unidad: Optional[int] = None,
    id_cliente: Optional[int] = None,
    id_obra: Optional[int] = None,
    estado: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Consulta garantías con cálculo dinámico de vigencia y datos relacionados."""
    filtros = ["g.id_empresa = %s"]
    params: List[Any] = [id_empresa]

    if id_unidad:
        filtros.append("g.id_unidad = %s")
        params.append(id_unidad)
    if id_cliente:
        filtros.append("g.id_cliente = %s")
        params.append(id_cliente)
    if id_obra:
        filtros.append("o.id_obra = %s")
        params.append(id_obra)
    if estado:
        filtros.append("g.estado = %s")
        params.append(estado)

    where_str = " AND ".join(filtros)
    sql = f"""
        SELECT g.id_garantia, g.id_empresa, g.id_unidad, u.codigo AS nombre_unidad,
               o.id_obra, o.nombre AS nombre_obra,
               g.id_cliente,
               COALESCE(NULLIF(TRIM(p.nombre_completo), ''), c.email) AS nombre_cliente,
               c.email AS email_cliente,
               g.tipo_garantia, g.descripcion_cobertura, g.condiciones,
               g.fecha_inicio, g.fecha_fin,
               CASE
                   WHEN g.estado = 'ANULADA' THEN 'ANULADA'
                   WHEN CURRENT_DATE > g.fecha_fin THEN 'VENCIDA'
                   ELSE 'VIGENTE'
               END AS estado_actual,
               g.estado AS estado_almacenado,
               g.created_at
        FROM {Config.SCHEMA}.t_unidad_garantia g
        INNER JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = g.id_unidad
        INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
        INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
        INNER JOIN {Config.SCHEMA}.t_crm_cliente c ON c.id_cliente = g.id_cliente
        INNER JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = c.id_persona
        WHERE {where_str}
        ORDER BY g.fecha_fin DESC, g.id_garantia DESC;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(sql, tuple(params), fetchall=True)
        res = []
        for r in (rows or []):
            res.append({
                "id_garantia": r[0],
                "id_empresa": r[1],
                "id_unidad": r[2],
                "nombre_unidad": r[3],
                "id_obra": r[4],
                "nombre_obra": r[5],
                "id_cliente": r[6],
                "nombre_cliente": r[7],
                "email_cliente": r[8],
                "tipo_garantia": r[9],
                "descripcion_cobertura": r[10],
                "condiciones": r[11],
                "fecha_inicio": r[12].isoformat() if hasattr(r[12], "isoformat") else str(r[12]),
                "fecha_fin": r[13].isoformat() if hasattr(r[13], "isoformat") else str(r[13]),
                "estado": r[14],
                "estado_almacenado": r[15],
                "created_at": r[16].isoformat() if hasattr(r[16], "isoformat") else str(r[16]),
            })
        return res
    finally:
        db.close_connection()


def obtener_garantia_por_id(id_garantia: int, id_empresa: int) -> Optional[Dict[str, Any]]:
    """Retorna una garantía específica asegurando pertenencia a la empresa."""
    sql = f"""
        SELECT g.id_garantia, g.id_empresa, g.id_unidad, u.codigo AS nombre_unidad,
               o.id_obra, o.nombre AS nombre_obra,
               g.id_cliente,
               COALESCE(NULLIF(TRIM(p.nombre_completo), ''), c.email) AS nombre_cliente,
               c.email AS email_cliente,
               g.tipo_garantia, g.descripcion_cobertura, g.condiciones,
               g.fecha_inicio, g.fecha_fin,
               CASE
                   WHEN g.estado = 'ANULADA' THEN 'ANULADA'
                   WHEN CURRENT_DATE > g.fecha_fin THEN 'VENCIDA'
                   ELSE 'VIGENTE'
               END AS estado_actual,
               g.created_at
        FROM {Config.SCHEMA}.t_unidad_garantia g
        INNER JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = g.id_unidad
        INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
        INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
        INNER JOIN {Config.SCHEMA}.t_crm_cliente c ON c.id_cliente = g.id_cliente
        INNER JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = c.id_persona
        WHERE g.id_garantia = %s AND g.id_empresa = %s;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        r = db.execute_query(sql, (id_garantia, id_empresa), fetchone=True)
        if not r:
            return None
        return {
            "id_garantia": r[0],
            "id_empresa": r[1],
            "id_unidad": r[2],
            "nombre_unidad": r[3],
            "id_obra": r[4],
            "nombre_obra": r[5],
            "id_cliente": r[6],
            "nombre_cliente": r[7],
            "email_cliente": r[8],
            "tipo_garantia": r[9],
            "descripcion_cobertura": r[10],
            "condiciones": r[11],
            "fecha_inicio": r[12].isoformat() if hasattr(r[12], "isoformat") else str(r[12]),
            "fecha_fin": r[13].isoformat() if hasattr(r[13], "isoformat") else str(r[13]),
            "estado": r[14],
            "created_at": r[15].isoformat() if hasattr(r[15], "isoformat") else str(r[15]),
        }
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# 3. SOLICITUDES DE POSVENTA (HU163 a HU168)
# ─────────────────────────────────────────────────────────────────────────────

def generar_codigo_ticket_unico(db: PostgreSQL) -> str:
    """Genera un código secuencial determinista e idempotente para el ticket (ej. PV-20261123-0001)."""
    prefijo = f"PV-{datetime.now().strftime('%Y%m%d')}"
    sql = f"""
        SELECT COUNT(*) + 1
        FROM {Config.SCHEMA}.t_posventa_solicitud
        WHERE codigo_ticket LIKE %s;
    """
    row = db.execute_query(sql, (f"{prefijo}-%",), fetchone=True)
    num = (row[0] if row else 1)
    return f"{prefijo}-{num:04d}"


def registrar_solicitud(
    id_empresa: int,
    id_unidad: int,
    id_cliente: int,
    titulo: str,
    descripcion_defecto: str,
    id_garantia: Optional[int],
    id_usuario_registro: Optional[int]
) -> Tuple[int, str]:
    """Crea una nueva solicitud con estado PENDIENTE y genera su código de ticket único."""
    db = PostgreSQL()
    db.create_connection()
    try:
        codigo = generar_codigo_ticket_unico(db)
        sql = f"""
            INSERT INTO {Config.SCHEMA}.t_posventa_solicitud (
                codigo_ticket, id_empresa, id_unidad, id_cliente,
                id_garantia, titulo, descripcion_defecto, estado, prioridad,
                id_usuario_registro
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, 'PENDIENTE', 'MEDIA', %s
            ) RETURNING id_solicitud, codigo_ticket;
        """
        row = db.execute_query(
            sql,
            (codigo, id_empresa, id_unidad, id_cliente, id_garantia,
             titulo, descripcion_defecto, id_usuario_registro),
            fetchone=True
        )
        id_solicitud = row[0]
        codigo_ticket = row[1]

        # Bitácora inicial
        sql_bit = f"""
            INSERT INTO {Config.SCHEMA}.t_posventa_bitacora (
                id_solicitud, id_usuario, tipo_evento, estado_anterior, estado_nuevo, detalle_acciones
            ) VALUES (
                %s, %s, 'REGISTRO_TICKET', NULL, 'PENDIENTE', 'Recepción y apertura exitosa del ticket de posventa por el cliente.'
            );
        """
        db.execute_query(sql_bit, (id_solicitud, id_usuario_registro))

        _commit(db)
        return id_solicitud, codigo_ticket
    except Exception:
        _rollback(db)
        raise
    finally:
        db.close_connection()


def clasificar_solicitud(
    id_solicitud: int,
    id_empresa: int,
    categoria: str,
    prioridad: str,
    aplica_garantia: bool,
    id_garantia: Optional[int],
    observaciones: Optional[str],
    id_usuario_clasifica: int
) -> bool:
    """Clasifica el ticket (HU164): categoría, prioridad, cobertura de garantía y estado CLASIFICADA."""
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = f"""
            UPDATE {Config.SCHEMA}.t_posventa_solicitud
            SET categoria = %s,
                prioridad = %s,
                aplica_garantia = %s,
                id_garantia = %s,
                observaciones_clasificacion = %s,
                id_usuario_clasifica = %s,
                estado = 'CLASIFICADA',
                updated_at = CURRENT_TIMESTAMP
            WHERE id_solicitud = %s AND id_empresa = %s
            RETURNING estado;
        """
        row = db.execute_query(
            sql,
            (categoria, prioridad, aplica_garantia, id_garantia, observaciones,
             id_usuario_clasifica, id_solicitud, id_empresa),
            fetchone=True
        )
        if not row:
            _rollback(db)
            return False

        # Bitácora de clasificación
        detalle = f"Clasificada en categoría '{categoria}', prioridad '{prioridad}'. " + \
                  (f"Aplica garantía (ID {id_garantia}). " if aplica_garantia else "Sin cobertura de garantía. ") + \
                  (f"Obs: {observaciones}" if observaciones else "")

        sql_bit = f"""
            INSERT INTO {Config.SCHEMA}.t_posventa_bitacora (
                id_solicitud, id_usuario, tipo_evento, estado_anterior, estado_nuevo, detalle_acciones
            ) VALUES (%s, %s, 'CLASIFICACION', 'PENDIENTE', 'CLASIFICADA', %s);
        """
        db.execute_query(sql_bit, (id_solicitud, id_usuario_clasifica, detalle))

        _commit(db)
        return True
    except Exception:
        _rollback(db)
        raise
    finally:
        db.close_connection()


def asignar_supervisor_solicitud(
    id_solicitud: int,
    id_empresa: int,
    id_supervisor: int,
    fecha_estimada_visita: date,
    instrucciones_tecnicas: Optional[str],
    id_usuario_asigna: int
) -> bool:
    """Asigna supervisor y programa fecha estimada de visita (HU165), estado ASIGNADA."""
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = f"""
            UPDATE {Config.SCHEMA}.t_posventa_solicitud
            SET id_supervisor_asignado = %s,
                fecha_estimada_visita = %s,
                instrucciones_tecnicas = %s,
                id_usuario_asigna = %s,
                estado = 'ASIGNADA',
                updated_at = CURRENT_TIMESTAMP
            WHERE id_solicitud = %s AND id_empresa = %s
            RETURNING estado;
        """
        row = db.execute_query(
            sql,
            (id_supervisor, fecha_estimada_visita, instrucciones_tecnicas,
             id_usuario_asigna, id_solicitud, id_empresa),
            fetchone=True
        )
        if not row:
            _rollback(db)
            return False

        detalle = f"Asignada a supervisor ID {id_supervisor} con fecha de visita estimada para {fecha_estimada_visita}. " + \
                  (f"Instrucciones: {instrucciones_tecnicas}" if instrucciones_tecnicas else "")

        sql_bit = f"""
            INSERT INTO {Config.SCHEMA}.t_posventa_bitacora (
                id_solicitud, id_usuario, tipo_evento, estado_anterior, estado_nuevo, detalle_acciones
            ) VALUES (%s, %s, 'ASIGNACION_SUPERVISOR', 'CLASIFICADA', 'ASIGNADA', %s);
        """
        db.execute_query(sql_bit, (id_solicitud, id_usuario_asigna, detalle))

        _commit(db)
        return True
    except Exception:
        _rollback(db)
        raise
    finally:
        db.close_connection()


def registrar_atencion_tecnica(
    id_solicitud: int,
    id_empresa: int,
    id_supervisor: int,
    nuevo_estado: str,
    acciones_realizadas: str,
    materiales_utilizados: Optional[str] = None,
    motivo_cierre: Optional[str] = None
) -> bool:
    """Registra la gestión de atención, materiales y actualización de estado (HU166)."""
    db = PostgreSQL()
    db.create_connection()
    try:
        # Obtener estado actual
        sql_cur = f"""
            SELECT estado FROM {Config.SCHEMA}.t_posventa_solicitud
            WHERE id_solicitud = %s AND id_empresa = %s;
        """
        cur_row = db.execute_query(sql_cur, (id_solicitud, id_empresa), fetchone=True)
        if not cur_row:
            _rollback(db)
            return False
        estado_ant = cur_row[0]

        es_cierre = nuevo_estado in ('RESUELTA', 'CERRADA')
        sql_up = f"""
            UPDATE {Config.SCHEMA}.t_posventa_solicitud
            SET estado = %s,
                fecha_cierre = {'CURRENT_TIMESTAMP' if es_cierre else 'fecha_cierre'},
                motivo_rechazo_cierre = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id_solicitud = %s AND id_empresa = %s;
        """
        db.execute_query(sql_up, (nuevo_estado, motivo_cierre, id_solicitud, id_empresa))

        tipo_ev = "CIERRE_TECNICO" if es_cierre else "ACCION_CORRECTIVA"
        sql_bit = f"""
            INSERT INTO {Config.SCHEMA}.t_posventa_bitacora (
                id_solicitud, id_usuario, tipo_evento, estado_anterior, estado_nuevo,
                detalle_acciones, materiales_utilizados
            ) VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        db.execute_query(sql_bit, (id_solicitud, id_supervisor, tipo_ev, estado_ant, nuevo_estado,
                                   acciones_realizadas, materiales_utilizados))

        _commit(db)
        return True
    except Exception:
        _rollback(db)
        raise
    finally:
        db.close_connection()


def agregar_evidencia(
    id_solicitud: int,
    tipo_evidencia: str,
    ruta_archivo: str,
    nombre_archivo: str,
    tipo_mime: Optional[str],
    tamano_bytes: Optional[int],
    id_usuario: Optional[int]
) -> int:
    """Inserta una fotografía o documento de evidencia asociado a la solicitud."""
    sql = f"""
        INSERT INTO {Config.SCHEMA}.t_posventa_evidencia (
            id_solicitud, tipo_evidencia, ruta_archivo, nombre_archivo,
            tipo_mime, tamano_bytes, id_usuario
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id_evidencia;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        r = db.execute_query(
            sql,
            (id_solicitud, tipo_evidencia, ruta_archivo, nombre_archivo,
             tipo_mime, tamano_bytes, id_usuario),
            fetchone=True
        )
        _commit(db)
        return r[0]
    except Exception:
        _rollback(db)
        raise
    finally:
        db.close_connection()


def listar_solicitudes(
    id_empresa: int,
    id_cliente: Optional[int] = None,
    id_supervisor: Optional[int] = None,
    id_obra: Optional[int] = None,
    id_unidad: Optional[int] = None,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    categoria: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Consulta la lista de solicitudes con filtros para cliente, supervisor, jefe de obra o admin."""
    filtros = ["s.id_empresa = %s"]
    params: List[Any] = [id_empresa]

    if id_cliente:
        filtros.append("s.id_cliente = %s")
        params.append(id_cliente)
    if id_supervisor:
        filtros.append("s.id_supervisor_asignado = %s")
        params.append(id_supervisor)
    if id_obra:
        filtros.append("o.id_obra = %s")
        params.append(id_obra)
    if id_unidad:
        filtros.append("s.id_unidad = %s")
        params.append(id_unidad)
    if estado:
        filtros.append("s.estado = %s")
        params.append(estado)
    if prioridad:
        filtros.append("s.prioridad = %s")
        params.append(prioridad)
    if categoria:
        filtros.append("s.categoria = %s")
        params.append(categoria)

    where_str = " AND ".join(filtros)
    sql = f"""
        SELECT s.id_solicitud, s.codigo_ticket, s.id_empresa,
               s.id_unidad, u.codigo AS nombre_unidad,
               o.id_obra, o.nombre AS nombre_obra,
               s.id_cliente,
               COALESCE(NULLIF(TRIM(p.nombre_completo), ''), c.email) AS nombre_cliente,
               s.id_garantia, g.tipo_garantia,
               s.aplica_garantia, s.titulo, s.descripcion_defecto, s.categoria, s.prioridad, s.estado,
               s.id_supervisor_asignado,
               COALESCE(NULLIF(TRIM(psup.nombre_completo), ''), usup.username) AS nombre_supervisor,
               s.fecha_estimada_visita, s.instrucciones_tecnicas, s.observaciones_clasificacion,
               s.fecha_cierre, s.created_at, s.updated_at,
               (SELECT COUNT(*) FROM {Config.SCHEMA}.t_posventa_evidencia ev WHERE ev.id_solicitud = s.id_solicitud) AS total_evidencias
        FROM {Config.SCHEMA}.t_posventa_solicitud s
        INNER JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = s.id_unidad
        INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
        INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
        INNER JOIN {Config.SCHEMA}.t_crm_cliente c ON c.id_cliente = s.id_cliente
        INNER JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = c.id_persona
        LEFT JOIN {Config.SCHEMA}.t_unidad_garantia g ON g.id_garantia = s.id_garantia
        LEFT JOIN {Config.SCHEMA}.t_usuario usup ON usup.id_usuario = s.id_supervisor_asignado
        LEFT JOIN {Config.SCHEMA}.t_persona psup ON psup.id_persona = usup.id_persona
        WHERE {where_str}
        ORDER BY s.id_solicitud DESC;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(sql, tuple(params), fetchall=True)
        res = []
        for r in (rows or []):
            res.append({
                "id_solicitud": r[0],
                "codigo_ticket": r[1],
                "id_empresa": r[2],
                "id_unidad": r[3],
                "nombre_unidad": r[4],
                "id_obra": r[5],
                "nombre_obra": r[6],
                "id_cliente": r[7],
                "nombre_cliente": r[8],
                "id_garantia": r[9],
                "tipo_garantia": r[10],
                "aplica_garantia": r[11],
                "titulo": r[12],
                "descripcion_defecto": r[13],
                "categoria": r[14],
                "prioridad": r[15],
                "estado": r[16],
                "id_supervisor_asignado": r[17],
                "nombre_supervisor": r[18],
                "fecha_estimada_visita": r[19].isoformat() if hasattr(r[19], "isoformat") else (str(r[19]) if r[19] else None),
                "instrucciones_tecnicas": r[20],
                "observaciones_clasificacion": r[21],
                "fecha_cierre": r[22].isoformat() if hasattr(r[22], "isoformat") else (str(r[22]) if r[22] else None),
                "created_at": r[23].isoformat() if hasattr(r[23], "isoformat") else str(r[23]),
                "updated_at": r[24].isoformat() if hasattr(r[24], "isoformat") else str(r[24]),
                "total_evidencias": r[25],
            })
        return res
    finally:
        db.close_connection()


def obtener_solicitud_detalle(id_solicitud: int, id_empresa: int) -> Optional[Dict[str, Any]]:
    """Obtiene el ticket completo con sus evidencias y línea de tiempo (bitácora)."""
    solicitudes = listar_solicitudes(id_empresa=id_empresa)
    target = next((s for s in solicitudes if s["id_solicitud"] == id_solicitud), None)
    if not target:
        return None

    db = PostgreSQL()
    db.create_connection()
    try:
        # Evidencias
        sql_ev = f"""
            SELECT id_evidencia, tipo_evidencia, ruta_archivo, nombre_archivo,
                   tipo_mime, tamano_bytes, id_usuario, created_at
            FROM {Config.SCHEMA}.t_posventa_evidencia
            WHERE id_solicitud = %s
            ORDER BY id_evidencia ASC;
        """
        ev_rows = db.execute_query(sql_ev, (id_solicitud,), fetchall=True)
        evidencias = []
        for e in (ev_rows or []):
            evidencias.append({
                "id_evidencia": e[0],
                "tipo_evidencia": e[1],
                "ruta_archivo": e[2],
                "nombre_archivo": e[3],
                "tipo_mime": e[4],
                "tamano_bytes": e[5],
                "id_usuario": e[6],
                "created_at": e[7].isoformat() if hasattr(e[7], "isoformat") else str(e[7]),
            })

        # Bitácora / Línea de tiempo
        sql_bit = f"""
            SELECT b.id_bitacora, b.id_usuario,
                   COALESCE(NULLIF(TRIM(p.nombre_completo), ''), u.username) AS nombre_usuario,
                   b.tipo_evento, b.estado_anterior, b.estado_nuevo,
                   b.detalle_acciones, b.materiales_utilizados, b.fecha
            FROM {Config.SCHEMA}.t_posventa_bitacora b
            LEFT JOIN {Config.SCHEMA}.t_usuario u ON u.id_usuario = b.id_usuario
            LEFT JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = u.id_persona
            WHERE b.id_solicitud = %s
            ORDER BY b.fecha ASC, b.id_bitacora ASC;
        """
        bit_rows = db.execute_query(sql_bit, (id_solicitud,), fetchall=True)
        timeline = []
        for b in (bit_rows or []):
            timeline.append({
                "id_bitacora": b[0],
                "id_usuario": b[1],
                "nombre_usuario": b[2] or "Sistema",
                "tipo_evento": b[3],
                "estado_anterior": b[4],
                "estado_nuevo": b[5],
                "detalle_acciones": b[6],
                "materiales_utilizados": b[7],
                "fecha": b[8].isoformat() if hasattr(b[8], "isoformat") else str(b[8]),
            })

        target["evidencias"] = evidencias
        target["linea_tiempo"] = timeline
        return target
    finally:
        db.close_connection()


def listar_supervisores_disponibles(id_empresa: int, id_obra: Optional[int] = None) -> List[Dict[str, Any]]:
    """Lista supervisores técnicos disponibles de la empresa para asignación."""
    sql = f"""
        SELECT DISTINCT u.id_usuario,
               COALESCE(NULLIF(TRIM(p.nombre_completo), ''), u.username) AS nombre_completo,
               r.nombre_rol, u.username
        FROM {Config.SCHEMA}.t_usuario u
        INNER JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = u.id_persona
        INNER JOIN {Config.SCHEMA}.t_rol r ON r.id_rol = u.id_rol
        WHERE u.id_empresa = %s
          AND u.estado = 'ACTIVO'
          AND upper(replace(r.nombre_rol, ' ', '_')) IN ('SUPERVISOR', 'SUPERVISOR_OBRA', 'JEFE_DE_OBRA', 'JEFE_OBRA')
        ORDER BY nombre_completo;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(sql, (id_empresa,), fetchall=True)
        return [
            {
                "id_usuario": r[0],
                "nombre_completo": r[1],
                "nombre_rol": r[2],
                "username": r[3],
            }
            for r in (rows or [])
        ]
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# 4. TRAZABILIDAD Y MÉTRICAS HISTÓRICAS (HU168)
# ─────────────────────────────────────────────────────────────────────────────

def obtener_metricas_posventa(id_empresa: int) -> Dict[str, Any]:
    """Calcula KPIs consolidados de posventa para auditoría y control de calidad."""
    sql = f"""
        SELECT
            COUNT(*) AS total_solicitudes,
            COUNT(*) FILTER (WHERE estado = 'PENDIENTE') AS pendientes,
            COUNT(*) FILTER (WHERE estado = 'CLASIFICADA') AS clasificadas,
            COUNT(*) FILTER (WHERE estado = 'ASIGNADA') AS asignadas,
            COUNT(*) FILTER (WHERE estado = 'EN_ATENCION') AS en_atencion,
            COUNT(*) FILTER (WHERE estado IN ('RESUELTA', 'CERRADA')) AS resueltas,
            COUNT(*) FILTER (WHERE aplica_garantia = TRUE) AS cubiertas_por_garantia,
            COUNT(*) FILTER (WHERE prioridad = 'URGENTE') AS urgentes,
            ROUND(AVG(EXTRACT(EPOCH FROM (fecha_cierre - created_at))/86400)::numeric, 1) AS promedio_dias_resolucion
        FROM {Config.SCHEMA}.t_posventa_solicitud
        WHERE id_empresa = %s;
    """
    sql_gar = f"""
        SELECT
            COUNT(*) AS total_garantias,
            COUNT(*) FILTER (WHERE CURRENT_DATE <= fecha_fin AND estado = 'VIGENTE') AS vigentes,
            COUNT(*) FILTER (WHERE CURRENT_DATE > fecha_fin OR estado = 'VENCIDA') AS vencidas
        FROM {Config.SCHEMA}.t_unidad_garantia
        WHERE id_empresa = %s;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        r_sol = db.execute_query(sql, (id_empresa,), fetchone=True)
        r_gar = db.execute_query(sql_gar, (id_empresa,), fetchone=True)
        return {
            "total_solicitudes": r_sol[0] if r_sol else 0,
            "pendientes": r_sol[1] if r_sol else 0,
            "clasificadas": r_sol[2] if r_sol else 0,
            "asignadas": r_sol[3] if r_sol else 0,
            "en_atencion": r_sol[4] if r_sol else 0,
            "resueltas": r_sol[5] if r_sol else 0,
            "cubiertas_por_garantia": r_sol[6] if r_sol else 0,
            "urgentes": r_sol[7] if r_sol else 0,
            "promedio_dias_resolucion": float(r_sol[8]) if (r_sol and r_sol[8] is not None) else 0.0,
            "total_garantias": r_gar[0] if r_gar else 0,
            "garantias_vigentes": r_gar[1] if r_gar else 0,
            "garantias_vencidas": r_gar[2] if r_gar else 0,
        }
    finally:
        db.close_connection()
