"""Persistencia CU39. Todas las operaciones reciben la conexión de la unidad local."""
from contextlib import contextmanager
from app.classes.postgres import PostgreSQL
from app.utils.cronograma_errors import CronogramaError


@contextmanager
def sesion(escritura=False):
    db = PostgreSQL()
    try:
        db.create_connection()
        db.conn.rollback()  # create_connection prueba SELECT 1 antes de devolver el cursor
        if escritura:
            db.execute_query("SET LOCAL lock_timeout='5s'")
            db.execute_query("SET LOCAL statement_timeout='30s'")
        if not escritura:
            db.execute_query('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        yield db
        if escritura:
            db.conn.commit()
    except Exception as exc:
        if getattr(exc, 'pgcode', None) in ('55P03', '40001', '40P01'):
            raise CronogramaError('El cronograma está siendo modificado. Recargue e intente nuevamente.', 409) from exc
        if getattr(exc, 'pgcode', None) in ('42P01', '42703'):
            raise CronogramaError('CU39 requiere instalar la migración de cronogramas en esta base.', 503) from exc
        raise
    finally:
        db.close_connection()


def obra(db, id_obra, empresa, bloquear=False):
    row = db.execute_query('''SELECT id_empresa, nombre FROM obras.t_obra
        WHERE id_obra=%s AND (%s IS NULL OR id_empresa=%s)''' + (' FOR SHARE' if bloquear else ''),
        (id_obra, empresa, empresa), fetchone=True)
    return dict(zip(('id_empresa', 'nombre'), row)) if row else None


def listar(db, id_obra):
    rows = db.execute_query('''SELECT id_cronograma,id_obra,nombre,descripcion,fecha_inicio,
        fecha_fin,version,creado_en,actualizado_en FROM obras.t_cronograma
        WHERE id_obra=%s ORDER BY fecha_inicio,id_cronograma''', (id_obra,), fetchall=True)
    fields = ('id_cronograma','id_obra','nombre','descripcion','fecha_inicio','fecha_fin','version','creado_en','actualizado_en')
    return [dict(zip(fields, row)) for row in rows]


def obtener(db, id_obra, id_cronograma, bloquear=False):
    row = db.execute_query('''SELECT id_cronograma,id_obra,nombre,descripcion,fecha_inicio,
        fecha_fin,version,creado_en,actualizado_en FROM obras.t_cronograma
        WHERE id_obra=%s AND id_cronograma=%s''' + (' FOR UPDATE' if bloquear else ''),
        (id_obra,id_cronograma), fetchone=True)
    if not row:
        raise CronogramaError('Cronograma no encontrado en esta obra.', 404)
    fields = ('id_cronograma','id_obra','nombre','descripcion','fecha_inicio','fecha_fin','version','creado_en','actualizado_en')
    crono = dict(zip(fields,row))
    rows = db.execute_query('''SELECT clave,nombre,descripcion,tipo,fecha_inicio,fecha_fin,
        inicio_real,fin_real,avance FROM obras.t_cronograma_actividad
        WHERE id_cronograma=%s ORDER BY orden,clave''',(id_cronograma,),fetchall=True)
    fields = ('clave','nombre','descripcion','tipo','fecha_inicio','fecha_fin','inicio_real','fin_real','avance')
    crono['actividades'] = [dict(zip(fields,row),dependencias=[]) for row in rows]
    by_key = {a['clave']: a for a in crono['actividades']}
    for clave, previa in db.execute_query('''SELECT actividad,predecesora
        FROM obras.t_cronograma_dependencia WHERE id_cronograma=%s ORDER BY actividad,predecesora''',
        (id_cronograma,),fetchall=True):
        by_key[clave]['dependencias'].append(previa)
    return crono


def crear(db, id_obra, datos):
    return db.execute_query('''INSERT INTO obras.t_cronograma
        (id_obra,nombre,descripcion,fecha_inicio,fecha_fin) VALUES (%s,%s,%s,%s,%s)
        RETURNING id_cronograma''', (id_obra,datos.nombre,datos.descripcion,datos.fecha_inicio,datos.fecha_fin),fetchone=True)[0]


def guardar(db, id_cronograma, datos):
    db.execute_query('''UPDATE obras.t_cronograma SET nombre=%s,descripcion=%s,
        fecha_inicio=%s,fecha_fin=%s,version=version+1,actualizado_en=CURRENT_TIMESTAMP
        WHERE id_cronograma=%s''',
        (datos.nombre,datos.descripcion,datos.fecha_inicio,datos.fecha_fin,id_cronograma))


def actividades(db, id_cronograma, items):
    db.execute_query('DELETE FROM obras.t_cronograma_dependencia WHERE id_cronograma=%s',(id_cronograma,))
    db.execute_query('DELETE FROM obras.t_cronograma_actividad WHERE id_cronograma=%s',(id_cronograma,))
    for orden,a in enumerate(items):
        db.execute_query('''INSERT INTO obras.t_cronograma_actividad
            (id_cronograma,clave,nombre,descripcion,tipo,fecha_inicio,fecha_fin,inicio_real,fin_real,avance,orden)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
            (id_cronograma,a.clave,a.nombre,a.descripcion,a.tipo,a.fecha_inicio,a.fecha_fin,a.inicio_real,a.fin_real,a.avance,orden))
    for a in items:
        for previa in a.dependencias:
            db.execute_query('''INSERT INTO obras.t_cronograma_dependencia
                (id_cronograma,actividad,predecesora) VALUES (%s,%s,%s)''',(id_cronograma,a.clave,previa))


def eliminar(db, id_cronograma):
    db.execute_query('DELETE FROM obras.t_cronograma WHERE id_cronograma=%s',(id_cronograma,))


def auditar(db, token, accion, id_obra, id_cronograma, ip):
    db.execute_query('''INSERT INTO obras.t_bitacora
        (id_usuario,modulo,accion,descripcion,ip,estado)
        VALUES (%s,'CRONOGRAMAS',%s,%s,%s,'EXITOSO')''',
        (token['nro_usuario'],accion,f'Obra {id_obra}; cronograma {id_cronograma}',(ip or 'unknown')[:20]))
