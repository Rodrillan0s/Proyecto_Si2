"""Control independiente; sin FK ni pool hacia la base que se restaura."""
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from psycopg2.extensions import parse_dsn
from app.config import Config
from app.services.backups.settings import Settings, BackupError

SCHEMA = 'backup_control.'
TABLES = {'ejecucion', 'archivo', 'restauracion', 'evento', 'programacion', 'control'}
FIELDS = {'estado', 'etapa', 'error', 'archivo', 'finished_at', 'lease_until', 'worker',
          'protegido', 'stage_db', 'stage_dir', 'desafio', 'validada_en', 'aplicar_en',
          'operacion', 'prebackup', 'diario', 'verificado_en', 'eliminado_en', 'remoto'}


def json(value):
    return Json(value)


@contextmanager
def transaction():
    settings = Settings.load()
    if not settings.enabled or not settings.control_dsn:
        raise BackupError('Las copias de respaldo requieren configurar la base de control.', 'BACKUP_SETUP_REQUIRED', 503)
    try:
        options = parse_dsn(settings.control_dsn)
        if not options.get('dbname') or options['dbname'] == Config.DB_NAME:
            raise BackupError('La base de control debe ser distinta de la base de negocio.', 'BACKUP_CONFIG', 503)
        conn = psycopg2.connect(settings.control_dsn, connect_timeout=5)
    except BackupError:
        raise
    except Exception as exc:
        raise BackupError('La base de control no está disponible.', 'BACKUP_CONTROL_UNAVAILABLE', 503) from exc
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SET LOCAL statement_timeout='10s'")
                yield cursor
    except psycopg2.errors.UndefinedTable as exc:
        raise BackupError('Falta aplicar la migración de control de respaldos.', 'BACKUP_SETUP_REQUIRED', 503) from exc
    finally:
        conn.close()


def one(cursor, query, args=()):
    cursor.execute(query, args)
    row = cursor.fetchone()
    return dict(row) if row else None


def get(kind, identifier, cursor=None):
    if kind not in TABLES:
        raise ValueError('Tabla no autorizada.')
    if cursor is None:
        with transaction() as cur:
            return get(kind, identifier, cur)
    return one(cursor, f'SELECT * FROM {SCHEMA}t_backup_{kind} WHERE id=%s', (str(identifier),))


def update(kind, identifier, **fields):
    if kind not in TABLES or not fields or not fields.keys() <= FIELDS:
        raise ValueError('Actualización no autorizada.')
    with transaction() as cur:
        cur.execute(f'UPDATE {SCHEMA}t_backup_{kind} SET '+','.join(key+'=%s' for key in fields)+' WHERE id=%s',
                    tuple(json(value) if key == 'diario' else value for key, value in fields.items())+(str(identifier),))


def event(resource, actor, kind, detail=None, cursor=None):
    if cursor is None:
        with transaction() as cur:
            return event(resource, actor, kind, detail, cur)
    cursor.execute(f'INSERT INTO {SCHEMA}t_backup_evento(recurso,id_usuario,tipo,detalle) VALUES(%s,%s,%s,%s)',
                   (str(resource) if resource else None, actor, kind, json(detail or {})))


def queue(actor, request, identity, origin='MANUAL', protected=False):
    identifier = str(uuid4())
    with transaction() as cur:
        row = one(cur, f'''INSERT INTO {SCHEMA}t_backup_ejecucion
            (id,id_usuario,solicitud,origen,identidad,estado,protegido)
            VALUES(%s,%s,%s,%s,%s,'PENDIENTE',%s)
            ON CONFLICT(identidad) DO UPDATE SET identidad=EXCLUDED.identidad RETURNING *''',
            (identifier, actor, json(request), origin, identity, protected))
        if row['id_usuario'] != actor or row['solicitud'] != request:
            raise BackupError('La clave de idempotencia ya corresponde a otra solicitud.')
        event(row['id'], actor, 'ENCOLADO', {'origen': origin}, cur)
        return row


def history(page=1, size=20, state=None):
    with transaction() as cur:
        args, clause = ([state], 'WHERE estado=%s') if state else ([], '')
        total = one(cur, f'SELECT count(*) AS total FROM {SCHEMA}t_backup_ejecucion {clause}', args)['total']
        cur.execute(f'SELECT * FROM {SCHEMA}t_backup_ejecucion {clause} ORDER BY created_at DESC LIMIT %s OFFSET %s',
                    args+[size, (page-1)*size])
        return {'items': [dict(row) for row in cur.fetchall()], 'total': total, 'pagina': page}


