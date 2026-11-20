from contextlib import contextmanager
from psycopg2.extras import RealDictCursor
from app.classes.postgres import PostgreSQL


@contextmanager
def conexion():
    db = PostgreSQL()
    db.create_connection()
    try:
        with db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        db.conn.commit()
    finally:
        db.close_connection()


def listar_planes():
    with conexion() as cur:
        cur.execute('SELECT * FROM obras.t_plan_suscripcion ORDER BY orden')
        return [dict(row) for row in cur.fetchall()]


def obtener_usuario(id_usuario):
    with conexion() as cur:
        cur.execute('SELECT u.id_empresa,u.estado,r.nombre_rol FROM obras.t_usuario u LEFT JOIN obras.t_rol r USING(id_rol) WHERE id_usuario = %s', (id_usuario,))
        row = cur.fetchone()
        return dict(row) if row else None


def listar_suscripciones(id_empresa=None):
    with conexion() as cur:
        cur.execute('''
            SELECT e.id_empresa, e.nombre_empresa, s.codigo_plan, p.nombre AS nombre_plan,
                   s.estado, s.fecha_inicio, s.fecha_fin, s.actualizado_en,
                   CASE WHEN s.id_empresa IS NULL THEN 'SIN_PLAN'
                        WHEN s.estado <> 'ACTIVA' THEN s.estado
                        WHEN s.fecha_inicio > (CURRENT_TIMESTAMP AT TIME ZONE 'America/La_Paz')::date THEN 'PROGRAMADA'
                        WHEN s.fecha_fin < (CURRENT_TIMESTAMP AT TIME ZONE 'America/La_Paz')::date THEN 'VENCIDA'
                        ELSE 'ACTIVA' END AS estado_efectivo,
                   (SELECT count(*) FROM obras.t_usuario u WHERE u.id_empresa=e.id_empresa) AS usuarios
                   ,p.limite_usuarios,p.limite_obras,p.consultas_ia_mes,p.nivel_reportes,
                   p.exportar_reportes,p.automatizar_reportes,p.modulos,p.version AS version_plan,
                   COALESCE(c.usuarios,0) AS usuarios_activos,COALESCE(c.obras,0) AS obras_activas,
                   COALESCE(ia.consultas,0) AS consultas_ia_usadas
            FROM obras.t_empresa e
            LEFT JOIN obras.t_suscripcion_empresa s ON s.id_empresa=e.id_empresa
            LEFT JOIN obras.t_plan_suscripcion p ON p.codigo=s.codigo_plan
            LEFT JOIN obras.t_suscripcion_cupo c ON c.id_empresa=e.id_empresa
            LEFT JOIN obras.t_suscripcion_ia_uso ia ON ia.id_empresa=e.id_empresa
                AND ia.mes=date_trunc('month',CURRENT_TIMESTAMP AT TIME ZONE 'America/La_Paz')::date
            WHERE (%s::integer IS NULL OR e.id_empresa=%s)
            ORDER BY e.id_empresa
        ''', (id_empresa, id_empresa))
        return [dict(row) for row in cur.fetchall()]


def asignar(id_empresa, datos, id_actor):
    with conexion() as cur:
        # Serializa cambios de la misma empresa y asegura existencia.
        cur.execute('SELECT id_empresa FROM obras.t_empresa WHERE id_empresa=%s FOR UPDATE', (id_empresa,))
        if not cur.fetchone():
            return False
        cur.execute('SELECT codigo FROM obras.t_plan_suscripcion WHERE codigo=%s FOR SHARE', (datos['codigo_plan'],))
        if not cur.fetchone():
            raise ValueError('El plan seleccionado no existe.')
        values = (id_empresa, datos['codigo_plan'], datos['estado'], datos['fecha_inicio'], datos['fecha_fin'], id_actor)
        cur.execute('''
            INSERT INTO obras.t_suscripcion_empresa
                (id_empresa,codigo_plan,estado,fecha_inicio,fecha_fin,actualizado_por)
            VALUES (%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id_empresa) DO UPDATE SET
                codigo_plan=EXCLUDED.codigo_plan, estado=EXCLUDED.estado,
                fecha_inicio=EXCLUDED.fecha_inicio, fecha_fin=EXCLUDED.fecha_fin,
                actualizado_por=EXCLUDED.actualizado_por, actualizado_en=CURRENT_TIMESTAMP
        ''', values)
        cur.execute('''
            INSERT INTO obras.t_suscripcion_historial
                (id_empresa,codigo_plan,estado,fecha_inicio,fecha_fin,id_actor)
            VALUES (%s,%s,%s,%s,%s,%s)
        ''', values)
        return True


