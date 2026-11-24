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


def obtener_id_cliente_por_usuario_empresa(id_usuario: int, id_empresa: int):
    sql = f"""
        SELECT c.id_cliente
        FROM {Config.SCHEMA}.t_usuario u
        INNER JOIN {Config.SCHEMA}.t_crm_cliente c ON c.id_persona = u.id_persona
        WHERE u.id_usuario = %s
          AND u.id_empresa = %s
          AND c.id_empresa = %s
          AND u.id_persona IS NOT NULL
          AND c.tipo_cliente = 'CLIENTE'
        LIMIT 1;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(sql, (id_usuario, id_empresa, id_empresa), fetchone=True)
        return row[0] if row else None
    finally:
        db.close_connection()


def obtener_id_usuario_por_cliente(id_cliente: int, id_empresa: int):
    """
    Resuelve el nro_usuario (t_usuario.id_usuario) asociado a un cliente CRM en su empresa.
    """
    sql = f"""
        SELECT u.id_usuario
        FROM {Config.SCHEMA}.t_crm_cliente c
        INNER JOIN {Config.SCHEMA}.t_usuario u ON u.id_persona = c.id_persona
        WHERE c.id_cliente = %s
          AND c.id_empresa = %s
          AND u.id_empresa = %s
          AND c.id_persona IS NOT NULL
        ORDER BY u.id_usuario ASC
        LIMIT 1;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(sql, (id_cliente, id_empresa, id_empresa), fetchone=True)
        return row[0] if row else None
    finally:
        db.close_connection()