def restore_history():
    with transaction() as cur:
        cur.execute(f'SELECT * FROM {SCHEMA}t_backup_restauracion ORDER BY created_at DESC LIMIT 20')
        return [dict(row) for row in cur.fetchall()]


def register_archive(job, name, digest, size, manifest, remote=None):
    identifier = str(uuid4())
    with transaction() as cur:
        one(cur, f'''INSERT INTO {SCHEMA}t_backup_archivo
          (id,ejecucion,nombre,sha256,bytes,alcance,key_id,manifiesto,remoto,protegido)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id''',
            (identifier, job['id'] if job else None, name, digest, size, manifest['alcance'],
             manifest['key_id'], json(manifest), remote, job['protegido'] if job else False))
        if job:
            missing = len(manifest.get('evidencias_no_disponibles', []))
            stage = (f'Respaldo de base cifrado disponible; {missing} evidencias externas ausentes'
                     if missing else 'Respaldo cifrado disponible')
            cur.execute(f"UPDATE {SCHEMA}t_backup_ejecucion SET archivo=%s,estado='LISTO',etapa=%s,finished_at=now(),lease_until=NULL WHERE id=%s", (identifier, stage, job['id']))
        event(identifier, job['id_usuario'] if job else None, 'ARCHIVO_PUBLICADO', {'sha256': digest}, cur)
    return identifier


def claim(worker):
    with transaction() as cur:
        # Serializar claims, programación y restauración sin locks durante I/O.
        cur.execute('SELECT pg_advisory_xact_lock(2026100403)')
        control = one(cur, f'SELECT * FROM {SCHEMA}t_backup_control WHERE id=1 FOR UPDATE')
        if not control:
            raise BackupError('Control de respaldo sin inicializar.', status=503)
        cur.execute(f'''UPDATE {SCHEMA}t_backup_ejecucion SET estado='FALLIDO',
            error='El worker perdió su lease. Revise el mantenimiento antes de reintentar.',finished_at=now()
            WHERE estado IN ('GENERANDO','VERIFICANDO') AND lease_until<now()''')
        cur.execute(f'''UPDATE {SCHEMA}t_backup_restauracion SET estado='REQUIERE_INTERVENCION',
            error='El worker se interrumpió; revise el diario de recuperación.'
            WHERE worker IS NOT NULL AND lease_until<now() AND estado IN
            ('VALIDANDO','MANTENIMIENTO','APLICANDO')''')
        cur.execute(f'''SELECT 1 FROM {SCHEMA}t_backup_ejecucion WHERE estado IN ('GENERANDO','VERIFICANDO')
            UNION ALL SELECT 1 FROM {SCHEMA}t_backup_restauracion
            WHERE worker IS NOT NULL AND estado IN ('VALIDANDO','VALIDADA','MANTENIMIENTO','APLICANDO') LIMIT 1''')
        if cur.fetchone() or control['mantenimiento']:
            return None
        cur.execute(f'UPDATE {SCHEMA}t_backup_control SET heartbeat=now() WHERE id=1')
        row = one(cur, f'''UPDATE {SCHEMA}t_backup_restauracion SET worker=%s,
            estado=CASE WHEN operacion='APLICAR' THEN 'MANTENIMIENTO' ELSE estado END,
            lease_until=now()+interval '90 seconds' WHERE id=(SELECT id FROM {SCHEMA}t_backup_restauracion
            WHERE worker IS NULL AND (estado='VALIDANDO' OR (estado='VALIDADA' AND aplicar_en IS NOT NULL))
            ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED) RETURNING *''', (str(worker),))
        if row:
            return 'restauracion', row
        row = one(cur, f'''UPDATE {SCHEMA}t_backup_ejecucion SET worker=%s,estado='GENERANDO',
            intentos=intentos+1,lease_until=now()+interval '90 seconds' WHERE id=(SELECT id FROM
            {SCHEMA}t_backup_ejecucion WHERE estado='PENDIENTE' ORDER BY created_at LIMIT 1
            FOR UPDATE SKIP LOCKED) RETURNING *''', (str(worker),))
        return ('ejecucion', row) if row else None


