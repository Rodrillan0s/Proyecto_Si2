from app.classes.postgres import PostgreSQL
from app.config import Config


def obtener_usuarios_por_roles(roles: list, id_empresa: int = None):
    """
    Obtiene los usuarios activos de t_usuario filtrados por lista de roles y
    opcionalmente por id_empresa (incluyendo también ADMINISTRADOR global).
    """
    if not roles:
        return []
    db = PostgreSQL()
    db.create_connection()
    try:
        roles_upper = [str(rol).strip().upper() for rol in roles if rol]
        format_strings = ','.join(['%s'] * len(roles_upper))
        params = list(roles_upper)
        filtro_empresa = ""
        if id_empresa is not None:
            filtro_empresa = " AND (u.id_empresa = %s OR UPPER(r.nombre_rol) = 'ADMINISTRADOR')"
            params.append(int(id_empresa))

        query = f"""
            SELECT u.id_usuario, u.nombre_usuario, r.nombre_rol, u.id_empresa
            FROM {Config.SCHEMA}.t_usuario u
            INNER JOIN {Config.SCHEMA}.t_rol r ON u.id_rol = r.id_rol
            WHERE UPPER(r.nombre_rol) IN ({format_strings})
              AND u.estado = 'ACTIVO'
              {filtro_empresa};
        """
        resultados = db.execute_query(query, tuple(params), fetchall=True) or []
        usuarios = []
        for r in resultados:
            usuarios.append({
                "nro_usuario": r[0],
                "nombre_usuario": r[1],
                "nombre_rol": r[2],
                "id_empresa": r[3],
            })
        return usuarios
    finally:
        db.close_connection()


def obtener_usuarios_por_taller(nro_taller: int):
    """
    Compatibilidad con consultas por empresa/taller usando t_usuario.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            SELECT id_usuario, nombre_usuario
            FROM {Config.SCHEMA}.t_usuario
            WHERE id_empresa = %s AND estado = 'ACTIVO';
        """
        resultados = db.execute_query(query, (nro_taller,), fetchall=True) or []
        return [
            {"nro_usuario": r[0], "nombre_usuario": r[1]}
            for r in resultados
        ]
    finally:
        db.close_connection()


def guardar_notificacion_db(
    titulo: str,
    cuerpo: str,
    tipo_referencia: str,
    nro_usuario: int,
    nro_emergencia: int = None,
):
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            INSERT INTO {Config.SCHEMA}.notificacion
            (titulo, cuerpo, tipo_referencia, nro_usuario, nro_emergencia)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id_notificacion, fecha_creacion;
        """
        row = db.execute_query(
            query,
            (titulo, cuerpo, tipo_referencia, int(nro_usuario), nro_emergencia),
            commit=True,
            fetchone=True,
        )
        if row:
            return {
                "id_notificacion": row[0],
                "fecha_creacion": row[1].strftime("%Y-%m-%d %H:%M:%S") if row[1] else None,
            }
        return {"id_notificacion": None, "fecha_creacion": None}
    finally:
        db.close_connection()


def obtener_notificaciones_por_usuario_db(nro_usuario: int):
    """
    Recupera el historial de alertas del usuario ordenado por las más recientes primero.
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            SELECT id_notificacion, titulo, cuerpo, tipo_referencia, leido, fecha_creacion, nro_emergencia
            FROM {Config.SCHEMA}.notificacion
            WHERE nro_usuario = %s
            ORDER BY fecha_creacion DESC, id_notificacion DESC
            LIMIT 100;
        """
        resultados = db.execute_query(query, (int(nro_usuario),), fetchall=True) or []
        alertas = []
        for r in resultados:
            fecha_str = r[5].strftime("%Y-%m-%d %H:%M:%S") if r[5] else None
            tipo_ref = r[3] or "GENERAL"
            alertas.append({
                "id_notificacion": r[0],
                "titulo": r[1],
                "cuerpo": r[2],
                "mensaje": r[2],
                "tipo_referencia": tipo_ref,
                "tipo": tipo_ref,
                "leido": bool(r[4]),
                "fecha_creacion": fecha_str,
                "created_at": fecha_str,
                "nro_emergencia": r[6],
            })
        return alertas
    finally:
        db.close_connection()


def marcar_notificacion_leida_db(id_notificacion: int, nro_usuario: int):
    """
    Modifica el estado de 'leido' a TRUE para una sola alerta (comprobando pertenencia).
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            UPDATE {Config.SCHEMA}.notificacion
            SET leido = TRUE
            WHERE id_notificacion = %s AND nro_usuario = %s;
        """
        filas_afectadas = db.execute_query(
            query,
            (int(id_notificacion), int(nro_usuario)),
            commit=True,
        )
        return (filas_afectadas or 0) > 0
    finally:
        db.close_connection()


def marcar_todas_las_notificaciones_leidas_db(nro_usuario: int):
    """
    Actualiza masivamente todas las alertas de un usuario a leídas (Botón masivo).
    """
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            UPDATE {Config.SCHEMA}.notificacion
            SET leido = TRUE
            WHERE nro_usuario = %s AND leido = FALSE;
        """
        filas_afectadas = db.execute_query(query, (int(nro_usuario),), commit=True)
        return filas_afectadas or 0
    finally:
        db.close_connection()
