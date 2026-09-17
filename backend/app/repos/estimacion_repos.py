from app.classes.postgres import PostgreSQL
from app.config import Config


def _query(sql, params=(), *, fetchall=False, fetchone=False, commit=False):
    db = PostgreSQL()
    db.create_connection()
    try:
        rows = db.execute_query(sql, params, fetchall=fetchall, fetchone=fetchone, commit=commit)
        if fetchall:
            columns = [item.name if hasattr(item, 'name') else item[0] for item in db.cur.description] if db.cur and db.cur.description else []
            return [dict(zip(columns, row)) for row in (rows or [])]
        if fetchone and rows:
            columns = [item.name if hasattr(item, 'name') else item[0] for item in db.cur.description] if db.cur and db.cur.description else []
            return dict(zip(columns, rows))
        return rows
    finally:
        db.close_connection()


def list_apu(id_empresa, id_obra=None, tipo=None, calidad=None, activo=True):
    sql = f"""SELECT a.*, um.nombre AS unidad_nombre, um.abreviatura,
        ROUND(COALESCE((SELECT SUM(ROUND(i.cantidad * i.precio_unitario, 2))
        FROM {Config.SCHEMA}.t_analisi_precio_unitario_insumo i
        WHERE i.id_analisis_precio_unitario=a.id_analisis_precio_unitario AND i.id_empresa=%s),0),2) AS costo_directo_unitario
        FROM {Config.SCHEMA}.t_analisis_precio_unitario a
        JOIN {Config.SCHEMA}.t_unidad_medida um ON um.id_unidad_medida=a.id_unidad_medida
        WHERE a.id_empresa=%s AND (%s IS NULL OR a.id_obra=%s) AND (%s IS NULL OR a.tipo_analisis_precio_unitario=%s)
        AND (%s IS NULL OR a.calidad=%s) AND (%s IS NULL OR a.activo=%s)
        ORDER BY a.nombre"""
    return _query(sql, (id_empresa, id_empresa, id_obra, id_obra, tipo, tipo, calidad, calidad, activo, activo), fetchall=True)


def get_apu(id_apu, id_empresa):
    header = _query(f"SELECT * FROM {Config.SCHEMA}.t_analisis_precio_unitario WHERE id_analisis_precio_unitario=%s AND id_empresa=%s", (id_apu, id_empresa), fetchone=True)
    if not header:
        return None
    header['insumos'] = _query(f"SELECT * FROM {Config.SCHEMA}.t_analisi_precio_unitario_insumo WHERE id_analisis_precio_unitario=%s AND id_empresa=%s ORDER BY orden, id_analisis_precio_unitario_insumo", (id_apu, id_empresa), fetchall=True)
    calculated = _query(f"SELECT {Config.SCHEMA}.fn_calcular_analisis_precio_unitario(%s,%s)", (id_apu, id_empresa), fetchone=True)
    header['calculo'] = calculated.get('fn_calcular_analisis_precio_unitario') if calculated else None
    return header


def create_apu(data, id_empresa):
    return _query(f"""INSERT INTO {Config.SCHEMA}.t_analisis_precio_unitario
        (id_obra,id_padre,id_estructura,nombre,descripcion,id_unidad_medida,tipo_analisis_precio_unitario,calidad,id_empresa)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id_analisis_precio_unitario""",
        (data.get('id_obra'), data.get('id_padre'), data.get('id_estructura'), data.get('nombre'), data.get('descripcion'), data.get('id_unidad_medida'), data.get('tipo_analisis_precio_unitario','OBRA_GRIS'), data.get('calidad'), id_empresa), fetchone=True, commit=True)


def update_apu(id_apu, data, id_empresa):
    return _query(f"""UPDATE {Config.SCHEMA}.t_analisis_precio_unitario SET nombre=COALESCE(%s,nombre), descripcion=COALESCE(%s,descripcion), id_unidad_medida=COALESCE(%s,id_unidad_medida), tipo_analisis_precio_unitario=COALESCE(%s,tipo_analisis_precio_unitario), calidad=%s, id_padre=%s, id_estructura=%s, activo=COALESCE(%s,activo)
        WHERE id_analisis_precio_unitario=%s AND id_empresa=%s RETURNING id_analisis_precio_unitario""", (data.get('nombre'), data.get('descripcion'), data.get('id_unidad_medida'), data.get('tipo_analisis_precio_unitario'), data.get('calidad'), data.get('id_padre'), data.get('id_estructura'), data.get('activo'), id_apu, id_empresa), fetchone=True, commit=True)


