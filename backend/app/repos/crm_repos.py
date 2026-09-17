from app.classes.postgres import PostgreSQL
from app.config import Config


# ─────────────────────────────────────────────────────────────────────────────
# Mapeador de fila → dict de Cliente
# ─────────────────────────────────────────────────────────────────────────────
_CLIENTE_FIELDS = (
    "id_cliente", "id_empresa", "id_persona", "email", "tipo_cliente", "estado",
    "origen", "presupuesto_estimado", "notas", "id_usuario_asignado",
    "created_at", "updated_at",
    "nombre_completo", "ci", "telefono", "telefono_ref", "direccion", "ubicacion",
    "nombre_empresa", "asesor_nombre", "asesor_username"
)


def _cliente_dict(row):
    if not row:
        return None
    d = dict(zip(_CLIENTE_FIELDS, row))
    if d.get("presupuesto_estimado") is not None:
        d["presupuesto_estimado"] = float(d["presupuesto_estimado"])
    return d


# ─────────────────────────────────────────────────────────────────────────────
# 1. LISTAR CLIENTES / PROSPECTOS
# ─────────────────────────────────────────────────────────────────────────────
def listar_clientes(id_empresa=None, tipo_cliente=None, estado=None, q=None, id_usuario_asignado=None, page=1, limit=20):
    filtros = []
    params = []

    if id_empresa is not None:
        filtros.append("c.id_empresa = %s")
        params.append(id_empresa)

    if tipo_cliente:
        filtros.append("c.tipo_cliente = %s")
        params.append(tipo_cliente.upper())

    if estado:
        filtros.append("c.estado = %s")
        params.append(estado.upper())

    if id_usuario_asignado:
        filtros.append("c.id_usuario_asignado = %s")
        params.append(id_usuario_asignado)

    if q:
        filtros.append(
            "(p.nombre_completo ILIKE %s OR p.ci ILIKE %s OR p.telefono ILIKE %s OR c.email ILIKE %s)"
        )
        like = f"%{q}%"
        params += [like, like, like, like]

    where = (" WHERE " + " AND ".join(filtros)) if filtros else ""

    sql = f"""
        SELECT c.id_cliente, c.id_empresa, c.id_persona, c.email, c.tipo_cliente, c.estado,
               c.origen, c.presupuesto_estimado, c.notas, c.id_usuario_asignado,
               c.created_at, c.updated_at,
               p.nombre_completo, p.ci, p.telefono, p.telefono_ref, p.direccion, p.ubicacion,
               COALESCE(e.nombre_empresa, 'Sin Empresa') AS nombre_empresa,
               pu.nombre_completo AS asesor_nombre,
               u.username AS asesor_username
        FROM {Config.SCHEMA}.t_crm_cliente c
        INNER JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = c.id_persona
        LEFT JOIN {Config.SCHEMA}.t_empresa e ON e.id_empresa = c.id_empresa
        LEFT JOIN {Config.SCHEMA}.t_usuario u ON u.id_usuario = c.id_usuario_asignado
        LEFT JOIN {Config.SCHEMA}.t_persona pu ON pu.id_persona = u.id_persona
        {where}
        ORDER BY c.created_at DESC
        LIMIT %s OFFSET %s;
    """

    count_sql = f"""
        SELECT COUNT(*)
        FROM {Config.SCHEMA}.t_crm_cliente c
        INNER JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = c.id_persona
        {where};
    """

    offset = (page - 1) * limit
    db = PostgreSQL()
    db.create_connection()
    try:
        total = db.execute_query(count_sql, tuple(params), fetchone=True)[0]
        rows = db.execute_query(sql, tuple(params + [limit, offset]), fetchall=True) or []
        items = [_cliente_dict(r) for r in rows]
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        return {
            "success": True,
            "data": items,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
            }
        }
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# 2. OBTENER DETALLE DE CLIENTE POR ID
# ─────────────────────────────────────────────────────────────────────────────
def obtener_cliente_por_id(id_cliente: int, id_empresa: int = None):
    filtros = ["c.id_cliente = %s"]
    params = [id_cliente]

    if id_empresa is not None:
        filtros.append("c.id_empresa = %s")
        params.append(id_empresa)

    sql = f"""
        SELECT c.id_cliente, c.id_empresa, c.id_persona, c.email, c.tipo_cliente, c.estado,
               c.origen, c.presupuesto_estimado, c.notas, c.id_usuario_asignado,
               c.created_at, c.updated_at,
               p.nombre_completo, p.ci, p.telefono, p.telefono_ref, p.direccion, p.ubicacion,
               COALESCE(e.nombre_empresa, 'Sin Empresa') AS nombre_empresa,
               pu.nombre_completo AS asesor_nombre,
               u.username AS asesor_username
        FROM {Config.SCHEMA}.t_crm_cliente c
        INNER JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = c.id_persona
        LEFT JOIN {Config.SCHEMA}.t_empresa e ON e.id_empresa = c.id_empresa
        LEFT JOIN {Config.SCHEMA}.t_usuario u ON u.id_usuario = c.id_usuario_asignado
        LEFT JOIN {Config.SCHEMA}.t_persona pu ON pu.id_persona = u.id_persona
        WHERE {" AND ".join(filtros)}
        LIMIT 1;
    """

    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(sql, tuple(params), fetchone=True)
        return _cliente_dict(row)
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# 3. GESTIÓN DE PERSONA Y CLIENTE
# ─────────────────────────────────────────────────────────────────────────────
def buscar_persona_por_ci(ci: str):
    if not ci or not str(ci).strip():
        return None
    sql = f"""
        SELECT id_persona, nombre_completo, ci, telefono, telefono_ref, direccion, ubicacion
        FROM {Config.SCHEMA}.t_persona
        WHERE UPPER(TRIM(ci)) = UPPER(TRIM(%s))
        LIMIT 1;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(sql, (str(ci).strip(),), fetchone=True)
        if row:
            return {
                "id_persona": row[0],
                "nombre_completo": row[1],
                "ci": row[2],
                "telefono": row[3],
                "telefono_ref": row[4],
                "direccion": row[5],
                "ubicacion": row[6],
            }
        return None
    finally:
        db.close_connection()


def crear_persona(nombre_completo: str, ci: str = None, telefono: str = None,
                  telefono_ref: str = None, direccion: str = None, ubicacion: str = None):
    sql = f"""
        INSERT INTO {Config.SCHEMA}.t_persona (nombre_completo, ci, telefono, telefono_ref, direccion, ubicacion)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id_persona;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        res = db.execute_query(sql, (
            nombre_completo.strip(), ci.strip() if ci else None,
            telefono.strip() if telefono else None, telefono_ref.strip() if telefono_ref else None,
            direccion.strip() if direccion else None, ubicacion.strip() if ubicacion else None
        ), fetchone=True, commit=True)
        return res[0] if res else None
    finally:
        db.close_connection()