def historial(id_empresa):
    with conexion() as cur:
        cur.execute('''SELECT id,codigo_plan,estado,fecha_inicio,fecha_fin,id_actor,origen,creado_en
                       FROM obras.t_suscripcion_historial WHERE id_empresa=%s
                       ORDER BY creado_en DESC,id DESC LIMIT 50''', (id_empresa,))
        return [dict(row) for row in cur.fetchall()]


def obtener_politica(id_empresa, cur=None):
    if cur is None:
        with conexion() as cursor:
            return obtener_politica(id_empresa, cursor)
    cur.execute('''SELECT s.*, p.limite_usuarios,p.limite_obras,p.consultas_ia_mes,
        p.nivel_reportes,p.exportar_reportes,p.automatizar_reportes,p.modulos,p.version AS version_plan,
        COALESCE(c.usuarios,0) AS usuarios_activos, COALESCE(c.obras,0) AS obras_activas,
        COALESCE(u.consultas,0) AS consultas_ia_usadas
        FROM obras.t_suscripcion_empresa s JOIN obras.t_plan_suscripcion p ON p.codigo=s.codigo_plan
        LEFT JOIN obras.t_suscripcion_cupo c USING(id_empresa)
        LEFT JOIN obras.t_suscripcion_ia_uso u ON u.id_empresa=s.id_empresa
          AND u.mes=date_trunc('month',CURRENT_TIMESTAMP AT TIME ZONE 'America/La_Paz')::date
        WHERE s.id_empresa=%s''', (id_empresa,))
    row = cur.fetchone()
    if not row:
        return None
    return dict(row) if isinstance(row, dict) else dict(zip([c[0] for c in cur.description], row))


def reservar_ia(empresa, mes):
    with conexion() as cur:
        # Revalida vigencia/plan y serializa con un cambio de suscripción.
        cur.execute('SELECT id_empresa FROM obras.t_suscripcion_empresa WHERE id_empresa=%s FOR UPDATE', (empresa,))
        cur.execute('''INSERT INTO obras.t_suscripcion_ia_uso(id_empresa,mes,consultas)
            SELECT s.id_empresa,%s,1 FROM obras.t_suscripcion_empresa s
            JOIN obras.t_plan_suscripcion p ON p.codigo=s.codigo_plan
            WHERE s.id_empresa=%s AND p.consultas_ia_mes>0 AND p.modulos ? 'ia' AND obras.fn_suscripcion_escritura(s.id_empresa)
            ON CONFLICT(id_empresa,mes) DO UPDATE SET consultas=t_suscripcion_ia_uso.consultas+1
            WHERE t_suscripcion_ia_uso.consultas < (SELECT p.consultas_ia_mes
              FROM obras.t_suscripcion_empresa s JOIN obras.t_plan_suscripcion p ON p.codigo=s.codigo_plan
              WHERE s.id_empresa=%s) RETURNING consultas''', (mes,empresa,empresa))
        return cur.fetchone() is not None


def liberar_ia(empresa, mes):
    with conexion() as cur:
        cur.execute('UPDATE obras.t_suscripcion_ia_uso SET consultas=GREATEST(0,consultas-1) WHERE id_empresa=%s AND mes=%s', (empresa,mes))