def validar_unidad_asociada_cliente(id_cliente: int, id_unidad: int) -> bool:
    """
    Verifica si una unidad de construcción está formalmente vinculada a un cliente CRM.
    """
    sql = f"""
        SELECT 1
        FROM {Config.SCHEMA}.t_crm_cliente_unidad
        WHERE id_cliente = %s AND id_unidad = %s
        LIMIT 1;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(sql, (id_cliente, id_unidad), fetchone=True)
        return bool(row)
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

    campos.append("updated_at = CURRENT_TIMESTAMP")

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


def listar_unidades_cliente_cu30(id_cliente: int, id_empresa: int):
    sql = f"""
        SELECT cu.id_cliente_unidad, cu.id_cliente, cu.id_unidad, cu.estado_asociacion,
               cu.monto_pactado, cu.fecha_asociacion, cu.observaciones,
               u.codigo AS codigo_unidad, u.tipo_unidad, u.superficie, u.estado AS estado_unidad_actual,
               o.id_obra, o.nombre AS nombre_obra, o.codigo AS codigo_obra
        FROM {Config.SCHEMA}.t_crm_cliente_unidad cu
        INNER JOIN {Config.SCHEMA}.t_crm_cliente c ON c.id_cliente = cu.id_cliente
        INNER JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = cu.id_unidad
        INNER JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
        INNER JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
        WHERE c.id_cliente = %s
          AND c.id_empresa = %s
          AND o.id_empresa = %s
        ORDER BY cu.fecha_asociacion DESC;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(sql, (id_cliente, id_empresa, id_empresa), fetchall=True) or []
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
          AND COALESCE(u.estado_comercial, 'DISPONIBLE') = 'DISPONIBLE'
          AND u.id_unidad NOT IN (
              SELECT id_unidad FROM {Config.SCHEMA}.t_crm_cliente_unidad
              WHERE estado_asociacion IN ('RESERVADO', 'VENDIDO', 'ENTREGADO')
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
            COUNT(*) FILTER (WHERE tipo_cliente = 'PROSPECTO' AND estado IN ('NEGOCIACION', 'EN_NEGOCIACION')) AS prospectos_negociacion,
            COUNT(*) FILTER (WHERE tipo_cliente = 'PROSPECTO' AND estado = 'RESERVADO') AS prospectos_reservados,
            COUNT(*) FILTER (WHERE tipo_cliente = 'PROSPECTO' AND estado = 'VENDIDO') AS prospectos_vendidos,
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
        m = db.execute_query(sql, (id_empresa,), fetchone=True) or (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        u = db.execute_query(sql_unidades, (id_empresa,), fetchone=True) or (0, 0, 0)
        return {
            "total_clientes": m[0] or 0,
            "total_prospectos": m[1] or 0,
            "prospectos_por_estado": {
                "NUEVO": m[2] or 0,
                "CONTACTADO": m[3] or 0,
                "INTERESADO": m[4] or 0,
                "EN_NEGOCIACION": m[5] or 0,
                "NEGOCIACION": m[5] or 0,
                "RESERVADO": m[6] or 0,
                "VENDIDO": m[7] or 0,
                "CONVERTIDO": m[8] or 0,
                "PERDIDO": m[9] or 0,
            },
            "unidades_asociadas": {
                "INTERESADO": u[0] or 0,
                "RESERVADO": u[1] or 0,
                "VENDIDO": u[2] or 0,
            }
        }
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# 7. LISTAR ASESORES / RESPONSABLES COMERCIALES DE LA EMPRESA
# ─────────────────────────────────────────────────────────────────────────────
def listar_asesores_empresa(id_empresa: int):
    sql = f"""
        SELECT u.id_usuario,
               COALESCE(p.nombre_completo, u.username) AS nombre_completo,
               u.username,
               u.correo,
               COALESCE(r.nombre_rol, 'Usuario') AS rol
        FROM {Config.SCHEMA}.t_usuario u
        LEFT JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = u.id_persona
        LEFT JOIN {Config.SCHEMA}.t_rol r ON r.id_rol = u.id_rol
        WHERE u.id_empresa = %s AND (u.estado = 'ACTIVO' OR u.estado IS NULL)
        ORDER BY p.nombre_completo ASC, u.username ASC;
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(sql, (id_empresa,), fetchall=True) or []
        return [
            {
                "id_usuario": r[0],
                "nombre_completo": r[1],
                "username": r[2],
                "email": r[3],
                "rol": r[4]
            }
            for r in rows
        ]
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# 8. FOTOGRAFÍAS DE UNIDAD PARA CLIENTE (HU115)
# ─────────────────────────────────────────────────────────────────────────────
def listar_fotografias_cliente_cu30(id_cliente: int, id_unidad: int, id_empresa: int):
    """
    HU115: Consulta fotografías de unidad sobre obras.t_unidad_fotografia.
    Garantiza pertenencia de obra y cliente al tenant, asociación del cliente
    a la unidad vía t_crm_cliente_unidad, tipos MIME de imagen válidos y orden temporal.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(
            f"""
            SELECT uf.id_fotografia,
                   uf.id_unidad,
                   uf.nombre_archivo,
                   uf.tipo_mime,
                   uf.tamano_bytes,
                   uf.es_principal,
                   uf.orden,
                   uf.created_at
            FROM {Config.SCHEMA}.t_unidad_fotografia uf
            JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = uf.id_unidad
            JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
            JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
            JOIN {Config.SCHEMA}.t_crm_cliente c
              ON c.id_cliente = %s
             AND c.id_empresa = %s
             AND c.tipo_cliente = 'CLIENTE'
            WHERE uf.id_unidad = %s
              AND o.id_empresa = %s
              AND EXISTS (
                  SELECT 1
                  FROM {Config.SCHEMA}.t_crm_cliente_unidad cu
                  WHERE cu.id_cliente = c.id_cliente
                    AND cu.id_unidad = u.id_unidad
              )
              AND uf.tipo_mime IN ('image/jpeg', 'image/png', 'image/webp', 'image/gif')
            ORDER BY uf.orden ASC, uf.created_at DESC, uf.id_fotografia DESC;
            """,
            (id_cliente, id_empresa, id_unidad, id_empresa),
            fetchall=True,
        ) or []
        return [
            {
                "id_fotografia": row[0],
                "id_unidad": row[1],
                "nombre_archivo": row[2],
                "tipo_mime": row[3],
                "tamano_bytes": row[4],
                "es_principal": bool(row[5]),
                "orden": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
                "fecha": row[7].isoformat() if row[7] else None,
                "id_evidencia": row[0],
            }
            for row in rows
        ]
    finally:
        db.close_connection()


def obtener_fotografia_cliente_cu30(id_cliente: int, id_unidad: int, id_fotografia: int, id_empresa: int):
    """
    HU115: Obtiene una fotografía específica verificando que pertenezca a la unidad,
    al cliente autenticado y al tenant autorizado.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            f"""
            SELECT uf.id_fotografia,
                   uf.id_unidad,
                   uf.ruta_archivo,
                   uf.nombre_archivo,
                   uf.tipo_mime,
                   uf.tamano_bytes
            FROM {Config.SCHEMA}.t_unidad_fotografia uf
            JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = uf.id_unidad
            JOIN {Config.SCHEMA}.t_estructura_obra e ON e.id_estructura = u.id_estructura
            JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = e.id_obra
            JOIN {Config.SCHEMA}.t_crm_cliente c
              ON c.id_cliente = %s
             AND c.id_empresa = %s
             AND c.tipo_cliente = 'CLIENTE'
            WHERE uf.id_fotografia = %s
              AND uf.id_unidad = %s
              AND o.id_empresa = %s
              AND EXISTS (
                  SELECT 1
                  FROM {Config.SCHEMA}.t_crm_cliente_unidad cu
                  WHERE cu.id_cliente = c.id_cliente
                    AND cu.id_unidad = u.id_unidad
              )
              AND uf.tipo_mime IN ('image/jpeg', 'image/png', 'image/webp', 'image/gif');
            """,
            (id_cliente, id_empresa, id_fotografia, id_unidad, id_empresa),
            fetchone=True,
        )
        if not row:
            return None
        return {
            "id_fotografia": row[0],
            "id_unidad": row[1],
            "ruta_archivo": row[2],
            "nombre_archivo": row[3],
            "tipo_mime": row[4],
            "tamano_bytes": row[5],
        }
    finally:
        db.close_connection()
# ─────────────────────────────────────────────────────────────────────────────
# 9. SOLICITUDES DE CLIENTE (HU117)
# ─────────────────────────────────────────────────────────────────────────────
def listar_solicitudes_cliente_cu30(id_cliente: int, id_usuario: int, id_empresa: int):
    """
    HU117: Lista solicitudes del cliente autenticado sobre obras.t_cliente_solicitud.
    Garantiza aislamiento por id_cliente, id_usuario y tenant id_empresa.
    Devuelve datos de solicitud, obra, unidad asociada, respuesta y fechas.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(
            f"""
            SELECT s.id_solicitud,
                   s.id_cliente,
                   s.id_usuario,
                   s.id_empresa,
                   s.id_obra,
                   o.nombre AS nombre_obra,
                   o.codigo AS codigo_obra,
                   s.id_unidad,
                   u.codigo AS codigo_unidad,
                   u.tipo_unidad,
                   s.titulo,
                   s.descripcion,
                   s.estado,
                   s.respuesta,
                   s.id_usuario_respuesta,
                   s.id_fotografia_evidencia,
                   s.fecha_creacion,
                   s.fecha_actualizacion,
                   s.fecha_respuesta
            FROM {Config.SCHEMA}.t_cliente_solicitud s
            JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = s.id_obra
            LEFT JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = s.id_unidad
            WHERE s.id_cliente = %s
              AND s.id_usuario = %s
              AND s.id_empresa = %s
            ORDER BY s.fecha_creacion DESC, s.id_solicitud DESC;
            """,
            (id_cliente, id_usuario, id_empresa),
            fetchall=True,
        ) or []
        return [
            {
                "id_solicitud": row[0],
                "id_cliente": row[1],
                "id_usuario": row[2],
                "id_empresa": row[3],
                "id_obra": row[4],
                "nombre_obra": row[5],
                "codigo_obra": row[6],
                "id_unidad": row[7],
                "codigo_unidad": row[8],
                "tipo_unidad": row[9],
                "titulo": row[10],
                "asunto": row[10],  # retrocompatibilidad
                "descripcion": row[11],
                "estado": row[12],
                "respuesta": row[13],
                "id_usuario_respuesta": row[14],
                "id_fotografia_evidencia": row[15],
                "fecha_creacion": row[16].isoformat() if row[16] else None,
                "fecha_actualizacion": row[17].isoformat() if row[17] else None,
                "fecha_respuesta": row[18].isoformat() if row[18] else None,
            }
            for row in rows
        ]
    finally:
        db.close_connection()
def obtener_solicitud_cliente_cu30(id_cliente: int, id_usuario: int, id_solicitud: int, id_empresa: int):
    """
    HU117: Obtiene el detalle de una solicitud garantizando pertenencia al cliente autenticado y su empresa.
    Si la solicitud pertenece a otro cliente o empresa, retorna None (aislamiento 404).
    Incluye metadatos de evidencia de fotografía si id_fotografia_evidencia existe.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            f"""
            SELECT s.id_solicitud,
                   s.id_cliente,
                   s.id_usuario,
                   s.id_empresa,
                   s.id_obra,
                   o.nombre AS nombre_obra,
                   o.codigo AS codigo_obra,
                   s.id_unidad,
                   u.codigo AS codigo_unidad,
                   u.tipo_unidad,
                   s.titulo,
                   s.descripcion,
                   s.estado,
                   s.respuesta,
                   s.id_usuario_respuesta,
                   s.id_fotografia_evidencia,
                   s.fecha_creacion,
                   s.fecha_actualizacion,
                   s.fecha_respuesta,
                   uf.nombre_archivo AS evidencia_nombre,
                   uf.tipo_mime AS evidencia_mime,
                   uf.tamano_bytes AS evidencia_tamano
            FROM {Config.SCHEMA}.t_cliente_solicitud s
            JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = s.id_obra
            LEFT JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = s.id_unidad
            LEFT JOIN {Config.SCHEMA}.t_unidad_fotografia uf ON uf.id_fotografia = s.id_fotografia_evidencia
            WHERE s.id_solicitud = %s
              AND s.id_cliente = %s
              AND s.id_usuario = %s
              AND s.id_empresa = %s;
            """,
            (id_solicitud, id_cliente, id_usuario, id_empresa),
            fetchone=True,
        )
        if not row:
            return None
        evidencia = None
        if row[15]:  # id_fotografia_evidencia
            evidencia = {
                "id_fotografia": row[15],
                "nombre_archivo": row[19],
                "tipo_mime": row[20],
                "tamano_bytes": row[21],
                "url_archivo": f"/api/crm/cliente/unidades/{row[7]}/fotografias/{row[15]}/archivo" if row[7] else None,
            }
        return {
            "id_solicitud": row[0],
            "id_cliente": row[1],
            "id_usuario": row[2],
            "id_empresa": row[3],
            "id_obra": row[4],
            "nombre_obra": row[5],
            "codigo_obra": row[6],
            "id_unidad": row[7],
            "codigo_unidad": row[8],
            "tipo_unidad": row[9],
            "titulo": row[10],
            "asunto": row[10],
            "descripcion": row[11],
            "estado": row[12],
            "respuesta": row[13],
            "id_usuario_respuesta": row[14],
            "id_fotografia_evidencia": row[15],
            "evidencia": evidencia,
            "fecha_creacion": row[16].isoformat() if row[16] else None,
            "fecha_actualizacion": row[17].isoformat() if row[17] else None,
            "fecha_respuesta": row[18].isoformat() if row[18] else None,
        }
    finally:
        db.close_connection()
def crear_solicitud_cliente_db(id_cliente: int, id_usuario: int, id_empresa: int, id_obra: int, id_unidad: int | None, titulo: str, descripcion: str):
    """
    HU117: Inserta una nueva solicitud de cliente en estado PENDIENTE.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            f"""
            INSERT INTO {Config.SCHEMA}.t_cliente_solicitud
                (id_cliente, id_usuario, id_empresa, id_obra, id_unidad, titulo, descripcion, estado)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, 'PENDIENTE')
            RETURNING id_solicitud, id_cliente, id_usuario, id_empresa, id_obra, id_unidad,
                      titulo, descripcion, estado, fecha_creacion;
            """,
            (id_cliente, id_usuario, id_empresa, id_obra, id_unidad, titulo, descripcion),
            fetchone=True,
            commit=True,
        )
        return {
            "id_solicitud": row[0],
            "id_cliente": row[1],
            "id_usuario": row[2],
            "id_empresa": row[3],
            "id_obra": row[4],
            "id_unidad": row[5],
            "titulo": row[6],
            "asunto": row[6],
            "descripcion": row[7],
            "estado": row[8],
            "fecha_creacion": row[9].isoformat() if row[9] else None,
        }
    finally:
        db.close_connection()
def obtener_solicitud_por_id(id_solicitud: int, id_empresa: int | None = None):
    """
    Consulta básica de solicitud para constructora.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        where_tenant = "AND s.id_empresa = %s" if id_empresa is not None else ""
        params = [id_solicitud]
        if id_empresa is not None:
            params.append(id_empresa)
        row = db.execute_query(
            f"""
            SELECT s.id_solicitud, s.id_cliente, s.id_usuario, s.id_empresa, s.id_obra, s.id_unidad,
                   s.titulo, s.descripcion, s.estado, s.respuesta, s.id_usuario_respuesta,
                   s.id_fotografia_evidencia, s.fecha_creacion, s.fecha_actualizacion, s.fecha_respuesta,
                   o.nombre AS nombre_obra, u.codigo AS codigo_unidad
            FROM {Config.SCHEMA}.t_cliente_solicitud s
            JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = s.id_obra
            LEFT JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = s.id_unidad
            WHERE s.id_solicitud = %s {where_tenant};
            """,
            tuple(params),
            fetchone=True,
        )
        if not row:
            return None
        return {
            "id_solicitud": row[0],
            "id_cliente": row[1],
            "id_usuario": row[2],
            "id_empresa": row[3],
            "id_obra": row[4],
            "id_unidad": row[5],
            "titulo": row[6],
            "asunto": row[6],
            "descripcion": row[7],
            "estado": row[8],
            "respuesta": row[9],
            "id_usuario_respuesta": row[10],
            "id_fotografia_evidencia": row[11],
            "fecha_creacion": row[12].isoformat() if row[12] else None,
            "fecha_actualizacion": row[13].isoformat() if row[13] else None,
            "fecha_respuesta": row[14].isoformat() if row[14] else None,
            "nombre_obra": row[15],
            "codigo_unidad": row[16],
        }
    finally:
        db.close_connection()
def responder_solicitud_constructora_db(
    id_solicitud: int,
    id_empresa: int | None,
    estado: str,
    respuesta: str | None,
    id_usuario_respuesta: int,
    id_fotografia_evidencia: int | None = None
):
    """
    HU117: Actualiza estado, respuesta y fecha de atención de una solicitud por parte de la constructora.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        where_tenant = "AND id_empresa = %s" if id_empresa is not None else ""
        fecha_resp_clause = "CURRENT_TIMESTAMP" if (estado == 'ATENDIDA' or respuesta) else "fecha_respuesta"

        params = [estado, respuesta, id_usuario_respuesta, id_fotografia_evidencia, id_solicitud]
        if id_empresa is not None:
            params.append(id_empresa)

        row = db.execute_query(
            f"""
            UPDATE {Config.SCHEMA}.t_cliente_solicitud
            SET estado = %s,
                respuesta = %s,
                id_usuario_respuesta = %s,
                id_fotografia_evidencia = %s,
                fecha_respuesta = {fecha_resp_clause},
                fecha_actualizacion = CURRENT_TIMESTAMP
            WHERE id_solicitud = %s
              {where_tenant}
            RETURNING id_solicitud, estado, respuesta, fecha_respuesta, fecha_actualizacion, id_obra, id_cliente;
            """,
            tuple(params),
            fetchone=True,
            commit=True,
        )
        if not row:
            return None
        return {
            "id_solicitud": row[0],
            "estado": row[1],
            "respuesta": row[2],
            "fecha_respuesta": row[3].isoformat() if row[3] else None,
            "fecha_actualizacion": row[4].isoformat() if row[4] else None,
            "id_obra": row[5],
            "id_cliente": row[6],
        }
    finally:
        db.close_connection()
def listar_solicitudes_constructora(id_empresa: int | None = None, id_obra: int | None = None, estado: str | None = None):
    """
    HU117: Lista solicitudes para gestión administrativa por parte de la constructora.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        filtros = []
        params = []
        if id_empresa is not None:
            filtros.append("s.id_empresa = %s")
            params.append(id_empresa)
        if id_obra is not None:
            filtros.append("s.id_obra = %s")
            params.append(id_obra)
        if estado:
            filtros.append("s.estado = %s")
            params.append(estado.upper())

        where = ("WHERE " + " AND ".join(filtros)) if filtros else ""
        rows = db.execute_query(
            f"""
            SELECT s.id_solicitud, s.id_cliente, s.id_usuario, s.id_empresa, s.id_obra, s.id_unidad,
                   s.titulo, s.descripcion, s.estado, s.respuesta, s.id_usuario_respuesta,
                   s.id_fotografia_evidencia, s.fecha_creacion, s.fecha_actualizacion, s.fecha_respuesta,
                   o.nombre AS nombre_obra, u.codigo AS codigo_unidad,
                   p.nombre_completo AS nombre_cliente
            FROM {Config.SCHEMA}.t_cliente_solicitud s
            JOIN {Config.SCHEMA}.t_obra o ON o.id_obra = s.id_obra
            LEFT JOIN {Config.SCHEMA}.t_unidad_construccion u ON u.id_unidad = s.id_unidad
            JOIN {Config.SCHEMA}.t_crm_cliente c ON c.id_cliente = s.id_cliente
            JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = c.id_persona
            {where}
            ORDER BY s.fecha_creacion DESC, s.id_solicitud DESC;
            """,
            tuple(params),
            fetchall=True,
        ) or []
        return [
            {
                "id_solicitud": r[0],
                "id_cliente": r[1],
                "id_usuario": r[2],
                "id_empresa": r[3],
                "id_obra": r[4],
                "id_unidad": r[5],
                "titulo": r[6],
                "asunto": r[6],
                "descripcion": r[7],
                "estado": r[8],
                "respuesta": r[9],
                "id_usuario_respuesta": r[10],
                "id_fotografia_evidencia": r[11],
                "fecha_creacion": r[12].isoformat() if r[12] else None,
                "fecha_actualizacion": r[13].isoformat() if r[13] else None,
                "fecha_respuesta": r[14].isoformat() if r[14] else None,
                "nombre_obra": r[15],
                "codigo_unidad": r[16],
                "nombre_cliente": r[17],
            }
            for r in rows
        ]
    finally:
        db.close_connection()
