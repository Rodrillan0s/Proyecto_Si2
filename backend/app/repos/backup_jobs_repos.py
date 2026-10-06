"""Adaptador de la aplicación a public.backup_jobs; nunca reclama ni ejecuta jobs."""
from datetime import datetime, timedelta, timezone
from uuid import uuid5, NAMESPACE_URL
from app.repos import backup_repos as control_repo
from app.services.backups.settings import BackupError

transaction = control_repo.transaction
one = control_repo.one
json = control_repo.json


def event(job, actor, kind, detail=None, cursor=None):
    # El diario legacy exige UUID; conservar el ID físico en detalle.
    resource = uuid5(NAMESPACE_URL, 'obratec:vm-job:'+str(job)) if job is not None else None
    control_repo.event(resource, actor, kind, dict(detail or {}, job_id=str(job) if job else None), cursor)


def installation():
    with transaction() as cur:
        tables = one(cur, """SELECT to_regclass('public.backup_jobs') AS jobs,
            to_regclass('backup_control.t_backup_vm_request') AS requests""")
        if not tables['jobs']:
            raise BackupError('No se encontró public.backup_jobs; no se crea ni sustituye la cola del daemon.', 'BACKUP_SETUP_REQUIRED', 503)
        grants = one(cur, """SELECT has_schema_privilege(current_user,'public','USAGE') AS schema_usage,
            has_table_privilege(current_user,'public.backup_jobs','SELECT') AS read,
            has_table_privilege(current_user,'public.backup_jobs','INSERT') AS write,
            has_sequence_privilege(current_user,pg_get_serial_sequence('public.backup_jobs','id'),'USAGE') AS sequence""")
        if not all(grants.values()):
            raise BackupError('Conceder SELECT/INSERT en public.backup_jobs y USAGE en su secuencia a la cuenta de aplicación.', 'BACKUP_CONTROL_FORBIDDEN', 503)
        if not tables['requests']:
            raise BackupError('Falta aplicar la migración auxiliar 20261005_backup_vm_integration.sql en el control.', 'BACKUP_SETUP_REQUIRED', 503)
        auxiliary = one(cur, """SELECT
            has_table_privilege(current_user,'backup_control.t_backup_vm_request','SELECT') AS request_read,
            has_table_privilege(current_user,'backup_control.t_backup_vm_request','INSERT') AS request_write,
            has_table_privilege(current_user,'backup_control.t_backup_evento','INSERT') AS audit_write,
            has_sequence_privilege(current_user,pg_get_serial_sequence('backup_control.t_backup_evento','id'),'USAGE') AS audit_sequence""")
        if not all(auxiliary.values()):
            raise BackupError('Revisar permisos de idempotencia y auditoría en backup_control para la cuenta de aplicación.', 'BACKUP_CONTROL_FORBIDDEN', 503)


def get(identifier, cursor=None):
    if cursor is None:
        with transaction() as cur:
            return get(identifier, cur)
    return one(cursor, 'SELECT * FROM public.backup_jobs WHERE id=%s', (identifier,))


def download_installation():
    with transaction() as cur:
        table = one(cur, "SELECT to_regclass('public.backup_download_requests') AS requests")
        if not table['requests']:
            raise BackupError('Falta la tabla de solicitudes de descarga del daemon Oracle.', 'BACKUP_DOWNLOAD_SETUP', 503)
        grants = one(cur, """SELECT
            has_schema_privilege(current_user,'public','USAGE') AS schema_usage,
            has_table_privilege(current_user,'public.backup_download_requests','SELECT') AS read,
            has_table_privilege(current_user,'public.backup_download_requests','INSERT') AS write,
            has_sequence_privilege(current_user,pg_get_serial_sequence('public.backup_download_requests','id'),'USAGE') AS sequence""")
        if not all(grants.values()):
            raise BackupError('Revisar SELECT/INSERT y USAGE de la secuencia de solicitudes de descarga.', 'BACKUP_DOWNLOAD_FORBIDDEN', 503)


def request_download(identifier, actor, validate_source):
    with transaction() as cur:
        # Lock corto de aplicación: no requiere UPDATE sobre las tablas del daemon.
        cur.execute('SELECT pg_advisory_xact_lock(2026100503)')
        source = validate_source(get(identifier, cur))
        row = one(cur, """SELECT * FROM public.backup_download_requests
            WHERE job_id=%s AND solicitado_por=%s AND
            (estado IN ('PENDIENTE','PROCESANDO') OR
             (estado='COMPLETADO' AND par_url IS NOT NULL AND expira_en > now() + interval '5 seconds'))
            ORDER BY id DESC LIMIT 1""", (identifier, actor))
        if row is None:
            row = one(cur, """INSERT INTO public.backup_download_requests(job_id,solicitado_por)
                VALUES(%s,%s) RETURNING *""", (identifier, actor))
            event(identifier, actor, 'VM_DESCARGA_SOLICITADA', {'solicitud_id': str(row['id'])}, cur)
        return row, source