def actualizar_persona(id_persona: int, nombre_completo: str = None, ci: str = None,
                        telefono: str = None, telefono_ref: str = None,
                        direccion: str = None, ubicacion: str = None):
    campos = []
    params = []
    if nombre_completo is not None:
        campos.append("nombre_completo = %s")
        params.append(nombre_completo.strip())
    if ci is not None:
        campos.append("ci = %s")
        params.append(ci.strip() or None)
    if telefono is not None:
        campos.append("telefono = %s")
        params.append(telefono.strip() or None)
    if telefono_ref is not None:
        campos.append("telefono_ref = %s")
        params.append(telefono_ref.strip() or None)
    if direccion is not None:
        campos.append("direccion = %s")
        params.append(direccion.strip() or None)
    if ubicacion is not None:
        campos.append("ubicacion = %s")
        params.append(ubicacion.strip() or None)

    if not campos:
        return True

    params.append(id_persona)
    sql = f"UPDATE {Config.SCHEMA}.t_persona SET {', '.join(campos)} WHERE id_persona = %s;"
    db = PostgreSQL()
    db.create_connection()
    try:
        db.execute_query(sql, tuple(params), commit=True)
        return True
    finally:
        db.close_connection()


def crear_cliente_crm(id_empresa: int, id_persona: int, email: str = None,
                      tipo_cliente: str = "PROSPECTO", estado: str = "NUEVO",
                      origen: str = "DIRECTO", presupuesto_estimado: float = None,
                      notas: str = None, id_usuario_asignado: int = None):
    sql = f"""
        INSERT INTO {Config.SCHEMA}.t_crm_cliente (
            id_empresa, id_persona, email, tipo_cliente, estado,
            origen, presupuesto_estimado, notas, id_usuario_asignado
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id_cliente;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        res = db.execute_query(sql, (
            id_empresa, id_persona, email.strip() if email else None,
            tipo_cliente.upper(), estado.upper(), origen.upper() if origen else 'DIRECTO',
            presupuesto_estimado, notas, id_usuario_asignado
        ), fetchone=True, commit=True)
        return res[0] if res else None
    finally:
        db.close_connection()


def actualizar_cliente_crm(id_cliente: int, id_empresa: int, email: str = None,
                           origen: str = None, presupuesto_estimado: float = None,
                           notas: str = None, id_usuario_asignado: int = None):
    campos = []
    params = []
    if email is not None:
        campos.append("email = %s")
        params.append(email.strip() or None)
    if origen is not None:
        campos.append("origen = %s")
        params.append(origen.strip().upper())
    if presupuesto_estimado is not None:
        campos.append("presupuesto_estimado = %s")
        params.append(presupuesto_estimado)
    if notas is not None:
        campos.append("notas = %s")
        params.append(notas.strip() or None)
    if id_usuario_asignado is not None:
        campos.append("id_usuario_asignado = %s")
        params.append(id_usuario_asignado if id_usuario_asignado > 0 else None)

    if not campos:
        return True

    params += [id_cliente, id_empresa]
    sql = f"""
        UPDATE {Config.SCHEMA}.t_crm_cliente
        SET {', '.join(campos)}
        WHERE id_cliente = %s AND id_empresa = %s;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        db.execute_query(sql, tuple(params), commit=True)
        return True
    finally:
        db.close_connection()