def duplicate_apu(id_apu, id_empresa):
    return _query(f"""WITH nuevo AS (INSERT INTO {Config.SCHEMA}.t_analisis_precio_unitario(id_obra,id_padre,id_estructura,nombre,descripcion,id_unidad_medida,tipo_analisis_precio_unitario,calidad,id_empresa)
        SELECT id_obra,id_padre,id_estructura,nombre || ' - copia',descripcion,id_unidad_medida,tipo_analisis_precio_unitario,calidad,id_empresa FROM {Config.SCHEMA}.t_analisis_precio_unitario WHERE id_analisis_precio_unitario=%s AND id_empresa=%s RETURNING id_analisis_precio_unitario)
        SELECT id_analisis_precio_unitario FROM nuevo""", (id_apu, id_empresa), fetchone=True, commit=True)


def list_insumos(id_apu, id_empresa):
    return _query(f"SELECT * FROM {Config.SCHEMA}.t_analisi_precio_unitario_insumo WHERE id_analisis_precio_unitario=%s AND id_empresa=%s ORDER BY orden, id_analisis_precio_unitario_insumo", (id_apu, id_empresa), fetchall=True)


def create_insumo(id_apu, data, id_empresa):
    return _query(f"""INSERT INTO {Config.SCHEMA}.t_analisi_precio_unitario_insumo(id_analisis_precio_unitario,tipo_insumo,id_material,id_mano_obra,nombre,id_unidad_medida,cantidad,precio_unitario,orden,id_empresa)
        SELECT %s,%s,%s,%s,%s,%s,ROUND(%s::numeric,4),ROUND(%s::numeric,2),%s,%s WHERE EXISTS (SELECT 1 FROM {Config.SCHEMA}.t_analisis_precio_unitario WHERE id_analisis_precio_unitario=%s AND id_empresa=%s) RETURNING id_analisis_precio_unitario_insumo""",
        (id_apu, data['tipo_insumo'], data.get('id_material'), data.get('id_mano_obra'), data['nombre'], data['id_unidad_medida'], data['cantidad'], data['precio_unitario'], data.get('orden',1), id_empresa, id_apu, id_empresa), fetchone=True, commit=True)


def update_insumo(insumo_id, data, id_empresa):
    return _query(f"""UPDATE {Config.SCHEMA}.t_analisi_precio_unitario_insumo SET nombre=COALESCE(%s,nombre), id_unidad_medida=COALESCE(%s,id_unidad_medida), cantidad=COALESCE(ROUND(%s::numeric,4),cantidad), precio_unitario=COALESCE(ROUND(%s::numeric,2),precio_unitario), orden=COALESCE(%s,orden)
        WHERE id_analisis_precio_unitario_insumo=%s AND id_empresa=%s RETURNING id_analisis_precio_unitario_insumo""", (data.get('nombre'), data.get('id_unidad_medida'), data.get('cantidad'), data.get('precio_unitario'), data.get('orden'), insumo_id, id_empresa), fetchone=True, commit=True)


def list_estimaciones(id_empresa, id_obra=None):
    return _query(f"SELECT * FROM {Config.SCHEMA}.t_estimacion WHERE id_empresa=%s AND (%s IS NULL OR id_obra=%s) ORDER BY id_obra, version DESC", (id_empresa, id_obra, id_obra), fetchall=True)


def get_estimacion(id_estimacion, id_empresa):
    row = _query(f"SELECT * FROM {Config.SCHEMA}.t_estimacion WHERE id_estimacion=%s AND id_empresa=%s", (id_estimacion, id_empresa), fetchone=True)
    if row:
        calc = _query(f"SELECT {Config.SCHEMA}.fn_calcular_estimacion(%s,%s)", (id_estimacion, id_empresa), fetchone=True)
        row['calculo'] = calc.get('fn_calcular_estimacion') if calc else None
    return row


