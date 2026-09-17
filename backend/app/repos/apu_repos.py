import datetime
from app.classes.postgres import PostgreSQL


def _row_to_dict(row, keys):
    if not row:
        return None
    return {k: (float(v) if hasattr(v, 'as_integer_ratio') else v) for k, v in zip(keys, row)}


def listar_categorias_apu():
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = """
            SELECT c.id_categoria, c.nombre, c.descripcion, c.icono, c.activo,
                   (SELECT COUNT(*) FROM obras.t_apu a WHERE a.id_categoria = c.id_categoria AND a.es_base = TRUE) AS total_base,
                   (SELECT COUNT(*) FROM obras.t_apu a WHERE a.id_categoria = c.id_categoria AND a.es_base = FALSE) AS total_empresa
            FROM obras.t_categoria_apu c
            WHERE c.activo = TRUE
            ORDER BY c.nombre ASC;
        """
        rows = db.execute_query(sql, fetchall=True) or []
        keys = ["id_categoria", "nombre", "descripcion", "icono", "activo", "total_base", "total_empresa"]
        return [_row_to_dict(r, keys) for r in rows]
    finally:
        db.close_connection()


def listar_apus_base(id_categoria: int = None, q: str = None):
    db = PostgreSQL()
    db.create_connection()
    try:
        conds = ["a.es_base = TRUE", "a.estado = 'ACTIVO'"]
        params = []
        if id_categoria:
            conds.append("a.id_categoria = %s")
            params.append(id_categoria)
        if q and q.strip():
            conds.append("(a.codigo ILIKE %s OR a.nombre ILIKE %s OR a.descripcion ILIKE %s)")
            term = f"%{q.strip()}%"
            params.extend([term, term, term])

        where_clause = " AND ".join(conds)
        sql = f"""
            SELECT a.id_apu, a.codigo, a.codigo_base, a.nombre, a.descripcion,
                   a.id_unidad_medida, um.nombre AS unidad_medida_nombre, um.abreviatura AS unidad_medida_abrev,
                   a.rendimiento_base, a.costo_materiales, a.costo_mano_obra, a.costo_equipos,
                   a.costo_directo, a.porcentaje_gastos_generales, a.monto_gastos_generales,
                   a.porcentaje_utilidad, a.monto_utilidad, a.porcentaje_impuestos, a.monto_impuestos,
                   a.precio_unitario, a.costo_unitario_total, a.version, a.es_base,
                   c.id_categoria, c.nombre AS categoria_nombre, c.icono AS categoria_icono,
                   (SELECT COUNT(*) FROM obras.t_apu_componente comp WHERE comp.id_apu = a.id_apu) AS total_componentes
            FROM obras.t_apu a
            JOIN obras.t_categoria_apu c ON c.id_categoria = a.id_categoria
            JOIN obras.t_unidad_medida um ON um.id_unidad_medida = a.id_unidad_medida
            WHERE {where_clause}
            ORDER BY c.nombre ASC, a.nombre ASC;
        """
        rows = db.execute_query(sql, tuple(params), fetchall=True) or []
        keys = [
            "id_apu", "codigo", "codigo_base", "nombre", "descripcion",
            "id_unidad_medida", "unidad_medida_nombre", "unidad_medida_abrev",
            "rendimiento_base", "costo_materiales", "costo_mano_obra", "costo_equipos",
            "costo_directo", "porcentaje_gastos_generales", "monto_gastos_generales",
            "porcentaje_utilidad", "monto_utilidad", "porcentaje_impuestos", "monto_impuestos",
            "precio_unitario", "costo_unitario_total", "version", "es_base",
            "id_categoria", "categoria_nombre", "categoria_icono", "total_componentes"
        ]
        return [_row_to_dict(r, keys) for r in rows]
    finally:
        db.close_connection()


def copiar_apu_base(id_apu_base: int, id_empresa: int, codigo_personalizado: str = None) -> int:
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = "SELECT obras.fn_copiar_apu_base_empresa(%s, %s, %s);"
        row = db.execute_query(sql, (id_apu_base, id_empresa, codigo_personalizado), fetchone=True, commit=True)
        return row[0] if row else None
    finally:
        db.close_connection()