def download_request(identifier, actor):
    with transaction() as cur:
        row = one(cur, """SELECT * FROM public.backup_download_requests
            WHERE id=%s AND solicitado_por=%s""", (identifier, actor))
        return (row, get(row['job_id'], cur)) if row else (None, None)


def queue(actor, identity, origin='MANUAL', cursor=None):
    if cursor is None:
        with transaction() as cur:
            return queue(actor, identity, origin, cur)
    # Idempotencia en tabla auxiliar, sin alterar la cola consumida por la VM.
    cursor.execute('SELECT pg_advisory_xact_lock(2026100501)')
    previous = one(cursor, 'SELECT * FROM backup_control.t_backup_vm_request WHERE identidad=%s', (identity,))
    if previous:
        if previous['id_usuario'] != actor or previous['origen'] != origin:
            raise BackupError('La clave de idempotencia corresponde a otra solicitud.')
        existing = get(previous['job_id'], cursor)
        if not existing:
            raise BackupError('El trabajo de esta clave ya no existe en la cola VM; utilizar una nueva solicitud.', 'BACKUP_JOB_UNAVAILABLE')
        return existing
    state = one(cursor, 'SELECT mantenimiento FROM backup_control.t_backup_control WHERE id=1 FOR UPDATE')
    if not state or state['mantenimiento']:
        raise BackupError('No se pueden encolar copias durante mantenimiento.', 'BACKUP_MAINTENANCE', 503)
    row = one(cursor, """INSERT INTO public.backup_jobs(tipo,origen,estado,solicitado_por)
        VALUES('BACKUP',%s,'PENDIENTE',%s) RETURNING *""", (origin, actor))
    cursor.execute('INSERT INTO backup_control.t_backup_vm_request(identidad,job_id,id_usuario,origen) VALUES(%s,%s,%s,%s)',
                   (identity, row['id'], actor, origin))
    event(row['id'], actor, 'VM_BACKUP_ENCOLADO', {'origen': origin}, cursor)
    return row


def history(page=1, size=20, state=None):
    with transaction() as cur:
        args = [state] if state else []
        clause = "WHERE tipo='BACKUP'" + (' AND estado=%s' if state else '')
        total = one(cur, f'SELECT count(*) AS total FROM public.backup_jobs {clause}', args)['total']
        cur.execute(f'SELECT * FROM public.backup_jobs {clause} ORDER BY fecha_solicitud DESC,id DESC LIMIT %s OFFSET %s',
                    args+[size, (page-1)*size])
        return {'items': [dict(row) for row in cur.fetchall()], 'total': total, 'pagina': page}


def restore_history():
    with transaction() as cur:
        cur.execute("SELECT * FROM public.backup_jobs WHERE tipo='RESTORE' ORDER BY fecha_solicitud DESC LIMIT 20")
        return [dict(row) for row in cur.fetchall()]


def dispatch_schedule(authorize):
    from app.services.backups.contracts import Schedule, next_run
    now = datetime.now(timezone.utc)
    with transaction() as cur:
        row = one(cur, 'SELECT * FROM backup_control.t_backup_programacion WHERE id=1 FOR UPDATE')
        if not row or not row['configuracion']['habilitada'] or row['next_run'] > now:
            return None
        if row['configuracion'].get('alcance') != 'base_datos':
            raise BackupError('Guardar nuevamente la programación legacy con alcance schema obras antes de activarla.')
        config = Schedule.model_validate(row['configuracion'])
        authorize({'nro_usuario': row['id_usuario']})
        occurrence = row['next_run']
        candidate = next_run(config, max(occurrence-timedelta(seconds=1), now-timedelta(days=370)))
        omitted = 0
        while candidate <= now:
            occurrence = candidate
            omitted += 1
            candidate = next_run(config, candidate)
        job = queue(row['id_usuario'], 'schedule:'+occurrence.isoformat(), 'AUTOMATICO', cur)
        cur.execute('UPDATE backup_control.t_backup_programacion SET next_run=%s WHERE id=1', (next_run(config, now),))
        event(job['id'], row['id_usuario'], 'VM_OCURRENCIA_PROGRAMADA',
              {'ocurrencia': occurrence.isoformat(), 'omitidas': max(0, omitted-1)}, cur)
        return job
