"""Diagnóstico del entorno real; no aplica migraciones ni ejecuta la cola."""
import argparse
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg2
from app.services.backups.settings import Settings, BackupError
from app.services.backups import postgres
from app.services.backups import engine
from app.services.backups import crypto, packages
from app.repos import backup_repos as repo
from app.services.backups.settings import ROOT
from app.services import backup_services


def error_category(message):
    text = (message or '').lower()
    categories = (
        ('evidencias', 'evidencias'), ('escritores', 'escritores'),
        ('permisos insuficientes', 'permisos_postgresql'),
        ('versión incompatible', 'version_postgresql'),
        ('objeto/rol/extensión', 'objetos_postgresql'),
        ('autenticación', 'autenticacion'), ('lease', 'lease'),
        ('conectar postgresql', 'conexion_postgresql'),
        ('ruta insegura', 'ruta_evidencia'),
        ('espacio', 'espacio'), ('límite', 'cuota'),
        ('herramienta', 'herramienta_postgresql'),
    )
    return next((category for marker, category in categories if marker in text),
                'sin_error' if not text else 'otro_error')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--environment', required=True)
    parser.add_argument('--preflight', action='store_true',
                        help='Además prepara/verifica el directorio de respaldo configurado.')
    parser.add_argument('--scope', choices=('base_datos', 'sistema_completo'), default='sistema_completo',
                        help='Alcance para verificar disponibilidad de evidencias en el preflight.')
    parser.add_argument('--retry-manual', help='Encola una nueva copia base para un trabajo manual FALLIDO; no ejecuta la cola.')
    parser.add_argument('--verify-job', help='Verifica un trabajo LISTO, sin restaurar PostgreSQL.')
    args = parser.parse_args()
    settings = Settings.load()
    if args.environment != settings.environment or not settings.environment:
        raise BackupError('El entorno no coincide con BACKUP_ENVIRONMENT.')
    result = {'entorno': settings.environment,
              'requisitos': settings.requirements(),
              'requisitos_restauracion': settings.restore_requirements()}
    connections = (
        ('negocio', lambda: postgres.connection(settings)),
        ('control', lambda: psycopg2.connect(settings.control_dsn, connect_timeout=8)),
    )
    for label, connect in connections:
        conn = connect()
        try:
            conn.set_session(readonly=True)
            with conn.cursor() as cur:
                cur.execute("SET LOCAL statement_timeout='15s'")
                cur.execute("SELECT current_database(), current_setting('server_version'), "
                            "pg_database_size(current_database())")
                name, version, size = cur.fetchone()
                data = {'base': name, 'version': version, 'bytes': size}
                if label == 'negocio':
                    cur.execute("SELECT state, wait_event_type, wait_event "
                                "FROM pg_stat_activity WHERE datname=current_database() "
                                "AND application_name='pg_dump'")
                    data['pg_dump'] = [{'estado': state, 'espera_tipo': wait_type, 'espera': wait}
                                       for state, wait_type, wait in cur.fetchall()]
                    cur.execute('SELECT ruta_archivo FROM obras.t_incidencia_evidencia')
                    references = [row[0] for row in cur.fetchall()]
                    evidence_state = {'registros': len(references), 'archivos_ausentes': 0,
                                      'rutas_invalidas': 0}
                    root = settings.release_target or ROOT
                    upload_root = (root/'backend/uploads').resolve()
                    for reference in references:
                        try:
                            target = root/'backend'/packages.evidence_name(reference)
                            if upload_root not in target.resolve().parents or target.is_symlink():
                                evidence_state['rutas_invalidas'] += 1
                            elif not target.is_file():
                                evidence_state['archivos_ausentes'] += 1
                        except BackupError:
                            evidence_state['rutas_invalidas'] += 1
                    data['evidencias'] = evidence_state
                if label == 'control':
                    cur.execute("SELECT tablename FROM pg_tables "
                                "WHERE schemaname='backup_control' ORDER BY tablename")
                    data['tablas'] = [row[0] for row in cur.fetchall()]
                    cur.execute('SELECT mantenimiento, heartbeat FROM '
                                'backup_control.t_backup_control WHERE id=1')
                    row = cur.fetchone()
                    if not row:
                        raise BackupError('Control no inicializado.')
                    data['mantenimiento'] = row[0]
                    data['worker_activo'] = bool(row[1] and
                        (datetime.now(timezone.utc)-row[1]).total_seconds() < 120)
                    cur.execute('SELECT tipo, count(*), count(*) FILTER (WHERE lease_until < now()) '
                                'FROM backup_control.t_backup_escritor GROUP BY tipo')
                    data['escritores'] = [{'tipo': kind, 'cantidad': count, 'vencidos': expired}
                                          for kind, count, expired in cur.fetchall()]
                    cur.execute('SELECT id, estado, etapa, error, solicitud, intentos '
                                'FROM backup_control.t_backup_ejecucion '
                                'ORDER BY created_at DESC LIMIT 10')
                    data['ejecuciones'] = [
                        {'id': str(identifier), 'estado': state, 'etapa': stage,
                         'categoria_error': error_category(error),
                         'alcance': request.get('alcance'), 'intentos': attempts}
                        for identifier, state, stage, error, request, attempts in cur.fetchall()]
                    cur.execute('SELECT estado, operacion, count(*) FROM '
                                'backup_control.t_backup_restauracion GROUP BY estado, operacion')
                    data['restauraciones'] = [{'estado': state, 'operacion': operation, 'cantidad': count}
                                             for state, operation, count in cur.fetchall()]
                    cur.execute('SELECT configuracion, next_run FROM '
                                'backup_control.t_backup_programacion WHERE id=1')
                    row = cur.fetchone()
                    data['programacion'] = {'configuracion': row[0], 'next_run': str(row[1])} if row else None
                result[label] = data
        finally:
            conn.rollback()
            conn.close()
    print(json.dumps(result, ensure_ascii=True), flush=True)
    if args.preflight or args.retry_manual:
        versions = backup_services.preflight(settings)
        print(json.dumps({'preflight': 'OK', 'versiones': versions}), flush=True)
        conn = postgres.connection(settings)
        try:
            conn.set_session(readonly=True)
            with conn.cursor() as cur:
                cur.execute("SET LOCAL statement_timeout='15s'")
                cur.execute('SELECT ruta_archivo FROM obras.t_incidencia_evidencia')
                captured = {'evidencias': [row[0] for row in cur.fetchall()]}
            missing = []
            evidences = engine.evidence_inventory(settings.release_target or ROOT, captured,
                missing=missing if args.scope == 'base_datos' or args.retry_manual else None)
            print(json.dumps({'evidencias_verificadas': len(evidences),
                              'evidencias_ausentes': len(missing)}), flush=True)
        finally:
            conn.rollback()
            conn.close()
    if args.retry_manual:
        previous = repo.get('ejecucion', backup_services.identifier(args.retry_manual))
        if (not previous or previous['estado'] != 'FALLIDO' or previous['origen'] != 'MANUAL'
                or previous['solicitud'].get('alcance') != 'base_datos'):
            raise BackupError('Solo se reintenta un trabajo manual FALLIDO de base de datos.')
        if result['control']['mantenimiento'] or result['control']['restauraciones']:
            raise BackupError('Hay mantenimiento o restauraciones: no encolar el ensayo.')
        from app.services.backups.contracts import BackupRequest
        actor = backup_services.administrator({'nro_usuario': previous['id_usuario']})
        job = backup_services.create(actor, BackupRequest(alcance='base_datos'), 'configured-test-'+str(previous['id']))
        print(json.dumps({'reintento_manual': str(job['id']), 'estado': job['estado']}), flush=True)
    if args.verify_job:
        path, name = backup_services.download(args.verify_job)
        job = repo.get('ejecucion', backup_services.identifier(args.verify_job))
        archive = repo.get('archivo', job['archivo'])
        with tempfile.TemporaryDirectory(prefix='check-', dir=settings.directory/'work') as temporary:
            directory = Path(temporary)
            metadata = crypto.decrypt(path, directory/'package.zip', settings.keys, settings.max_bytes)
            manifest = packages.unpack(directory/'package.zip', directory/'package', settings)
            if (metadata['id'] != manifest['id'] or metadata['key_id'] != manifest['key_id']
                    or manifest != archive['manifiesto']):
                raise BackupError('Ciphertext, manifiesto y catálogo no coinciden.')
            listing = postgres.command(settings, [postgres.tool('pg_restore'), '--list',
                                       str(directory/'package'/'database.dump')])
            if not listing.strip():
                raise BackupError('El dump no contiene un catálogo legible.')
            from app.services.backups.restoration import check_evidence
            missing = manifest.get('evidencias_no_disponibles', [])
            integrity_manifest = dict(manifest)
            if manifest['alcance'] == 'base_datos':
                integrity_manifest['evidencias_no_disponibles'] = []
            check_evidence(settings, directory/'package', integrity_manifest)
            print(json.dumps({'verificacion': 'OK', 'archivo': name, 'bytes': archive['bytes'],
                              'sha256': archive['sha256'], 'alcance': manifest['alcance'],
                              'tablas': len(manifest['inventario_bd']['tablas']),
                              'evidencias': len(manifest['evidencias_sha256']),
                              'evidencias_no_disponibles': len(missing),
                              'pg_restore_list': 'OK', 'restauracion_aplicada': False}), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BackupError as exc:
        print(json.dumps({'error': exc.code, 'detalle': str(exc)}, ensure_ascii=True))
        raise SystemExit(1)
    except Exception as exc:
        print(json.dumps({'error': type(exc).__name__,
                          'detalle': 'Revisar conexion, permisos y configuracion sin compartir secretos.'}))
        raise SystemExit(1)