def heartbeat(kind, identifier, worker):
    if kind not in {'ejecucion', 'restauracion'}:
        raise ValueError()
    with transaction() as cur:
        cur.execute(f'''UPDATE {SCHEMA}t_backup_{kind} SET lease_until=now()+interval '90 seconds'
            WHERE id=%s AND worker=%s RETURNING id''', (str(identifier), str(worker)))
        if not cur.fetchone():
            raise BackupError('Se perdió la propiedad del trabajo.', 'BACKUP_LEASE_LOST')
        cur.execute(f'UPDATE {SCHEMA}t_backup_control SET heartbeat=now() WHERE id=1')


def control():
    with transaction() as cur:
        row = one(cur, f'SELECT * FROM {SCHEMA}t_backup_control WHERE id=1')
        if not row:
            raise BackupError('Control no inicializado.', status=503)
        return row


def barrier(owner, enabled, reason=''):
    with transaction() as cur:
        state = one(cur, f'SELECT * FROM {SCHEMA}t_backup_control WHERE id=1 FOR UPDATE')
        if state['mantenimiento'] and str(state['propietario']) != str(owner):
            raise BackupError('Otra operación mantiene el sistema bloqueado.', 'BACKUP_MAINTENANCE')
        cur.execute(f'UPDATE {SCHEMA}t_backup_control SET mantenimiento=%s,propietario=%s,motivo=%s,updated_at=now() WHERE id=1',
                    (enabled, str(owner) if enabled else None, reason if enabled else None))
        event(owner, None, 'MANTENIMIENTO' if enabled else 'MANTENIMIENTO_FINALIZADO', {}, cur)


def enter_writer(kind):
    identifier = str(uuid4())
    with transaction() as cur:
        state = one(cur, f'SELECT mantenimiento FROM {SCHEMA}t_backup_control WHERE id=1 FOR UPDATE')
        if not state or state['mantenimiento']:
            raise BackupError('Sistema en mantenimiento. Vuelve a intentar al finalizar.', 'BACKUP_MAINTENANCE', 503)
        cur.execute(f"INSERT INTO {SCHEMA}t_backup_escritor VALUES(%s,%s,now()+interval '90 seconds')", (identifier, kind))
    return identifier


def renew_writer(identifier):
    with transaction() as cur:
        cur.execute(f"UPDATE {SCHEMA}t_backup_escritor SET lease_until=now()+interval '90 seconds' WHERE id=%s", (identifier,))


def leave_writer(identifier):
    with transaction() as cur:
        cur.execute(f'DELETE FROM {SCHEMA}t_backup_escritor WHERE id=%s', (identifier,))


def active_writers():
    with transaction() as cur:
        # Una expiración es incertidumbre, nunca permiso para fotografiar datos.
        return one(cur, f'SELECT count(*) AS total FROM {SCHEMA}t_backup_escritor')['total']


def epoch(increment=False):
    if not Settings.load().enabled:
        return 0
    with transaction() as cur:
        if increment:
            cur.execute(f'UPDATE {SCHEMA}t_backup_control SET session_epoch=session_epoch+1 WHERE id=1')
        return one(cur, f'SELECT session_epoch FROM {SCHEMA}t_backup_control WHERE id=1')['session_epoch']


def save_schedule(config, actor, due):
    with transaction() as cur:
        row = one(cur, f'''INSERT INTO {SCHEMA}t_backup_programacion(id,configuracion,id_usuario,next_run)
            VALUES(1,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET configuracion=EXCLUDED.configuracion,
            id_usuario=EXCLUDED.id_usuario,next_run=EXCLUDED.next_run,updated_at=now() RETURNING *''',
            (json(config), actor, due))
        event(None, actor, 'PROGRAMACION_ACTUALIZADA', config, cur)
        return row


def due_schedule(now):
    from app.services.backups.contracts import next_run
    with transaction() as cur:
        row = one(cur, f'SELECT * FROM {SCHEMA}t_backup_programacion WHERE id=1 FOR UPDATE')
        if not row or not row['configuracion']['habilitada'] or row['next_run'] > now:
            return None
        occurrence = row['next_run']
        # Recuperar la última ocurrencia vencida, no atribuir el corte actual a meses atrás.
        from datetime import timedelta
        candidate = next_run(row['configuracion'], max(occurrence-timedelta(seconds=1), now-timedelta(days=370)))
        omitted = 0
        while candidate <= now:
            occurrence = candidate
            omitted += 1
            candidate = next_run(row['configuracion'], candidate)
        cur.execute(f'UPDATE {SCHEMA}t_backup_programacion SET next_run=%s WHERE id=1', (next_run(row['configuracion'], now),))
        # La inserción y el avance pertenecen a la misma transacción.
        job = one(cur, f'''INSERT INTO {SCHEMA}t_backup_ejecucion
            (id,id_usuario,solicitud,origen,identidad,estado) VALUES(%s,%s,%s,'AUTOMATICO',%s,'PENDIENTE')
            ON CONFLICT(identidad) DO NOTHING RETURNING *''',
            (str(uuid4()), row['id_usuario'], json({'alcance': row['configuracion']['alcance']}), 'schedule:'+occurrence.isoformat()))
        event(job['id'] if job else None, row['id_usuario'], 'OCURRENCIA_PROGRAMADA',
              {'ocurrencia': occurrence.isoformat(), 'atraso_segundos': max(0, int((now-occurrence).total_seconds())),
               'ocurrencias_intermedias_omitidas': max(0, omitted-1),
               'politica': 'Una ocurrencia recuperada; los períodos intermedios omitidos'}, cur)
        return job


