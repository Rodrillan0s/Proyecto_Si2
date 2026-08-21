# app/repos/prediccion_repos.py
from app.config import Config

def get_contexto_campana(db, id_campana):
    # ── 1. Datos base de la campaña + terreno ─────────────────────────────
    campana_query = f"""
        SELECT
            C.ID_CAMPANA, C.NOMBRE_CAMPANA, C.VARIEDAD, C.FECHA_SIEMBRA,
            C.FECHA_COSECHA, C.ESTADO, C.RENDIMIENTO_ESTIMADO, C.NRO_LOTE,
            T.NOMBRE_SECTOR, T.TAMANO_HECTAREAS, T.ESTADO AS ESTADO_TERRENO
        FROM {Config.SCHEMA}.{Config.T_CAMPANA} C
        JOIN {Config.SCHEMA}.{Config.T_TERRENO} T ON T.NRO_LOTE = C.NRO_LOTE
        WHERE C.ID_CAMPANA = %s
    """
    campana_row = db.execute_query(campana_query, (id_campana,), fetchone=True)

    if not campana_row:
        return None

    campana = {
        "id_campana":           campana_row[0],
        "nombre_campana":       campana_row[1],
        "variedad":             campana_row[2],
        "fecha_siembra":        str(campana_row[3]) if campana_row[3] else None,
        "fecha_cosecha":        str(campana_row[4]) if campana_row[4] else None,
        "estado":               campana_row[5],
        "rendimiento_estimado": float(campana_row[6]) if campana_row[6] else None,
        "nro_lote":             campana_row[7],
        "nombre_sector":        campana_row[8],
        "tamano_hectareas":     float(campana_row[9]) if campana_row[9] else None,
        "estado_terreno":       campana_row[10],
    }

    # ── 2. Historial de campañas anteriores del mismo lote (últimas 5) ────
    historial_query = f"""
        SELECT
            NOMBRE_CAMPANA, VARIEDAD, FECHA_SIEMBRA, FECHA_COSECHA,
            ESTADO, RENDIMIENTO_ESTIMADO, RENDIMIENTO_REAL
        FROM {Config.SCHEMA}.{Config.T_CAMPANA}
        WHERE NRO_LOTE = %s AND ID_CAMPANA != %s
        ORDER BY FECHA_SIEMBRA DESC
        LIMIT 5
    """
    historial_rows = db.execute_query(
        historial_query, (campana["nro_lote"], id_campana), fetchall=True
    )

    historial_lote = []
    if historial_rows:
        for r in historial_rows:
            historial_lote.append({
                "nombre_campana":       r[0],
                "variedad":             r[1],
                "fecha_siembra":        str(r[2]) if r[2] else None,
                "fecha_cosecha":        str(r[3]) if r[3] else None,
                "estado":               r[4],
                "rendimiento_estimado": float(r[5]) if r[5] else None,
                "rendimiento_real":     float(r[6]) if r[6] else None,
            })

    # ── 3. Órdenes de trabajo vinculadas a la campaña ─────────────────────
    ordenes_query = f"""
        SELECT NRO_ORDEN, TIPO_TRABAJO, ESTADO, FECHA_INICIO, FECHA_FIN
        FROM {Config.SCHEMA}.{Config.T_ORDEN}
        WHERE ID_CAMPANA = %s
        ORDER BY FECHA_INICIO
    """
    ordenes_rows = db.execute_query(ordenes_query, (id_campana,), fetchall=True)

    ordenes_trabajo = []
    if ordenes_rows:
        for r in ordenes_rows:
            ordenes_trabajo.append({
                "nro_orden":    r[0],
                "tipo_trabajo": r[1],
                "estado":       r[2],
                "fecha_inicio": str(r[3]) if r[3] else None,
                "fecha_fin":    str(r[4]) if r[4] else None,
            })

    # ── 4. Insumos usados en esas órdenes (bodega), agrupado por producto ─
    insumos_usados = []
    if ordenes_trabajo:
        nro_ordenes = [o["nro_orden"] for o in ordenes_trabajo]
        placeholders = ", ".join(["%s"] * len(nro_ordenes))
        insumos_query = f"""
            SELECT
                B.NOMBRE_PRODUCTO, B.CATEGORIA, B.UNIDAD_MEDIDA,
                SUM(DB.CANT_USADA) AS TOTAL_USADO
            FROM {Config.SCHEMA}.detalle_bodega DB
            JOIN {Config.SCHEMA}.bodega B ON B.ID_PRODUCTO = DB.ID_PRODUCTO
            WHERE DB.NRO_ORDEN IN ({placeholders})
            GROUP BY B.NOMBRE_PRODUCTO, B.CATEGORIA, B.UNIDAD_MEDIDA
            ORDER BY TOTAL_USADO DESC
        """
        insumos_rows = db.execute_query(insumos_query, tuple(nro_ordenes), fetchall=True)

        if insumos_rows:
            for r in insumos_rows:
                insumos_usados.append({
                    "producto":    r[0],
                    "categoria":   r[1],
                    "unidad":      r[2],
                    "total_usado": float(r[3]) if r[3] else 0,
                })

    # ── 5. Calidad histórica del lote (AVG humedad e impurezas) ───────────
    calidad_query = f"""
        SELECT
            AVG(cc2.porcentaje_humedad)   AS avg_humedad,
            AVG(cc2.porcentaje_impurezas) AS avg_impurezas,
            COUNT(*)                      AS total_controles
        FROM {Config.SCHEMA}.control_calidad cc2
        JOIN {Config.SCHEMA}.detalle_venta dv ON dv.id_detalle = cc2.id_detalle
        JOIN {Config.SCHEMA}.transaccion_comercial tc ON tc.nro_transaccion = dv.nro_transaccion
        WHERE tc.id_cliente IN (
            SELECT t.id_usuario
            FROM {Config.SCHEMA}.terreno t
            WHERE t.nro_lote = %s
        )
    """
    calidad_row = db.execute_query(
        calidad_query, (campana["nro_lote"],), fetchone=True
    )

    calidad_historica = {
        "avg_humedad":     round(float(calidad_row[0]), 2) if calidad_row and calidad_row[0] else None,
        "avg_impurezas":   round(float(calidad_row[1]), 2) if calidad_row and calidad_row[1] else None,
        "total_controles": int(calidad_row[2]) if calidad_row and calidad_row[2] else 0,
    }

    return {
        "campana":           campana,
        "historial_lote":    historial_lote,
        "ordenes_trabajo":   ordenes_trabajo,
        "insumos_usados":    insumos_usados,
        "calidad_historica": calidad_historica,
    }