def listar_mis_apus(id_empresa: int, id_categoria: int = None, solo_vigentes: bool = False, q: str = None, id_obra: int = None):
    db = PostgreSQL()
    db.create_connection()
    try:
        conds = ["a.id_empresa = %s", "a.es_base = FALSE"]
        params = [id_empresa]

        if id_obra:
            conds.append("(a.id_obra = %s OR a.id_obra IS NULL)")
            params.append(id_obra)
        if id_categoria:
            conds.append("a.id_categoria = %s")
            params.append(id_categoria)
        if solo_vigentes:
            conds.append("a.es_vigente = TRUE")
        if q and q.strip():
            conds.append("(a.codigo ILIKE %s OR a.nombre ILIKE %s OR a.descripcion ILIKE %s)")
            term = f"%{q.strip()}%"
            params.extend([term, term, term])

        where_clause = " AND ".join(conds)
        sql = f"""
            SELECT a.id_apu, a.id_empresa, a.id_obra, a.codigo, a.codigo_base, a.nombre, a.descripcion,
                   a.id_unidad_medida, um.nombre AS unidad_medida_nombre, um.abreviatura AS unidad_medida_abrev,
                   a.rendimiento_base, a.costo_materiales, a.costo_mano_obra, a.costo_equipos,
                   a.costo_directo, a.porcentaje_gastos_generales, a.monto_gastos_generales,
                   a.porcentaje_utilidad, a.monto_utilidad, a.porcentaje_impuestos, a.monto_impuestos,
                   a.precio_unitario, a.costo_unitario_total, a.version, a.estado, a.es_vigente, a.es_base,
                   a.id_apu_base, a.created_at, a.updated_at,
                   c.id_categoria, c.nombre AS categoria_nombre, c.icono AS categoria_icono,
                   (SELECT COUNT(*) FROM obras.t_apu_componente comp WHERE comp.id_apu = a.id_apu) AS total_componentes,
                   (SELECT COUNT(*) FROM obras.t_partida_presupuesto pp WHERE pp.id_apu = a.id_apu) AS total_partidas_usando
            FROM obras.t_apu a
            JOIN obras.t_categoria_apu c ON c.id_categoria = a.id_categoria
            JOIN obras.t_unidad_medida um ON um.id_unidad_medida = a.id_unidad_medida
            WHERE {where_clause}
            ORDER BY a.codigo_base ASC, a.version DESC;
        """
        rows = db.execute_query(sql, tuple(params), fetchall=True) or []
        keys = [
            "id_apu", "id_empresa", "id_obra", "codigo", "codigo_base", "nombre", "descripcion",
            "id_unidad_medida", "unidad_medida_nombre", "unidad_medida_abrev",
            "rendimiento_base", "costo_materiales", "costo_mano_obra", "costo_equipos",
            "costo_directo", "porcentaje_gastos_generales", "monto_gastos_generales",
            "porcentaje_utilidad", "monto_utilidad", "porcentaje_impuestos", "monto_impuestos",
            "precio_unitario", "costo_unitario_total", "version", "estado", "es_vigente", "es_base",
            "id_apu_base", "created_at", "updated_at",
            "id_categoria", "categoria_nombre", "categoria_icono", "total_componentes", "total_partidas_usando"
        ]
        res = []
        for r in rows:
            item = _row_to_dict(r, keys)
            item["en_uso"] = bool(item.get("total_partidas_usando", 0) > 0)
            res.append(item)
        return res
    finally:
        db.close_connection()


