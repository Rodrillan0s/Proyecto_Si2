from app.classes.postgres import PostgreSQL
from app.config import Config


# ─────────────────────────────────────────────────────────────────────────────
# Mapeadores de Filas (Row Mappers)
# ─────────────────────────────────────────────────────────────────────────────

def _row_to_presupuesto(row):
    if not row:
        return None
    return {
        "id_presupuesto": row[0],
        "id_obra": row[1],
        "codigo": row[2],
        "nombre": row[3],
        "descripcion": row[4],
        "version": row[5],
        "estado": row[6],
        "es_vigente": row[7],
        "fecha": str(row[8]) if row[8] else None,
        "superficie_m2": float(row[9]) if row[9] is not None else None,
        "tipo_suelo": row[10],
        "costo_m2_estimado": float(row[11]) if row[11] is not None else None,
        "monto_estimado_inicial": float(row[12]) if row[12] is not None else None,
        "total_presupuesto": float(row[13]) if row[13] is not None else 0.0,
        "observaciones": row[14],
        "created_at": str(row[15]) if row[15] else None,
        "updated_at": str(row[16]) if row[16] else None,
        "nombre_obra": row[17] if len(row) > 17 else None,
        "codigo_obra": row[18] if len(row) > 18 else None,
        "id_empresa": row[19] if len(row) > 19 else None,
        "moneda": row[20] if len(row) > 20 else "BOB"
    }


def _row_to_partida(row):
    if not row:
        return None
    return {
        "id_partida": row[0],
        "id_presupuesto": row[1],
        "id_apu": row[2],
        "codigo": row[3],
        "nombre": row[4],
        "descripcion": row[5],
        "id_unidad_medida": row[6],
        "cantidad": float(row[7]) if row[7] is not None else 0.0,
        "precio_unitario": float(row[8]) if row[8] is not None else 0.0,
        "importe_total": float(row[9]) if row[9] is not None else 0.0,
        "orden": row[10],
        "id_estructura": row[11],
        "id_unidad_construccion": row[12],
        "created_at": str(row[13]) if row[13] else None,
        "updated_at": str(row[14]) if row[14] else None,
        "unidad_medida_nombre": row[15] if len(row) > 15 else None,
        "unidad_medida_abrev": row[16] if len(row) > 16 else None,
        "apu_codigo": row[17] if len(row) > 17 else None,
        "apu_nombre": row[18] if len(row) > 18 else None
    }


def _row_to_apu(row):
    if not row:
        return None
    return {
        "id_apu": row[0],
        "id_empresa": row[1],
        "id_obra": row[2],
        "codigo": row[3],
        "nombre": row[4],
        "descripcion": row[5],
        "id_unidad_medida": row[6],
        "rendimiento_base": float(row[7]) if row[7] is not None else 1.0,
        "costo_unitario_total": float(row[8]) if row[8] is not None else 0.0,
        "estado": row[9],
        "created_at": str(row[10]) if row[10] else None,
        "updated_at": str(row[11]) if row[11] else None,
        "unidad_medida_nombre": row[12] if len(row) > 12 else None,
        "unidad_medida_abrev": row[13] if len(row) > 13 else None,
        "total_componentes": row[14] if len(row) > 14 else 0
    }


def _row_to_componente(row):
    if not row:
        return None
    return {
        "id_componente": row[0],
        "id_apu": row[1],
        "tipo_recurso": row[2],
        "id_recurso": row[3],
        "descripcion_recurso": row[4],
        "id_unidad_medida": row[5],
        "cantidad": float(row[6]) if row[6] is not None else 0.0,
        "precio_unitario": float(row[7]) if row[7] is not None else 0.0,
        "subtotal": float(row[8]) if row[8] is not None else 0.0,
        "created_at": str(row[9]) if row[9] else None,
        "unidad_medida_nombre": row[10] if len(row) > 10 else None,
        "unidad_medida_abrev": row[11] if len(row) > 11 else None,
        "material_codigo": row[12] if len(row) > 12 else None
    }


# ─────────────────────────────────────────────────────────────────────────────
# Consultas de Obra y Contexto
# ─────────────────────────────────────────────────────────────────────────────