def cambiar_clasificacion_crm(id_cliente: int, id_empresa: int, nuevo_tipo: str, nuevo_estado: str):
    sql = f"""
        UPDATE {Config.SCHEMA}.t_crm_cliente
        SET tipo_cliente = %s, estado = %s
        WHERE id_cliente = %s AND id_empresa = %s
        RETURNING id_cliente;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        res = db.execute_query(sql, (nuevo_tipo.upper(), nuevo_estado.upper(), id_cliente, id_empresa), fetchone=True, commit=True)
        return bool(res)
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# 4. INTERACCIONES COMERCIALES (HU84, HU81)
# ─────────────────────────────────────────────────────────────────────────────
def registrar_interaccion(id_cliente: int, id_usuario: int, tipo: str, asunto: str,
                          detalle: str, fecha_interaccion=None, fecha_proximo_contacto=None):
    sql = f"""
        INSERT INTO {Config.SCHEMA}.t_crm_interaccion (
            id_cliente, id_usuario, tipo, asunto, detalle,
            fecha_interaccion, fecha_proximo_contacto
        )
        VALUES (%s, %s, %s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP), %s)
        RETURNING id_interaccion;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        res = db.execute_query(sql, (
            id_cliente, id_usuario, tipo.upper(), asunto.strip(),
            detalle.strip(), fecha_interaccion, fecha_proximo_contacto
        ), fetchone=True, commit=True)
        return res[0] if res else None
    finally:
        db.close_connection()


