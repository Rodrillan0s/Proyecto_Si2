from contextlib import contextmanager
from psycopg2.extras import RealDictCursor, Json
from app.classes.postgres import PostgreSQL
import json


@contextmanager
def transaccion():
    db=PostgreSQL(); db.create_connection()
    try:
        with db.conn.cursor(cursor_factory=RealDictCursor) as cur: yield cur
        db.conn.commit()
    finally: db.close_connection()


def obtener(cur,codigo,bloquear=False):
    cur.execute('SELECT * FROM obras.t_plan_suscripcion WHERE codigo=%s'+(' FOR UPDATE' if bloquear else ''),(codigo,))
    fila=cur.fetchone()
    return dict(fila) if fila else None


def empresas(cur,codigo):
    cur.execute('''SELECT e.id_empresa,e.nombre_empresa,s.estado,s.fecha_inicio,s.fecha_fin,
        COALESCE(c.usuarios,0) AS usuarios_activos,COALESCE(c.obras,0) AS obras_activas
        FROM obras.t_suscripcion_empresa s JOIN obras.t_empresa e USING(id_empresa)
        LEFT JOIN obras.t_suscripcion_cupo c USING(id_empresa)
        WHERE s.codigo_plan=%s ORDER BY e.id_empresa''',(codigo,))
    return [dict(f) for f in cur.fetchall()]


def guardar(cur,codigo,datos):
    cur.execute('''UPDATE obras.t_plan_suscripcion SET nombre=%s,descripcion=%s,
        modulos=%s,limite_usuarios=%s,limite_obras=%s,consultas_ia_mes=%s,nivel_reportes=%s,
        exportar_reportes=%s,automatizar_reportes=%s,prestaciones=%s,version=version+1,actualizado_en=CURRENT_TIMESTAMP
        WHERE codigo=%s RETURNING *''', (datos['nombre'],datos['descripcion'],Json(datos['modulos']),
        datos['limite_usuarios'],datos['limite_obras'],datos['consultas_ia_mes'],datos['nivel_reportes'],
        datos['exportar_reportes'],datos['automatizar_reportes'],Json(datos['prestaciones']),codigo))
    return dict(cur.fetchone())


def historial_insertar(cur,codigo,actor,antes,despues,afectadas):
    def valor(dato): return Json(dato,dumps=lambda value:json.dumps(value,default=str,ensure_ascii=False))
    cur.execute('''INSERT INTO obras.t_plan_suscripcion_historial(codigo_plan,version,id_actor,antes,despues,empresas_afectadas)
        VALUES (%s,%s,%s,%s,%s,%s)''',(codigo,despues['version'],actor,valor(antes),valor(despues),valor(afectadas)))


def historial(codigo):
    with transaccion() as cur:
        cur.execute('''SELECT id,version,id_actor,antes,despues,empresas_afectadas,creado_en
            FROM obras.t_plan_suscripcion_historial WHERE codigo_plan=%s ORDER BY version DESC LIMIT 50''',(codigo,))
        return [dict(f) for f in cur.fetchall()]