def obtener_obra_por_id(id_obra: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = """
            SELECT o.id_obra, o.id_empresa, o.codigo, o.nombre, o.estado_obra, o.moneda
            FROM obras.t_obra o
            WHERE o.id_obra = %s;
        """
        row = db.execute_query(sql, (id_obra,), fetchone=True)
        if not row:
            return None
        return {
            "id_obra": row[0],
            "id_empresa": row[1],
            "codigo": row[2],
            "nombre": row[3],
            "estado_obra": row[4],
            "moneda": row[5] or "BOB"
        }
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# HU53: Presupuesto
# ─────────────────────────────────────────────────────────────────────────────

def listar_presupuestos_obra(id_obra: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = """
            SELECT p.id_presupuesto, p.id_obra, p.codigo, p.nombre, p.descripcion,
                   p.version, p.estado, p.es_vigente, p.fecha, p.superficie_m2,
                   p.tipo_suelo, p.costo_m2_estimado, p.monto_estimado_inicial,
                   p.total_presupuesto, p.observaciones, p.created_at, p.updated_at,
                   o.nombre AS nombre_obra, o.codigo AS codigo_obra, o.id_empresa, o.moneda
            FROM obras.t_presupuesto p
            JOIN obras.t_obra o ON o.id_obra = p.id_obra
            WHERE p.id_obra = %s
            ORDER BY p.version DESC, p.id_presupuesto DESC;
        """
        rows = db.execute_query(sql, (id_obra,), fetchall=True)
        return [_row_to_presupuesto(r) for r in (rows or [])]
    finally:
        db.close_connection()


def obtener_presupuesto_por_id(id_presupuesto: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = """
            SELECT p.id_presupuesto, p.id_obra, p.codigo, p.nombre, p.descripcion,
                   p.version, p.estado, p.es_vigente, p.fecha, p.superficie_m2,
                   p.tipo_suelo, p.costo_m2_estimado, p.monto_estimado_inicial,
                   p.total_presupuesto, p.observaciones, p.created_at, p.updated_at,
                   o.nombre AS nombre_obra, o.codigo AS codigo_obra, o.id_empresa, o.moneda
            FROM obras.t_presupuesto p
            JOIN obras.t_obra o ON o.id_obra = p.id_obra
            WHERE p.id_presupuesto = %s;
        """
        row = db.execute_query(sql, (id_presupuesto,), fetchone=True)
        return _row_to_presupuesto(row)
    finally:
        db.close_connection()


def crear_presupuesto(
    id_obra: int, codigo: str, nombre: str, descripcion: str = None,
    superficie_m2: float = None, tipo_suelo: str = None,
    costo_m2_estimado: float = None, monto_estimado_inicial: float = None,
    observaciones: str = None
):
    db = PostgreSQL()
    db.create_connection()
    try:
        # Calcular siguiente versión para la obra
        ver_row = db.execute_query(
            "SELECT COALESCE(MAX(version), 0) + 1 FROM obras.t_presupuesto WHERE id_obra = %s;",
            (id_obra,), fetchone=True
        )
        sig_version = ver_row[0] if ver_row else 1

        # Si no se envió monto_estimado_inicial pero hay m2 y costo_m2, calcularlo
        if monto_estimado_inicial is None and superficie_m2 and costo_m2_estimado:
            monto_estimado_inicial = round(float(superficie_m2) * float(costo_m2_estimado), 2)

        sql = """
            INSERT INTO obras.t_presupuesto (
                id_obra, codigo, nombre, descripcion, version, estado, es_vigente,
                superficie_m2, tipo_suelo, costo_m2_estimado, monto_estimado_inicial,
                total_presupuesto, observaciones
            ) VALUES (
                %s, %s, %s, %s, %s, 'BORRADOR', FALSE,
                %s, %s, %s, %s, 0.00, %s
            ) RETURNING id_presupuesto;
        """
        params = (
            id_obra, codigo, nombre, descripcion, sig_version,
            superficie_m2, tipo_suelo, costo_m2_estimado, monto_estimado_inicial,
            observaciones
        )
        row = db.execute_query(sql, params, fetchone=True, commit=True)
        return row[0] if row else None
    finally:
        db.close_connection()


def actualizar_presupuesto(id_presupuesto: int, nombre: str, descripcion: str,
                           superficie_m2: float, tipo_suelo: str,
                           costo_m2_estimado: float, monto_estimado_inicial: float,
                           observaciones: str):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = """
            UPDATE obras.t_presupuesto
            SET nombre = %s, descripcion = %s, superficie_m2 = %s, tipo_suelo = %s,
                costo_m2_estimado = %s, monto_estimado_inicial = %s, observaciones = %s
            WHERE id_presupuesto = %s AND estado IN ('BORRADOR', 'EN_REVISION');
        """
        return db.execute_query(
            sql,
            (nombre, descripcion, superficie_m2, tipo_suelo, costo_m2_estimado,
             monto_estimado_inicial, observaciones, id_presupuesto),
            commit=True
        )
    finally:
        db.close_connection()


def eliminar_presupuesto(id_presupuesto: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = "DELETE FROM obras.t_presupuesto WHERE id_presupuesto = %s AND estado = 'BORRADOR';"
        return db.execute_query(sql, (id_presupuesto,), commit=True)
    finally:
        db.close_connection()


def recalcular_total_presupuesto(id_presupuesto: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = """
            UPDATE obras.t_presupuesto
            SET total_presupuesto = COALESCE(
                (SELECT SUM(importe_total) FROM obras.t_partida_presupuesto WHERE id_presupuesto = %s),
                0.00
            )
            WHERE id_presupuesto = %s
            RETURNING total_presupuesto;
        """
        row = db.execute_query(sql, (id_presupuesto, id_presupuesto), fetchone=True, commit=True)
        return float(row[0]) if row else 0.0
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# HU54 & HU57: Partidas Presupuestarias
# ─────────────────────────────────────────────────────────────────────────────

def listar_partidas_presupuesto(id_presupuesto: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = """
            SELECT p.id_partida, p.id_presupuesto, p.id_apu, p.codigo, p.nombre, p.descripcion,
                   p.id_unidad_medida, p.cantidad, p.precio_unitario, p.importe_total,
                   p.orden, p.id_estructura, p.id_unidad_construccion,
                   p.created_at, p.updated_at,
                   um.nombre AS unidad_medida_nombre, um.abreviatura AS unidad_medida_abrev,
                   a.codigo AS apu_codigo, a.nombre AS apu_nombre
            FROM obras.t_partida_presupuesto p
            JOIN obras.t_unidad_medida um ON um.id_unidad_medida = p.id_unidad_medida
            LEFT JOIN obras.t_apu a ON a.id_apu = p.id_apu
            WHERE p.id_presupuesto = %s
            ORDER BY p.orden ASC, p.id_partida ASC;
        """
        rows = db.execute_query(sql, (id_presupuesto,), fetchall=True)
        return [_row_to_partida(r) for r in (rows or [])]
    finally:
        db.close_connection()


def obtener_partida_por_id(id_partida: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = """
            SELECT p.id_partida, p.id_presupuesto, p.id_apu, p.codigo, p.nombre, p.descripcion,
                   p.id_unidad_medida, p.cantidad, p.precio_unitario, p.importe_total,
                   p.orden, p.id_estructura, p.id_unidad_construccion,
                   p.created_at, p.updated_at,
                   um.nombre AS unidad_medida_nombre, um.abreviatura AS unidad_medida_abrev,
                   a.codigo AS apu_codigo, a.nombre AS apu_nombre
            FROM obras.t_partida_presupuesto p
            JOIN obras.t_unidad_medida um ON um.id_unidad_medida = p.id_unidad_medida
            LEFT JOIN obras.t_apu a ON a.id_apu = p.id_apu
            WHERE p.id_partida = %s;
        """
        row = db.execute_query(sql, (id_partida,), fetchone=True)
        return _row_to_partida(row)
    finally:
        db.close_connection()


def crear_partida(
    id_presupuesto: int, codigo: str, nombre: str, id_unidad_medida: int,
    cantidad: float, precio_unitario: float = 0.0, descripcion: str = None,
    orden: int = 0, id_apu: int = None, id_estructura: int = None,
    id_unidad_construccion: int = None
):
    db = PostgreSQL()
    db.create_connection()
    try:
        # Snapshot de precio unitario desde el APU si fue seleccionado y no se especificó precio
        if id_apu and (precio_unitario is None or float(precio_unitario) <= 0):
            apu_row = db.execute_query(
                "SELECT costo_unitario_total FROM obras.t_apu WHERE id_apu = %s;",
                (id_apu,), fetchone=True
            )
            if apu_row:
                precio_unitario = float(apu_row[0])

        precio_unitario = float(precio_unitario or 0.0)
        cantidad = float(cantidad or 0.0)
        importe_total = round(cantidad * precio_unitario, 2)

        sql = """
            INSERT INTO obras.t_partida_presupuesto (
                id_presupuesto, id_apu, codigo, nombre, descripcion,
                id_unidad_medida, cantidad, precio_unitario, importe_total,
                orden, id_estructura, id_unidad_construccion
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_partida;
        """
        params = (
            id_presupuesto, id_apu, codigo, nombre, descripcion,
            id_unidad_medida, cantidad, precio_unitario, importe_total,
            orden, id_estructura, id_unidad_construccion
        )
        row = db.execute_query(sql, params, fetchone=True, commit=True)
        id_partida = row[0] if row else None

        if id_partida:
            recalcular_total_presupuesto(id_presupuesto)

        return id_partida
    finally:
        db.close_connection()


def actualizar_partida(
    id_partida: int, codigo: str, nombre: str, id_unidad_medida: int,
    cantidad: float, precio_unitario: float, descripcion: str = None,
    orden: int = 0, id_apu: int = None
):
    db = PostgreSQL()
    db.create_connection()
    try:
        # Obtener presupuesto padre
        p_row = db.execute_query(
            "SELECT id_presupuesto FROM obras.t_partida_presupuesto WHERE id_partida = %s;",
            (id_partida,), fetchone=True
        )
        if not p_row:
            return None
        id_presupuesto = p_row[0]

        cantidad = float(cantidad or 0.0)
        precio_unitario = float(precio_unitario or 0.0)
        importe_total = round(cantidad * precio_unitario, 2)

        sql = """
            UPDATE obras.t_partida_presupuesto
            SET codigo = %s, nombre = %s, id_unidad_medida = %s, cantidad = %s,
                precio_unitario = %s, importe_total = %s, descripcion = %s,
                orden = %s, id_apu = %s
            WHERE id_partida = %s;
        """
        params = (
            codigo, nombre, id_unidad_medida, cantidad, precio_unitario,
            importe_total, descripcion, orden, id_apu, id_partida
        )
        db.execute_query(sql, params, commit=True)
        recalcular_total_presupuesto(id_presupuesto)
        return id_partida
    finally:
        db.close_connection()


def eliminar_partida(id_partida: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        p_row = db.execute_query(
            "SELECT id_presupuesto FROM obras.t_partida_presupuesto WHERE id_partida = %s;",
            (id_partida,), fetchone=True
        )
        if not p_row:
            return False
        id_presupuesto = p_row[0]

        db.execute_query(
            "DELETE FROM obras.t_partida_presupuesto WHERE id_partida = %s;",
            (id_partida,), commit=True
        )
        recalcular_total_presupuesto(id_presupuesto)
        return True
    finally:
        db.close_connection()


def asociar_apu_a_partida(id_partida: int, id_apu: int):
    """
    HU57: Asocia un APU a la partida y CONGELA (snapshot) su costo unitario
    en el precio_unitario de la partida.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        # Obtener costo unitario actual del APU
        apu_row = db.execute_query(
            "SELECT costo_unitario_total FROM obras.t_apu WHERE id_apu = %s AND estado = 'ACTIVO';",
            (id_apu,), fetchone=True
        )
        if not apu_row:
            return {"success": False, "error": "El APU seleccionado no existe o está inactivo."}

        costo_unitario_apu = float(apu_row[0])

        # Obtener datos de la partida
        partida_row = db.execute_query(
            "SELECT id_presupuesto, cantidad FROM obras.t_partida_presupuesto WHERE id_partida = %s;",
            (id_partida,), fetchone=True
        )
        if not partida_row:
            return {"success": False, "error": "La partida especificada no existe."}

        id_presupuesto, cantidad = partida_row[0], float(partida_row[1] or 0.0)
        nuevo_importe = round(cantidad * costo_unitario_apu, 2)

        sql = """
            UPDATE obras.t_partida_presupuesto
            SET id_apu = %s, precio_unitario = %s, importe_total = %s
            WHERE id_partida = %s;
        """
        db.execute_query(sql, (id_apu, costo_unitario_apu, nuevo_importe, id_partida), commit=True)
        recalcular_total_presupuesto(id_presupuesto)

        return {
            "success": True,
            "id_partida": id_partida,
            "id_apu": id_apu,
            "precio_unitario_aplicado": costo_unitario_apu,
            "importe_total": nuevo_importe
        }
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# HU55 & HU56: Catálogo de APU y Componentes
# ─────────────────────────────────────────────────────────────────────────────

def listar_apus_empresa(id_empresa: int, id_obra: int = None, q: str = None):
    db = PostgreSQL()
    db.create_connection()
    try:
        condiciones = ["a.id_empresa = %s"]
        params = [id_empresa]

        if id_obra is not None:
            condiciones.append("(a.id_obra IS NULL OR a.id_obra = %s)")
            params.append(id_obra)

        if q:
            condiciones.append("(a.nombre ILIKE %s OR a.codigo ILIKE %s)")
            params.extend([f"%{q}%", f"%{q}%"])

        where_clause = " AND ".join(condiciones)

        sql = f"""
            SELECT a.id_apu, a.id_empresa, a.id_obra, a.codigo, a.nombre, a.descripcion,
                   a.id_unidad_medida, a.rendimiento_base, a.costo_unitario_total, a.estado,
                   a.created_at, a.updated_at,
                   um.nombre AS unidad_medida_nombre, um.abreviatura AS unidad_medida_abrev,
                   (SELECT COUNT(*) FROM obras.t_apu_componente c WHERE c.id_apu = a.id_apu) AS total_componentes
            FROM obras.t_apu a
            JOIN obras.t_unidad_medida um ON um.id_unidad_medida = a.id_unidad_medida
            WHERE {where_clause}
            ORDER BY a.codigo ASC;
        """
        rows = db.execute_query(sql, tuple(params), fetchall=True)
        return [_row_to_apu(r) for r in (rows or [])]
    finally:
        db.close_connection()


def obtener_apu_detalle(id_apu: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql_apu = """
            SELECT a.id_apu, a.id_empresa, a.id_obra, a.codigo, a.nombre, a.descripcion,
                   a.id_unidad_medida, a.rendimiento_base, a.costo_unitario_total, a.estado,
                   a.created_at, a.updated_at,
                   um.nombre AS unidad_medida_nombre, um.abreviatura AS unidad_medida_abrev
            FROM obras.t_apu a
            JOIN obras.t_unidad_medida um ON um.id_unidad_medida = a.id_unidad_medida
            WHERE a.id_apu = %s;
        """
        apu_row = db.execute_query(sql_apu, (id_apu,), fetchone=True)
        if not apu_row:
            return None

        apu = _row_to_apu(apu_row)

        sql_comp = """
            SELECT c.id_componente, c.id_apu, c.tipo_recurso, c.id_recurso,
                   c.descripcion_recurso, c.id_unidad_medida, c.cantidad,
                   c.precio_unitario, c.subtotal, c.created_at,
                   um.nombre AS unidad_medida_nombre, um.abreviatura AS unidad_medida_abrev,
                   m.codigo AS material_codigo
            FROM obras.t_apu_componente c
            JOIN obras.t_unidad_medida um ON um.id_unidad_medida = c.id_unidad_medida
            LEFT JOIN obras.t_material m ON m.id_material = c.id_recurso
            WHERE c.id_apu = %s
            ORDER BY c.tipo_recurso ASC, c.id_componente ASC;
        """
        comp_rows = db.execute_query(sql_comp, (id_apu,), fetchall=True)
        apu["componentes"] = [_row_to_componente(r) for r in (comp_rows or [])]

        return apu
    finally:
        db.close_connection()


def crear_apu(id_empresa: int, codigo: str, nombre: str, id_unidad_medida: int,
              descripcion: str = None, rendimiento_base: float = 1.0,
              id_obra: int = None):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = """
            INSERT INTO obras.t_apu (
                id_empresa, id_obra, codigo, nombre, descripcion,
                id_unidad_medida, rendimiento_base, costo_unitario_total, estado
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 0.00, 'ACTIVO')
            RETURNING id_apu;
        """
        params = (
            id_empresa, id_obra, codigo, nombre, descripcion,
            id_unidad_medida, rendimiento_base
        )
        row = db.execute_query(sql, params, fetchone=True, commit=True)
        return row[0] if row else None
    finally:
        db.close_connection()


def actualizar_apu(id_apu: int, codigo: str, nombre: str, id_unidad_medida: int,
                   descripcion: str = None, rendimiento_base: float = 1.0,
                   estado: str = "ACTIVO"):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = """
            UPDATE obras.t_apu
            SET codigo = %s, nombre = %s, id_unidad_medida = %s,
                descripcion = %s, rendimiento_base = %s, estado = %s
            WHERE id_apu = %s;
        """
        params = (codigo, nombre, id_unidad_medida, descripcion, rendimiento_base, estado, id_apu)
        return db.execute_query(sql, params, commit=True)
    finally:
        db.close_connection()


def recalcular_costo_unitario_apu(id_apu: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = """
            UPDATE obras.t_apu
            SET costo_unitario_total = COALESCE(
                (SELECT SUM(subtotal) FROM obras.t_apu_componente WHERE id_apu = %s),
                0.00
            )
            WHERE id_apu = %s
            RETURNING costo_unitario_total;
        """
        row = db.execute_query(sql, (id_apu, id_apu), fetchone=True, commit=True)
        return float(row[0]) if row else 0.0
    finally:
        db.close_connection()


def agregar_componente_apu(
    id_apu: int, tipo_recurso: str, descripcion_recurso: str,
    id_unidad_medida: int, cantidad: float, precio_unitario: float = 0.0,
    id_recurso: int = None
):
    """
    HU56: Asocia un recurso al APU.
    Si tipo_recurso es MATERIAL y se provee id_recurso sin precio,
    se obtiene el precio actual del catálogo de materiales como snapshot base.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        if tipo_recurso == "MATERIAL" and id_recurso and (precio_unitario is None or float(precio_unitario) <= 0):
            mat_row = db.execute_query(
                "SELECT precio FROM obras.t_material WHERE id_material = %s;",
                (id_recurso,), fetchone=True
            )
            if mat_row and mat_row[0]:
                precio_unitario = float(mat_row[0])

        cantidad = float(cantidad or 0.0)
        precio_unitario = float(precio_unitario or 0.0)
        subtotal = round(cantidad * precio_unitario, 2)

        sql = """
            INSERT INTO obras.t_apu_componente (
                id_apu, tipo_recurso, id_recurso, descripcion_recurso,
                id_unidad_medida, cantidad, precio_unitario, subtotal
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_componente;
        """
        params = (
            id_apu, tipo_recurso, id_recurso, descripcion_recurso,
            id_unidad_medida, cantidad, precio_unitario, subtotal
        )
        row = db.execute_query(sql, params, fetchone=True, commit=True)
        id_componente = row[0] if row else None

        if id_componente:
            recalcular_costo_unitario_apu(id_apu)

        return id_componente
    finally:
        db.close_connection()


def actualizar_componente_apu(
    id_componente: int, tipo_recurso: str, descripcion_recurso: str,
    id_unidad_medida: int, cantidad: float, precio_unitario: float,
    id_recurso: int = None
):
    db = PostgreSQL()
    db.create_connection()
    try:
        c_row = db.execute_query(
            "SELECT id_apu FROM obras.t_apu_componente WHERE id_componente = %s;",
            (id_componente,), fetchone=True
        )
        if not c_row:
            return None
        id_apu = c_row[0]

        cantidad = float(cantidad or 0.0)
        precio_unitario = float(precio_unitario or 0.0)
        subtotal = round(cantidad * precio_unitario, 2)

        sql = """
            UPDATE obras.t_apu_componente
            SET tipo_recurso = %s, descripcion_recurso = %s, id_unidad_medida = %s,
                cantidad = %s, precio_unitario = %s, subtotal = %s, id_recurso = %s
            WHERE id_componente = %s;
        """
        params = (
            tipo_recurso, descripcion_recurso, id_unidad_medida,
            cantidad, precio_unitario, subtotal, id_recurso, id_componente
        )
        db.execute_query(sql, params, commit=True)
        recalcular_costo_unitario_apu(id_apu)
        return id_componente
    finally:
        db.close_connection()


def eliminar_componente_apu(id_componente: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        c_row = db.execute_query(
            "SELECT id_apu FROM obras.t_apu_componente WHERE id_componente = %s;",
            (id_componente,), fetchone=True
        )
        if not c_row:
            return False
        id_apu = c_row[0]

        db.execute_query(
            "DELETE FROM obras.t_apu_componente WHERE id_componente = %s;",
            (id_componente,), commit=True
        )
        recalcular_costo_unitario_apu(id_apu)
        return True
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# HU58: Presupuesto Consolidado y Aprobación de Línea Base
# ─────────────────────────────────────────────────────────────────────────────

def obtener_presupuesto_consolidado(id_presupuesto: int):
    """
    HU58: Obtiene el presupuesto consolidado analítico:
    - Datos generales del presupuesto y obra
    - Partidas con subtotales y porcentaje de incidencia
    - Desglose consolidado por tipo de recurso (MATERIAL, MANO_OBRA, EQUIPO, OTROS)
    - Desglose por estructura (CU12)
    - Comparativa paramétrica con estimación preliminar
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        total_presupuesto = recalcular_total_presupuesto(id_presupuesto)
        presupuesto = obtener_presupuesto_por_id(id_presupuesto)
        if not presupuesto:
            return None

        partidas = listar_partidas_presupuesto(id_presupuesto)

        recursos_totales = {
            "MATERIAL": 0.0,
            "MANO_OBRA": 0.0,
            "EQUIPO": 0.0,
            "OTROS": 0.0
        }
        estructura_totales = {}

        for p in partidas:
            imp_total = p.get("importe_total") or 0.0
            p["incidencia_pct"] = round((imp_total / total_presupuesto * 100), 2) if total_presupuesto > 0 else 0.0

            id_apu = p.get("id_apu")
            if id_apu:
                comp_rows = db.execute_query("""
                    SELECT tipo_recurso, SUM(subtotal)
                    FROM obras.t_apu_componente
                    WHERE id_apu = %s
                    GROUP BY tipo_recurso;
                """, (id_apu,), fetchall=True)

                partida_cant = float(p.get("cantidad") or 1.0)
                p_recursos = {}
                for c in (comp_rows or []):
                    tipo = c[0]
                    subtotal_unitario = float(c[1] or 0.0)
                    monto_partida_recurso = round(partida_cant * subtotal_unitario, 2)
                    p_recursos[tipo] = monto_partida_recurso
                    if tipo in recursos_totales:
                        recursos_totales[tipo] = round(recursos_totales[tipo] + monto_partida_recurso, 2)
                    else:
                        recursos_totales["OTROS"] = round(recursos_totales["OTROS"] + monto_partida_recurso, 2)
                p["desglose_recursos"] = p_recursos
            else:
                recursos_totales["OTROS"] = round(recursos_totales["OTROS"] + imp_total, 2)
                p["desglose_recursos"] = {"SIN_APU": imp_total}

            id_est = p.get("id_estructura")
            id_uni = p.get("id_unidad_construccion")
            if id_est or id_uni:
                key = f"est_{id_est}_uni_{id_uni}"
                if key not in estructura_totales:
                    estructura_totales[key] = {
                        "id_estructura": id_est,
                        "id_unidad_construccion": id_uni,
                        "total": 0.0,
                        "cantidad_partidas": 0
                    }
                estructura_totales[key]["total"] = round(estructura_totales[key]["total"] + imp_total, 2)
                estructura_totales[key]["cantidad_partidas"] += 1

        recursos_resumen = []
        for tipo, monto in recursos_totales.items():
            pct = round((monto / total_presupuesto * 100), 2) if total_presupuesto > 0 else 0.0
            recursos_resumen.append({
                "tipo_recurso": tipo,
                "monto_total": monto,
                "porcentaje": pct
            })

        superficie = presupuesto.get("superficie_m2")
        estimado_inicial = presupuesto.get("monto_estimado_inicial")
        costo_m2_real = round(total_presupuesto / float(superficie), 2) if superficie and float(superficie) > 0 else None

        desviacion = None
        desviacion_pct = None
        if estimado_inicial is not None and float(estimado_inicial) > 0:
            desviacion = round(total_presupuesto - float(estimado_inicial), 2)
            desviacion_pct = round((desviacion / float(estimado_inicial)) * 100, 2)

        return {
            "presupuesto": presupuesto,
            "total_presupuesto": total_presupuesto,
            "total_partidas": len(partidas),
            "partidas": partidas,
            "desglose_recursos": recursos_resumen,
            "desglose_estructura": list(estructura_totales.values()),
            "metricas_parametricas": {
                "superficie_m2": superficie,
                "tipo_suelo": presupuesto.get("tipo_suelo"),
                "costo_m2_estimado": presupuesto.get("costo_m2_estimado"),
                "monto_estimado_inicial": estimado_inicial,
                "costo_m2_analitico_real": costo_m2_real,
                "desviacion_monto": desviacion,
                "desviacion_porcentaje": desviacion_pct
            }
        }
    finally:
        db.close_connection()


def aprobar_presupuesto_transaccional(id_presupuesto: int):
    """
    HU58: Aprobación Línea Base de Presupuesto.
    Transaccionalmente:
    1. Bloquea la fila del presupuesto.
    2. Valida que el estado actual sea BORRADOR o EN_REVISION.
    3. Valida que tenga al menos 1 partida con costo > 0.
    4. Desmarca cualquier versión vigente anterior para la misma obra (es_vigente = FALSE).
    5. Actualiza este presupuesto a: estado = 'APROBADO', es_vigente = TRUE, updated_at = NOW.
    6. Recalcula el total definitivo.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        cur = db.conn.cursor()
        cur.execute("""
            SELECT id_obra, estado, version, total_presupuesto 
            FROM obras.t_presupuesto 
            WHERE id_presupuesto = %s 
            FOR UPDATE;
        """, (id_presupuesto,))
        p_row = cur.fetchone()
        if not p_row:
            db.conn.rollback()
            return {"error": "Presupuesto no encontrado.", "status_code": 404}

        id_obra, estado, version, _ = p_row
        if estado not in ('BORRADOR', 'EN_REVISION'):
            db.conn.rollback()
            return {
                "error": f"No se puede aprobar un presupuesto en estado '{estado}'. Solo borradores o presupuestos en revisión.",
                "status_code": 400
            }

        cur.execute("SELECT COUNT(*) FROM obras.t_partida_presupuesto WHERE id_presupuesto = %s;", (id_presupuesto,))
        cant_partidas = cur.fetchone()[0]
        if cant_partidas == 0:
            db.conn.rollback()
            return {
                "error": "El presupuesto no contiene ninguna partida. Agregue partidas antes de aprobar la línea base.",
                "status_code": 400
            }

        cur.execute("""
            UPDATE obras.t_presupuesto
            SET total_presupuesto = COALESCE(
                (SELECT SUM(importe_total) FROM obras.t_partida_presupuesto WHERE id_presupuesto = %s),
                0.00
            )
            WHERE id_presupuesto = %s;
        """, (id_presupuesto, id_presupuesto))

        cur.execute("""
            UPDATE obras.t_presupuesto
            SET es_vigente = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE id_obra = %s AND es_vigente = TRUE AND id_presupuesto != %s;
        """, (id_obra, id_presupuesto))

        cur.execute("""
            UPDATE obras.t_presupuesto
            SET estado = 'APROBADO',
                es_vigente = TRUE,
                updated_at = CURRENT_TIMESTAMP
            WHERE id_presupuesto = %s
            RETURNING id_presupuesto, id_obra, version, estado, es_vigente, total_presupuesto;
        """, (id_presupuesto,))
        res = cur.fetchone()
        db.conn.commit()

        return {
            "success": True,
            "id_presupuesto": res[0],
            "id_obra": res[1],
            "version": res[2],
            "estado": res[3],
            "es_vigente": res[4],
            "total_presupuesto": float(res[5])
        }
    except Exception as e:
        if db.conn:
            db.conn.rollback()
        raise e
    finally:
        db.close_connection()


def cambiar_estado_presupuesto(id_presupuesto: int, nuevo_estado: str):
    """
    Permite transicionar entre BORRADOR y EN_REVISION, o CERRADO.
    Para APROBADO se debe usar aprobar_presupuesto_transaccional.
    """
    if nuevo_estado == "APROBADO":
        return aprobar_presupuesto_transaccional(id_presupuesto)

    db = PostgreSQL()
    db.create_connection()
    try:
        p = obtener_presupuesto_por_id(id_presupuesto)
        if not p:
            return {"error": "Presupuesto no encontrado.", "status_code": 404}

        estado_actual = p["estado"]
        if estado_actual == "APROBADO" and nuevo_estado not in ("CERRADO",):
            return {"error": "Un presupuesto aprobado no puede regresar a borrador o revisión. Debe generar una nueva versión.", "status_code": 400}

        es_vigente = False if nuevo_estado == "CERRADO" else p["es_vigente"]

        sql = """
            UPDATE obras.t_presupuesto
            SET estado = %s, es_vigente = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id_presupuesto = %s
            RETURNING id_presupuesto, estado, es_vigente;
        """
        row = db.execute_query(sql, (nuevo_estado, es_vigente, id_presupuesto), fetchone=True, commit=True)
        return {
            "success": True,
            "id_presupuesto": row[0],
            "estado": row[1],
            "es_vigente": row[2]
        }
    finally:
        db.close_connection()


def crear_nueva_version_presupuesto(id_presupuesto_origen: int, nuevo_codigo: str = None, nombre: str = None):
    """
    HU53/HU58: Clona un presupuesto existente para generar una nueva versión (e.g. Versión 2, 3...)
    - El nuevo presupuesto nace en estado 'BORRADOR' y 'es_vigente = FALSE'.
    - Clona todas las partidas con sus snapshots de precios y APUs.
    - Garantiza trazabilidad sin alterar el presupuesto histórico original.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        cur = db.conn.cursor()
        cur.execute("""
            SELECT id_obra, codigo, nombre, descripcion, superficie_m2, tipo_suelo,
                   costo_m2_estimado, monto_estimado_inicial, observaciones
            FROM obras.t_presupuesto
            WHERE id_presupuesto = %s;
        """, (id_presupuesto_origen,))
        orig = cur.fetchone()
        if not orig:
            return {"error": "Presupuesto de origen no encontrado.", "status_code": 404}

        id_obra = orig[0]
        cur.execute("SELECT COALESCE(MAX(version), 0) + 1 FROM obras.t_presupuesto WHERE id_obra = %s;", (id_obra,))
        nueva_version = cur.fetchone()[0]

        cod = (nuevo_codigo or f"{orig[1]}-V{nueva_version}").strip()
        nom = (nombre or f"{orig[2]} (v{nueva_version})").strip()

        cur.execute("""
            INSERT INTO obras.t_presupuesto (
                id_obra, codigo, nombre, descripcion, version, estado, es_vigente,
                fecha, superficie_m2, tipo_suelo, costo_m2_estimado,
                monto_estimado_inicial, total_presupuesto, observaciones
            ) VALUES (
                %s, %s, %s, %s, %s, 'BORRADOR', FALSE,
                CURRENT_DATE, %s, %s, %s, %s, 0.00, %s
            ) RETURNING id_presupuesto;
        """, (
            id_obra, cod, nom, orig[3], nueva_version,
            orig[4], orig[5], orig[6], orig[7], orig[8]
        ))
        nuevo_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO obras.t_partida_presupuesto (
                id_presupuesto, id_apu, codigo, nombre, descripcion,
                id_unidad_medida, cantidad, precio_unitario, importe_total,
                orden, id_estructura, id_unidad_construccion
            )
            SELECT
                %s, id_apu, codigo, nombre, descripcion,
                id_unidad_medida, cantidad, precio_unitario, importe_total,
                orden, id_estructura, id_unidad_construccion
            FROM obras.t_partida_presupuesto
            WHERE id_presupuesto = %s
            ORDER BY orden, id_partida;
        """, (nuevo_id, id_presupuesto_origen))

        cur.execute("""
            UPDATE obras.t_presupuesto
            SET total_presupuesto = COALESCE(
                (SELECT SUM(importe_total) FROM obras.t_partida_presupuesto WHERE id_presupuesto = %s),
                0.00
            )
            WHERE id_presupuesto = %s;
        """, (nuevo_id, nuevo_id))

        db.conn.commit()
        return obtener_presupuesto_por_id(nuevo_id)
    except Exception as e:
        if db.conn:
            db.conn.rollback()
        raise e
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# HU59: Costos Ejecutados
# ─────────────────────────────────────────────────────────────────────────────

def _row_to_costo_ejecutado(row):
    if not row:
        return None
    return {
        "id_costo_ejecutado": row[0],
        "id_obra": row[1],
        "id_partida": row[2],
        "codigo_costo": row[3],
        "origen_costo": row[4],
        "tipo_recurso": row[5],
        "descripcion": row[6],
        "id_unidad_medida": row[7],
        "cantidad": float(row[8]) if row[8] is not None else 0.0,
        "costo_unitario": float(row[9]) if row[9] is not None else 0.0,
        "importe_total": float(row[10]) if row[10] is not None else 0.0,
        "fecha": str(row[11]) if row[11] else None,
        "observacion": row[12],
        "id_usuario_registro": row[13],
        "created_at": str(row[14]) if row[14] else None,
        "unidad_medida_nombre": row[15] if len(row) > 15 else None,
        "unidad_medida_abrev": row[16] if len(row) > 16 else None,
        "partida_codigo": row[17] if len(row) > 17 else None,
        "partida_nombre": row[18] if len(row) > 18 else None
    }


def listar_costos_ejecutados(
    id_obra: int,
    id_partida: int = None,
    tipo_recurso: str = None,
    origen_costo: str = None,
    fecha_inicio: str = None,
    fecha_fin: str = None
):
    """
    HU59: Lista los costos ejecutados reales de una obra con filtros opcionales.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = """
            SELECT 
                c.id_costo_ejecutado, c.id_obra, c.id_partida, c.codigo_costo,
                c.origen_costo, c.tipo_recurso, c.descripcion, c.id_unidad_medida,
                c.cantidad, c.costo_unitario, c.importe_total, c.fecha,
                c.observacion, c.id_usuario_registro, c.created_at,
                u.nombre AS unidad_medida_nombre, u.abreviatura AS unidad_medida_abrev,
                p.codigo AS partida_codigo, p.nombre AS partida_nombre
            FROM obras.t_costo_ejecutado c
            LEFT JOIN obras.t_unidad_medida u ON c.id_unidad_medida = u.id_unidad_medida
            LEFT JOIN obras.t_partida_presupuesto p ON c.id_partida = p.id_partida
            WHERE c.id_obra = %s
        """
        params = [id_obra]

        if id_partida:
            sql += " AND c.id_partida = %s"
            params.append(id_partida)
        if tipo_recurso:
            sql += " AND c.tipo_recurso = %s"
            params.append(tipo_recurso)
        if origen_costo:
            sql += " AND c.origen_costo = %s"
            params.append(origen_costo)
        if fecha_inicio:
            sql += " AND c.fecha >= %s"
            params.append(fecha_inicio)
        if fecha_fin:
            sql += " AND c.fecha <= %s"
            params.append(fecha_fin)

        sql += " ORDER BY c.fecha DESC, c.id_costo_ejecutado DESC;"

        rows = db.execute_query(sql, tuple(params), fetchall=True)
        costos = [_row_to_costo_ejecutado(r) for r in (rows or [])]
        total = sum(c["importe_total"] for c in costos)

        return {
            "total_registros": len(costos),
            "monto_total_ejecutado": round(total, 2),
            "costos": costos
        }
    finally:
        db.close_connection()


def registrar_costo_ejecutado(
    id_obra: int,
    descripcion: str,
    cantidad: float,
    costo_unitario: float,
    id_usuario_registro: int,
    id_partida: int = None,
    codigo_costo: str = None,
    origen_costo: str = "REGISTRO_MANUAL",
    tipo_recurso: str = "MATERIAL",
    id_unidad_medida: int = None,
    fecha: str = None,
    observacion: str = None
):
    """
    HU59: Registra un costo ejecutado real en la obra.
    No muta el presupuesto ni las partidas.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        cantidad = float(cantidad or 1.0)
        costo_unitario = float(costo_unitario or 0.0)
        importe_total = round(cantidad * costo_unitario, 2)

        sql = """
            INSERT INTO obras.t_costo_ejecutado (
                id_obra, id_partida, codigo_costo, origen_costo, tipo_recurso,
                descripcion, id_unidad_medida, cantidad, costo_unitario,
                importe_total, fecha, observacion, id_usuario_registro
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, COALESCE(%s, CURRENT_DATE), %s, %s
            ) RETURNING id_costo_ejecutado;
        """
        params = (
            id_obra, id_partida, codigo_costo, origen_costo, tipo_recurso,
            descripcion, id_unidad_medida, cantidad, costo_unitario,
            importe_total, fecha, observacion, id_usuario_registro
        )
        row = db.execute_query(sql, params, fetchone=True, commit=True)
        return row[0] if row else None
    finally:
        db.close_connection()


def eliminar_costo_ejecutado(id_costo_ejecutado: int):
    """
    HU59: Elimina un registro de costo ejecutado.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = "DELETE FROM obras.t_costo_ejecutado WHERE id_costo_ejecutado = %s RETURNING id_costo_ejecutado;"
        row = db.execute_query(sql, (id_costo_ejecutado,), fetchone=True, commit=True)
        return bool(row)
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# HU60: Comparativa Presupuestado vs Ejecutado
# ─────────────────────────────────────────────────────────────────────────────

def obtener_comparativa_presupuesto_ejecutado(id_obra: int, id_presupuesto: int = None):
    """
    HU60: Genera el informe comparativo entre lo presupuestado y lo ejecutado.
    - Utiliza el presupuesto vigente si no se especifica uno.
    - Agrupa costos ejecutados por partida.
    - Identifica variaciones y desvíos (sobrecostos o ahorros).
    - Incluye costos directos sin partida asignada.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        if not id_presupuesto:
            p_row = db.execute_query("""
                SELECT id_presupuesto FROM obras.t_presupuesto 
                WHERE id_obra = %s AND es_vigente = TRUE 
                LIMIT 1;
            """, (id_obra,), fetchone=True)
            if p_row:
                id_presupuesto = p_row[0]
            else:
                p_row_any = db.execute_query("""
                    SELECT id_presupuesto FROM obras.t_presupuesto 
                    WHERE id_obra = %s 
                    ORDER BY version DESC LIMIT 1;
                """, (id_obra,), fetchone=True)
                if p_row_any:
                    id_presupuesto = p_row_any[0]

        presupuesto = obtener_presupuesto_por_id(id_presupuesto) if id_presupuesto else None
        total_presupuestado = float(presupuesto["total_presupuesto"]) if presupuesto else 0.0

        partidas_comp = []
        if id_presupuesto:
            partidas = listar_partidas_presupuesto(id_presupuesto)
            for p in partidas:
                id_partida = p["id_partida"]
                ejec_row = db.execute_query("""
                    SELECT COALESCE(SUM(importe_total), 0.0), COALESCE(SUM(cantidad), 0.0)
                    FROM obras.t_costo_ejecutado
                    WHERE id_partida = %s;
                """, (id_partida,), fetchone=True)

                monto_ejecutado = float(ejec_row[0]) if ejec_row else 0.0
                cant_ejecutada = float(ejec_row[1]) if ejec_row else 0.0
                monto_presupuestado = float(p.get("importe_total") or 0.0)

                variacion_monto = round(monto_ejecutado - monto_presupuestado, 2)
                variacion_pct = round((variacion_monto / monto_presupuestado * 100), 2) if monto_presupuestado > 0 else 0.0

                if variacion_monto > 0:
                    estado_desvio = "SOBRECOSTO"
                elif variacion_monto < 0 and monto_ejecutado > 0:
                    estado_desvio = "AHORRO"
                elif monto_ejecutado == 0:
                    estado_desvio = "NO_INICIADO"
                else:
                    estado_desvio = "EN_PRESUPUESTO"

                partidas_comp.append({
                    "id_partida": id_partida,
                    "codigo": p["codigo"],
                    "nombre": p["nombre"],
                    "unidad_medida": p.get("unidad_medida_abrev") or p.get("unidad_medida_nombre"),
                    "cantidad_presupuestada": p["cantidad"],
                    "precio_unitario_presupuestado": p["precio_unitario"],
                    "importe_presupuestado": monto_presupuestado,
                    "cantidad_ejecutada": cant_ejecutada,
                    "importe_ejecutado": monto_ejecutado,
                    "variacion_monto": variacion_monto,
                    "variacion_porcentaje": variacion_pct,
                    "estado_desvio": estado_desvio
                })

        sin_partida_rows = db.execute_query("""
            SELECT COALESCE(SUM(importe_total), 0.0), COUNT(*)
            FROM obras.t_costo_ejecutado
            WHERE id_obra = %s AND id_partida IS NULL;
        """, (id_obra,), fetchone=True)
        monto_sin_partida = float(sin_partida_rows[0]) if sin_partida_rows else 0.0
        cant_costos_sin_partida = sin_partida_rows[1] if sin_partida_rows else 0

        tot_ejec_row = db.execute_query("""
            SELECT COALESCE(SUM(importe_total), 0.0)
            FROM obras.t_costo_ejecutado
            WHERE id_obra = %s;
        """, (id_obra,), fetchone=True)
        total_ejecutado = float(tot_ejec_row[0]) if tot_ejec_row else 0.0

        variacion_global_monto = round(total_ejecutado - total_presupuestado, 2)
        variacion_global_pct = round((variacion_global_monto / total_presupuestado * 100), 2) if total_presupuestado > 0 else 0.0
        cpi = round(total_presupuestado / total_ejecutado, 2) if total_ejecutado > 0 else 1.0

        return {
            "id_obra": id_obra,
            "presupuesto_evaluado": presupuesto,
            "total_presupuestado": total_presupuestado,
            "total_ejecutado": total_ejecutado,
            "variacion_global_monto": variacion_global_monto,
            "variacion_global_porcentaje": variacion_global_pct,
            "indice_eficiencia_cpi": cpi,
            "total_costos_sin_partida": monto_sin_partida,
            "cantidad_costos_sin_partida": cant_costos_sin_partida,
            "comparativa_partidas": partidas_comp
        }
    finally:
        db.close_connection()
