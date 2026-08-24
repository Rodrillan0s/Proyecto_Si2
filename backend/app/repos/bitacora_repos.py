import atexit
from threading import Lock

from psycopg2.pool import ThreadedConnectionPool

from app.classes.postgres import PostgreSQL
from app.config import Config


_bitacora_pool = None
_bitacora_pool_lock = Lock()


def _obtener_pool_bitacora():
    global _bitacora_pool
    if _bitacora_pool is None:
        with _bitacora_pool_lock:
            if _bitacora_pool is None:
                _bitacora_pool = ThreadedConnectionPool(
                    1,
                    5,
                    host=Config.DB_HOST,
                    port=Config.DB_PORT,
                    dbname=Config.DB_NAME,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    connect_timeout=5,
                    options="-c statement_timeout=5000",
                )
                atexit.register(_bitacora_pool.closeall)
    return _bitacora_pool


def registrar_evento_bitacora(
    id_usuario,
    modulo,
    accion,
    descripcion,
    ip,
    estado,
    db=None,
):
    created = False
    if db is None:
        db = PostgreSQL()
        db.create_connection()
        created = True

    try:
        query = f"SELECT {Config.SCHEMA}.fn_registrar_bitacora(%s, %s, %s, %s, %s, %s);"
        db.execute_query(
            query,
            (id_usuario, modulo, accion, descripcion, ip, estado),
            commit=True,
        )
    finally:
        if created:
            db.close_connection()


def registrar_bitacora(
    id_usuario,
    modulo,
    accion,
    descripcion,
    ip,
    estado,
    db=None,
):
    return registrar_evento_bitacora(
        id_usuario,
        modulo,
        accion,
        descripcion,
        ip,
        estado,
        db=db,
    )


def obtener_bitacora(fecha=None, id_usuario=None, usuario=None, accion=None, page=1, limit=20):
    pool = _obtener_pool_bitacora()
    conn = pool.getconn()
    db = PostgreSQL()
    db.conn = conn
    db.cur = conn.cursor()

    try:
        filtros = []
        parametros = []

        if fecha is not None:
            filtros.append("b.fecha_accion::date = %s")
            parametros.append(fecha)
        if id_usuario is not None:
            filtros.append("b.id_usuario = %s")
            parametros.append(id_usuario)
        if usuario is not None:
            filtros.append("(p.nombre_completo ILIKE %s OR u.username ILIKE %s)")
            parametros.extend((f"%{usuario}%", f"%{usuario}%"))
        if accion is not None:
            filtros.append("b.accion ILIKE %s")
            parametros.append(f"%{accion}%")

        where = f"WHERE {' AND '.join(filtros)}" if filtros else ""
        offset = (page - 1) * limit

        data_query = f"""
             SELECT b.id_bitacora,
                 b.id_usuario,
                 COALESCE(NULLIF(p.nombre_completo, ''), u.username) AS nombre,
                 b.modulo,
                 b.accion,
                 b.descripcion,
                 b.ip,
                 b.estado,
                 b.fecha_accion,
                 COUNT(*) OVER() AS total
             FROM {Config.SCHEMA}.t_bitacora b
             LEFT JOIN {Config.SCHEMA}.t_usuario u ON u.id_usuario = b.id_usuario
             LEFT JOIN {Config.SCHEMA}.t_persona p ON p.id_persona = u.id_persona
            {where}
             ORDER BY b.fecha_accion DESC NULLS LAST, b.id_bitacora DESC
            LIMIT %s OFFSET %s;
        """
        data_parametros = (*parametros, limit, offset)
        filas = db.execute_query(data_query, data_parametros, fetchall=True) or []
        total = filas[0][9] if filas else 0

        return {
            "rows": [
                {
                    "id_bitacora": fila[0],
                    "id_usuario": fila[1],
                    "nombre": fila[2],
                    "modulo": fila[3],
                    "accion": fila[4],
                    "descripcion": fila[5],
                    "ip": fila[6],
                    "estado": fila[7],
                    "fecha": fila[8].date().isoformat() if fila[8] else None,
                    "hora": fila[8].time().isoformat() if fila[8] else None,
                }
                for fila in filas
            ],
            "total": total,
        }
    finally:
        try:
            db.cur.close()
            conn.rollback()
            pool.putconn(conn)
        except Exception:
            pool.putconn(conn, close=True)