def listar_interacciones_cliente(id_cliente: int):
    sql = f"""
        SELECT i.id_interaccion, i.id_cliente, i.id_usuario, i.tipo, i.asunto, i.detalle,
               i.fecha_interaccion, i.fecha_proximo_contacto, i.created_at,
               u.username AS usuario_username,
               p.nombre_completo AS usuario_nombre
        FROM {Config.SCHEMA}.t_crm_interaccion i
        INNER JOIN {Config.SCHEMA}.t_usuario u ON u.id_usuario = i.id_usuario
        INNER JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = u.id_persona
        WHERE i.id_cliente = %s
        ORDER BY i.fecha_interaccion DESC;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(sql, (id_cliente,), fetchall=True) or []
        res = []
        for r in rows:
            res.append({
                "id_interaccion": r[0],
                "id_cliente": r[1],
                "id_usuario": r[2],
                "tipo": r[3],
                "asunto": r[4],
                "detalle": r[5],
                "fecha_interaccion": r[6].isoformat() if r[6] else None,
                "fecha_proximo_contacto": r[7].isoformat() if r[7] else None,
                "created_at": r[8].isoformat() if r[8] else None,
                "usuario_username": r[9],
                "usuario_nombre": r[10],
            })
        return res
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# 5. ASOCIACIÓN CLIENTE ↔ UNIDAD INMOBILIARIA (HU85, HU81)
# ─────────────────────────────────────────────────────────────────────────────
def obtener_empresa_unidad(id_unidad: int):
    """Obtiene id_obra e id_empresa a partir de id_unidad mediante la jerarquía oficial."""
    sql = f"""
        SELECT o.id_obra, o.id_empresa, o.nombre AS nombre_obra, o.codigo AS codigo_obra,
               u.codigo AS codigo_unidad, u.tipo_unidad, u.superficie, u.estado AS estado_unidad
        FROM {Config.SCHEMA}.t_unidad_construccion u
        INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
        INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
        WHERE u.id_unidad = %s;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(sql, (id_unidad,), fetchone=True)
        if row:
            return {
                "id_obra": row[0],
                "id_empresa": row[1],
                "nombre_obra": row[2],
                "codigo_obra": row[3],
                "codigo_unidad": row[4],
                "tipo_unidad": row[5],
                "superficie": float(row[6]) if row[6] is not None else None,
                "estado_unidad": row[7],
            }
        return None
    finally:
        db.close_connection()


def asociar_cliente_unidad(id_cliente: int, id_unidad: int, estado_asociacion: str = "INTERESADO",
                           monto_pactado: float = None, observaciones: str = None):
    sql = f"""
        INSERT INTO {Config.SCHEMA}.t_crm_cliente_unidad (
            id_cliente, id_unidad, estado_asociacion, monto_pactado, observaciones
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id_cliente_unidad;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        res = db.execute_query(sql, (
            id_cliente, id_unidad, estado_asociacion.upper(), monto_pactado, observaciones
        ), fetchone=True, commit=True)
        return res[0] if res else None
    finally:
        db.close_connection()


def cambiar_estado_asociacion_unidad(id_cliente_unidad: int, nuevo_estado: str, observaciones: str = None):
    sql = f"""
        UPDATE {Config.SCHEMA}.t_crm_cliente_unidad
        SET estado_asociacion = %s,
            observaciones = COALESCE(%s, observaciones)
        WHERE id_cliente_unidad = %s
        RETURNING id_cliente_unidad, id_unidad;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        res = db.execute_query(sql, (nuevo_estado.upper(), observaciones, id_cliente_unidad), fetchone=True, commit=True)
        return res if res else None
    finally:
        db.close_connection()