def obtener_apu_detalle(id_apu: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql_apu = """
            SELECT a.id_apu, a.id_empresa, a.id_obra, a.codigo, a.codigo_base, a.nombre, a.descripcion,
                   a.id_unidad_medida, um.nombre AS unidad_medida_nombre, um.abreviatura AS unidad_medida_abrev,
                   a.rendimiento_base, a.costo_materiales, a.costo_mano_obra, a.costo_equipos,
                   a.costo_directo, a.porcentaje_gastos_generales, a.monto_gastos_generales,
                   a.porcentaje_utilidad, a.monto_utilidad, a.porcentaje_impuestos, a.monto_impuestos,
                   a.precio_unitario, a.costo_unitario_total, a.version, a.estado, a.es_vigente, a.es_base,
                   a.id_apu_base, a.created_at, a.updated_at,
                   c.id_categoria, c.nombre AS categoria_nombre, c.icono AS categoria_icono,
                   (SELECT COUNT(*) FROM obras.t_partida_presupuesto pp WHERE pp.id_apu = a.id_apu) AS total_partidas_usando
            FROM obras.t_apu a
            JOIN obras.t_categoria_apu c ON c.id_categoria = a.id_categoria
            JOIN obras.t_unidad_medida um ON um.id_unidad_medida = a.id_unidad_medida
            WHERE a.id_apu = %s;
        """
        apu_row = db.execute_query(sql_apu, (id_apu,), fetchone=True)
        if not apu_row:
            return None

        keys_apu = [
            "id_apu", "id_empresa", "id_obra", "codigo", "codigo_base", "nombre", "descripcion",
            "id_unidad_medida", "unidad_medida_nombre", "unidad_medida_abrev",
            "rendimiento_base", "costo_materiales", "costo_mano_obra", "costo_equipos",
            "costo_directo", "porcentaje_gastos_generales", "monto_gastos_generales",
            "porcentaje_utilidad", "monto_utilidad", "porcentaje_impuestos", "monto_impuestos",
            "precio_unitario", "costo_unitario_total", "version", "estado", "es_vigente", "es_base",
            "id_apu_base", "created_at", "updated_at",
            "id_categoria", "categoria_nombre", "categoria_icono", "total_partidas_usando"
        ]
        apu = _row_to_dict(apu_row, keys_apu)
        apu["en_uso"] = bool(apu.get("total_partidas_usando", 0) > 0)

        # Cargar componentes
        sql_comp = """
            SELECT comp.id_componente, comp.id_apu, comp.tipo_recurso, comp.id_recurso,
                   comp.id_material, comp.id_mano_obra, comp.id_equipo,
                   comp.descripcion_recurso, comp.id_unidad_medida,
                   um.nombre AS unidad_medida_nombre, um.abreviatura AS unidad_medida_abrev,
                   COALESCE(comp.rendimiento, comp.cantidad) AS rendimiento,
                   comp.precio_unitario, comp.subtotal, comp.created_at,
                   COALESCE(m.codigo, eq.codigo, '') AS recurso_codigo
            FROM obras.t_apu_componente comp
            JOIN obras.t_unidad_medida um ON um.id_unidad_medida = comp.id_unidad_medida
            LEFT JOIN obras.t_material m ON m.id_material = COALESCE(comp.id_material, comp.id_recurso) AND comp.tipo_recurso = 'MATERIAL'
            LEFT JOIN obras.t_equipo eq ON eq.id_equipo = COALESCE(comp.id_equipo, comp.id_recurso) AND comp.tipo_recurso = 'EQUIPO'
            WHERE comp.id_apu = %s
            ORDER BY 
                CASE comp.tipo_recurso 
                    WHEN 'MATERIAL' THEN 1 
                    WHEN 'MANO_OBRA' THEN 2 
                    WHEN 'EQUIPO' THEN 3 
                    ELSE 4 
                END,
                comp.id_componente ASC;
        """
        comp_rows = db.execute_query(sql_comp, (id_apu,), fetchall=True) or []
        keys_comp = [
            "id_componente", "id_apu", "tipo_recurso", "id_recurso",
            "id_material", "id_mano_obra", "id_equipo",
            "descripcion_recurso", "id_unidad_medida",
            "unidad_medida_nombre", "unidad_medida_abrev",
            "rendimiento", "precio_unitario", "subtotal", "created_at", "recurso_codigo"
        ]
        componentes = [_row_to_dict(r, keys_comp) for r in comp_rows]
        apu["componentes"] = componentes

        # Separar en listas para UI cómoda
        apu["materiales"] = [c for c in componentes if c["tipo_recurso"] == "MATERIAL"]
        apu["mano_obra"] = [c for c in componentes if c["tipo_recurso"] == "MANO_OBRA"]
        apu["equipos"] = [c for c in componentes if c["tipo_recurso"] == "EQUIPO"]

        return apu
    finally:
        db.close_connection()


def generar_codigo_siguiente_apu(id_empresa: int, anio: int = None) -> str:
    db = PostgreSQL()
    db.create_connection()
    try:
        if not anio:
            anio = datetime.date.today().year
        prefix = f"APU-{anio}-"
        sql = """
            SELECT codigo, codigo_base 
            FROM obras.t_apu 
            WHERE id_empresa = %s AND (codigo LIKE %s OR codigo_base LIKE %s);
        """
        rows = db.execute_query(sql, (id_empresa, f"{prefix}%", f"{prefix}%"), fetchall=True) or []
        max_num = 0
        for r in rows:
            for cod in (r[0], r[1]):
                if cod and cod.startswith(prefix):
                    parts = cod.split("-")
                    if len(parts) >= 3:
                        num_part = parts[2].split("v")[0].split(".")[0]
                        try:
                            val = int(num_part)
                            if val > max_num:
                                max_num = val
                        except ValueError:
                            pass
        next_num = max_num + 1
        return f"APU-{anio}-{next_num:04d}"
    finally:
        db.close_connection()


def crear_apu_empresa(id_empresa: int, data: dict) -> int:
    db = PostgreSQL()
    db.create_connection()
    try:
        codigo = data.get("codigo") or generar_codigo_siguiente_apu(id_empresa)
        codigo_base = data.get("codigo_base") or codigo
        nombre = data["nombre"].strip()
        descripcion = data.get("descripcion")
        id_categoria = int(data["id_categoria"])
        id_unidad_medida = int(data["id_unidad_medida"])
        rendimiento_base = float(data.get("rendimiento_base") or 1.0)
        id_obra = int(data["id_obra"]) if data.get("id_obra") else None
        
        pct_gg = float(data.get("porcentaje_gastos_generales") if data.get("porcentaje_gastos_generales") is not None else 8.00)
        pct_ut = float(data.get("porcentaje_utilidad") if data.get("porcentaje_utilidad") is not None else 15.00)
        pct_it = float(data.get("porcentaje_impuestos") if data.get("porcentaje_impuestos") is not None else 3.09)

        sql = """
            INSERT INTO obras.t_apu (
                id_empresa, id_obra, codigo, codigo_base, version, nombre, descripcion,
                id_categoria, id_unidad_medida, rendimiento_base, es_base,
                porcentaje_gastos_generales, porcentaje_utilidad, porcentaje_impuestos,
                estado, es_vigente
            ) VALUES (
                %s, %s, %s, %s, 1, %s, %s, %s, %s, %s, FALSE, %s, %s, %s, 'ACTIVO', TRUE
            ) RETURNING id_apu;
        """
        row = db.execute_query(sql, (
            id_empresa, id_obra, codigo, codigo_base, nombre, descripcion,
            id_categoria, id_unidad_medida, rendimiento_base, pct_gg, pct_ut, pct_it
        ), fetchone=True, commit=True)
        nuevo_id = row[0] if row else None

        if nuevo_id:
            recalcular_apu(nuevo_id)

        return nuevo_id
    finally:
        db.close_connection()


def actualizar_apu_empresa(id_apu: int, data: dict):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = """
            UPDATE obras.t_apu
            SET nombre = COALESCE(%s, nombre),
                descripcion = %s,
                id_categoria = COALESCE(%s, id_categoria),
                id_unidad_medida = COALESCE(%s, id_unidad_medida),
                rendimiento_base = COALESCE(%s, rendimiento_base),
                porcentaje_gastos_generales = COALESCE(%s, porcentaje_gastos_generales),
                porcentaje_utilidad = COALESCE(%s, porcentaje_utilidad),
                porcentaje_impuestos = COALESCE(%s, porcentaje_impuestos),
                estado = COALESCE(%s, estado),
                updated_at = CURRENT_TIMESTAMP
            WHERE id_apu = %s;
        """
        params = (
            data.get("nombre"),
            data.get("descripcion"),
            data.get("id_categoria"),
            data.get("id_unidad_medida"),
            data.get("rendimiento_base"),
            data.get("porcentaje_gastos_generales"),
            data.get("porcentaje_utilidad"),
            data.get("porcentaje_impuestos"),
            data.get("estado"),
            id_apu
        )
        db.execute_query(sql, params, commit=True)
        recalcular_apu(id_apu)
        return True
    finally:
        db.close_connection()


def versionar_apu(id_apu_original: int) -> int:
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = "SELECT obras.fn_versionar_apu(%s);"
        row = db.execute_query(sql, (id_apu_original,), fetchone=True, commit=True)
        return row[0] if row else None
    finally:
        db.close_connection()


def duplicar_apu(id_apu_original: int, id_empresa: int, nuevo_codigo: str = None) -> int:
    db = PostgreSQL()
    db.create_connection()
    try:
        apu_orig = obtener_apu_detalle(id_apu_original)
        if not apu_orig:
            raise ValueError(f"APU {id_apu_original} no encontrado.")

        cod = nuevo_codigo or generar_codigo_siguiente_apu(id_empresa)
        nuevo_id = crear_apu_empresa(id_empresa, {
            "codigo": cod,
            "codigo_base": cod,
            "nombre": f"{apu_orig['nombre']} (Copia)",
            "descripcion": apu_orig.get("descripcion"),
            "id_categoria": apu_orig["id_categoria"],
            "id_unidad_medida": apu_orig["id_unidad_medida"],
            "rendimiento_base": apu_orig.get("rendimiento_base", 1.0),
            "porcentaje_gastos_generales": apu_orig.get("porcentaje_gastos_generales", 8.0),
            "porcentaje_utilidad": apu_orig.get("porcentaje_utilidad", 15.0),
            "porcentaje_impuestos": apu_orig.get("porcentaje_impuestos", 3.09)
        })

        for c in apu_orig.get("componentes", []):
            agregar_componente_apu(
                id_apu=nuevo_id,
                tipo_recurso=c["tipo_recurso"],
                descripcion_recurso=c["descripcion_recurso"],
                id_unidad_medida=c["id_unidad_medida"],
                rendimiento=c["rendimiento"],
                precio_unitario=c["precio_unitario"],
                id_recurso=c.get("id_recurso"),
                id_material=c.get("id_material"),
                id_mano_obra=c.get("id_mano_obra"),
                id_equipo=c.get("id_equipo")
            )

        return nuevo_id
    finally:
        db.close_connection()


def cambiar_estado_apu(id_apu: int, nuevo_estado: str):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = "UPDATE obras.t_apu SET estado = %s, updated_at = CURRENT_TIMESTAMP WHERE id_apu = %s;"
        db.execute_query(sql, (nuevo_estado, id_apu), commit=True)
        return True
    finally:
        db.close_connection()


def recalcular_apu(id_apu: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = "SELECT * FROM obras.fn_calcular_apu(%s);"
        return db.execute_query(sql, (id_apu,), fetchone=True, commit=True)
    finally:
        db.close_connection()


def agregar_componente_apu(
    id_apu: int, tipo_recurso: str, descripcion_recurso: str,
    id_unidad_medida: int, rendimiento: float, precio_unitario: float = 0.0,
    id_recurso: int = None, id_material: int = None, id_mano_obra: int = None, id_equipo: int = None
) -> int:
    db = PostgreSQL()
    db.create_connection()
    try:
        rend = float(rendimiento if rendimiento is not None else 1.0)
        pu = float(precio_unitario or 0.0)

        # Resolver claves según tipo_recurso
        if tipo_recurso == "MATERIAL":
            id_material = id_material or id_recurso
            if id_material and pu <= 0:
                m_row = db.execute_query("SELECT precio FROM obras.t_material WHERE id_material = %s;", (id_material,), fetchone=True)
                if m_row and m_row[0]:
                    pu = float(m_row[0])
        elif tipo_recurso == "MANO_OBRA":
            id_mano_obra = id_mano_obra or id_recurso
            if id_mano_obra and pu <= 0:
                mo_row = db.execute_query("SELECT costo_unitario FROM obras.t_mano_obra WHERE id_mano_obra = %s;", (id_mano_obra,), fetchone=True)
                if mo_row and mo_row[0]:
                    pu = float(mo_row[0])
        elif tipo_recurso == "EQUIPO":
            id_equipo = id_equipo or id_recurso
            if id_equipo and pu <= 0:
                eq_row = db.execute_query("SELECT costo_unitario FROM obras.t_equipo WHERE id_equipo = %s;", (id_equipo,), fetchone=True)
                if eq_row and eq_row[0]:
                    pu = float(eq_row[0])

        subtotal = round(rend * pu, 2)
        rec_id = id_material or id_mano_obra or id_equipo or id_recurso

        sql = """
            INSERT INTO obras.t_apu_componente (
                id_apu, tipo_recurso, id_recurso, id_material, id_mano_obra, id_equipo,
                descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_componente;
        """
        row = db.execute_query(sql, (
            id_apu, tipo_recurso, rec_id, id_material, id_mano_obra, id_equipo,
            descripcion_recurso, id_unidad_medida, rend, rend, pu, subtotal
        ), fetchone=True, commit=True)
        id_comp = row[0] if row else None

        recalcular_apu(id_apu)
        return id_comp
    finally:
        db.close_connection()


def actualizar_componente_apu(
    id_componente: int, tipo_recurso: str, descripcion_recurso: str,
    id_unidad_medida: int, rendimiento: float, precio_unitario: float,
    id_recurso: int = None, id_material: int = None, id_mano_obra: int = None, id_equipo: int = None
):
    db = PostgreSQL()
    db.create_connection()
    try:
        c_row = db.execute_query("SELECT id_apu FROM obras.t_apu_componente WHERE id_componente = %s;", (id_componente,), fetchone=True)
        if not c_row:
            return None
        id_apu = c_row[0]

        rend = float(rendimiento if rendimiento is not None else 1.0)
        pu = float(precio_unitario or 0.0)
        subtotal = round(rend * pu, 2)
        rec_id = id_material or id_mano_obra or id_equipo or id_recurso

        sql = """
            UPDATE obras.t_apu_componente
            SET tipo_recurso = %s, descripcion_recurso = %s, id_unidad_medida = %s,
                cantidad = %s, rendimiento = %s, precio_unitario = %s, subtotal = %s,
                id_recurso = %s, id_material = %s, id_mano_obra = %s, id_equipo = %s
            WHERE id_componente = %s;
        """
        db.execute_query(sql, (
            tipo_recurso, descripcion_recurso, id_unidad_medida,
            rend, rend, pu, subtotal,
            rec_id, id_material, id_mano_obra, id_equipo, id_componente
        ), commit=True)

        recalcular_apu(id_apu)
        return id_componente
    finally:
        db.close_connection()


def eliminar_componente_apu(id_componente: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        c_row = db.execute_query("SELECT id_apu FROM obras.t_apu_componente WHERE id_componente = %s;", (id_componente,), fetchone=True)
        if not c_row:
            return False
        id_apu = c_row[0]

        db.execute_query("DELETE FROM obras.t_apu_componente WHERE id_componente = %s;", (id_componente,), commit=True)
        recalcular_apu(id_apu)
        return True
    finally:
        db.close_connection()


# ─────────────────────────────────────────────────────────────────────────────
# Catálogos de Recursos para selectores
# ─────────────────────────────────────────────────────────────────────────────

def listar_materiales_empresa(id_empresa: int, q: str = None):
    db = PostgreSQL()
    db.create_connection()
    try:
        conds = ["(m.id_empresa = %s OR m.id_empresa = 1)", "m.estado = 'ACTIVO'"]
        params = [id_empresa]
        if q and q.strip():
            conds.append("(m.nombre_material ILIKE %s OR m.codigo ILIKE %s)")
            params.extend([f"%{q.strip()}%", f"%{q.strip()}%"])

        where_clause = " AND ".join(conds)
        sql = f"""
            SELECT m.id_material, m.codigo, m.nombre_material, m.precio,
                   m.id_unidad_medida, um.nombre AS unidad_medida_nombre, um.abreviatura AS unidad_medida_abrev
            FROM obras.t_material m
            LEFT JOIN obras.t_unidad_medida um ON um.id_unidad_medida = m.id_unidad_medida
            WHERE {where_clause}
            ORDER BY m.nombre_material ASC
            LIMIT 100;
        """
        rows = db.execute_query(sql, tuple(params), fetchall=True) or []
        keys = ["id_material", "codigo", "nombre_material", "precio", "id_unidad_medida", "unidad_medida_nombre", "unidad_medida_abrev"]
        return [_row_to_dict(r, keys) for r in rows]
    finally:
        db.close_connection()


def listar_mano_obra_empresa(id_empresa: int, q: str = None):
    db = PostgreSQL()
    db.create_connection()
    try:
        conds = ["(mo.id_empresa = %s OR mo.id_empresa = 1)", "mo.activo = TRUE"]
        params = [id_empresa]
        if q and q.strip():
            conds.append("mo.nombre ILIKE %s")
            params.append(f"%{q.strip()}%")

        where_clause = " AND ".join(conds)
        sql = f"""
            SELECT mo.id_mano_obra, mo.nombre, mo.descripcion, mo.costo_unitario,
                   mo.id_unidad_medida, um.nombre AS unidad_medida_nombre, um.abreviatura AS unidad_medida_abrev
            FROM obras.t_mano_obra mo
            LEFT JOIN obras.t_unidad_medida um ON um.id_unidad_medida = mo.id_unidad_medida
            WHERE {where_clause}
            ORDER BY mo.nombre ASC;
        """
        rows = db.execute_query(sql, tuple(params), fetchall=True) or []
        keys = ["id_mano_obra", "nombre", "descripcion", "costo_unitario", "id_unidad_medida", "unidad_medida_nombre", "unidad_medida_abrev"]
        return [_row_to_dict(r, keys) for r in rows]
    finally:
        db.close_connection()


def listar_equipos_empresa(id_empresa: int, q: str = None):
    db = PostgreSQL()
    db.create_connection()
    try:
        conds = ["(eq.id_empresa = %s OR eq.id_empresa = 1)", "eq.activo = TRUE"]
        params = [id_empresa]
        if q and q.strip():
            conds.append("(eq.nombre ILIKE %s OR eq.codigo ILIKE %s)")
            params.extend([f"%{q.strip()}%", f"%{q.strip()}%"])

        where_clause = " AND ".join(conds)
        sql = f"""
            SELECT eq.id_equipo, eq.codigo, eq.nombre, eq.descripcion, eq.costo_unitario,
                   eq.id_unidad_medida, um.nombre AS unidad_medida_nombre, um.abreviatura AS unidad_medida_abrev
            FROM obras.t_equipo eq
            LEFT JOIN obras.t_unidad_medida um ON um.id_unidad_medida = eq.id_unidad_medida
            WHERE {where_clause}
            ORDER BY eq.nombre ASC;
        """
        rows = db.execute_query(sql, tuple(params), fetchall=True) or []
        keys = ["id_equipo", "codigo", "nombre", "descripcion", "costo_unitario", "id_unidad_medida", "unidad_medida_nombre", "unidad_medida_abrev"]
        return [_row_to_dict(r, keys) for r in rows]
    finally:
        db.close_connection()


def listar_unidades_medida():
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = "SELECT id_unidad_medida, nombre, abreviatura, tipo FROM obras.t_unidad_medida WHERE estado = 'ACTIVO' ORDER BY nombre ASC;"
        rows = db.execute_query(sql, fetchall=True) or []
        keys = ["id_unidad_medida", "nombre", "abreviatura", "tipo"]
        return [_row_to_dict(r, keys) for r in rows]
    finally:
        db.close_connection()