def create_estimacion(data, id_empresa):
    factor_utilidad = data.get('factor_utilidad')
    result = _query(f"""INSERT INTO {Config.SCHEMA}.t_estimacion(id_obra,nombre,version,descripcion,factor_indirectos,factor_utilidad,id_empresa)
        SELECT %s,%s,COALESCE((SELECT MAX(version)+1 FROM {Config.SCHEMA}.t_estimacion WHERE id_obra=%s AND id_empresa=%s),1),%s,0,%s,%s
        WHERE EXISTS (SELECT 1 FROM {Config.SCHEMA}.t_obra WHERE id_obra=%s AND id_empresa=%s)
        RETURNING id_estimacion, id_obra""", (data['id_obra'], data['nombre'], data['id_obra'], id_empresa, data.get('descripcion'), factor_utilidad, id_empresa, data['id_obra'], id_empresa), fetchone=True, commit=True)
    if result:
        _query(f"UPDATE {Config.SCHEMA}.t_obra SET estado_estimacion='EN_ESTIMACION' WHERE id_obra=%s AND id_empresa=%s", (result['id_obra'], id_empresa), commit=True)
    return result


def update_estimacion(id_estimacion, data, id_empresa):
    return _query(f"UPDATE {Config.SCHEMA}.t_estimacion SET nombre=COALESCE(%s,nombre), descripcion=COALESCE(%s,descripcion), estado=COALESCE(%s,estado), factor_indirectos=0, factor_utilidad=%s WHERE id_estimacion=%s AND id_empresa=%s RETURNING id_estimacion", (data.get('nombre'), data.get('descripcion'), data.get('estado'), data.get('factor_utilidad'), id_estimacion, id_empresa), fetchone=True, commit=True)


def approve_estimacion(id_estimacion, id_empresa):
    result = _query(f"UPDATE {Config.SCHEMA}.t_estimacion SET estado='APROBADA' WHERE id_estimacion=%s AND id_empresa=%s RETURNING id_obra", (id_estimacion, id_empresa), fetchone=True, commit=True)
    if result:
        _query(f"UPDATE {Config.SCHEMA}.t_obra SET estado_estimacion='APROBADA' WHERE id_obra=%s AND id_empresa=%s", (result['id_obra'], id_empresa), commit=True)
    return result


def add_estimacion_apu(id_estimacion, data, id_empresa):
    return _query(f"""INSERT INTO {Config.SCHEMA}.t_estimacion_analisis_precio_unitario(id_estimacion,id_analisis_precio_unitario,cantidad,orden,observacion)
        SELECT %s,%s,ROUND(%s::numeric,3),%s,%s WHERE EXISTS (SELECT 1 FROM {Config.SCHEMA}.t_estimacion e JOIN {Config.SCHEMA}.t_analisis_precio_unitario a ON a.id_empresa=e.id_empresa WHERE e.id_estimacion=%s AND e.id_empresa=%s AND a.id_analisis_precio_unitario=%s) RETURNING id_estimacion_analisis_precio_unitario""", (id_estimacion, data['id_analisis_precio_unitario'], data['cantidad'], data.get('orden',1), data.get('observacion'), id_estimacion, id_empresa, data['id_analisis_precio_unitario']), fetchone=True, commit=True)


def update_estimacion_apu(det_id, data, id_empresa):
    return _query(f"""UPDATE {Config.SCHEMA}.t_estimacion_analisis_precio_unitario d SET cantidad=COALESCE(ROUND(%s::numeric,3),cantidad), orden=COALESCE(%s,orden), observacion=COALESCE(%s,observacion)
        FROM {Config.SCHEMA}.t_estimacion e WHERE d.id_estimacion_analisis_precio_unitario=%s AND d.id_estimacion=e.id_estimacion AND e.id_empresa=%s RETURNING d.id_estimacion_analisis_precio_unitario""", (data.get('cantidad'), data.get('orden'), data.get('observacion'), det_id, id_empresa), fetchone=True, commit=True)


def delete_estimacion_apu(det_id, id_empresa):
    return _query(f"DELETE FROM {Config.SCHEMA}.t_estimacion_analisis_precio_unitario d USING {Config.SCHEMA}.t_estimacion e WHERE d.id_estimacion_analisis_precio_unitario=%s AND d.id_estimacion=e.id_estimacion AND e.id_empresa=%s", (det_id, id_empresa), commit=True)


def delete_where(table, key, value, id_empresa):
    if table == 't_estimacion_analisis_precio_unitario':
        sql = f"DELETE FROM {Config.SCHEMA}.{table} d USING {Config.SCHEMA}.t_estimacion e WHERE d.{key}=%s AND d.id_estimacion=e.id_estimacion AND e.id_empresa=%s"
    elif table == 't_analisi_precio_unitario_insumo':
        sql = f"DELETE FROM {Config.SCHEMA}.{table} WHERE {key}=%s AND id_empresa=%s"
    else:
        raise ValueError('Entidad no permitida')
    return _query(sql, (value, id_empresa), commit=True)