def listar_unidades_cliente(id_cliente: int):
    sql = f"""
        SELECT cu.id_cliente_unidad, cu.id_cliente, cu.id_unidad, cu.estado_asociacion,
               cu.monto_pactado, cu.fecha_asociacion, cu.observaciones,
               u.codigo AS codigo_unidad, u.tipo_unidad, u.superficie, u.estado AS estado_unidad_actual,
               o.id_obra, o.nombre AS nombre_obra, o.codigo AS codigo_obra
        FROM {Config.SCHEMA}.t_crm_cliente_unidad cu
        INNER JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = cu.id_unidad
        INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
        INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
        WHERE cu.id_cliente = %s
        ORDER BY cu.fecha_asociacion DESC;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(sql, (id_cliente,), fetchall=True) or []
        res = []
        for r in rows:
            res.append({
                "id_cliente_unidad": r[0],
                "id_cliente": r[1],
                "id_unidad": r[2],
                "estado_asociacion": r[3],
                "monto_pactado": float(r[4]) if r[4] is not None else None,
                "fecha_asociacion": r[5].isoformat() if r[5] else None,
                "observaciones": r[6],
                "codigo_unidad": r[7],
                "tipo_unidad": r[8],
                "superficie": float(r[9]) if r[9] is not None else None,
                "estado_unidad_actual": r[10],
                "id_obra": r[11],
                "nombre_obra": r[12],
                "codigo_obra": r[13],
            })
        return res
    finally:
        db.close_connection()


def listar_unidades_disponibles_empresa(id_empresa: int, id_obra: int = None):
    filtros = ["o.id_empresa = %s"]
    params = [id_empresa]
    if id_obra:
        filtros.append("o.id_obra = %s")
        params.append(id_obra)

    sql = f"""
        SELECT u.id_unidad, u.codigo, u.tipo_unidad, u.superficie, u.estado,
               o.id_obra, o.nombre AS nombre_obra, o.codigo AS codigo_obra,
               e.nombre AS nombre_estructura
        FROM {Config.SCHEMA}.t_unidad_construccion u
        INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
        INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
        WHERE {" AND ".join(filtros)}
          AND u.id_unidad NOT IN (
              SELECT id_unidad FROM {Config.SCHEMA}.t_crm_cliente_unidad
              WHERE estado_asociacion = 'VENDIDO'
          )
        ORDER BY o.nombre, u.codigo;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(sql, tuple(params), fetchall=True) or []
        res = []
        for r in rows:
            res.append({
                "id_unidad": r[0],
                "codigo": r[1],
                "tipo_unidad": r[2],
                "superficie": float(r[3]) if r[3] is not None else None,
                "estado": r[4],
                "id_obra": r[5],
                "nombre_obra": r[6],
                "codigo_obra": r[7],
                "nombre_estructura": r[8],
            })
        return res
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# 6. MÉTRICAS CONTROLADAS PARA CRM E IA (HU109)
# ─────────────────────────────────────────────────────────────────────────────
def obtener_metricas_crm(id_empresa: int):
    sql = f"""
        SELECT 
            COUNT(*) FILTER (WHERE tipo_cliente = 'CLIENTE') AS total_clientes,
            COUNT(*) FILTER (WHERE tipo_cliente = 'PROSPECTO') AS total_prospectos,
            COUNT(*) FILTER (WHERE tipo_cliente = 'PROSPECTO' AND estado = 'NUEVO') AS prospectos_nuevos,
            COUNT(*) FILTER (WHERE tipo_cliente = 'PROSPECTO' AND estado = 'CONTACTADO') AS prospectos_contactados,
            COUNT(*) FILTER (WHERE tipo_cliente = 'PROSPECTO' AND estado = 'INTERESADO') AS prospectos_interesados,
            COUNT(*) FILTER (WHERE tipo_cliente = 'PROSPECTO' AND estado = 'EN_NEGOCIACION') AS prospectos_negociacion,
            COUNT(*) FILTER (WHERE tipo_cliente = 'PROSPECTO' AND estado = 'CONVERTIDO') AS prospectos_convertidos,
            COUNT(*) FILTER (WHERE tipo_cliente = 'PROSPECTO' AND estado = 'PERDIDO') AS prospectos_perdidos
        FROM {Config.SCHEMA}.t_crm_cliente
        WHERE id_empresa = %s;
    """
    sql_unidades = f"""
        SELECT 
            COUNT(*) FILTER (WHERE cu.estado_asociacion = 'INTERESADO') AS unidades_interes,
            COUNT(*) FILTER (WHERE cu.estado_asociacion = 'RESERVADO') AS unidades_reservadas,
            COUNT(*) FILTER (WHERE cu.estado_asociacion = 'VENDIDO') AS unidades_vendidas
        FROM {Config.SCHEMA}.t_crm_cliente_unidad cu
        INNER JOIN {Config.SCHEMA}.t_crm_cliente c ON c.id_cliente = cu.id_cliente
        WHERE c.id_empresa = %s;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        m = db.execute_query(sql, (id_empresa,), fetchone=True) or (0, 0, 0, 0, 0, 0, 0, 0)
        u = db.execute_query(sql_unidades, (id_empresa,), fetchone=True) or (0, 0, 0)
        return {
            "total_clientes": m[0] or 0,
            "total_prospectos": m[1] or 0,
            "prospectos_por_estado": {
                "NUEVO": m[2] or 0,
                "CONTACTADO": m[3] or 0,
                "INTERESADO": m[4] or 0,
                "EN_NEGOCIACION": m[5] or 0,
                "CONVERTIDO": m[6] or 0,
                "PERDIDO": m[7] or 0,
            },
            "unidades_asociadas": {
                "INTERESADO": u[0] or 0,
                "RESERVADO": u[1] or 0,
                "VENDIDO": u[2] or 0,
            }
        }
    finally:
        db.close_connection()