def validate_queue(archive, actor):
    with transaction() as cur:
        row = one(cur, f'''INSERT INTO {SCHEMA}t_backup_restauracion(id,archivo,id_usuario,estado,etapa)
          VALUES(%s,%s,%s,'VALIDANDO','En cola para restaurar a base temporal') RETURNING *''',
                  (str(uuid4()), str(archive), actor))
        event(row['id'], actor, 'VALIDACION_ENCOLADA', {}, cur)
        return row


def confirm_restore(identifier, actor, challenge):
    with transaction() as cur:
        row = one(cur, f'SELECT * FROM {SCHEMA}t_backup_restauracion WHERE id=%s FOR UPDATE', (str(identifier),))
        if not row or row['id_usuario'] != actor or row['estado'] != 'VALIDADA' or row['desafio'] != challenge:
            raise BackupError('La validación o confirmación no corresponde a este actor.')
        if (datetime.now(timezone.utc)-row['validada_en']).total_seconds() > 3600:
            raise BackupError('La validación venció. Vuelve a validar la copia.')
        if row['aplicar_en'] is not None:
            return row
        cur.execute(f"UPDATE {SCHEMA}t_backup_restauracion SET aplicar_en=now(),operacion='APLICAR',worker=NULL,etapa='Aplicación confirmada; en cola' WHERE id=%s", (str(identifier),))
        event(identifier, actor, 'APLICACION_CONFIRMADA', {}, cur)
        return get('restauracion', identifier, cur)


def retention_candidates(days):
    with transaction() as cur:
        cur.execute(f'''SELECT a.* FROM {SCHEMA}t_backup_archivo a WHERE eliminado_en IS NULL
            AND NOT protegido AND created_at<now()-(%s*interval '1 day')
            AND id IS DISTINCT FROM (SELECT id FROM {SCHEMA}t_backup_archivo WHERE verificado_en IS NOT NULL
                AND eliminado_en IS NULL ORDER BY verificado_en DESC LIMIT 1)
            AND NOT EXISTS(SELECT 1 FROM {SCHEMA}t_backup_restauracion r WHERE r.archivo=a.id
                AND r.estado IN ('VALIDANDO','VALIDADA','MANTENIMIENTO','APLICANDO','REQUIERE_INTERVENCION'))''', (days,))
        return [dict(row) for row in cur.fetchall()]


def last_verified():
    with transaction() as cur:
        return one(cur, f'SELECT max(verificado_en) AS fecha FROM {SCHEMA}t_backup_archivo WHERE eliminado_en IS NULL')['fecha']


def interrupted_maintenance():
    with transaction() as cur:
        state = one(cur, f'SELECT * FROM {SCHEMA}t_backup_control WHERE id=1 FOR UPDATE')
        if not state['mantenimiento'] or not state['propietario']:
            return
        cur.execute(f'''UPDATE {SCHEMA}t_backup_restauracion SET estado='REQUIERE_INTERVENCION',
            error='El worker perdió su lease durante mantenimiento. Revisar el diario de recuperación.'
            WHERE id=%s AND worker IS NOT NULL AND lease_until<now()
            AND estado IN ('MANTENIMIENTO','APLICANDO')''', (state['propietario'],))
        cur.execute(f'''UPDATE {SCHEMA}t_backup_ejecucion SET estado='FALLIDO',
            error='Worker interrumpido durante captura; el mantenimiento se conserva para revisión.'
            WHERE id=%s AND worker IS NOT NULL AND lease_until<now() AND estado IN ('GENERANDO','VERIFICANDO')''',
            (state['propietario'],))
